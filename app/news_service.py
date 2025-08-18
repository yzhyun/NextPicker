# app/news_service.py
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from heapq import nlargest
import logging

from app.news_crawler import fetch_rss_news

logger = logging.getLogger(__name__)

UTC = timezone.utc
KST = timezone(timedelta(hours=9))

US_FEEDS = [
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/headlines/section/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/headlines/section/SCIENCE?hl=en-US&gl=US&ceid=US:en",
]

KR_FEEDS = [
    "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/headlines/section/BUSINESS?hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/headlines/section/SCIENCE?hl=ko&gl=KR&ceid=KR:ko",
]

def _iso_to_dt(s: str | None, tz: timezone = UTC) -> datetime:
    """'2025-08-18T01:23:45Z' → datetime(tz). 비정상/누락이면 최소값."""
    if not s:
        return datetime.min.replace(tzinfo=tz)
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(tz)
    except Exception:
        return datetime.min.replace(tzinfo=tz)

def _dedupe_by_id(items: list[dict]) -> list[dict]:
    seen, out = set(), []
    for it in items:
        nid = it.get("id")
        if not nid or nid in seen:
            continue
        seen.add(nid)
        out.append(it)
    return out

def _collect_one_region(
    feeds: list[str],
    days: float,
    top: int,
    per_feed_limit: int,
    tz: timezone,
) -> tuple[list[dict], dict]:
    """한 지역: 수집 → dedupe → 기간 필터 → 최신 N개."""
    raw = fetch_rss_news(feeds, limit_per_feed=per_feed_limit)
    deduped = _dedupe_by_id(raw)

    cutoff = datetime.now(tz) - timedelta(days=days)
    filtered = [it for it in deduped if _iso_to_dt(it.get("published"), tz) >= cutoff]

    keyf = lambda it: _iso_to_dt(it.get("published"), tz)
    latest = nlargest(top, filtered, key=keyf)
    latest.sort(key=keyf, reverse=True)

    meta = {
        "collected": len(raw),
        "after_dedupe": len(deduped),
        "after_filter": len(filtered),
        "returned": len(latest),
        "cutoff": cutoff.isoformat(),
    }
    return latest, meta

def collect_recent_news(
    *,
    days: float = 3.0,
    top: int = 30,
    per_region: bool = True,      # 미국/한국 각각 N개
    per_feed_limit: int = 100,    # 피드당 충분히 수집(전역 Top N 안정화)
    tz: timezone = UTC,           # 한국 기준이면 tz=KST
) -> tuple[list[dict], dict]:
    """
    지정 기간(days) 내 기사들을 최신순으로 상위 N개 반환.
    - per_region=True: 미국 N개 + 한국 N개 (합쳐서 최대 2N개)
    - per_region=False: 두 지역 합산 풀에서 전역 기준 N개
    반환: (items, summary)
    """
    us_latest, us_meta = _collect_one_region(US_FEEDS, days, top, per_feed_limit, tz)
    kr_latest, kr_meta = _collect_one_region(KR_FEEDS, days, top, per_feed_limit, tz)

    if per_region:
        combined = _dedupe_by_id(us_latest + kr_latest)  # 이론상 2N, 중복 시 줄 수 있음
    else:
        pool = _dedupe_by_id(us_latest + kr_latest)
        keyf = lambda it: _iso_to_dt(it.get("published"), tz)
        combined = nlargest(top, pool, key=keyf)
        combined.sort(key=keyf, reverse=True)

    summary = {
        "params": {
            "days": days,
            "top": top,
            "per_region": per_region,
            "per_feed_limit": per_feed_limit,
            "tz": "KST" if tz is KST else "UTC",
        },
        "by_region": {"US": us_meta, "KR": kr_meta},
        "returned_total": len(combined),
    }
    return combined, summary
