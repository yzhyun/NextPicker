# app/slack_notifier.py
import os
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class SlackNotifier:
    """슬랙 알림을 보내는 클래스"""
    
    def __init__(self):
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.channels = os.getenv("SLACK_CHANNELS", "#general").split(",")
        self.enabled = os.getenv("ENABLE_SLACK_NOTIFICATIONS", "false").lower() == "true"
        
        if not self.enabled:
            logger.info("Slack notifications are disabled")
        elif not self.bot_token:
            logger.warning("SLACK_BOT_TOKEN not set, notifications disabled")
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
            # 여러 채널에 메시지 전송
            target_channels = [channel] if channel else self.channels
            
            for target_channel in target_channels:
                target_channel = target_channel.strip()
                
                payload = {
                    "channel": target_channel,
                    "text": message
                }
                
                headers = {
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-type": "application/json"
                }
                
                response = requests.post(
                    "https://slack.com/api/chat.postMessage",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                
                result = response.json()
                if not result.get("ok"):
                    logger.error(f"Slack API error: {result.get('error')}")
                    return False
                
                logger.info(f"Slack message sent to {target_channel}: {message[:50]}...")
            
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
    
    def notify_daily_collection(self, results: Dict[str, int]) -> None:
        """일일 뉴스 수집 완료 시 알림"""
        total_news = sum(results.values())
        message = f"📰 *일일 뉴스 수집 완료!*\n"
        
        for country, count in results.items():
            message += f"• {country}: {count}개\n"
        
        message += f"• 총 {total_news}개 기사 수집\n"
        message += f"🔗 <https://lumina-next-picker.vercel.app/news|뉴스 확인하기>"
        
        self.send_message(message)
    
    def notify_collection_start(self) -> None:
        """뉴스 수집 시작 시 알림"""
        message = "🕗 일일 뉴스 수집을 시작합니다..."
        self.send_message(message)

# 전역 인스턴스
slack = SlackNotifier()
