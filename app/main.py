# app/main.py
import logging
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import init_db
from app.news_service import (
    get_recent_news,
    get_news_by_section,
    collect_news,
    refresh_all_feeds,
    build_summary
)
from app.rss_feeds import get_all_feeds
from app.slack_notifier import slack

# FastAPI 앱 생성
app = FastAPI(title="NextPicker News", version="3.0.0")

# 정적 파일과 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행되는 함수"""
    logger.info("Starting NextPicker News server...")
    
    # 데이터베이스 초기화
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        slack.notify_error(str(e), "데이터베이스 초기화 실패")
    
    # 슬랙 알림: 서버 시작
    slack.notify_server_start()
    
    logger.info("Server ready - use /api/refresh to collect news manually")

# 메인 뉴스 페이지
@app.get("/news", response_class=HTMLResponse)
async def news_home(
    request: Request,
    days_us: int = 1,
    days_kr: int = 1,
    limit: int = 30,
):
    """메인 뉴스 페이지 - 미국과 한국 뉴스를 모두 표시"""
    try:
        # 데이터베이스에서 뉴스 가져오기
        news_us = get_recent_news('US', days=days_us, limit=limit)
        news_kr = get_recent_news('KR', days=days_kr, limit=limit)
        
        # 요약 정보 생성
        summary = build_summary(news_us, news_kr, days_us, days_kr)
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request, 
                "news_us": news_us, 
                "news_kr": news_kr, 
                "summary": summary
            },
        )
    except Exception as e:
        logger.error(f"Error loading news page: {e}")
        slack.notify_error(str(e), "뉴스 페이지 로딩 실패")
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request, 
                "news_us": [], 
                "news_kr": [], 
                "summary": {"total": 0, "us": 0, "kr": 0, "error": str(e)}
            },
        )

# 미국 뉴스만 보기
@app.get("/news/us", response_class=HTMLResponse)
async def news_us_page(request: Request, days: int = 1, limit: int = 30):
    """미국 뉴스만 표시하는 페이지"""
    try:
        news_us = get_recent_news('US', days=days, limit=limit)
        summary = {"total": len(news_us), "us": len(news_us), "kr": 0}
        
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "news_us": news_us, "news_kr": [], "summary": summary},
        )
    except Exception as e:
        logger.error(f"Error loading US news: {e}")
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "news_us": [], "news_kr": [], "summary": {"total": 0, "us": 0, "kr": 0}},
        )

# 한국 뉴스만 보기
@app.get("/news/kr", response_class=HTMLResponse)
async def news_kr_page(request: Request, days: int = 1, limit: int = 30):
    """한국 뉴스만 표시하는 페이지"""
    try:
        news_kr = get_recent_news('KR', days=days, limit=limit)
        summary = {"total": len(news_kr), "us": 0, "kr": len(news_kr)}
        
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "news_us": [], "news_kr": news_kr, "summary": summary},
        )
    except Exception as e:
        logger.error(f"Error loading KR news: {e}")
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "news_us": [], "news_kr": [], "summary": {"total": 0, "us": 0, "kr": 0}},
        )

# API 엔드포인트들
@app.post("/api/refresh")
async def trigger_refresh():
    """뉴스 피드를 새로고침합니다"""
    try:
        # 동기적으로 피드 새로고침 실행
        result = refresh_all_feeds()
        
        return {
            "message": "뉴스 새로고침이 완료되었습니다.",
            "status": "completed",
            "result": result
        }
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        slack.notify_error(str(e), "뉴스 새로고침 실패")
        return {"error": str(e)}

@app.get("/api/news")
async def api_news(days_us: int = 1, days_kr: int = 1, limit: int = 30):
    """JSON 형태로 뉴스 데이터를 반환합니다"""
    try:
        news_us = get_recent_news('US', days=days_us, limit=limit)
        news_kr = get_recent_news('KR', days=days_kr, limit=limit)
        summary = build_summary(news_us, news_kr, days_us, days_kr)
        
        return {
            "summary": summary,
            "news_us": news_us,
            "news_kr": news_kr
        }
    except Exception as e:
        logger.error(f"API error: {e}")
        return {"error": str(e)}

@app.get("/api/news/section/{section}")
async def api_news_by_section(section: str, country: str = None, days: int = 1, limit: int = 50):
    """특정 섹션의 뉴스를 JSON 형태로 반환합니다"""
    try:
        news = get_news_by_section(section, country, days, limit)
        
        return {
            "section": section,
            "country": country,
            "days": days,
            "count": len(news),
            "news": news
        }
    except Exception as e:
        logger.error(f"Section API error: {e}")
        return {"error": str(e)}

@app.get("/api/feeds")
async def api_feeds():
    """설정된 RSS 피드 정보를 반환합니다"""
    try:
        feeds = get_all_feeds()
        return feeds
    except Exception as e:
        logger.error(f"Feeds API error: {e}")
        return {"error": str(e)}

@app.get("/api/status")
async def get_status():
    """서버 상태를 확인합니다"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "message": "NextPicker News is running"
    }

# 리다이렉트
@app.get("/")
async def root_redirect():
    """루트 경로를 뉴스 페이지로 리다이렉트"""
    return RedirectResponse(url="/news", status_code=307)

@app.get("/view")
async def legacy_view_redirect(days_us: int = 1, days_kr: int = 1):
    """구 버전 URL 호환성"""
    return RedirectResponse(url=f"/news?days_us={days_us}&days_kr={days_kr}", status_code=307)

# 헬스체크
@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    return {"status": "healthy", "timestamp": time.time()}
