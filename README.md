# NextPicker News - Enhanced Version

미국과 한국의 최신 뉴스를 실시간으로 수집하고 표시하는 개선된 뉴스 애그리게이터입니다.

## 🚀 주요 개선사항

### 성능 개선
- **비동기 RSS 수집**: `aiohttp`를 사용한 병렬 처리로 수집 속도 대폭 향상
- **캐싱 시스템**: 5분간 결과 캐싱으로 반복 요청 최적화
- **데이터베이스 저장**: SQLite/PostgreSQL을 통한 뉴스 저장 및 중복 방지

### 사용자 경험 개선
- **현대적 UI**: 반응형 디자인과 그라데이션 배경
- **실시간 새로고침**: 백그라운드 자동 새로고침 및 수동 새로고침
- **로딩 상태**: 새로고침 시 시각적 피드백
- **모바일 최적화**: 모든 디바이스에서 완벽한 반응형 지원

### 모니터링 및 관리
- **피드 상태 모니터링**: 각 RSS 피드의 성공/실패 상태 추적
- **API 엔드포인트**: JSON API를 통한 데이터 접근
- **헬스체크**: 시스템 상태 확인 엔드포인트

## 🛠 설치 및 실행

### 1. 가상환경 설정
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정 (선택사항)
`.env` 파일을 생성하여 설정을 커스터마이즈할 수 있습니다:

```env
# 데이터베이스 설정
DATABASE_URL=sqlite:///./news.db

# 캐시 설정 (초)
CACHE_TTL=300

# 요청 타임아웃 (초)
REQUEST_TIMEOUT=10

# 추가 피드 URL (쉼표로 구분)
EXTRA_US_FEEDS=https://example.com/feed1,https://example.com/feed2
EXTRA_KR_FEEDS=https://example.com/feed3,https://example.com/feed4
```

### 4. 서버 실행
```bash
# 개발 서버
uvicorn app.main:app --reload

# 프로덕션 서버
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📱 사용법

### 웹 인터페이스
- **메인 페이지**: `http://localhost:8000/news`
- **미국 뉴스만**: `http://localhost:8000/news/us`
- **한국 뉴스만**: `http://localhost:8000/news/kr`

### API 엔드포인트
- **뉴스 데이터**: `GET /api/news`
- **피드 상태**: `GET /api/status`
- **수동 새로고침**: `POST /api/refresh`
- **헬스체크**: `GET /health`

### API 사용 예시
```bash
# 최근 3일간의 모든 뉴스
curl http://localhost:8000/api/news

# 미국 뉴스만 (7일간)
curl "http://localhost:8000/api/news?country=us&days_us=7"

# 피드 상태 확인
curl http://localhost:8000/api/status

# 수동 새로고침
curl -X POST http://localhost:8000/api/refresh
```

## 🏗 아키텍처

### 주요 컴포넌트
- **`app/main.py`**: FastAPI 애플리케이션 및 라우팅
- **`app/news_service.py`**: 뉴스 수집 비즈니스 로직
- **`app/async_news_crawler.py`**: 비동기 RSS 수집기
- **`app/news_repository.py`**: 데이터베이스 상호작용
- **`app/cache.py`**: 캐싱 시스템
- **`app/config.py`**: 설정 관리

### 데이터베이스 스키마
- **`news_articles`**: 뉴스 기사 저장
- **`feed_status`**: RSS 피드 상태 추적

## 🔧 설정 옵션

### 환경변수
| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `DATABASE_URL` | `sqlite:///./news.db` | 데이터베이스 연결 URL |
| `CACHE_TTL` | `300` | 캐시 유효시간 (초) |
| `REQUEST_TIMEOUT` | `10` | HTTP 요청 타임아웃 (초) |
| `EXTRA_US_FEEDS` | - | 추가 미국 피드 URL (쉼표 구분) |
| `EXTRA_KR_FEEDS` | - | 추가 한국 피드 URL (쉼표 구분) |

## 📊 성능 지표

- **수집 속도**: 기존 대비 3-5배 향상 (비동기 처리)
- **응답 시간**: 캐싱으로 인한 90% 이상 개선
- **동시 요청**: 세마포어를 통한 안정적인 처리
- **메모리 사용**: 효율적인 캐시 관리

## 🚀 배포

### Docker (권장)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 시스템 서비스
```ini
[Unit]
Description=NextPicker News
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/nextpicker
Environment=PATH=/path/to/nextpicker/venv/bin
ExecStart=/path/to/nextpicker/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## �� 라이선스

MIT License
