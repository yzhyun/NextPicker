# app/news_crawler.py
from datetime import datetime, timezone
import feedparser
import time
from hashlib import md5
import trafilatura

FEEDS = [
    "http://rss.cnn.com/rss/money_latest.rss",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://www.marketwatch.com/feeds/topstories",

# 한국 뉴스
    "https://www.yna.co.kr/rss/headline.xml",         # 연합뉴스
    "https://biz.chosun.com/rss/feed.xml",            # 조선비즈
    "https://file.mk.co.kr/news/rss/rss_50300009.xml", # 매일경제 속보
    "https://rss.hankyung.com/feed/economy",           # 한국경제 경제
]

def _utc_now_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def fetch_rss_news(limit_per_feed=30, total_limit=100, fetch_content=False):
    items, seen = [], set()
    for url in FEEDS:
        feed = feedparser.parse(url)
        source = feed.feed.get("title", url)
        for e in feed.entries[:limit_per_feed]:
            title = getattr(e, "title", "").strip()
            link = getattr(e, "link", "").strip()
            if not title or not link:
                continue
            key = md5(link.encode()).hexdigest()
            if key in seen:
                continue
            seen.add(key)

            published = getattr(e, "published", "") or getattr(e, "updated", "")
            if not published:
                published = _utc_now_str()

            summary = getattr(e, "summary", "").strip()
            content = ""
            if fetch_content:
                try:
                    downloaded = trafilatura.fetch_url(link, no_ssl=True, timeout=10)
                    if downloaded:
                        content = trafilatura.extract(downloaded, include_comments=False) or ""
                except Exception:
                    pass
                time.sleep(0.4)

            items.append({
                "title": title,
                "url": link,
                "source": source,
                "published": published,
                "summary": summary,
                "content": content,
                "scraped_at": _utc_now_str(),
            })

    # 📌 전체 합친 뒤 최신순 정렬
    items.sort(key=lambda x: x["published"], reverse=True)

    # 📌 total_limit 만큼만 자르기
    return items[:total_limit]
