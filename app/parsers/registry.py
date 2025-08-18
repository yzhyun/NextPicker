# app/parsers/registry.py
from __future__ import annotations
from urllib.parse import urlparse
from typing import Type

from .base import BaseFeedParser
from .generic import GenericParser
from .google_news import GoogleNewsParser

_PARSERS: list[tuple[str, Type[BaseFeedParser]]] = [
    ("news.google.com", GoogleNewsParser),
    # 예: ("rss.nytimes.com", NYTParser), ("www.cnbc.com", CNBCParser),
]

def get_parser(feed_url: str) -> BaseFeedParser:
    try:
        netloc = (urlparse(feed_url).netloc or "").lower()
    except Exception:
        netloc = ""
    for host, klass in _PARSERS:
        if host in netloc:
            return klass()
    return GenericParser()
