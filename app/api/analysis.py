# app/api/analysis.py
import logging
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import BaseResponse
from app.utils import create_success_response, handle_api_error, validate_pagination_params

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])


@router.get("/us-news")
async def get_us_news_for_analysis(
    days: int = Query(1, ge=1, le=30, description="Days to look back"),
    limit: int = Query(50, ge=1, le=100, description="Number of articles")
):
    """AI 분석용 미국 뉴스 데이터 (TSV 형식)"""
    try:
        days, limit = validate_pagination_params(days, limit)
        
        db = next(get_db())
        try:
            from datetime import datetime, timedelta
            from app.database import NewsArticle
            
            # 날짜 기준으로 뉴스 가져오기
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            articles = db.query(NewsArticle).filter(
                NewsArticle.country == 'US',
                NewsArticle.published >= cutoff_date
            ).order_by(NewsArticle.published.desc()).limit(limit).all()
            
            # TSV 데이터 생성
            tsv_data = []
            for article in articles:
                # datetime을 문자열로 변환
                published_str = article.published.isoformat() if article.published else ''
                tsv_row = f"{article.title}\t{article.url}\t{article.source}\t{published_str}\t{article.summary or ''}\t{article.section or 'general'}\t{article.country}"
                tsv_data.append(tsv_row)
            
            return create_success_response(
                data={
                    "format": "tsv",
                    "content": tsv_data
                },
                message=f"Retrieved {len(tsv_data)} US news articles for analysis",
                meta={
                    "count": len(tsv_data),
                    "days": days,
                    "limit": limit
                }
            )
            
        finally:
            db.close()
            
    except Exception as e:
        raise handle_api_error(e, "Failed to get US news for analysis")
