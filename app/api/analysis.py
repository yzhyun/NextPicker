# app/api/analysis.py
import logging
from fastapi import APIRouter, Query

from app.database import get_db
from app.repositories import NewsRepository
from app.utils import create_success_response, handle_api_error, validate_pagination_params, format_news_article

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
            repo = NewsRepository(db)
            articles = repo.get_us_news_for_analysis(days=days, limit=limit)
        finally:
            db.close()
        
        # 단순 문자열 데이터 생성
        text_data = []
        for article in articles:
            text_row = f"제목: {article['title']}\n출처: {article['source']}\n요약: {article['summary'] or '요약 없음'}\n섹션: {article['section'] or 'general'}\n국가: {article['country']}\n---"
            text_data.append(text_row)
        
        return create_success_response(
            data=text_data,
            message=f"Retrieved {len(text_data)} US news articles for analysis",
            meta={
                "count": len(text_data),
                "days": days,
                "limit": limit
            }
        )
            
    except Exception as e:
        raise handle_api_error(e, "Failed to get US news for analysis")
