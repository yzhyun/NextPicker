import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # 데이터베이스 설정
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./news.db")
    
    # 캐시 설정
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5분
    
    # RSS 피드 설정
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "10"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    
    # 피드 URL들 (환경변수에서도 설정 가능)
    US_FEEDS: List[str] = [
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "https://news.google.com/rss?hl=en&gl=US&ceid=US:en",
        "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en&gl=US&ceid=US:en",
        "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en&gl=US&ceid=US:en",
    ]
    
    KR_FEEDS: List[str] = [
        "https://www.hankyung.com/feed/it",
        "https://www.hankyung.com/feed/economy",
        "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko",
        "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=ko&gl=KR&ceid=KR:ko",
    ]
    
    # 환경변수에서 추가 피드 로드
    if os.getenv("EXTRA_US_FEEDS"):
        US_FEEDS.extend(os.getenv("EXTRA_US_FEEDS", "").split(","))
    
    if os.getenv("EXTRA_KR_FEEDS"):
        KR_FEEDS.extend(os.getenv("EXTRA_KR_FEEDS", "").split(","))

settings = Settings()
