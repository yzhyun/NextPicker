from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import logging

from app.db.models import NewsArticle, FeedStatus
from app.db.database import get_db

logger = logging.getLogger(__name__)

class NewsRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def save_articles(self, articles: List[Dict]) -> int:
        """뉴스 기사들을 데이터베이스에 저장"""
        saved_count = 0
        for article_data in articles:
            try:
                # 기존 기사 확인 (URL로도 확인)
                existing = self.db.query(NewsArticle).filter(
                    (NewsArticle.id == article_data['id']) | 
                    (NewsArticle.url == article_data['url'])
                ).first()
                
                if existing:
                    # 기존 기사 업데이트
                    existing.title = article_data['title']
                    existing.summary = article_data['summary']
                    existing.updated_at = datetime.utcnow()
                else:
                    # 새 기사 생성
                    article = NewsArticle(
                        id=article_data['id'],
                        title=article_data['title'],
                        url=article_data['url'],
                        source=article_data['source'],
                        published=datetime.fromisoformat(article_data['published'].replace('Z', '+00:00')),
                        summary=article_data['summary'],
                        country=article_data['country'],
                        local_tz=article_data['local_tz']
                    )
                    self.db.add(article)
                    saved_count += 1
                
            except Exception as e:
                logger.error(f"Error saving article {article_data.get('id', 'unknown')}: {e}")
                continue
        
        try:
            self.db.commit()
            logger.info(f"Saved {saved_count} new articles")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error committing articles: {e}")
            return 0
        
        return saved_count
    
    def get_recent_articles(self, days: int = 3, country: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """최근 기사들을 가져오기"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(NewsArticle).filter(
            NewsArticle.published >= cutoff
        )
        
        if country:
            query = query.filter(NewsArticle.country == country)
        
        articles = query.order_by(desc(NewsArticle.published)).limit(limit).all()
        
        return [
            {
                'id': article.id,
                'title': article.title,
                'url': article.url,
                'source': article.source,
                'published': article.published.isoformat() + 'Z',
                'summary': article.summary,
                'country': article.country,
                'local_tz': article.local_tz,
                'published_local_str': article.published.strftime('%Y-%m-%d %H:%M:%S'),
            }
            for article in articles
        ]
    
    def update_feed_status(self, feed_url: str, success: bool, entries_count: int = 0, error_msg: str = None):
        """피드 상태 업데이트"""
        try:
            status = self.db.query(FeedStatus).filter(
                FeedStatus.feed_url == feed_url
            ).first()
            
            if not status:
                status = FeedStatus(feed_url=feed_url)
                self.db.add(status)
            
            if success:
                status.last_success = datetime.utcnow()
                status.success_count += 1
                status.last_entries_count = entries_count
            else:
                status.last_error = datetime.utcnow()
                status.error_count += 1
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating feed status for {feed_url}: {e}")
            self.db.rollback()
    
    def get_feed_status(self) -> List[Dict]:
        """모든 피드 상태 가져오기"""
        statuses = self.db.query(FeedStatus).all()
        return [
            {
                'feed_url': status.feed_url,
                'last_success': status.last_success.isoformat() if status.last_success else None,
                'last_error': status.last_error.isoformat() if status.last_error else None,
                'error_count': status.error_count,
                'success_count': status.success_count,
                'last_entries_count': status.last_entries_count,
            }
            for status in statuses
        ]
    
    def cleanup_old_articles(self, days: int = 30) -> int:
        """오래된 기사들 삭제"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted_count = self.db.query(NewsArticle).filter(
            NewsArticle.published < cutoff
        ).delete()
        
        self.db.commit()
        logger.info(f"Cleaned up {deleted_count} old articles")
        return deleted_count
