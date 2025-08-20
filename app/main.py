# app/main.py
from __future__ import annotations

from fastapi import FastAPI, Request, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import logging
import threading
import time

from app.news_service import (
    collect_recent_news_us,
    collect_recent_news_kr,
    build_summary,
    refresh_all_feeds,
    get_feed_status,
)
from app.db.database import engine, get_db
from app.db.models import Base

app = FastAPI(title="NextPicker News", version="2.0.0")

# 정적파일
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 데이터베이스 초기화
@app.on_event("startup")
async def startup_event():
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # 백그라운드에서 초기 데이터 수집
    def initial_refresh():
        time.sleep(2)  # 서버 시작 후 2초 대기
        refresh_all_feeds()
    
    thread = threading.Thread(target=initial_refresh, daemon=True)
    thread.start()
    logger.info("Background refresh thread started")

# /news (US/KR 분리 페이지)
@app.get("/news", response_class=HTMLResponse)
async def news_home(
    request: Request,
    days_us: int = 3,
    days_kr: int = 3,
    limit: int = 30,
):
    news_us = collect_recent_news_us(days=days_us, limit_per_feed=limit)
    news_kr = collect_recent_news_kr(days=days_kr, limit_per_feed=limit)
    summary = build_summary(news_us, news_kr, days_us=days_us, days_kr=days_kr)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "news_us": news_us, "news_kr": news_kr, "summary": summary},
    )

# /news/us (미국만)
@app.get("/news/us", response_class=HTMLResponse)
async def news_us_page(request: Request, days: int = 3, limit: int = 30):
    news_us = collect_recent_news_us(days=days, limit_per_feed=limit)
    summary = {"total": len(news_us), "us": len(news_us), "kr": 0,
               "range_us": "", "range_kr": ""}
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "news_us": news_us, "news_kr": [], "summary": summary},
    )

# /news/kr (한국만)
@app.get("/news/kr", response_class=HTMLResponse)
async def news_kr_page(request: Request, days: int = 3, limit: int = 30):
    news_kr = collect_recent_news_kr(days=days, limit_per_feed=limit)
    summary = {"total": len(news_kr), "us": 0, "kr": len(news_kr),
               "range_us": "", "range_kr": ""}
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "news_us": [], "news_kr": news_kr, "summary": summary},
    )

# /api/refresh (백그라운드 새로고침)
@app.post("/api/refresh")
async def trigger_refresh(background_tasks: BackgroundTasks):
    background_tasks.add_task(refresh_all_feeds)
    return {"message": "Refresh started in background"}

# /api/status (피드 상태 모니터링)
@app.get("/api/status")
async def get_status():
    feed_status = get_feed_status()
    return {
        "feed_status": feed_status,
        "total_feeds": len(feed_status),
        "healthy_feeds": len([f for f in feed_status if f.get("last_success")]),
        "timestamp": time.time()
    }

# /api/news (JSON API)
@app.get("/api/news")
async def api_news(
    days_us: int = 3,
    days_kr: int = 3,
    limit: int = 30,
    country: str = None
):
    if country == "us":
        news_us = collect_recent_news_us(days=days_us, limit_per_feed=limit)
        news_kr = []
    elif country == "kr":
        news_us = []
        news_kr = collect_recent_news_kr(days=days_kr, limit_per_feed=limit)
    else:
        news_us = collect_recent_news_us(days=days_us, limit_per_feed=limit)
        news_kr = collect_recent_news_kr(days=days_kr, limit_per_feed=limit)
    
    summary = build_summary(news_us, news_kr, days_us=days_us, days_kr=days_kr)
    
    return {
        "summary": summary,
        "news_us": news_us,
        "news_kr": news_kr
    }

# 구 URL 호환: /view → /news
@app.get("/view")
async def legacy_view_redirect(days_us: int = 3, days_kr: int = 3):
    return RedirectResponse(url=f"/news?days_us={days_us}&days_kr={days_kr}", status_code=307)

# 루트 리다이렉트
@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/news", status_code=307)

# 헬스체크
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

# 테스트 엔드포인트
@app.get("/test")
async def test_endpoint():
    try:
        kr_news = collect_recent_news_kr(days=1, limit_per_feed=5)
        us_news = collect_recent_news_us(days=1, limit_per_feed=5)
        
        return {
            "kr_count": len(kr_news),
            "us_count": len(us_news),
            "kr_sample": kr_news[0] if kr_news else None,
            "us_sample": us_news[0] if us_news else None
        }
    except Exception as e:
        return {"error": str(e)}
