# app/news_service.py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Dict
from zoneinfo import ZoneInfo

from app.news_crawler import fetch_rss_news

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
# 핵심 수집기 (UTC 비교 + 로컬표시)
# -----------------------
def _collect(
    feeds: List[str],
    display_tz: ZoneInfo,
    days: int,
    country_tag: str,
    limit_per_feed: int = 30
) -> List[Dict]:
    # ★ 중요: KR/US별 기본 타임존을 fetch 단계에 전달
    items = fetch_rss_news(
        feeds,
        limit_per_feed=limit_per_feed,
        default_tz=display_tz,   # ← 이 줄 때문에 KR이 다시 잡힘
    )

    cutoff = _cutoff_utc(days)
    out: List[Dict] = []

    for n in items:
        pub_str = n.get("published")
        if not pub_str:
            continue
        try:
            pub_dt_utc = _parse_utc_iso_z(pub_str)
        except Exception:
            continue

        if pub_dt_utc >= cutoff:
            n["published_dt_utc"]    = pub_dt_utc
            n["published_local_str"] = _fmt_local(pub_dt_utc, display_tz)
            n["local_tz"] = _tz_label(display_tz)
            if country_tag:
                n["country"] = country_tag
            out.append(n)

    out.sort(key=lambda x: x["published_dt_utc"], reverse=True)
    return out

def collect_recent_news_kr(days: int = 3, limit_per_feed: int = 30) -> List[Dict]:
    return _collect(KR_FEEDS, KST, days, "kr", limit_per_feed)

def collect_recent_news_us(days: int = 3, limit_per_feed: int = 30) -> List[Dict]:
    return _collect(US_FEEDS, ET, days, "us", limit_per_feed)

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
