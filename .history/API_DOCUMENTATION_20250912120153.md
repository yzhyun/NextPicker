# NextPicker News API Documentation

## 개요
NextPicker News는 AI 기반 뉴스 수집 및 분석 서비스입니다. 이 문서는 v3.0.0 API의 사용법을 설명합니다.

## 기본 정보
- **Base URL**: `https://your-domain.com`
- **API Version**: v3.0.0
- **Content-Type**: `application/json`

## 응답 형식

### 성공 응답
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... },
  "meta": {
    "total": 100,
    "page": 1,
    "limit": 30,
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "error": null
}
```

### 에러 응답
```json
{
  "success": false,
  "message": "Error description",
  "data": null,
  "meta": {},
  "error": {
    "code": "error_code",
    "details": { ... }
  }
}
```

## API 엔드포인트

### 1. 뉴스 API (`/api/v1/news`)

#### 1.1 전체 뉴스 조회
```http
GET /api/v1/news/
```

**파라미터:**
- `days_us` (int, optional): 미국 뉴스 조회 일수 (기본값: 1, 범위: 1-30)
- `days_kr` (int, optional): 한국 뉴스 조회 일수 (기본값: 1, 범위: 1-30)
- `limit` (int, optional): 국가별 최대 기사 수 (기본값: 30, 범위: 1-100)

**응답:**
```json
{
  "success": true,
  "message": "Retrieved 60 news articles",
  "data": [
    {
      "id": "abc123",
      "title": "뉴스 제목",
      "url": "https://example.com/article",
      "source": "뉴스 소스",
      "published": "2024-01-01T12:00:00Z",
      "summary": "뉴스 요약",
      "section": "politics",
      "country": "KR",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ],
  "meta": {
    "total": 60,
    "us_count": 30,
    "kr_count": 30,
    "days_us": 1,
    "days_kr": 1,
    "limit": 30
  }
}
```

#### 1.2 국가별 뉴스 조회
```http
GET /api/v1/news/{country}
```

**파라미터:**
- `country` (string, required): 국가 코드 (`US` 또는 `KR`)
- `days` (int, optional): 조회 일수 (기본값: 1, 범위: 1-30)
- `limit` (int, optional): 최대 기사 수 (기본값: 30, 범위: 1-100)

#### 1.3 섹션별 뉴스 조회
```http
GET /api/v1/news/sections/{section}
```

**파라미터:**
- `section` (string, required): 섹션명 (`politics`, `business`, `technology`, `sports`, `entertainment`, `health`, `science`, `general`)
- `country` (string, optional): 국가 필터 (`US` 또는 `KR`)
- `days` (int, optional): 조회 일수 (기본값: 1, 범위: 1-30)
- `limit` (int, optional): 최대 기사 수 (기본값: 50, 범위: 1-100)

#### 1.4 경제/정치 뉴스 조회
```http
GET /api/v1/news/economy-politics
```

**파라미터:**
- `days` (int, optional): 조회 일수 (기본값: 1, 범위: 1-30)
- `limit` (int, optional): 국가별 최대 기사 수 (기본값: 20, 범위: 1-100)

### 2. 피드 API (`/api/v1/feeds`)

#### 2.1 피드 목록 조회
```http
GET /api/v1/feeds/
```

**응답:**
```json
{
  "success": true,
  "message": "Retrieved feed information",
  "data": [
    {
      "country": "US",
      "section": "business",
      "feeds": [
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://news.google.com/rss/headlines/section/BUSINESS?hl=en&gl=US&ceid=US:en"
      ]
    }
  ],
  "meta": {
    "total_feeds": 10
  }
}
```

#### 2.2 피드 새로고침
```http
POST /api/v1/feeds/refresh
```

**응답:**
```json
{
  "success": true,
  "message": "Feed refresh completed. Collected 150 articles",
  "data": {
    "US": 75,
    "KR": 75
  },
  "meta": {
    "total_articles": 150
  }
}
```

### 3. 분석 API (`/api/v1/analysis`)

#### 3.1 AI 분석용 데이터 (TSV 형식)
```http
GET /api/v1/analysis/us-news
```

**파라미터:**
- `days` (int, optional): 조회 일수 (기본값: 1, 범위: 1-30)
- `limit` (int, optional): 최대 기사 수 (기본값: 50, 범위: 1-100)

**응답:**
```json
{
  "success": true,
  "message": "Retrieved 50 US news articles for analysis",
  "data": {
    "format": "tsv",
    "content": [
      "제목\tURL\t소스\t발행일\t요약\t섹션\t국가",
      "뉴스 제목\thttps://example.com\t소스명\t2024-01-01\t요약문\tpolitics\tUS"
    ]
  },
  "meta": {
    "count": 50,
    "days": 1,
    "limit": 50
  }
}
```

### 4. 알림 API (`/api/v1/notifications`)

#### 4.1 Slack 경제/정치 뉴스 알림
```http
POST /api/v1/notifications/slack/economy-politics
```

**응답:**
```json
{
  "success": true,
  "message": "Economy/politics notification sent successfully",
  "data": {
    "KR": 20,
    "US": 20,
    "total": 40
  },
  "meta": {
    "kr_articles": 20,
    "us_articles": 20,
    "total_articles": 40
  }
}
```

### 5. 헬스체크 API (`/api/v1`)

#### 5.1 서버 상태 확인
```http
GET /api/v1/health
```

**응답:**
```json
{
  "success": true,
  "message": "Health check completed",
  "data": {
    "status": "healthy",
    "timestamp": 1704067200.0,
    "database": "healthy",
    "message": "NextPicker News is running"
  },
  "meta": {}
}
```

## 웹 페이지 엔드포인트

### HTML 페이지
- `GET /` - 루트 리다이렉트
- `GET /news` - 메인 뉴스 페이지 (미국 + 한국)
- `GET /news/us` - 미국 뉴스만 표시
- `GET /news/kr` - 한국 뉴스만 표시
- `GET /view` - 레거시 호환성 리다이렉트

### 레거시 API (호환성 유지)
- `GET /health` - 레거시 헬스체크

## 에러 코드

| 코드 | 설명 |
|------|------|
| `400` | 잘못된 요청 (파라미터 오류) |
| `404` | 리소스를 찾을 수 없음 |
| `500` | 서버 내부 오류 |

## 사용 예시

### Python
```python
import requests

# 전체 뉴스 조회
response = requests.get("https://your-domain.com/api/v1/news/")
data = response.json()

# 미국 뉴스만 조회
response = requests.get("https://your-domain.com/api/v1/news/US?days=3&limit=50")
data = response.json()

# 정치 뉴스 조회
response = requests.get("https://your-domain.com/api/v1/news/sections/politics?country=KR")
data = response.json()

# 피드 새로고침
response = requests.post("https://your-domain.com/api/v1/feeds/refresh")
data = response.json()
```

### JavaScript
```javascript
// 전체 뉴스 조회
const response = await fetch('https://your-domain.com/api/v1/news/');
const data = await response.json();

// 경제/정치 뉴스 조회
const response = await fetch('https://your-domain.com/api/v1/news/economy-politics?days=2&limit=30');
const data = await response.json();
```

## 변경 사항 (v3.0.0)

### 새로운 기능
- ✅ 통일된 API 응답 형식
- ✅ 개선된 에러 처리
- ✅ API 버전 관리 (`/api/v1/`)
- ✅ 모듈화된 라우터 구조
- ✅ 향상된 파라미터 검증
- ✅ 자동 API 문서화 (Swagger UI)

### 제거된 기능
- ❌ 중복된 API 엔드포인트
- ❌ 일관성 없는 응답 형식
- ❌ 분산된 에러 처리

### 호환성
- ✅ 기존 웹 페이지 엔드포인트 유지
- ✅ 레거시 API 엔드포인트 유지
- ✅ 기존 데이터베이스 스키마 호환
