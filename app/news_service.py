# app/news_service.py
from datetime import datetime, timedelta, timezone
from dateutil import parser
import logging

from app.news_crawler import fetch_rss_news
from app.news_normalizer import normalize_item, dedupe

# 미국 RSS
US_FEEDS = [
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
]

# 한국 RSS (2025 기준 정상 주소만)
KR_FEEDS = [
    # 네이버 카테고리
    "https://rss.naver.com/rss/section/100.xml",  # 정치
    "https://rss.naver.com/rss/section/101.xml",  # 경제
    "https://rss.naver.com/rss/section/102.xml",  # 사회
    "https://rss.naver.com/rss/section/103.xml",  # 생활/문화
    "https://rss.naver.com/rss/section/104.xml",  # 세계
    "https://rss.naver.com/rss/section/105.xml",  # IT/과학
    # 구글 뉴스 (한국)
    "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/headlines/section/BUSINESS?hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/headlines/section/SCIENCE?hl=ko&gl=KR&ceid=KR:ko",
]

def _safe_parse_date(date_str):
    if not date_str:
        return None
    try:
        dt = parser.parse(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def collect_recent_news(days=3, disable_date_filter=False):
    """항상 (items, summary_dict) 반환"""
    started_at = datetime.now(timezone.utc)

    us_raw = fetch_rss_news(US_FEEDS, limit_per_feed=30)
    kr_raw = fetch_rss_news(KR_FEEDS, limit_per_feed=30)

    us = [normalize_item(n, "us") for n in us_raw]
    kr = [normalize_item(n, "kr") for n in kr_raw]

    combined = dedupe(us + kr)
    prefilter_count = len(combined)

    if disable_date_filter:
        summary = {
            "generated_at": started_at.isoformat(),
            "days": days,
            "prefilter_total": prefilter_count,
            "after_filter_total": prefilter_count,
            "us_count": len(us),
            "kr_count": len(kr),
            "filtered": False,
        }
        logging.info(f"[NEWS] fetched total: {prefilter_count} (US:{len(us)} / KR:{len(kr)}) no filter")
        return combined, summary

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    filtered = []
    for n in combined:
        pub_dt = _safe_parse_date(n.get("published"))
        if pub_dt and pub_dt >= cutoff:
            filtered.append(n)

    summary = {
        "generated_at": started_at.isoformat(),
        "days": days,
        "prefilter_total": prefilter_count,
        "after_filter_total": len(filtered),
        "us_count": len(us),
        "kr_count": len(kr),
        "filtered": True,
        "cutoff_utc": cutoff.isoformat(),
    }

    logging.info(f"[NEWS] after date filter({days}d): {len(filtered)} "
                 f"(prefilter {prefilter_count}, US:{len(us)} / KR:{len(kr)})")

    return filtered, summary