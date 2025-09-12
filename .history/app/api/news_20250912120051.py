# app/api/news.py
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db, NewsArticle
from app.news_service import get_recent_news, get_news_by_section
from app.schemas import NewsResponse
from app.utils import (
    create_success_response, 
    handle_api_error, 
    validate_country, 
    validate_section,
    validate_pagination_params,
    format_news_article
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/news", tags=["news"])


@router.get("/")
async def get_all_news(
    days_us: int = Query(1, ge=1, le=30, description="US news days"),
    days_kr: int = Query(1, ge=1, le=30, description="KR news days"),
    limit: int = Query(30, ge=1, le=100, description="Limit per country")
):
    """전체 뉴스 조회 (미국 + 한국)"""
    try:
        validate_pagination_params(days_us, limit)
        validate_pagination_params(days_kr, limit)
        
        news_us = get_recent_news('US', days=days_us, limit=limit)
        news_kr = get_recent_news('KR', days=days_kr, limit=limit)
        
        all_news = news_us + news_kr
        
        meta = {
            "total": len(all_news),
            "us_count": len(news_us),
            "kr_count": len(news_kr),
            "days_us": days_us,
            "days_kr": days_kr,
            "limit": limit
        }
        
        return create_success_response(
            data=all_news,
            message=f"Retrieved {len(all_news)} news articles",
            meta=meta
        )
        
    except Exception as e:
        raise handle_api_error(e, "Failed to get all news")


@router.get("/{country}", response_model=NewsResponse)
async def get_news_by_country(
    country: str,
    days: int = Query(1, ge=1, le=30, description="Days to look back"),
    limit: int = Query(30, ge=1, le=100, description="Number of articles")
):
    """국가별 뉴스 조회"""
    try:
        country = validate_country(country)
        days, limit = validate_pagination_params(days, limit)
        
        news = get_recent_news(country, days=days, limit=limit)
        
        meta = {
            "total": len(news),
            "country": country,
            "days": days,
            "limit": limit
        }
        
        return create_success_response(
            data=news,
            message=f"Retrieved {len(news)} {country} news articles",
            meta=meta
        )
        
    except Exception as e:
        raise handle_api_error(e, f"Failed to get {country} news")


@router.get("/sections/{section}", response_model=NewsResponse)
async def get_news_by_section(
    section: str,
    country: Optional[str] = Query(None, description="Country filter"),
    days: int = Query(1, ge=1, le=30, description="Days to look back"),
    limit: int = Query(50, ge=1, le=100, description="Number of articles")
):
    """섹션별 뉴스 조회"""
    try:
        section = validate_section(section)
        if country:
            country = validate_country(country)
        days, limit = validate_pagination_params(days, limit)
        
        news = get_news_by_section(section, country, days, limit)
        
        meta = {
            "total": len(news),
            "section": section,
            "country": country,
            "days": days,
            "limit": limit
        }
        
        return create_success_response(
            data=news,
            message=f"Retrieved {len(news)} {section} news articles",
            meta=meta
        )
        
    except Exception as e:
        raise handle_api_error(e, f"Failed to get {section} news")


@router.get("/economy-politics", response_model=NewsResponse)
async def get_economy_politics_news(
    days: int = Query(1, ge=1, le=30, description="Days to look back"),
    limit: int = Query(20, ge=1, le=100, description="Number of articles per country")
):
    """경제/정치 뉴스 조회"""
    try:
        days, limit = validate_pagination_params(days, limit)
        
        # 경제, 정치 기사 필터링 조건
        economy_politics_filter = or_(
            NewsArticle.section.in_(['business', 'economy', 'politics', 'finance']),
            NewsArticle.title.ilike('%경제%'),
            NewsArticle.title.ilike('%정치%'),
            NewsArticle.title.ilike('%금융%'),
            NewsArticle.title.ilike('%투자%'),
            NewsArticle.title.ilike('%주식%'),
            NewsArticle.title.ilike('%부동산%'),
            NewsArticle.title.ilike('%기업%'),
            NewsArticle.title.ilike('%정부%'),
            NewsArticle.title.ilike('%의회%'),
            NewsArticle.title.ilike('%대통령%'),
            NewsArticle.title.ilike('%총리%'),
            NewsArticle.title.ilike('%장관%'),
            NewsArticle.title.ilike('%economy%'),
            NewsArticle.title.ilike('%politics%'),
            NewsArticle.title.ilike('%business%'),
            NewsArticle.title.ilike('%finance%'),
            NewsArticle.title.ilike('%government%'),
            NewsArticle.title.ilike('%congress%'),
            NewsArticle.title.ilike('%senate%'),
            NewsArticle.title.ilike('%president%'),
            NewsArticle.title.ilike('%federal%'),
            NewsArticle.title.ilike('%market%'),
            NewsArticle.title.ilike('%stock%'),
            NewsArticle.title.ilike('%investment%')
        )
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        db = next(get_db())
        try:
            # 한국 경제, 정치 기사
            kr_articles = db.query(NewsArticle).filter(
                NewsArticle.country == 'KR',
                NewsArticle.published >= cutoff_date,
                economy_politics_filter
            ).order_by(NewsArticle.published.desc()).limit(limit).all()
            
            # 미국 경제, 정치 기사
            us_articles = db.query(NewsArticle).filter(
                NewsArticle.country == 'US',
                NewsArticle.published >= cutoff_date,
                economy_politics_filter
            ).order_by(NewsArticle.published.desc()).limit(limit).all()
            
            all_articles = [format_news_article(article) for article in kr_articles + us_articles]
            
            meta = {
                "total": len(all_articles),
                "kr_count": len(kr_articles),
                "us_count": len(us_articles),
                "days": days,
                "limit": limit
            }
            
            return create_success_response(
                data=all_articles,
                message=f"Retrieved {len(all_articles)} economy/politics news articles",
                meta=meta
            )
            
        finally:
            db.close()
            
    except Exception as e:
        raise handle_api_error(e, "Failed to get economy/politics news")
