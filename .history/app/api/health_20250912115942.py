# app/api/health.py
import time
import logging
from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import HealthResponse
from app.utils import create_success_response, handle_api_error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """서버 상태 확인"""
    try:
        # 데이터베이스 연결 확인
        db = next(get_db())
        try:
            # 간단한 쿼리로 DB 연결 확인
            db.execute(text("SELECT 1"))
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        finally:
            db.close()
        
        health_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "database": db_status,
            "message": "NextPicker News is running"
        }
        
        return create_success_response(
            data=health_data,
            message="Health check completed"
        )
        
    except Exception as e:
        raise handle_api_error(e, "Health check failed")
