# app/repositories/news_repository.py
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import NewsArticle

logger = logging.getLogger(__name__)

class NewsRepository:
    """뉴스 데이터 접근을 담당하는 Repository 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
        # 데이터베이스 타입을 한 번만 체크하여 저장
        database_url = os.getenv("DATABASE_URL", "")
        self.is_postgresql = database_url and "postgresql" in database_url
    
    def get_recent_news(self, country: str, days: int = 3, limit: int = 50) -> List[Dict[str, Any]]:
        """데이터베이스에서 최근 뉴스를 가져옵니다."""
        try:
            if self.is_postgresql:
                # PostgreSQL용 Raw SQL
                query = text("""
                    SELECT id, title, url, source, published, summary, section, country, created_at
                    FROM news_articles 
                    WHERE country = :country 
                      AND published >= NOW() - INTERVAL ':days days'
                    ORDER BY published DESC 
                    LIMIT :limit
                """)
                result = self.db.execute(query, {
                    'country': country.upper(),
                    'days': days,
                    'limit': limit
                })
            else:
                # SQLite용 Raw SQL
                cutoff_date = datetime.now() - timedelta(days=days)
                query = text("""
                    SELECT id, title, url, source, published, summary, section, country, created_at
                    FROM news_articles 
                    WHERE country = :country 
                      AND published >= :cutoff_date
                    ORDER BY published DESC 
                    LIMIT :limit
                """)
                result = self.db.execute(query, {
                    'country': country.upper(),
                    'cutoff_date': cutoff_date,
                    'limit': limit
                })
            
            # 결과를 딕셔너리로 변환
            articles = []
            for row in result.fetchall():
                articles.append({
                    'title': row.title,
                    'url': row.url,
                    'source': row.source,
                    'published': row.published,
                    'summary': row.summary,
                    'section': row.section,
                    'country': row.country,
                    'created_at': row.created_at
                })
            
            return articles
        except Exception as e:
            logger.error(f"Error getting recent news for {country}: {e}")
            raise
    
    def get_news_by_section(self, section: str, country: Optional[str] = None, days: int = 3, limit: int = 50) -> List[Dict[str, Any]]:
        """특정 섹션의 뉴스를 가져옵니다."""
        try:
            if self.is_postgresql:
                # PostgreSQL용 Raw SQL
                if country:
                    query = text("""
                        SELECT id, title, url, source, published, summary, section, country, created_at
                        FROM news_articles 
                        WHERE section = :section 
                          AND country = :country
                          AND published >= NOW() - INTERVAL ':days days'
                        ORDER BY published DESC 
                        LIMIT :limit
                    """)
                    result = self.db.execute(query, {
                        'section': section,
                        'country': country.upper(),
                        'days': days,
                        'limit': limit
                    })
                else:
                    query = text("""
                        SELECT id, title, url, source, published, summary, section, country, created_at
                        FROM news_articles 
                        WHERE section = :section 
                          AND published >= NOW() - INTERVAL ':days days'
                        ORDER BY published DESC 
                        LIMIT :limit
                    """)
                    result = self.db.execute(query, {
                        'section': section,
                        'days': days,
                        'limit': limit
                    })
            else:
                # SQLite용 Raw SQL
                cutoff_date = datetime.now() - timedelta(days=days)
                if country:
                    query = text("""
                        SELECT id, title, url, source, published, summary, section, country, created_at
                        FROM news_articles 
                        WHERE section = :section 
                          AND country = :country
                          AND published >= :cutoff_date
                        ORDER BY published DESC 
                        LIMIT :limit
                    """)
                    result = self.db.execute(query, {
                        'section': section,
                        'country': country.upper(),
                        'cutoff_date': cutoff_date,
                        'limit': limit
                    })
                else:
                    query = text("""
                        SELECT id, title, url, source, published, summary, section, country, created_at
                        FROM news_articles 
                        WHERE section = :section 
                          AND published >= :cutoff_date
                        ORDER BY published DESC 
                        LIMIT :limit
                    """)
                    result = self.db.execute(query, {
                        'section': section,
                        'cutoff_date': cutoff_date,
                        'limit': limit
                    })
            
            # 결과를 딕셔너리로 변환
            articles = []
            for row in result.fetchall():
                articles.append({
                    'title': row.title,
                    'url': row.url,
                    'source': row.source,
                    'published': row.published,
                    'summary': row.summary,
                    'section': row.section,
                    'country': row.country
                })
            
            return articles
        except Exception as e:
            logger.error(f"Error getting news by section {section}: {e}")
            raise
    
    def get_economy_politics_news(self, days: int = 1, limit: int = 20) -> List[Dict[str, Any]]:
        """경제/정치 뉴스를 가져옵니다."""
        try:
            if self.is_postgresql:
                # PostgreSQL용 Raw SQL
                query = text("""
                    SELECT id, title, url, source, published, summary, section, country, created_at
                    FROM news_articles 
                    WHERE published >= NOW() - INTERVAL ':days days'
                      AND section IN ('business', 'politics')
                    ORDER BY published DESC 
                    LIMIT :limit
                """)
                result = self.db.execute(query, {
                    'days': days,
                    'limit': limit * 2
                })
            else:
                # SQLite용 Raw SQL
                cutoff_date = datetime.now() - timedelta(days=days)
                query = text("""
                    SELECT id, title, url, source, published, summary, section, country, created_at
                    FROM news_articles 
                    WHERE published >= :cutoff_date
                      AND section IN ('business', 'politics')
                    ORDER BY published DESC 
                    LIMIT :limit
                """)
                result = self.db.execute(query, {
                    'cutoff_date': cutoff_date,
                    'limit': limit * 2
                })
            
            # 결과를 딕셔너리로 변환
            all_articles = []
            for row in result.fetchall():
                all_articles.append({
                    'title': row.title,
                    'url': row.url,
                    'source': row.source,
                    'published': row.published,
                    'summary': row.summary,
                    'section': row.section,
                    'country': row.country
                })
            
            return all_articles
        except Exception as e:
            logger.error(f"Error getting economy/politics news: {e}")
            raise
    
    def get_us_news_for_analysis(self, days: int = 1, limit: int = 50) -> List[Dict[str, Any]]:
        """AI 분석용 US 뉴스를 가져옵니다."""
        try:
            if self.is_postgresql:
                # PostgreSQL용 Raw SQL
                query = text("""
                    SELECT id, title, source, published, summary, section, country, created_at
                    FROM news_articles 
                    WHERE country = 'US' 
                      AND published >= NOW() - INTERVAL ':days days'
                    ORDER BY published DESC 
                    LIMIT :limit
                """)
                result = self.db.execute(query, {
                    'days': days,
                    'limit': limit
                })
            else:
                # SQLite용 Raw SQL
                cutoff_date = datetime.now() - timedelta(days=days)
                query = text("""
                    SELECT id, title, source, published, summary, section, country, created_at
                    FROM news_articles 
                    WHERE country = 'US' 
                      AND published >= :cutoff_date
                    ORDER BY published DESC 
                    LIMIT :limit
                """)
                result = self.db.execute(query, {
                    'cutoff_date': cutoff_date,
                    'limit': limit
                })
            
            # 결과를 딕셔너리로 변환
            articles = []
            for row in result.fetchall():
                articles.append({
                    'title': row.title,
                    'source': row.source,
                    'published': row.published,
                    'summary': row.summary,
                    'section': row.section,
                    'country': row.country
                })
            
            return articles
        except Exception as e:
            logger.error(f"Error getting US news for analysis: {e}")
            raise
    
    def get_article_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """URL로 기사를 조회합니다."""
        try:
            query = text("""
                SELECT id, title, url, source, published, summary, section, country, created_at
                FROM news_articles 
                WHERE url = :url
                LIMIT 1
            """)
            result = self.db.execute(query, {'url': url})
            row = result.fetchone()
            
            if row:
                return {
                    'id': row.id,
                    'title': row.title,
                    'url': row.url,
                    'source': row.source,
                    'published': row.published,
                    'summary': row.summary,
                    'section': row.section,
                    'country': row.country,
                    'created_at': row.created_at
                }
            return None
        except Exception as e:
            logger.error(f"Error getting article by URL {url}: {e}")
            raise
    
    def save_article(self, article_data: Dict[str, Any]) -> bool:
        """기사를 데이터베이스에 저장합니다."""
        try:
            # 기존 기사 확인
            existing = self.get_article_by_url(article_data['url'])
            if existing:
                return False  # 이미 존재
            
            # 새 기사 저장
            query = text("""
                INSERT INTO news_articles (id, title, url, source, published, summary, section, country, created_at)
                VALUES (:id, :title, :url, :source, :published, :summary, :section, :country, :created_at)
            """)
            
            self.db.execute(query, {
                'id': article_data['id'],
                'title': article_data['title'],
                'url': article_data['url'],
                'source': article_data['source'],
                'published': article_data['published'],
                'summary': article_data['summary'],
                'section': article_data.get('section', 'general'),
                'country': article_data['country'],
                'created_at': datetime.now()
            })
            
            return True
        except Exception as e:
            logger.error(f"Error saving article {article_data.get('url', 'unknown')}: {e}")
            raise
    
    def commit(self):
        """변경사항을 커밋합니다."""
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Database commit failed: {e}")
            raise
    
    def get_news_count_by_country(self, country: str, days: int = 1) -> int:
        """국가별 뉴스 개수를 조회합니다."""
        try:
            if self.is_postgresql:
                # PostgreSQL용 Raw SQL
                query = text("""
                    SELECT COUNT(*) as count
                    FROM news_articles 
                    WHERE country = :country 
                      AND published >= NOW() - INTERVAL ':days days'
                """)
                result = self.db.execute(query, {
                    'country': country.upper(),
                    'days': days
                })
            else:
                # SQLite용 Raw SQL
                cutoff_date = datetime.now() - timedelta(days=days)
                query = text("""
                    SELECT COUNT(*) as count
                    FROM news_articles 
                    WHERE country = :country 
                      AND published >= :cutoff_date
                """)
                result = self.db.execute(query, {
                    'country': country.upper(),
                    'cutoff_date': cutoff_date
                })
            
            row = result.fetchone()
            return row.count if row else 0
        except Exception as e:
            logger.error(f"Error getting news count for {country}: {e}")
            raise
