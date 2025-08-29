# app/rss_feeds.py
"""
RSS 피드 설정 파일
Google News RSS(섹션별 토픽) 기반으로 일원화합니다.
- 섹션별 토픽 코드:
  WORLD, NATION, BUSINESS, TECHNOLOGY, ENTERTAINMENT, SPORTS, SCIENCE, HEALTH
- 국가별 파라미터:
  US: hl=en-US&gl=US&ceid=US:en
  KR: hl=ko&gl=KR&ceid=KR:ko
- 참고: 섹션 URL은 리다이렉트가 발생할 수 있으므로 클라이언트에서 follow_redirects 권장(curl -L 등)
"""

from typing import List, Dict, Optional

# 공통 URL 빌더
def _topic_url(topic: str, country: str) -> str:
    country = country.upper()
    if country == "US":
        return f"https://news.google.com/rss/headlines/section/topic/{topic}?hl=en-US&gl=US&ceid=US:en"
    elif country == "KR":
        return f"https://news.google.com/rss/headlines/section/topic/{topic}?hl=ko&gl=KR&ceid=KR:ko"
    else:
        raise ValueError(f"Unsupported country: {country}")

# ── 국가별 일반(종합) 피드 ───────────────────────────────────────────────
US_FEEDS: Dict[str, Dict] = {
    "Google": {
        "name": "Google News",
        "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
        "category": "general",
        "language": "en",
        "description": "Google News Top stories (US)"
    }
}

KR_FEEDS: Dict[str, Dict] = {
    "Google": {
        "name": "Google News Korea",
        "url": "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
        "category": "general",
        "language": "ko",
        "description": "Google News 주요 뉴스 (한국)"
    }
}

# ── 섹션별 피드(토픽 코드 기반) ──────────────────────────────────────────
# 사용 가능한 토픽: WORLD, NATION, BUSINESS, TECHNOLOGY, ENTERTAINMENT, SPORTS, SCIENCE, HEALTH
SECTION_FEEDS: Dict[str, Dict[str, Dict[str, Dict]]] = {
    "world": {
        "us": {
            "google_world_us": {
                "name": "Google News World (US)",
                "url": _topic_url("WORLD", "US"),
                "category": "world",
                "language": "en",
                "description": "World news (US edition)"
            }
        },
        "kr": {
            "google_world_kr": {
                "name": "Google News World (KR)",
                "url": _topic_url("WORLD", "KR"),
                "category": "world",
                "language": "ko",
                "description": "세계 뉴스 (한국 에디션)"
            }
        }
    },
    "nation": {  # 국내/정치 포함 개념(구글 토픽명은 NATION)
        "us": {
            "google_nation_us": {
                "name": "Google News Nation (US)",
                "url": _topic_url("NATION", "US"),
                "category": "nation",
                "language": "en",
                "description": "US nation news"
            }
        },
        "kr": {
            "google_nation_kr": {
                "name": "Google News Nation (KR)",
                "url": _topic_url("NATION", "KR"),
                "category": "nation",
                "language": "ko",
                "description": "국내 뉴스 (한국 에디션)"
            }
        }
    },
    "business": {
        "us": {
            "google_business_us": {
                "name": "Google News Business (US)",
                "url": _topic_url("BUSINESS", "US"),
                "category": "business",
                "language": "en",
                "description": "Business news (US edition)"
            }
        },
        "kr": {
            "google_business_kr": {
                "name": "Google News Business (KR)",
                "url": _topic_url("BUSINESS", "KR"),
                "category": "business",
                "language": "ko",
                "description": "경제 뉴스 (한국 에디션)"
            }
        }
    },
    "technology": {
        "us": {
            "google_tech_us": {
                "name": "Google News Technology (US)",
                "url": _topic_url("TECHNOLOGY", "US"),
                "category": "technology",
                "language": "en",
                "description": "Technology news (US edition)"
            }
        },
        "kr": {
            "google_tech_kr": {
                "name": "Google News Technology (KR)",
                "url": _topic_url("TECHNOLOGY", "KR"),
                "category": "technology",
                "language": "ko",
                "description": "기술/IT 뉴스 (한국 에디션)"
            }
        }
    },
    "entertainment": {
        "us": {
            "google_ent_us": {
                "name": "Google News Entertainment (US)",
                "url": _topic_url("ENTERTAINMENT", "US"),
                "category": "entertainment",
                "language": "en",
                "description": "Entertainment news (US edition)"
            }
        },
        "kr": {
            "google_ent_kr": {
                "name": "Google News Entertainment (KR)",
                "url": _topic_url("ENTERTAINMENT", "KR"),
                "category": "entertainment",
                "language": "ko",
                "description": "연예 뉴스 (한국 에디션)"
            }
        }
    },
    "sports": {
        "us": {
            "google_sports_us": {
                "name": "Google News Sports (US)",
                "url": _topic_url("SPORTS", "US"),
                "category": "sports",
                "language": "en",
                "description": "Sports news (US edition)"
            }
        },
        "kr": {
            "google_sports_kr": {
                "name": "Google News Sports (KR)",
                "url": _topic_url("SPORTS", "KR"),
                "category": "sports",
                "language": "ko",
                "description": "스포츠 뉴스 (한국 에디션)"
            }
        }
    },
    "science": {
        "us": {
            "google_science_us": {
                "name": "Google News Science (US)",
                "url": _topic_url("SCIENCE", "US"),
                "category": "science",
                "language": "en",
                "description": "Science news (US edition)"
            }
        },
        "kr": {
            "google_science_kr": {
                "name": "Google News Science (KR)",
                "url": _topic_url("SCIENCE", "KR"),
                "category": "science",
                "language": "ko",
                "description": "과학 뉴스 (한국 에디션)"
            }
        }
    },
    "health": {
        "us": {
            "google_health_us": {
                "name": "Google News Health (US)",
                "url": _topic_url("HEALTH", "US"),
                "category": "health",
                "language": "en",
                "description": "Health news (US edition)"
            }
        },
        "kr": {
            "google_health_kr": {
                "name": "Google News Health (KR)",
                "url": _topic_url("HEALTH", "KR"),
                "category": "health",
                "language": "ko",
                "description": "건강 뉴스 (한국 에디션)"
            }
        }
    },
}

def get_feeds_by_country(country: str) -> List[str]:
    """국가별 RSS 피드 URL 목록을 반환합니다."""
    c = country.upper()
    if c == 'US':
        return [feed["url"] for feed in US_FEEDS.values()]
    elif c == 'KR':
        return [feed["url"] for feed in KR_FEEDS.values()]
    else:
        return []

def get_feeds_by_section(section: str, country: Optional[str] = None) -> List[str]:
    """섹션별 RSS 피드 URL 목록을 반환합니다."""
    key = section.lower()
    if key not in SECTION_FEEDS:
        return []

    if country:
        c_key = country.lower()  # <-- 대소문자 혼용 버그 수정
        if c_key in SECTION_FEEDS[key]:
            return [feed["url"] for feed in SECTION_FEEDS[key][c_key].values()]
        else:
            return []
    else:
        # 모든 국가의 해당 섹션 피드 반환
        urls: List[str] = []
        for country_feeds in SECTION_FEEDS[key].values():
            urls.extend([feed["url"] for feed in country_feeds.values()])
        return urls

def get_all_feeds() -> Dict[str, Dict]:
    """모든 RSS 피드 정보를 반환합니다."""
    return {
        "us": US_FEEDS,
        "kr": KR_FEEDS,
        "sections": SECTION_FEEDS
    }

def get_feed_info(url: str) -> Optional[Dict]:
    """URL로 피드 정보를 찾아 반환합니다."""
    # US 피드에서 검색
    for feed_id, feed_info in US_FEEDS.items():
        if feed_info["url"] == url:
            return {"id": feed_id, "country": "US", **feed_info}

    # KR 피드에서 검색
    for feed_id, feed_info in KR_FEEDS.items():
        if feed_info["url"] == url:
            return {"id": feed_id, "country": "KR", **feed_info}

    # 섹션 피드에서 검색
    for section, countries in SECTION_FEEDS.items():
        for country, feeds in countries.items():
            for feed_id, feed_info in feeds.items():
                if feed_info["url"] == url:
                    return {"id": feed_id, "country": country.upper(), "section": section, **feed_info}

    return None
