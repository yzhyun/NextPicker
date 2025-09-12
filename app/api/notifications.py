# app/api/notifications.py
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import NewsRepository
from app.schemas import BaseResponse
from app.slack_notifier import slack
from app.utils import create_success_response, handle_api_error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.post("/slack/economy-politics")
async def send_economy_politics_notification():
    """경제/정치 뉴스 Slack 알림 전송"""
    try:
        db = next(get_db())
        try:
            repo = NewsRepository(db)
            # 경제/정치 뉴스 조회 (이미 분류된 섹션 사용)
            all_articles = repo.get_economy_politics_news(days=1, limit=20)
            
            # 국가별로 분리
            kr_articles = [a for a in all_articles if a['country'] == 'KR']
            us_articles = [a for a in all_articles if a['country'] == 'US']
            
            # Slack 메시지 구성
            message = "📊 *경제·정치 뉴스 요약*\n\n"
            
            message += f"🇰🇷 *한국 경제·정치 기사 ({len(kr_articles)}개)*\n"
            for i, article in enumerate(kr_articles, 1):
                section_info = f"[{article['section']}]" if article['section'] else ""
                message += f"{i}. {section_info} <{article['url']}|{article['title'][:45]}...>\n"
            
            message += f"\n🇺🇸 *미국 경제·정치 기사 ({len(us_articles)}개)*\n"
            for i, article in enumerate(us_articles, 1):
                section_info = f"[{article['section']}]" if article['section'] else ""
                message += f"{i}. {section_info} <{article['url']}|{article['title'][:45]}...>\n"
            
            message += f"\n🔗 <https://lumina-next-picker.vercel.app/news|전체 뉴스 보기>"
            
            # Slack 알림 전송
            slack.send_message(message)
            
            return create_success_response(
                data={
                    "KR": len(kr_articles),
                    "US": len(us_articles),
                    "total": len(kr_articles) + len(us_articles)
                },
                message="Economy/politics notification sent successfully",
                meta={
                    "kr_articles": len(kr_articles),
                    "us_articles": len(us_articles),
                    "total_articles": len(kr_articles) + len(us_articles)
                }
            )
            
        finally:
            db.close()
            
    except Exception as e:
        raise handle_api_error(e, "Failed to send economy/politics notification")
