# app/news_service.py
from datetime import datetime, timedelta, timezone
from dateutil import parser
import logging

from app.news_crawler import fetch_rss_news

def collect_recent_news(days=3):
    all_news = fetch_rss_news()
    logging.info(f"Fetched {len(all_news)} news")
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    filtered_news = []

    for n in all_news:
        pub_dt = _safe_parse_date(n.get('published') or n.get('scraped_at'))
        if pub_dt >= cutoff:
            filtered_news.append(n)

    return filtered_news

def _safe_parse_date(date_str):
    """다양한 날짜 형식을 안전하게 datetime으로 변환"""
    if not date_str:
        return datetime.now(timezone.utc)
    try:
        dt = parser.parse(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)
