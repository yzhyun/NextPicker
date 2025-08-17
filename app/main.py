# app/main.py
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.news_service import collect_recent_news
import logging

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
def api_news(days: int = 3):
    items, summary = collect_recent_news(days=days)
    return JSONResponse({"summary": summary, "items": items})

@app.get("/view")
def collect_news_view(request: Request, days: int = 3):
    news_items, summary = collect_recent_news(days=days)
    return templates.TemplateResponse(
        "news.html",
        {"request": request, "news": news_items, "summary": summary, "days": days},
    )
