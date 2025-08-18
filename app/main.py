# app/main.py
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging

from app.news_service import collect_recent_news

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/news")
def api_news(days: float = 1.0, top: int = 30):
    """
    지정 기간(days) 내 기사들을 최신순으로 상위 top개씩 (미국/한국 각각) 반환.
    기존 응답 구조(summary, items)는 그대로 유지.
    """
    items, summary = collect_recent_news(days=days, top=top, per_region=True)
    return JSONResponse({"summary": summary, "items": items})

@app.get("/view")
def collect_news_view(request: Request, days: float = 1.0, top: int = 30):
    """
    템플릿 렌더: 지정 기간 내 최신순 상위 top개씩(미국/한국 각각)을 합쳐서 표시.
    (items는 combined 리스트이므로 템플릿은 기존과 동일하게 렌더)
    """
    news_items, summary = collect_recent_news(days=days, top=top, per_region=True)
    return templates.TemplateResponse(
        "news.html",
        {"request": request, "news": news_items, "summary": summary, "days": days, "top": top},
    )
