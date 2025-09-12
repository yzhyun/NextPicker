# app/api/news.py
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db, NewsArticle
from app.news_service import get_recent_news, get_news_by_section
# from app.schemas import NewsResponse
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


@router.get("/economy-politics")
async def get_economy_politics_news(
    days: int = Query(1, ge=1, le=30, description="Days to look back"),
    limit: int = Query(20, ge=1, le=100, description="Number of articles per country")
):
    """경제/정치 뉴스 조회 - 이미 분류된 섹션으로 필터링"""
    try:
        days, limit = validate_pagination_params(days, limit)
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        db = next(get_db())
        try:
            # 단순하게 섹션만으로 필터링 (이미 DB에서 분류됨)
            articles = db.query(NewsArticle).filter(
                NewsArticle.published >= cutoff_date,
                NewsArticle.section.in_(['business', 'politics'])
            ).order_by(NewsArticle.published.desc()).limit(limit * 2).all()
            
            # 국가별로 분리
            kr_articles = [a for a in articles if a.country == 'KR'][:limit]
            us_articles = [a for a in articles if a.country == 'US'][:limit]
            
            # 기사를 표준 형식으로 변환
            all_articles = [format_news_article(article) for article in articles]
            
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


@router.get("/sections/{section}")
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
        
        # 직접 데이터베이스에서 조회
        db = next(get_db())
        try:
            from datetime import datetime, timedelta
            
            # 날짜 기준으로 뉴스 가져오기
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            query = db.query(NewsArticle).filter(
                NewsArticle.section == section,
                NewsArticle.published >= cutoff_date
            )
            
            if country:
                query = query.filter(NewsArticle.country == country.upper())
            
            articles = query.order_by(NewsArticle.published.desc()).limit(limit).all()
            
            news = [format_news_article(article) for article in articles]
        finally:
            db.close()
        
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


@router.get("/{country}")
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
