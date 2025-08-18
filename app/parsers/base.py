# app/parsers/base.py
from __future__ import annotations
from typing import Tuple, List, Dict, Any, Optional
from urllib.parse import urljoin
import re, html

class BaseFeedParser:
    """피드 전용 파서 인터페이스(확장 포인트)."""

    def extract_link(self, entry: dict, feed_base: str | None, feed_url: str) -> str:
        def _norm(u: Optional[str]) -> str:
            if not isinstance(u, str):
                return ""
            u = u.strip()
            if feed_base and u and not u.startswith("http"):
                u = urljoin(feed_base, u)
            return u

        lf = entry.get("link")
        if isinstance(lf, dict):
            href = _norm(lf.get("href"))
            if href.startswith("http"):
                return href

        candidates = [
            entry.get("link"),
            entry.get("origlink"),
            entry.get("feedburner_origlink"),
            entry.get("id") or entry.get("guid"),
        ]

        for l in (entry.get("links") or []):
            rel = (l.get("rel") or "").lower()
            href = _norm(l.get("href"))
            if href and href.startswith("http") and rel == "alternate":
                candidates.append(href)
        for l in (entry.get("links") or []):
            href = _norm(l.get("href"))
            if href and href.startswith("http"):
                candidates.append(href)

        html_blob = self._get_summary_html(entry)
        if html_blob:
            m = re.search(r'href=["\'](https?://[^"\']+)["\']', html_blob)
            if m:
                candidates.append(_norm(m.group(1)))

        seen = set()
        for u in candidates:
            u = _norm(u)
            if not u or u in seen:
                continue
            seen.add(u)
            if u.startswith(("http://", "https://")):
                return u
        return ""

    def normalize_title(self, entry: dict, link: str) -> str:
        return (entry.get("title") or link or "[No title]").strip()

    def extract_summary_fields(
        self, entry: dict, feed_base: str | None, feed_url: str, max_len: int = 280
    ) -> Tuple[str, str, List[Dict[str, Any]]]:
        summary_html = self._get_summary_html(entry)
        summary_text = self._clean_html(summary_html)
        if max_len and len(summary_text) > max_len:
            summary_text = summary_text[:max_len].rstrip() + "…"
        return summary_text, summary_html, []

    @staticmethod
    def _get_summary_html(entry: dict) -> str:
        for key in ("summary", "subtitle", "description"):
            v = entry.get(key)
            if isinstance(v, dict):
                v = v.get("value")
            if isinstance(v, str) and v.strip():
                return v
        content = entry.get("content") or []
        if content and isinstance(content, list):
            v = content[0].get("value")
            if isinstance(v, str) and v.strip():
                return v
        return ""

    @staticmethod
    def _clean_html(s: str) -> str:
        if not isinstance(s, str):
            return ""
        s = re.sub(r"(?is)<(script|style)\b.*?>.*?</\1>", "", s)
        s = re.sub(r"(?is)<[^>]+>", " ", s)
        s = html.unescape(s)
        s = re.sub(r"\s+", " ", s).strip()
        return s
