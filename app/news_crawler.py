# app/news_crawler.py
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import md5
from typing import Iterable, List, Dict, Any
import logging

import requests
import feedparser

from app.parsers import get_parser  # 피드사별 파서 선택

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


def _safe_struct_to_dt(t) -> datetime:
    """
    feedparser의 published_parsed / updated_parsed (time.struct_time)를 datetime(UTC)로.
    실패 시 1970-01-01 UTC 반환(정렬 시 맨 뒤로 밀리도록).
    """
    try:
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc)
    except Exception:
        pass
    return datetime(1970, 1, 1, tzinfo=timezone.utc)


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
    """
    주어진 RSS/Atom 피드들에서 기사 목록 수집.
    - 시간은 RSS가 제공하는 published/updated 기준(원문 페이지 추가 크롤링 없음)
    - 파서 플러그인 구조: 피드사별로 링크/요약 처리 다르게 적용
    반환 아이템 공통 스키마:
      {
        id, title, url, link, source, published(UTC ISO Z),
        summary, summary_text, summary_html, related[], scraped_at
      }
    """
    items: List[Dict[str, Any]] = []

    for feed_url in feeds:
        meta = _http_fetch(feed_url, timeout=request_timeout)

        # 피드사별 파서 선택
        parser = get_parser(feed_url)

        # 1순위: 바이트로 직접 파싱(헤더 적용됨)
        if meta["content"]:
            parsed = feedparser.parse(meta["content"])
        else:
            # 2순위: feedparser가 직접 가져가게(여기도 헤더 넣음)
            parsed = feedparser.parse(feed_url, request_headers=DEFAULT_HEADERS)

        feed_info = parsed.get("feed", {}) or {}
        source = (feed_info.get("title") or feed_info.get("link") or feed_url).strip()
        feed_base = (feed_info.get("link") or feed_url).strip()

        bozo = getattr(parsed, "bozo", 0)
        bozo_exc = getattr(parsed, "bozo_exception", "")
        entries = (parsed.get("entries") or [])[:limit_per_feed]

        logger.info(
            "FEED diag | url=%s status=%s entries=%s bozo=%s err=%s",
            feed_url, meta["status"], len(entries), bozo, meta["error"] or bozo_exc
        )

        empty_links = 0
        for e in entries:
            # 링크/제목/요약은 파서에게 위임
            link = parser.extract_link(e, feed_base, feed_url)
            if not link:
                empty_links += 1
                logger.warning(
                    "ENTRY skipping (empty link) | feed=%s title=%s keys=%s",
                    source, (e.get("title") or "")[:80], sorted(list(e.keys()))
                )
                continue

            title = parser.normalize_title(e, link)
            published_dt = _safe_struct_to_dt(e.get("published_parsed") or e.get("updated_parsed"))
            summary_text, summary_html, related = parser.extract_summary_fields(e, feed_base, feed_url)

            items.append({
                "id": _hash_id(link or title),
                "title": title,
                "url": link,
                "link": link,  # 호환성
                "source": source,
                "published": published_dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "summary": summary_text,        # 호환 키
                "summary_text": summary_text,   # 평문화 텍스트
                "summary_html": summary_html,   # 원본 HTML (있을 때)
                "related": related,             # 구글 뉴스 묶음 등 구조화
                "scraped_at": _utc_now_str(),
            })

        if empty_links:
            logger.info("FEED stat | feed=%s empty_links=%d/%d", source, empty_links, len(entries))

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
