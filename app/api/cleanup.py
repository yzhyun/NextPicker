# app/api/cleanup.py
import logging
import os
import re
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils import create_success_response, handle_api_error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/cleanup", tags=["cleanup"])


def clean_html_summary(summary: str) -> str:
    """HTML 태그를 제거하고 텍스트를 정리합니다."""
    if not summary:
        return ""
    
    # HTML 엔티티 디코딩
    text = summary.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"').replace('&#34;', '"')
    
    # HTML 태그 제거
    text = re.sub(r'<[^>]*>', '', text)
    
    # URL 패턴 제거
    text = re.sub(r'https?://[^\s]+', '', text)
    
    # 공백 정리
    text = ' '.join(text.split())
    
    return text


@router.post("/html-tags")
async def cleanup_html_tags():
    """데이터베이스에서 HTML 태그를 정리합니다."""
    try:
        db = next(get_db())
        try:
            # 데이터베이스 타입 확인
            is_postgresql = os.getenv("DATABASE_URL", "").startswith("postgres")
            
            if is_postgresql:
                # PostgreSQL용 쿼리
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
                updated_count = result.rowcount
            else:
                # SQLite용 - Python에서 처리
                articles_query = text("""
                    SELECT id, summary FROM news_articles 
                    WHERE summary LIKE '%<%' OR summary LIKE '%&lt;%'
                """)
                
                articles = db.execute(articles_query).fetchall()
                updated_count = 0
                
                for article_id, old_summary in articles:
                    cleaned_summary = clean_html_summary(old_summary)
                    if cleaned_summary != old_summary:
                        update_query = text("""
                            UPDATE news_articles SET summary = :new_summary WHERE id = :article_id
                        """)
                        db.execute(update_query, {
                            'new_summary': cleaned_summary,
                            'article_id': article_id
                        })
                        updated_count += 1
            
            db.commit()
            
            return create_success_response(
                data={"updated_rows": updated_count},
                message=f"Cleaned HTML tags from {updated_count} articles"
            )
            
        finally:
            db.close()
            
    except Exception as e:
        raise handle_api_error(e, "Failed to cleanup HTML tags")
