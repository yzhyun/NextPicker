# app/api/feeds.py
import logging
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.news_service import refresh_all_feeds
from app.rss_feeds import get_all_feeds
from app.schemas import FeedsResponse, RefreshResponse
from app.utils import create_success_response, handle_api_error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/feeds", tags=["feeds"])


@router.get("/", response_model=FeedsResponse)
async def get_feeds():
    """RSS 피드 목록 조회"""
    try:
        feeds = get_all_feeds()
        
        return create_success_response(
            data=feeds,
            message="Retrieved feed information",
            meta={"total_feeds": len(feeds)}
        )
        
    except Exception as e:
        raise handle_api_error(e, "Failed to get feeds")


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_feeds():
    """뉴스 피드 새로고침"""
    try:
        result = refresh_all_feeds()
        
        total_articles = sum(result.values())
        
        return create_success_response(
            data=result,
            message=f"Feed refresh completed. Collected {total_articles} articles",
            meta={"total_articles": total_articles}
        )
        
    except Exception as e:
        raise handle_api_error(e, "Failed to refresh feeds")
