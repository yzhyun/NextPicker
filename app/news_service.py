# app/news_service.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Dict
from zoneinfo import ZoneInfo
import asyncio
import logging

from app.config import settings
from app.cache import cached
from app.async_news_crawler import fetch_and_filter_news_async
from app.news_repository import NewsRepository
from app.db.database import get_db

logger = logging.getLogger(__name__)

# -----------------------
# 피드
# -----------------------
US_FEEDS = [
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",

    # Google News - 미국
    "https://news.google.com/rss?hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en&gl=US&ceid=US:en",
]

KR_FEEDS = [
    "https://www.hankyung.com/feed/it",
    "https://www.hankyung.com/feed/economy",


    # Google News - 한국
    "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=ko&gl=KR&ceid=KR:ko",
]


# -----------------------
# 타임존/포맷
# -----------------------
KST = ZoneInfo("Asia/Seoul")
ET  = ZoneInfo("America/New_York")
ISO_Z_FMT = "%Y-%m-%dT%H:%M:%SZ"  # fetch_rss_news가 반환하는 UTC ISO-Z

def _cutoff_utc(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)

def _parse_utc_iso_z(s: str) -> datetime:
    return datetime.strptime(s, ISO_Z_FMT).replace(tzinfo=timezone.utc)

def _fmt_local(dt_utc: datetime, tz: ZoneInfo, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return dt_utc.astimezone(tz).strftime(fmt)

def _tz_label(tz: ZoneInfo) -> str:
    return "KST" if tz.key == "Asia/Seoul" else ("ET" if tz.key == "America/New_York" else tz.key)

# -----------------------
# 핵심 수집기 (UTC 비교 + 로컬표시) - 레거시 함수 (호환성용)
# -----------------------
def _collect(
    feeds: List[str],
    display_tz: ZoneInfo,
    days: int,
    country_tag: str,
    limit_per_feed: int = 30
) -> List[Dict]:
    # 이 함수는 레거시 호환성을 위해 유지하지만 실제로는 사용하지 않음
    logger.warning("_collect function is deprecated, use _collect_fresh_news functions instead")
    return []

# -----------------------
# 캐시된 뉴스 수집 (데이터베이스 우선)
# -----------------------
@cached(ttl=300)  # 5분 캐시
def collect_recent_news_kr(days: int = 3, limit_per_feed: int = 30) -> List[Dict]:
    """한국 뉴스 수집 (실시간 수집)"""
    logger.info("Fetching fresh KR news from feeds")
    return _collect_fresh_news_kr(days, limit_per_feed)

@cached(ttl=300)  # 5분 캐시
def collect_recent_news_us(days: int = 3, limit_per_feed: int = 30) -> List[Dict]:
    """미국 뉴스 수집 (실시간 수집)"""
    logger.info("Fetching fresh US news from feeds")
    return _collect_fresh_news_us(days, limit_per_feed)

def _collect_fresh_news_kr(days: int, limit_per_feed: int) -> List[Dict]:
    """한국 뉴스 실시간 수집"""
    try:
        # 기존 이벤트 루프가 있는지 확인
        try:
            loop = asyncio.get_running_loop()
            # 이미 실행 중인 루프가 있으면 새 스레드에서 실행
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, fetch_and_filter_news_async(
                    settings.KR_FEEDS, days, 'kr', KST, limit_per_feed
                ))
                articles = future.result()
        except RuntimeError:
            # 실행 중인 루프가 없으면 직접 실행
            articles = asyncio.run(fetch_and_filter_news_async(
                settings.KR_FEEDS, days, 'kr', KST, limit_per_feed
            ))
        
        return articles
    except Exception as e:
        logger.error(f"Error collecting KR news: {e}")
        return []

def _collect_fresh_news_us(days: int, limit_per_feed: int) -> List[Dict]:
    """미국 뉴스 실시간 수집"""
    try:
        # 기존 이벤트 루프가 있는지 확인
        try:
            loop = asyncio.get_running_loop()
            # 이미 실행 중인 루프가 있으면 새 스레드에서 실행
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, fetch_and_filter_news_async(
                    settings.US_FEEDS, days, 'us', ET, limit_per_feed
                ))
                articles = future.result()
        except RuntimeError:
            # 실행 중인 루프가 없으면 직접 실행
            articles = asyncio.run(fetch_and_filter_news_async(
                settings.US_FEEDS, days, 'us', ET, limit_per_feed
            ))
        
        return articles
    except Exception as e:
        logger.error(f"Error collecting US news: {e}")
        return []

# -----------------------
# 상단 요약
# -----------------------
def build_summary(us_list: List[Dict], kr_list: List[Dict], days_us: int = 3, days_kr: int = 3) -> Dict:
    now_us = datetime.now(ET)
    now_kr = datetime.now(KST)
    return {
        "total": len(us_list) + len(kr_list),
        "us": len(us_list),
        "kr": len(kr_list),
        "range_us": f"{(now_us - timedelta(days=days_us)):%Y-%m-%d %H:%M} ~ {now_us:%Y-%m-%d %H:%M} (ET)",
        "range_kr": f"{(now_kr - timedelta(days=days_kr)):%Y-%m-%d %H:%M} ~ {now_kr:%Y-%m-%d %H:%M} (KST)",
    }

# -----------------------
# 백그라운드 작업
# -----------------------
def refresh_all_feeds():
    """모든 피드를 백그라운드에서 새로고침"""
    try:
        logger.info("Starting background feed refresh")
        
        # 한국 뉴스 수집
        kr_articles = _collect_fresh_news_kr(days=7, limit_per_feed=50)
        
        # 미국 뉴스 수집
        us_articles = _collect_fresh_news_us(days=7, limit_per_feed=50)
        
        logger.info(f"Background refresh completed: {len(kr_articles)} KR, {len(us_articles)} US articles")
        
        # 오래된 기사 정리
        db = next(get_db())
        repo = NewsRepository(db)
        cleaned = repo.cleanup_old_articles(days=30)
        logger.info(f"Cleaned up {cleaned} old articles")
        
    except Exception as e:
        logger.error(f"Error in background refresh: {e}")

def get_feed_status() -> List[Dict]:
    """피드 상태 정보 반환"""
    try:
        db = next(get_db())
        repo = NewsRepository(db)
        return repo.get_feed_status()
    except Exception as e:
        logger.error(f"Error getting feed status: {e}")
        return []
