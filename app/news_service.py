from datetime import datetime, timedelta, timezone
from dateutil import parser

from app.news_crawler import fetch_rss_news
import logging

# 미국 RSS 피드
US_FEEDS = [
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://news.google.com/rss?hl=en&gl=US&ceid=US:en",
]

# 한국 RSS 피드
KR_FEEDS = [
    "https://rss.hankyung.com/feed/it.xml",
    "https://rss.hankyung.com/feed/economy.xml",
    "https://rss.yonhapnews.co.kr/it.xml",
    "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
]

logger = logging.getLogger(__name__)

def collect_recent_news(days: float = 1.0, top: int = 30):
    """
    최근 일정 기간(days) 이내의 기사 중 최신순으로 top 개 반환
    - 미국 / 한국 뉴스 각각에서 충분히 긁어옴 (per_feed_limit=100)
    - UTC 기준 published 필드 사용
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # 충분히 수집
    us_news = fetch_rss_news(US_FEEDS, limit_per_feed=100)
    kr_news = fetch_rss_news(KR_FEEDS, limit_per_feed=100)

    all_news = us_news + kr_news
    logger.info(f"Fetched {len(all_news)} total news items")

    # 날짜 필터링
    filtered = []
    for n in all_news:
        try:
            pub_dt = parser.parse(n.get("published"))
            if pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=timezone.utc)
        except Exception:
            continue

        if pub_dt >= cutoff:
            n["_parsed_date"] = pub_dt  # 정렬용 캐시
            filtered.append(n)

    logger.info(f"Filtered down to {len(filtered)} items within {days} days")

    # 최신순 정렬 후 상위 N개
    filtered.sort(key=lambda x: x["_parsed_date"], reverse=True)
    final_items = filtered[:top]

    return final_items, {
        "total": len(all_news),
        "after_filter": len(filtered),
        "returned": len(final_items),
        "cutoff": cutoff.isoformat(),
    }
