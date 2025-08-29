# app/news_service.py
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser
from typing import List, Dict, Optional
from app.database import get_db, NewsArticle
from app.rss_feeds import get_feeds_by_country, get_feeds_by_section, get_feed_info
import re

from app.slack_notifier import slack

logger = logging.getLogger(__name__)

# RSS 피드 목록
US_FEEDS = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.cnn.com/rss/edition.rss",
    "https://feeds.npr.org/1001/rss.xml",
]

KR_FEEDS = [
    "https://www.yonhapnews.co.kr/feed/headlines.xml",
    "https://www.koreaherald.com/rss.xml",
    "https://www.koreatimes.co.kr/rss/rss.xml",
]

def get_article_id(url: str) -> str:
    """URL의 MD5 해시를 반환합니다."""
    return hashlib.md5(url.encode()).hexdigest()

def extract_summary(content: str) -> str:
    """HTML 콘텐츠에서 텍스트 요약을 추출합니다."""
    try:
        soup = BeautifulSoup(content, 'html.parser')
        # HTML 태그 제거하고 텍스트만 추출
        text = soup.get_text()
        # 공백 정리
        text = ' '.join(text.split())
        # 200자로 제한
        return text[:200] + "..." if len(text) > 200 else text
    except:
        return content[:200] + "..." if len(content) > 200 else content

def fetch_rss_feed(feed_url: str) -> List[Dict[str, Any]]:
    """RSS 피드에서 뉴스를 가져옵니다."""
    try:
        feed = feedparser.parse(feed_url)
        articles = []
        
        for entry in feed.entries:
            # 발행일 파싱 (한국 시각으로 변환)
            published = getattr(entry, 'published_parsed', None)
            if published:
                # UTC 시간을 한국 시각으로 변환
                published = datetime(*published[:6]).replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=9)))
            else:
                published = datetime.now(timezone(timedelta(hours=9)))
            
            # 요약 추출
            summary = ""
            if hasattr(entry, 'summary'):
                summary = extract_summary(entry.summary)
            elif hasattr(entry, 'content'):
                summary = extract_summary(entry.content[0].value)
            
            # 소스 정보 추출 - 구글 뉴스의 경우 entry.source 사용
            source = feed.feed.title if hasattr(feed.feed, 'title') else feed_url
            if hasattr(entry, 'source'):
                if isinstance(entry.source, dict) and 'title' in entry.source:
                    source = entry.source['title']
                elif hasattr(entry.source, 'title'):
                    source = entry.source.title
            
            # 섹션 분류
            section = classify_news_section(entry.title, summary)
            
            articles.append({
                'title': entry.title,
                'url': entry.link,
                'source': source,
                'published': published,
                'summary': summary,
                'section': section
            })
        
        logger.info(f"Fetched {len(articles)} articles from {feed_url}")
        return articles
        
    except Exception as e:
        logger.error(f"Error fetching {feed_url}: {e}")
        slack.notify_error(str(e), f"RSS 피드 가져오기 실패: {feed_url}")
        return []

def save_articles_to_db(articles: List[Dict[str, Any]], country: str, db: Session) -> int:
    """뉴스 기사들을 데이터베이스에 저장합니다."""
    saved_count = 0
    
    for article_data in articles:
        try:
            # 기존 기사 확인
            existing = db.query(NewsArticle).filter(
                NewsArticle.url == article_data['url']
            ).first()
            
            if existing:
                continue  # 이미 존재하면 건너뛰기
            
            # 새 기사 생성
            article = NewsArticle(
                id=get_article_id(article_data['url']),
                title=article_data['title'],
                url=article_data['url'],
                source=article_data['source'],
                published=article_data['published'],
                summary=article_data['summary'],
                section=article_data.get('section', 'general'),
                country=country
            )
            
            db.add(article)
            saved_count += 1
            
        except Exception as e:
            logger.error(f"Error saving article {article_data.get('url', 'unknown')}: {e}")
    
    try:
        db.commit()
        logger.info(f"Saved {saved_count} new articles for {country}")
        
        # 슬랙 알림: 데이터 저장 완료
        if saved_count > 0:
            slack.notify_data_saved(country, saved_count)
            
    except Exception as e:
        db.rollback()
        logger.error(f"Database commit failed: {e}")
        slack.notify_error(str(e), "데이터베이스 저장 실패")
    
    return saved_count

def collect_news(country: str, days: int = 3) -> List[Dict[str, Any]]:
    """지정된 국가의 뉴스를 수집하고 저장합니다."""
    feeds = get_feeds_by_country(country)
    
    all_articles = []
    total_saved = 0
    
    # 각 피드에서 뉴스 가져오기
    for feed_url in feeds:
        articles = fetch_rss_feed(feed_url)
        all_articles.extend(articles)
    
    # 최근 N일 내 기사만 필터링 (Python에서 필터링 제거, SQL에서 처리)
    recent_articles = all_articles
    
    # 데이터베이스에 저장
    db = next(get_db())
    try:
        total_saved = save_articles_to_db(recent_articles, country, db)
    finally:
        db.close()
    
    return recent_articles

def get_news_by_section(section: str, country: str = None, days: int = 3, limit: int = 50) -> List[Dict[str, Any]]:
    """특정 섹션의 뉴스를 가져옵니다."""
    db = next(get_db())
    try:
        # PostgreSQL에서 한국 시각으로 필터링
        query = db.query(NewsArticle).filter(
            NewsArticle.section == section,
            NewsArticle.published >= func.now() - func.interval(f'{days} days')
        )
        
        if country:
            query = query.filter(NewsArticle.country == country.upper())
        
        articles = query.order_by(NewsArticle.published.desc()).limit(limit).all()
        
        return [
            {
                'title': article.title,
                'url': article.url,
                'source': article.source,
                'published': article.published,
                'summary': article.summary,
                'section': article.section,
                'country': article.country
            }
            for article in articles
        ]
    finally:
        db.close()

def get_recent_news(country: str, days: int = 3, limit: int = 50) -> List[Dict[str, Any]]:
    """데이터베이스에서 최근 뉴스를 가져옵니다."""
    db = next(get_db())
    try:
        # PostgreSQL에서 한국 시각으로 필터링
        articles = db.query(NewsArticle).filter(
            NewsArticle.country == country.upper(),
            NewsArticle.published >= func.now() - func.interval(f'{days} days')
        ).order_by(NewsArticle.published.desc()).limit(limit).all()
        
        return [
            {
                'title': article.title,
                'url': article.url,
                'source': article.source,
                'published': article.published,
                'summary': article.summary,
                'section': article.section,
                'country': article.country
            }
            for article in articles
        ]
    finally:
        db.close()

def refresh_all_feeds() -> Dict[str, int]:
    """모든 피드를 새로고침합니다."""
    logger.info("Starting feed refresh...")
    
    results = {}
    
    # 미국 뉴스 수집
    try:
        us_articles = collect_news('US', days=3)
        results['US'] = len(us_articles)
    except Exception as e:
        logger.error(f"Error collecting US news: {e}")
        slack.notify_error(str(e), "미국 뉴스 수집 실패")
        results['US'] = 0
    
    # 한국 뉴스 수집
    try:
        kr_articles = collect_news('KR', days=3)
        results['KR'] = len(kr_articles)
    except Exception as e:
        logger.error(f"Error collecting KR news: {e}")
        slack.notify_error(str(e), "한국 뉴스 수집 실패")
        results['KR'] = 0
    
    # 슬랙 알림: 피드 새로고침 완료
    total_success = sum(results.values())
    total_feeds = len(US_FEEDS) + len(KR_FEEDS)
    slack.notify_feed_refresh(total_success, total_feeds)
    
    logger.info(f"Feed refresh completed: {results}")
    return results

def build_summary(us_news: List[Dict], kr_news: List[Dict], days_us: int = 3, days_kr: int = 3) -> Dict[str, Any]:
    """뉴스 요약 정보를 생성합니다."""
    return {
        'total': len(us_news) + len(kr_news),
        'us': len(us_news),
        'kr': len(kr_news),
        'range_us': f"최근 {days_us}일",
        'range_kr': f"최근 {days_kr}일"
    }

def classify_news_section(title: str, summary: str = "") -> str:
    """
    뉴스 제목과 내용을 분석하여 섹션을 분류합니다.
    """
    text = (title + " " + summary).lower()
    
    # 정치 관련 키워드
    politics_keywords = [
        'politics', 'political', 'election', 'president', 'congress', 'senate', 'government',
        'democrat', 'republican', 'campaign', 'vote', 'voting', 'poll', 'polls',
        'white house', 'capitol', 'legislation', 'bill', 'law', 'policy',
        'minister', 'parliament', 'election', 'vote', 'campaign', 'political party',
        '정치', '대선', '선거', '국회', '정부', '여당', '야당', '정책', '법안'
    ]
    
    # 경제/비즈니스 관련 키워드
    business_keywords = [
        'business', 'economy', 'economic', 'finance', 'financial', 'market', 'stock',
        'trade', 'commerce', 'investment', 'investor', 'bank', 'banking', 'money',
        'dollar', 'euro', 'currency', 'inflation', 'recession', 'gdp', 'unemployment',
        'company', 'corporation', 'ceo', 'executive', 'profit', 'revenue', 'earnings',
        '경제', '금융', '주식', '투자', '은행', '기업', '매출', '수익', '인플레이션'
    ]
    
    # 기술 관련 키워드
    technology_keywords = [
        'technology', 'tech', 'digital', 'computer', 'software', 'hardware', 'internet',
        'ai', 'artificial intelligence', 'machine learning', 'data', 'cyber', 'cybersecurity',
        'app', 'application', 'mobile', 'smartphone', 'social media', 'online',
        'startup', 'innovation', 'robot', 'automation', 'blockchain', 'crypto',
        '기술', '디지털', '컴퓨터', '소프트웨어', '인공지능', '스마트폰', '앱'
    ]
    
    # 스포츠 관련 키워드
    sports_keywords = [
        'sports', 'football', 'basketball', 'baseball', 'soccer', 'tennis', 'golf',
        'nfl', 'nba', 'mlb', 'nhl', 'olympics', 'championship', 'tournament',
        'player', 'team', 'coach', 'game', 'match', 'score', 'win', 'lose',
        '스포츠', '축구', '야구', '농구', '골프', '테니스', '선수', '팀', '경기'
    ]
    
    # 엔터테인먼트 관련 키워드
    entertainment_keywords = [
        'entertainment', 'movie', 'film', 'tv', 'television', 'show', 'series',
        'actor', 'actress', 'director', 'producer', 'celebrity', 'star', 'hollywood',
        'music', 'song', 'album', 'artist', 'singer', 'concert', 'performance',
        'game', 'gaming', 'video game', 'streaming', 'netflix', 'disney',
        '엔터테인먼트', '영화', '드라마', '연예인', '가수', '음악', '게임'
    ]
    
    # 건강 관련 키워드
    health_keywords = [
        'health', 'medical', 'medicine', 'doctor', 'hospital', 'patient', 'disease',
        'covid', 'coronavirus', 'vaccine', 'vaccination', 'treatment', 'therapy',
        'mental health', 'psychology', 'psychiatrist', 'therapy', 'wellness',
        '건강', '의료', '병원', '의사', '질병', '코로나', '백신', '치료'
    ]
    
    # 과학 관련 키워드
    science_keywords = [
        'science', 'scientific', 'research', 'study', 'discovery', 'experiment',
        'space', 'nasa', 'astronomy', 'planet', 'earth', 'climate', 'environment',
        'biology', 'chemistry', 'physics', 'mathematics', 'engineering',
        '과학', '연구', '발견', '우주', '천문학', '지구', '환경', '생물학'
    ]
    
    # 각 섹션별 키워드 매칭
    sections = {
        'politics': politics_keywords,
        'business': business_keywords,
        'technology': technology_keywords,
        'sports': sports_keywords,
        'entertainment': entertainment_keywords,
        'health': health_keywords,
        'science': science_keywords
    }
    
    # 키워드 매칭 점수 계산
    scores = {}
    for section, keywords in sections.items():
        score = sum(1 for keyword in keywords if keyword in text)
        scores[section] = score
    
    # 가장 높은 점수의 섹션 반환
    if scores:
        max_score = max(scores.values())
        if max_score > 0:
            for section, score in scores.items():
                if score == max_score:
                    return section
    
    # 매칭되는 섹션이 없으면 'general' 반환
    return 'general'
