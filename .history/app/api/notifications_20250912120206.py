# app/api/notifications.py
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import SessionLocal, NewsArticle
from app.schemas import BaseResponse
from app.slack_notifier import slack
from app.utils import create_success_response, handle_api_error

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.post("/slack/economy-politics")
async def send_economy_politics_notification():
    """경제/정치 뉴스 Slack 알림 전송"""
    try:
        # 최근 1일간 뉴스 가져오기
        cutoff_date = datetime.utcnow() - timedelta(days=1)
        
        # 경제, 정치 기사 필터링 조건
        economy_politics_filter = or_(
            NewsArticle.section.in_(['business', 'economy', 'politics', 'finance']),
            NewsArticle.title.ilike('%경제%'),
            NewsArticle.title.ilike('%정치%'),
            NewsArticle.title.ilike('%금융%'),
            NewsArticle.title.ilike('%투자%'),
            NewsArticle.title.ilike('%주식%'),
            NewsArticle.title.ilike('%부동산%'),
            NewsArticle.title.ilike('%기업%'),
            NewsArticle.title.ilike('%정부%'),
            NewsArticle.title.ilike('%의회%'),
            NewsArticle.title.ilike('%대통령%'),
            NewsArticle.title.ilike('%총리%'),
            NewsArticle.title.ilike('%장관%'),
            NewsArticle.title.ilike('%economy%'),
            NewsArticle.title.ilike('%politics%'),
            NewsArticle.title.ilike('%business%'),
            NewsArticle.title.ilike('%finance%'),
            NewsArticle.title.ilike('%government%'),
            NewsArticle.title.ilike('%congress%'),
            NewsArticle.title.ilike('%senate%'),
            NewsArticle.title.ilike('%president%'),
            NewsArticle.title.ilike('%federal%'),
            NewsArticle.title.ilike('%market%'),
            NewsArticle.title.ilike('%stock%'),
            NewsArticle.title.ilike('%investment%')
        )
        
        db = SessionLocal()
        try:
            # 한국 경제, 정치 기사 20개
            kr_articles = db.query(NewsArticle).filter(
                NewsArticle.country == 'KR',
                NewsArticle.published >= cutoff_date,
                economy_politics_filter
            ).order_by(NewsArticle.published.desc()).limit(20).all()
            
            # 미국 경제, 정치 기사 20개
            us_articles = db.query(NewsArticle).filter(
                NewsArticle.country == 'US',
                NewsArticle.published >= cutoff_date,
                economy_politics_filter
            ).order_by(NewsArticle.published.desc()).limit(20).all()
            
            # Slack 메시지 구성
            message = "📊 *경제·정치 뉴스 요약*\n\n"
            
            message += f"🇰🇷 *한국 경제·정치 기사 ({len(kr_articles)}개)*\n"
            for i, article in enumerate(kr_articles, 1):
                section_info = f"[{article.section}]" if article.section else ""
                message += f"{i}. {section_info} <{article.url}|{article.title[:45]}...>\n"
            
            message += f"\n🇺🇸 *미국 경제·정치 기사 ({len(us_articles)}개)*\n"
            for i, article in enumerate(us_articles, 1):
                section_info = f"[{article.section}]" if article.section else ""
                message += f"{i}. {section_info} <{article.url}|{article.title[:45]}...>\n"
            
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
