# app/api/cleanup.py
import logging
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils import create_success_response, handle_api_error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/cleanup", tags=["cleanup"])


@router.post("/html-tags")
async def cleanup_html_tags():
    """데이터베이스에서 HTML 태그를 정리합니다."""
    try:
        db = next(get_db())
        try:
            # HTML 태그 제거 쿼리
            cleanup_query = text("""
                UPDATE news_articles 
                SET summary = REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        REGEXP_REPLACE(
                            REGEXP_REPLACE(
                                REGEXP_REPLACE(
                                    REGEXP_REPLACE(
                                        REGEXP_REPLACE(
                                            REGEXP_REPLACE(
                                                REGEXP_REPLACE(
                                                    REGEXP_REPLACE(summary, '&lt;', '<', 'g'),
                                                    '&gt;', '>', 'g'
                                                ),
                                                '&amp;', '&', 'g'
                                            ),
                                            '&quot;', '"', 'g'
                                        ),
                                        '&#34;', '"', 'g'
                                    ),
                                    '<[^>]+>', '', 'g'
                                ),
                                '  ', ' ', 'g'
                            ),
                            '   ', ' ', 'g'
                        ),
                        '    ', ' ', 'g'
                    ),
                    '^\\s+|\\s+$', '', 'g'
                )
                WHERE summary LIKE '%<%' OR summary LIKE '%&lt;%'
            """)
            
            result = db.execute(cleanup_query)
            db.commit()
            
            return create_success_response(
                data={"updated_rows": result.rowcount},
                message=f"Cleaned HTML tags from {result.rowcount} articles"
            )
            
        finally:
            db.close()
            
    except Exception as e:
        raise handle_api_error(e, "Failed to cleanup HTML tags")
