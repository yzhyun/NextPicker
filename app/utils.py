# app/utils.py
import logging
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from app.schemas import BaseResponse, ErrorResponse

logger = logging.getLogger(__name__)


def create_success_response(
    data: Any = None,
    message: str = None,
    meta: Dict[str, Any] = None
) -> BaseResponse:
    """성공 응답 생성"""
    return BaseResponse(
        success=True,
        message=message,
        data=data,
        meta=meta or {}
    )


def create_error_response(
    message: str,
    error_code: str = None,
    details: Dict[str, Any] = None
) -> ErrorResponse:
    """에러 응답 생성"""
    return ErrorResponse(
        success=False,
        message=message,
        error={
            "code": error_code,
            "details": details or {}
        }
    )


def handle_api_error(
    error: Exception,
    context: str = "API Error",
    status_code: int = 500
) -> JSONResponse:
    """API 에러 처리"""
    logger.error(f"{context}: {str(error)}")
    
    error_response = create_error_response(
        message=f"{context}: {str(error)}",
        error_code=context.lower().replace(" ", "_"),
        details={"exception_type": type(error).__name__}
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.dict()
    )


def validate_country(country: str) -> str:
    """국가 코드 검증 및 정규화"""
    if not country:
        raise HTTPException(status_code=400, detail="Country parameter is required")
    
    country = country.upper()
    if country not in ['US', 'KR']:
        raise HTTPException(status_code=400, detail="Country must be 'US' or 'KR'")
    
    return country


def validate_section(section: str) -> str:
    """섹션 검증 및 정규화"""
    if not section:
        raise HTTPException(status_code=400, detail="Section parameter is required")
    
    valid_sections = [
        'politics', 'business', 'technology', 'sports', 
        'entertainment', 'health', 'science', 'general'
    ]
    
    section = section.lower()
    if section not in valid_sections:
        raise HTTPException(
            status_code=400, 
            detail=f"Section must be one of: {', '.join(valid_sections)}"
        )
    
    return section


def validate_pagination_params(days: int = 1, limit: int = 30) -> tuple[int, int]:
    """페이지네이션 파라미터 검증"""
    if days < 1 or days > 30:
        raise HTTPException(status_code=400, detail="Days must be between 1 and 30")
    
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    
    return days, limit


def format_news_article(article: Any) -> Dict[str, Any]:
    """뉴스 기사를 표준 형식으로 변환"""
    return {
        "id": article.id,
        "title": article.title,
        "url": article.url,
        "source": article.source,
        "published": article.published.isoformat() if article.published else None,
        "summary": article.summary,
        "section": article.section,
        "country": article.country,
        "created_at": article.created_at.isoformat() if article.created_at else None
    }
