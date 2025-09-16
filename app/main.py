# app/main.py
import logging
import time
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import init_db
from app.news_service import get_recent_news, build_summary
from app.slack_notifier import slack

# API 라우터 import
from app.api import news, feeds, analysis, notifications, health, cleanup

# FastAPI 앱 생성
app = FastAPI(
    title="NextPicker News", 
    version="3.0.0",
    description="AI-powered news aggregation service",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 정적 파일과 템플릿 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# API 라우터 등록
app.include_router(news.router)
app.include_router(feeds.router)
app.include_router(analysis.router)
app.include_router(notifications.router)
app.include_router(health.router)
app.include_router(cleanup.router)

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

# 기존 API 엔드포인트들은 별도 라우터로 이동됨
# 새로운 API는 /api/v1/ 경로를 사용

# 리다이렉트
@app.get("/")
async def root_redirect():
    """루트 경로를 뉴스 페이지로 리다이렉트"""
    return RedirectResponse(url="/news", status_code=307)

@app.get("/view")
async def legacy_view_redirect(days_us: int = 1, days_kr: int = 1):
    """구 버전 URL 호환성"""
    return RedirectResponse(url=f"/news?days_us={days_us}&days_kr={days_kr}", status_code=307)

# 레거시 헬스체크 (호환성 유지)
@app.get("/health")
async def legacy_health_check():
    """레거시 헬스체크 엔드포인트 (호환성 유지)"""
    return {"status": "healthy", "timestamp": time.time()}
