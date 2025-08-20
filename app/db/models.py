from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Index
from sqlalchemy.sql import func
from app.db.database import Base

class NewsArticle(Base):
    __tablename__ = "news_articles"
    
    id = Column(String(32), primary_key=True)  # MD5 hash of URL
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False, unique=True)
    source = Column(String(200), nullable=False)
    published = Column(DateTime(timezone=True), nullable=False)
    summary = Column(Text)
    country = Column(String(2), nullable=False)  # 'us' or 'kr'
    local_tz = Column(String(10), nullable=False)  # 'ET' or 'KST'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 인덱스 추가로 검색 성능 향상
    __table_args__ = (
        Index('idx_published', 'published'),
        Index('idx_country', 'country'),
        Index('idx_source', 'source'),
    )

class FeedStatus(Base):
    __tablename__ = "feed_status"
    
    id = Column(Integer, primary_key=True)
    feed_url = Column(String(1000), nullable=False, unique=True)
    last_success = Column(DateTime(timezone=True))
    last_error = Column(DateTime(timezone=True))
    error_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    last_entries_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
