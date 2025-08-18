# app/parsers/google_news.py
from __future__ import annotations
from typing import Tuple, List, Dict, Any
from urllib.parse import urlparse, parse_qs, urljoin
import re

from .base import BaseFeedParser

class GoogleNewsParser(BaseFeedParser):
    @staticmethod
    def _prefer_original(u: str) -> str:
        try:
            pu = urlparse(u)
            if pu.netloc.endswith("news.google.com"):
                qs = parse_qs(pu.query or "")
                cand = qs.get("url") or qs.get("u")
                if cand and isinstance(cand, list) and cand[0].startswith(("http://", "https://")):
                    return cand[0]
        except Exception:
            pass
        return u

    def extract_link(self, entry: dict, feed_base: str | None, feed_url: str) -> str:
        link = super().extract_link(entry, feed_base, feed_url)
        return self._prefer_original(link)

    def extract_summary_fields(
        self, entry: dict, feed_base: str | None, feed_url: str, max_len: int = 280
    ) -> Tuple[str, str, List[Dict[str, Any]]]:
        summary_html = self._get_summary_html(entry)
        summary_text = self._clean_html(summary_html)

        related: List[Dict[str, Any]] = []
        if summary_html and ("<li" in summary_html or "<ol" in summary_html):
            for li in re.finditer(r"(?is)<li[^>]*>(.*?)</li>", summary_html):
                block = li.group(1) or ""
                a = re.search(r'(?is)<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', block)
                if not a:
                    continue
                href = a.group(1).strip()
                if feed_base and href and not href.startswith("http"):
                    href = urljoin(feed_base, href)
                href = self._prefer_original(href)
                title_html = a.group(2)
                src_m = re.search(r"(?is)<font[^>]*>(.*?)</font>", block)
                source_html = src_m.group(1) if src_m else ""
                related.append({
                    "title": self._clean_html(title_html),
                    "source": self._clean_html(source_html),
                    "url": href,
                })

        if max_len and len(summary_text) > max_len:
            summary_text = summary_text[:max_len].rstrip() + "…"

        return summary_text, summary_html, related
