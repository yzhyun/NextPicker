# app/main.py
from urllib.request import Request

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from app.news_service import collect_recent_news


app = FastAPI()
templates = Jinja2Templates(directory="templates")
@app.get("/")
def collect_news(days: int = 3):
    news_items = collect_recent_news(days=days)
    return {"count": len(news_items), "news": news_items}

@app.get("/collect-news-view")
def collect_news_view(request: Request, days: int = 3):
    news_items = collect_recent_news(days=days)
    return templates.TemplateResponse("news.html", {"request": request, "news": news_items, "days": days})
