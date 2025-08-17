# app/news_crawler.py
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import md5
from typing import Iterable, List, Dict, Any
import logging

import requests
import feedparser

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


def _summary_from_entry(entry: dict) -> str:
    for key in ("summary", "subtitle", "description"):
        v = entry.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _safe_struct_to_dt(t) -> datetime:
    # feedparser의 published_parsed / updated_parsed (time.struct_time)
    try:
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    except Exception:
        pass
    return _utc_now()


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


def fetch_rss_news(
    feeds: Iterable[str],
    limit_per_feed: int = 30,
    request_timeout: int = 10,
) -> List[Dict[str, Any]]:
    """주어진 RSS/Atom 피드들에서 기사 목록 수집."""
    items: List[Dict[str, Any]] = []

    for url in feeds:
        meta = _http_fetch(url, timeout=request_timeout)

        # 1순위: 바이트로 직접 파싱(헤더 적용됨)
        if meta["content"]:
            parsed = feedparser.parse(meta["content"])
            source = parsed.get("feed", {}).get("title") or parsed.get("feed", {}).get("link") or url
        else:
            # 2순위: feedparser가 직접 가져가게(여기도 헤더 넣음)
            parsed = feedparser.parse(url, request_headers=DEFAULT_HEADERS)
            source = parsed.get("feed", {}).get("title") or parsed.get("feed", {}).get("link") or url

        bozo = getattr(parsed, "bozo", 0)
        bozo_exc = getattr(parsed, "bozo_exception", "")
        entries = (parsed.get("entries") or [])[:limit_per_feed]

        logger.info(
            "FEED diag | url=%s status=%s entries=%s bozo=%s err=%s",
            url, meta["status"], len(entries), bozo, meta["error"] or bozo_exc
        )

        for e in entries:
            link = (e.get("link") or "").strip()
            title = (e.get("title") or link or "[No title]").strip()
            published_dt = _safe_struct_to_dt(e.get("published_parsed") or e.get("updated_parsed"))
            summary = _summary_from_entry(e)

            items.append({
                "id": _hash_id(link or title),
                "title": title,
                "url": link,
                "source": (source or "").strip(),
                "published": published_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "summary": summary,
                "scraped_at": _utc_now_str(),
            })

    return items


def debug_fetch(feeds: Iterable[str]) -> List[Dict[str, Any]]:
    """피드별 상태/엔트리/bozo 진단용."""
    report = []
    for url in feeds:
        meta = _http_fetch(url)
        if meta["content"]:
            parsed = feedparser.parse(meta["content"])
        else:
            parsed = feedparser.parse(url, request_headers=DEFAULT_HEADERS)
        entries = parsed.get("entries") or []
        report.append({
            "url": url,
            "http_status": meta["status"],
            "entries": len(entries),
            "bozo": int(getattr(parsed, "bozo", 0)),
            "error": meta["error"] or str(getattr(parsed, "bozo_exception", "")) or None,
            "feed_title": (parsed.get("feed", {}).get("title") or ""),
        })
    return report
