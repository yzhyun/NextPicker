# app/main.py
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging

from app.news_service import (
    collect_recent_news_us,
    collect_recent_news_kr,
    build_summary,
)

app = FastAPI()

# 정적파일
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)
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

# 구 URL 호환: /view → /news
@app.get("/view")
async def legacy_view_redirect(days_us: int = 3, days_kr: int = 3):
    return RedirectResponse(url=f"/news?days_us={days_us}&days_kr={days_kr}", status_code=307)

# 루트 리다이렉트
@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/news", status_code=307)
