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
    """AI 분석용 미국 뉴스 데이터 (경제, 정치, 기술만)"""
    try:
        days, limit = validate_pagination_params(days, limit)
        
        db = next(get_db())
        try:
            repo = NewsRepository(db)
            # 경제, 정치, 기술 섹션만 조회
            target_sections = ['business', 'politics', 'technology']
            all_articles = []
            
            for section in target_sections:
                articles = repo.get_news_by_section(section, 'US', days, limit)
                all_articles.extend(articles)
            
            # 섹션별로 정렬 (경제, 정치, 기술 순)
            section_order = {'business': 0, 'politics': 1, 'technology': 2}
            all_articles.sort(key=lambda x: section_order.get(x.get('section', ''), 999))
            
        finally:
            db.close()
        
        # 단순 문자열 데이터 생성
        text_data = []
        for article in all_articles:
            text_row = f"제목: {article['title']}\n출처: {article['source']}\n요약: {article['summary'] or '요약 없음'}\n섹션: {article['section'] or 'general'}\n국가: {article['country']}\n---"
            text_data.append(text_row)
        
        return create_success_response(
            data=text_data,
            message=f"Retrieved {len(text_data)} US news articles for analysis (business, politics, technology only)",
            meta={
                "count": len(text_data),
                "sections": target_sections,
                "days": days,
                "limit": limit
            }
        )
            
    except Exception as e:
        raise handle_api_error(e, "Failed to get US news for analysis")
