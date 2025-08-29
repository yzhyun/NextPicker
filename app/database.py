# app/database.py
import os
import logging
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

logger = logging.getLogger(__name__)

# 환경 변수에서 DB URL 가져오기 (Vercel Postgres 우선)
DATABASE_URL = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")

# Vercel Postgres URL 처리
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    # Heroku/Vercel 스타일 URL을 SQLAlchemy 형식으로 변환
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 로컬 개발용 SQLite (DATABASE_URL이 없을 때)
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./news.db"
    logger.info("Using local SQLite database")
else:
    logger.info("Using Vercel Postgres database")

# 엔진 생성
engine = create_engine(
    DATABASE_URL,
    echo=False,  # SQL 로그 비활성화
    pool_pre_ping=True,  # 연결 상태 확인
    pool_recycle=300,  # 5분마다 연결 재생성
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 베이스 클래스
Base = declarative_base()

class NewsArticle(Base):
    """뉴스 기사 모델"""
    __tablename__ = "news_articles"
    
    id = Column(String(32), primary_key=True)  # URL의 MD5 해시
    title = Column(String(500), nullable=False)
    url = Column(String(1000), unique=True, nullable=False)
    source = Column(String(100), nullable=False)
    published = Column(DateTime, nullable=False)
    summary = Column(Text)
    section = Column(String(50))  # 섹션 분류 (politics, business, technology, etc.)
    country = Column(String(2), nullable=False)  # 'US' 또는 'KR'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<NewsArticle(title='{self.title[:30]}...', country='{self.country}')>"

def get_db():
    """데이터베이스 세션을 반환합니다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """데이터베이스 테이블을 생성합니다."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
