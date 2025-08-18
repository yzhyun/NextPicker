from datetime import datetime, timedelta, timezone
from dateutil import parser
import logging

from app.news_crawler import fetch_rss_news
from app.feeds import FEEDS

LIMIT_PER_FEED = 100
logger = logging.getLogger(__name__)


def collect_recent_news(
    days: float = 1.0,
    top: int = 30,
    country: str | None = None,
    section: str | None = None
):
    """
    최근 일정 기간(days) 이내의 기사 중 최신순으로 top개 반환
    - FEEDS 구조: FEEDS[country][section]
    - country, section이 None이면 전체 다 긁어옴
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    all_news = []

    # 국가 필터링
    selected_countries = [country] if country else FEEDS.keys()

    for c in selected_countries:
        sections = FEEDS[c]

        # 섹션 필터링
        selected_sections = [section] if section else sections.keys()

        for s in selected_sections:
            feeds = sections[s]
            items = fetch_rss_news(feeds, limit_per_feed=LIMIT_PER_FEED)

            for n in items:
                n["country"] = c
                n["section"] = s
            all_news.extend(items)
    # ✅ 중복 제거 (여기서 바로 처리)
    seen = set()
    deduped = []
    for n in all_news:
        if n["id"] in seen:
            continue
        seen.add(n["id"])
        deduped.append(n)

    all_news = deduped
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
            n["_parsed_date"] = pub_dt
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
