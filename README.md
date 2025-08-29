# NextPicker

News aggregation service with Slack notifications.

<!-- Trigger Vercel redeploy -->

간단하고 효율적인 뉴스 수집 및 조회 서비스입니다.

## ✨ 주요 기능

- **미국/한국 뉴스 수집**: RSS 피드에서 최신 뉴스를 자동으로 수집
- **웹 인터페이스**: 직관적인 웹 페이지에서 뉴스 조회
- **슬랙 알림**: 데이터 저장, 오류 발생 시 자동 알림
- **Vercel 배포**: 무료 클라우드 배포 지원
- **간단한 구조**: 이해하기 쉬운 코드 구조

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`env.example` 파일을 참고하여 `.env` 파일을 생성하세요:

```bash
# 슬랙 알림 설정 (선택사항)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
ENABLE_SLACK_NOTIFICATIONS=true

# 로컬 개발용 SQLite (기본값)
# DATABASE_URL=sqlite:///./news.db
```

### 3. 서버 실행

```bash
uvicorn app.main:app --reload
```

브라우저에서 `http://localhost:8000/news`로 접속하세요.

## 📊 API 엔드포인트

| 엔드포인트 | 설명 |
|-----------|------|
| `/news` | 메인 뉴스 페이지 (미국+한국) |
| `/news/us` | 미국 뉴스만 |
| `/news/kr` | 한국 뉴스만 |
| `/api/news` | JSON 형태 뉴스 데이터 |
| `/api/refresh` | 뉴스 새로고침 |
| `/api/status` | 서버 상태 확인 |
| `/health` | 헬스체크 |

## 🔧 슬랙 알림 설정

1. 슬랙 워크스페이스에서 Incoming Webhook 앱 추가
2. 웹훅 URL 복사
3. `.env` 파일에 설정:

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
ENABLE_SLACK_NOTIFICATIONS=true
```

### 알림 이벤트

- 🚀 **서버 시작**: 앱이 시작될 때
- 📰 **데이터 저장**: 새 뉴스가 저장될 때
- 🔄 **피드 새로고침**: RSS 피드 업데이트 완료 시
- ❌ **오류 발생**: 예외 발생 시

## ☁️ Vercel 배포

### 1. Supabase PostgreSQL 설정

1. [Supabase](https://supabase.com)에서 새 프로젝트 생성
2. Database → Settings → Connection string 복사
3. Vercel 환경 변수에 설정

### 2. Vercel 배포

```bash
# Vercel CLI 설치
npm i -g vercel

# 배포
vercel
```

### 3. 환경 변수 설정 (Vercel 대시보드)

```
DATABASE_URL=postgresql://username:password@host:port/database
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
ENABLE_SLACK_NOTIFICATIONS=true
```

## 📁 프로젝트 구조

```
NextPicker/
├── app/
│   ├── main.py              # FastAPI 메인 앱
│   ├── database.py          # 데이터베이스 설정
│   ├── news_service.py      # 뉴스 수집 로직
│   └── slack_notifier.py    # 슬랙 알림
├── templates/
│   └── index.html           # 웹 페이지 템플릿
├── static/
│   └── style.css            # 스타일시트
├── requirements.txt         # Python 의존성
├── vercel.json             # Vercel 배포 설정
└── env.example             # 환경 변수 예시
```

## 🔄 RSS 피드

### 미국 뉴스
- BBC News
- CNN
- NPR

### 한국 뉴스
- 연합뉴스
- The Korea Herald
- The Korea Times

## 🛠️ 개발

### 로컬 개발

```bash
# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 데이터베이스 초기화
python -c "from app.database import init_db; init_db()"
```

### 테스트

```bash
# API 테스트
curl http://localhost:8000/api/news
curl http://localhost:8000/api/status
```

## 📝 라이센스

MIT License
