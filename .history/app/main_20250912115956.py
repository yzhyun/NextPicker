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
from app.api import news, feeds, analysis, notifications, health

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

@app.get("/api/analysis/us-news")
async def api_analysis_us_news(days: int = 1, limit: int = 50):
    """AI 분석용 미국 뉴스 데이터를 TSV 형식으로 반환합니다"""
    try:
        from sqlalchemy import text
        from app.database import get_db
        
        db = next(get_db())
        try:
            # PostgreSQL용 쿼리 (배포 환경용)
            query = text(f"""
                SELECT 
                    title || E'\t' ||
                    url || E'\t' ||
                    source || E'\t' ||
                    published || E'\t' ||
                    COALESCE(summary, '') || E'\t' ||
                    COALESCE(section, 'general') || E'\t' ||
                    country AS tsv_row
                FROM news_articles 
                WHERE country = 'US' 
                AND published >= now() - interval '{days} days'
                ORDER BY published DESC 
                LIMIT {limit}
            """)
            
            result = db.execute(query)
            rows = result.fetchall()
            
            # TSV 데이터 생성
            tsv_data = []
            for row in rows:
                tsv_data.append(row[0])  # tsv_row 컬럼
            
            return {
                "count": len(tsv_data),
                "days": days,
                "format": "tsv",
                "data": tsv_data
            }
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Analysis API error: {e}")
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



@app.post("/api/slack/economy-politics-notification")
async def send_economy_politics_notification():
    """경제, 정치 기사로 한국과 미국 기사 각각 20개씩 Slack으로 전송합니다"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import or_
        from app.database import SessionLocal, NewsArticle
        
        # 오늘 날짜 기준으로 최근 1일간 뉴스 가져오기
        cutoff_date = datetime.utcnow() - timedelta(days=1)
        
        db = SessionLocal()
        try:
            # 경제, 정치 기사 필터링 조건
            economy_politics_filter = or_(
                NewsArticle.section.in_(['business', 'economy', 'politics', 'finance']),
                NewsArticle.title.ilike('%경제%'),
                NewsArticle.title.ilike('%정치%'),
                NewsArticle.title.ilike('%금융%'),
                NewsArticle.title.ilike('%투자%'),
                NewsArticle.title.ilike('%주식%'),
                NewsArticle.title.ilike('%부동산%'),
                NewsArticle.title.ilike('%기업%'),
                NewsArticle.title.ilike('%정부%'),
                NewsArticle.title.ilike('%의회%'),
                NewsArticle.title.ilike('%대통령%'),
                NewsArticle.title.ilike('%총리%'),
                NewsArticle.title.ilike('%장관%'),
                NewsArticle.title.ilike('%economy%'),
                NewsArticle.title.ilike('%politics%'),
                NewsArticle.title.ilike('%business%'),
                NewsArticle.title.ilike('%finance%'),
                NewsArticle.title.ilike('%government%'),
                NewsArticle.title.ilike('%congress%'),
                NewsArticle.title.ilike('%senate%'),
                NewsArticle.title.ilike('%president%'),
                NewsArticle.title.ilike('%federal%'),
                NewsArticle.title.ilike('%market%'),
                NewsArticle.title.ilike('%stock%'),
                NewsArticle.title.ilike('%investment%')
            )
            
            # 한국 경제, 정치 기사 20개
            kr_articles = db.query(NewsArticle).filter(
                NewsArticle.country == 'KR',
                NewsArticle.published >= cutoff_date,
                economy_politics_filter
            ).order_by(NewsArticle.published.desc()).limit(20).all()
            
            # 미국 경제, 정치 기사 20개
            us_articles = db.query(NewsArticle).filter(
                NewsArticle.country == 'US',
                NewsArticle.published >= cutoff_date,
                economy_politics_filter
            ).order_by(NewsArticle.published.desc()).limit(20).all()
            
            # Slack 메시지 구성
            message = "📊 *경제·정치 뉴스 요약*\n\n"
            
            message += f"🇰🇷 *한국 경제·정치 기사 ({len(kr_articles)}개)*\n"
            for i, article in enumerate(kr_articles, 1):
                section_info = f"[{article.section}]" if article.section else ""
                message += f"{i}. {section_info} <{article.url}|{article.title[:45]}...>\n"
            
            message += f"\n🇺🇸 *미국 경제·정치 기사 ({len(us_articles)}개)*\n"
            for i, article in enumerate(us_articles, 1):
                section_info = f"[{article.section}]" if article.section else ""
                message += f"{i}. {section_info} <{article.url}|{article.title[:45]}...>\n"
            
            message += f"\n🔗 <https://lumina-next-picker.vercel.app/news|전체 뉴스 보기>"
            
            # Slack 알림 전송
            slack.send_message(message)
            
            return {
                "message": "경제·정치 뉴스 알림이 전송되었습니다.",
                "status": "sent",
                "result": {
                    "KR": len(kr_articles),
                    "US": len(us_articles),
                    "total": len(kr_articles) + len(us_articles)
                }
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Economy politics notification error: {e}")
        slack.notify_error(str(e), "경제·정치 뉴스 알림 전송 실패")
        return {"error": str(e)}

@app.get("/api/news/economy-politics")
async def get_economy_politics_news(days: int = 1, limit: int = 20):
    """경제, 정치 기사를 JSON 형태로 반환합니다"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import or_
        from app.database import SessionLocal, NewsArticle
        
        # 날짜 기준으로 뉴스 가져오기
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        db = SessionLocal()
        try:
            # 경제, 정치 기사 필터링 조건
            economy_politics_filter = or_(
                NewsArticle.section.in_(['business', 'economy', 'politics', 'finance']),
                NewsArticle.title.ilike('%경제%'),
                NewsArticle.title.ilike('%정치%'),
                NewsArticle.title.ilike('%금융%'),
                NewsArticle.title.ilike('%투자%'),
                NewsArticle.title.ilike('%주식%'),
                NewsArticle.title.ilike('%부동산%'),
                NewsArticle.title.ilike('%기업%'),
                NewsArticle.title.ilike('%정부%'),
                NewsArticle.title.ilike('%의회%'),
                NewsArticle.title.ilike('%대통령%'),
                NewsArticle.title.ilike('%총리%'),
                NewsArticle.title.ilike('%장관%'),
                NewsArticle.title.ilike('%economy%'),
                NewsArticle.title.ilike('%politics%'),
                NewsArticle.title.ilike('%business%'),
                NewsArticle.title.ilike('%finance%'),
                NewsArticle.title.ilike('%government%'),
                NewsArticle.title.ilike('%congress%'),
                NewsArticle.title.ilike('%senate%'),
                NewsArticle.title.ilike('%president%'),
                NewsArticle.title.ilike('%federal%'),
                NewsArticle.title.ilike('%market%'),
                NewsArticle.title.ilike('%stock%'),
                NewsArticle.title.ilike('%investment%')
            )
            
            # 한국 경제, 정치 기사
            kr_articles = db.query(NewsArticle).filter(
                NewsArticle.country == 'KR',
                NewsArticle.published >= cutoff_date,
                economy_politics_filter
            ).order_by(NewsArticle.published.desc()).limit(limit).all()
            
            # 미국 경제, 정치 기사
            us_articles = db.query(NewsArticle).filter(
                NewsArticle.country == 'US',
                NewsArticle.published >= cutoff_date,
                economy_politics_filter
            ).order_by(NewsArticle.published.desc()).limit(limit).all()
            
            # JSON 형태로 변환
            def article_to_dict(article):
                return {
                    "id": article.id,
                    "title": article.title,
                    "url": article.url,
                    "source": article.source,
                    "published": article.published.isoformat() if article.published else None,
                    "summary": article.summary,
                    "section": article.section,
                    "country": article.country,
                    "created_at": article.created_at.isoformat() if article.created_at else None
                }
            
            return {
                "days": days,
                "limit": limit,
                "summary": {
                    "KR": len(kr_articles),
                    "US": len(us_articles),
                    "total": len(kr_articles) + len(us_articles)
                },
                "news_kr": [article_to_dict(article) for article in kr_articles],
                "news_us": [article_to_dict(article) for article in us_articles]
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Economy politics news API error: {e}")
        return {"error": str(e)}

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
