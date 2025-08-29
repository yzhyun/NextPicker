# app/slack_notifier.py
import os
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SlackNotifier:
    """슬랙 알림을 보내는 클래스"""
    
    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.enabled = os.getenv("ENABLE_SLACK_NOTIFICATIONS", "false").lower() == "true"
        
        if not self.enabled:
            logger.info("Slack notifications are disabled")
        elif not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not set, notifications disabled")
            self.enabled = False
    
    def send_message(self, message: str, channel: Optional[str] = None) -> bool:
        """
        슬랙으로 메시지를 보냅니다.
        
        Args:
            message: 보낼 메시지
            channel: 채널명 (선택사항, 기본값 사용)
        
        Returns:
            성공 여부
        """
        if not self.enabled:
            return False
            
        try:
            payload = {"text": message}
            if channel:
                payload["channel"] = channel
                
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Slack message sent successfully: {message[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False
    
    def notify_data_saved(self, country: str, count: int) -> None:
        """데이터 저장 시 알림"""
        message = f"📰 뉴스 데이터 저장 완료\n• 국가: {country.upper()}\n• 저장된 기사: {count}개"
        self.send_message(message)
    
    def notify_error(self, error: str, context: str = "") -> None:
        """오류 발생 시 알림"""
        message = f"❌ 오류 발생\n• 컨텍스트: {context}\n• 오류: {error}"
        self.send_message(message)
    
    def notify_server_start(self) -> None:
        """서버 시작 시 알림"""
        message = "🚀 NextPicker 서버가 시작되었습니다."
        self.send_message(message)
    
    def notify_feed_refresh(self, success_count: int, total_count: int) -> None:
        """피드 새로고침 완료 시 알림"""
        message = f"🔄 피드 새로고침 완료\n• 성공: {success_count}/{total_count}"
        self.send_message(message)

# 전역 인스턴스
slack = SlackNotifier()
