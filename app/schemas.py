# app/schemas.py
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """기본 API 응답 형식"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    meta: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    error: Optional[Dict[str, Any]] = None


class NewsArticle(BaseModel):
    """뉴스 기사 스키마"""
    id: str
    title: str
    url: str
    source: str
    published: datetime
    summary: Optional[str] = None
    section: Optional[str] = None
    country: str
    created_at: Optional[datetime] = None


class NewsResponse(BaseResponse):
    """뉴스 응답 스키마"""
    data: List[NewsArticle]
    meta: Dict[str, Any] = Field(default_factory=dict)


class NewsSummaryResponse(BaseResponse):
    """뉴스 요약 응답 스키마"""
    data: Dict[str, Any]
    meta: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseResponse):
    """에러 응답 스키마"""
    success: bool = False
    data: Optional[Any] = None


class HealthResponse(BaseResponse):
    """헬스체크 응답 스키마"""
    data: Dict[str, Any] = Field(default_factory=dict)


class RefreshResponse(BaseResponse):
    """새로고침 응답 스키마"""
    data: Dict[str, int] = Field(default_factory=dict)


class FeedInfo(BaseModel):
    """피드 정보 스키마"""
    country: str
    section: str
    feeds: List[str]


class FeedsResponse(BaseResponse):
    """피드 목록 응답 스키마"""
    data: List[FeedInfo]
