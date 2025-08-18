# app/news_crawler.py
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from hashlib import md5
from typing import Iterable, List, Dict, Any, Optional
import logging
import calendar

import requests
import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as dtparser  # ← 문자열 날짜 파싱

# 한국 매체 일부가 UA/언어 헤더 없으면 403/차단하는 케이스가 있어 헤더 강화
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

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_str() -> str:
    return _utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _hash_id(text: str) -> str:
    return md5(text.encode("utf-8", errors="ignore")).hexdigest()


def _struct_time_to_utc(t) -> Optional[datetime]:
    """
    feedparser의 published_parsed / updated_parsed (time.struct_time)를
    안전하게 UTC datetime으로 변환.
    struct_time은 tz를 안가지므로 'UTC 기준의 절대 시각'으로 처리한다.
    """
    if not t:
        return None
    try:
        # struct_time -> epoch(UTC) -> datetime(UTC)
        ts = calendar.timegm(t)  # timegm은 입력을 UTC로 간주
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except Exception:
        return None


def _http_fetch(url: str, timeout: int = 10) -> dict:
    """피드 URL을 먼저 requests로 가져오고, 실패 시 상태/에러를 함께 리턴."""
    out = {"status": None, "content": None, "error": None}
    try:
        resp = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )
        out["status"] = resp.status_code
        if resp.ok:
            out["content"] = resp.content  # 바이트 그대로 파서에 전달
        else:
            out["error"] = f"http_status_{resp.status_code}"
    except Exception as e:
        out["error"] = repr(e)
    return out


def _parse_entry_datetime(e: dict, default_tz: timezone) -> datetime:
    """
    엔트리에서 날짜를 파싱해 tz-aware UTC datetime으로 반환.
    우선순위:
      1) published / updated 문자열 → dateutil로 파싱
         - tz 없으면 default_tz 적용
      2) published_parsed / updated_parsed(struct_time) → UTC로 변환
      3) 실패 시 현재 UTC
    """
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


def fetch_rss_news(
    feeds: Iterable[str],
    limit_per_feed: int = 30,
    request_timeout: int = 10,
    default_tz: Optional[timezone] = timezone.utc,  # ★ 피드별 기본 타임존
) -> List[Dict[str, Any]]:
    """
    주어진 RSS/Atom 피드들에서 기사 목록 수집.
    - 시간은 엔트리의 날짜를 tz-aware UTC로 정규화하여 published에 ISO Z로 저장
    반환 아이템 공통 스키마:
      {
        id, title, url, link, source, published(UTC ISO Z),
        summary, summary_text, summary_html, related[], scraped_at
      }
    """
    items: List[Dict[str, Any]] = []
    default_tz = default_tz or timezone.utc  # None 방지

    for feed_url in feeds:
        meta = _http_fetch(feed_url, timeout=request_timeout)

        # 1순위: 바이트로 직접 파싱(헤더 적용됨)
        if meta["content"]:
            parsed = feedparser.parse(meta["content"])
        else:
            # 2순위: feedparser가 직접 가져가게(여기도 헤더 넣음)
            parsed = feedparser.parse(feed_url, request_headers=DEFAULT_HEADERS)

        feed_info = parsed.get("feed", {}) or {}
        source = (feed_info.get("title") or feed_info.get("link") or feed_url).strip()

        bozo = int(getattr(parsed, "bozo", 0))
        bozo_exc = getattr(parsed, "bozo_exception", "")
        entries = (parsed.get("entries") or [])[:limit_per_feed]

        logger.info(
            "FEED diag | url=%s status=%s entries=%s bozo=%s err=%s",
            feed_url, meta["status"], len(entries), bozo, meta["error"] or bozo_exc
        )

        for e in entries:
            link = e.get("link")
            if not link:
                continue

            title = (e.get("title") or "").strip()
            # ★ 핵심: 피드 기본 타임존을 반영하여 UTC로 정규화
            published_dt_utc = _parse_entry_datetime(e, default_tz=default_tz)

            summary_html = e.get("summary", "") or e.get("content", [{}])[0].get("value", "")
            summary_text = BeautifulSoup(summary_html, "html.parser").get_text(" ").strip()

            items.append({
                "id": _hash_id(link),
                "title": title,
                "url": link,
                "link": link,
                "source": source,
                "published": published_dt_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),  # UTC ISO Z
                "summary": summary_text,
                "summary_text": summary_text,
                "summary_html": summary_html,
                "related": [],
                "scraped_at": _utc_now_str(),
            })
    return items


def debug_fetch(feeds: Iterable[str]) -> List[Dict[str, Any]]:
    """피드별 상태/엔트리/bozo 진단용."""
    report = []
    for feed_url in feeds:
        meta = _http_fetch(feed_url)
        if meta["content"]:
            parsed = feedparser.parse(meta["content"])
        else:
            parsed = feedparser.parse(feed_url, request_headers=DEFAULT_HEADERS)
        entries = parsed.get("entries") or []
        report.append({
            "url": feed_url,
            "http_status": meta["status"],
            "entries": len(entries),
            "bozo": int(getattr(parsed, "bozo", 0)),
            "error": meta["error"] or str(getattr(parsed, "bozo_exception", "")) or None,
            "feed_title": (parsed.get("feed", {}).get("title") or ""),
        })
    return report
