import asyncio
import aiohttp
import feedparser
from datetime import datetime, timezone, timedelta
from hashlib import md5
from typing import List, Dict, Any, Optional
import logging
import calendar
from bs4 import BeautifulSoup
from dateutil import parser as dtparser

from app.config import settings

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

def _hash_id(text: str) -> str:
    return md5(text.encode("utf-8", errors="ignore")).hexdigest()

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)

def _utc_now_str() -> str:
    return _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")

def _struct_time_to_utc(t) -> Optional[datetime]:
    """feedparser의 struct_time을 UTC datetime으로 변환"""
    if not t:
        return None
    try:
        ts = calendar.timegm(t)
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except Exception:
        return None

def _parse_entry_datetime(e: dict, default_tz: timezone) -> datetime:
    """엔트리에서 날짜를 파싱해 tz-aware UTC datetime으로 반환"""
    # 1) 문자열 우선
    raw = e.get("published") or e.get("updated") or e.get("dc:date") or e.get("pubDate")
    if raw:
        try:
            dt = dtparser.parse(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=default_tz)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass

    # 2) struct_time 보조
    dt2 = _struct_time_to_utc(e.get("published_parsed") or e.get("updated_parsed"))
    if dt2:
        return dt2

    # 3) 최후의 보루
    return _utc_now()

async def _fetch_feed_async(session: aiohttp.ClientSession, feed_url: str, default_tz: timezone) -> Dict[str, Any]:
    """단일 피드를 비동기로 가져오기"""
    try:
        async with session.get(feed_url, headers=DEFAULT_HEADERS, timeout=aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT)) as response:
            if response.status == 200:
                content = await response.text()
                parsed = feedparser.parse(content)
                
                feed_info = parsed.get("feed", {}) or {}
                source = (feed_info.get("title") or feed_info.get("link") or feed_url).strip()
                entries = (parsed.get("entries") or [])[:30]  # 최대 30개
                
                items = []
                for e in entries:
                    link = e.get("link")
                    if not link:
                        continue

                    title = (e.get("title") or "").strip()
                    published_dt_utc = _parse_entry_datetime(e, default_tz=default_tz)

                    summary_html = e.get("summary", "") or e.get("content", [{}])[0].get("value", "")
                    summary_text = BeautifulSoup(summary_html, "html.parser").get_text(" ").strip()

                    items.append({
                        "id": _hash_id(link),
                        "title": title,
                        "url": link,
                        "link": link,
                        "source": source,
                        "published": published_dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "summary": summary_text,
                        "summary_text": summary_text,
                        "summary_html": summary_html,
                        "related": [],
                        "scraped_at": _utc_now_str(),
                    })
                
                return {
                    "success": True,
                    "feed_url": feed_url,
                    "items": items,
                    "entries_count": len(items),
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "feed_url": feed_url,
                    "items": [],
                    "entries_count": 0,
                    "error": f"HTTP {response.status}"
                }
                
    except Exception as e:
        logger.error(f"Error fetching {feed_url}: {e}")
        return {
            "success": False,
            "feed_url": feed_url,
            "items": [],
            "entries_count": 0,
            "error": str(e)
        }

async def fetch_rss_news_async(
    feeds: List[str],
    default_tz: timezone = timezone.utc,
    max_concurrent: int = 10
) -> List[Dict[str, Any]]:
    """여러 RSS 피드를 비동기로 병렬 처리"""
    connector = aiohttp.TCPConnector(limit=max_concurrent, limit_per_host=5)
    timeout = aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # 세마포어로 동시 요청 수 제한
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(feed_url: str) -> Dict[str, Any]:
            async with semaphore:
                return await _fetch_feed_async(session, feed_url, default_tz)
        
        # 모든 피드를 병렬로 처리
        tasks = [fetch_with_semaphore(feed_url) for feed_url in feeds]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 수집
        all_items = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed with exception: {result}")
                continue
                
            if result["success"]:
                all_items.extend(result["items"])
                logger.info(f"Successfully fetched {result['entries_count']} items from {result['feed_url']}")
            else:
                logger.warning(f"Failed to fetch {result['feed_url']}: {result['error']}")
        
        return all_items

async def fetch_and_filter_news_async(
    feeds: List[str],
    days: int,
    country_tag: str,
    display_tz: timezone,
    limit_per_feed: int = 30
) -> List[Dict]:
    """뉴스를 가져오고 날짜 필터링"""
    cutoff = _utc_now() - timedelta(days=days)
    
    items = await fetch_rss_news_async(feeds, default_tz=display_tz)
    
    filtered_items = []
    for item in items:
        try:
            pub_dt_utc = datetime.strptime(item["published"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            if pub_dt_utc >= cutoff:
                item["published_dt_utc"] = pub_dt_utc
                item["published_local_str"] = pub_dt_utc.astimezone(display_tz).strftime("%Y-%m-%d %H:%M:%S")
                item["local_tz"] = "KST" if display_tz.key == "Asia/Seoul" else ("ET" if display_tz.key == "America/New_York" else display_tz.key)
                item["country"] = country_tag
                filtered_items.append(item)
        except Exception as e:
            logger.error(f"Error processing item {item.get('id', 'unknown')}: {e}")
            continue
    
    # 날짜순 정렬
    filtered_items.sort(key=lambda x: x["published_dt_utc"], reverse=True)
    return filtered_items
