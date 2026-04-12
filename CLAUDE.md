# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**JOG-POST**는 Strava API를 통해 사용자의 달리기 기록을 자동으로 수집·저장하고, 운동 데이터를 조회하며, LLM을 연동하여 기록 향상 조언을 제공하는 멀티 사용자 서비스입니다.

모노레포 구조로, `backend/`(FastAPI + PostgreSQL)와 `frontend/`(Vue 3 + Vuetify)가 단일 저장소에서 관리됩니다.

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), Alembic, uv |
| DB | PostgreSQL (asyncpg 드라이버, Alembic 마이그레이션은 psycopg2-binary 사용) |
| Frontend | Vue 3 + TypeScript, Vuetify 3, Pinia, Vue Router, axios |
| 인증 | Google OAuth2 + JWT (HttpOnly 쿠키) |
| 데이터 연동 | Strava OAuth2 (data_sources 테이블로 관리, 향후 Apple Health 등 확장) |
| 배포 | Railway 또는 Render (HTTPS 자동), 로컬 개발 시 ngrok으로 Webhook 수신 |
| LLM | 추상화 인터페이스 (`services/llm.py`) — 공급자 미결정 |

## 개발 명령어

### Backend (`backend/` 디렉토리에서)

```bash
# 의존성 설치
uv sync

# 개발 서버 실행
uv run uvicorn app.main:app --reload

# 테스트 실행
uv run pytest

# 단일 테스트 파일
uv run pytest tests/test_activities.py -v

# Alembic 마이그레이션 생성 (DB가 실행 중이어야 함)
uv run alembic revision --autogenerate -m "description"

# 마이그레이션 적용
uv run alembic upgrade head
```

### Frontend (`frontend/` 디렉토리에서)

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 빌드
npm run build

# TypeScript 타입 체크
npm run type-check
```

### 로컬 DB

```bash
# PostgreSQL 컨테이너 시작 (Docker Desktop WSL 통합 활성화 필요)
docker compose up -d
```

### Strava Webhook 로컬 테스트

```bash
# 1. ngrok으로 로컬 서버를 외부에 노출
ngrok http 8000

# 2. Strava 웹훅 구독 등록 (ngrok URL 사용)
cd backend
uv run python scripts/register_webhook.py \
  --callback-url https://abc123.ngrok.io/api/v1/webhook/strava

# 3. Strava 앱에서 실제 달리기 완료 → webhook POST 자동 수신
```

## 핵심 아키텍처

### Strava Webhook 자동 저장 흐름

```
Strava → POST /webhook/strava
    → 200 OK 즉시 응답
    → FastAPI BackgroundTask:
        1. owner_id(strava_id)로 users 조회
        2. access_token 만료 시 refresh → DB 업데이트
        3. GET strava.com/api/v3/activities/{id} (laps 포함)
        4. sport_type == "Run" 인 경우만 저장
        5. activities + laps upsert (strava_id UNIQUE → 멱등성 보장)
```

### 주요 설계 원칙

- **Webhook 멱등성**: `strava_id UNIQUE + upsert`로 중복 이벤트 안전 처리
- **인증/데이터 분리**: Google OAuth로 로그인(identity), Strava OAuth는 `data_sources` 테이블에 별도 저장(data). 향후 Apple Health·Samsung Health 추가 시 `data_sources`에 행만 추가하면 됨
- **JWT 인증**: Google 로그인 후 자체 JWT 발급 → HttpOnly 쿠키로 전달, `api/deps.py`의 `get_current_user` 의존성으로 라우터에서 사용
- **LLM 추상화**: `services/llm.py`의 Protocol 기반 인터페이스 — OpenAI/Anthropic/Ollama 교체 가능
- **raw_json 보관**: Strava 원본 응답을 JSONB로 보관하여 스키마 변경 없이 필드 추가 가능
- **Alembic sync 연결**: env.py에서 `postgresql+asyncpg://` → `postgresql://`로 URL 변환 (Alembic은 sync 엔진 사용)

### 구현 단계

| Phase | 내용 | 상태 |
|-------|------|------|
| 1 | 기반 인프라 (uv, Vue, DB, 모델) | ✅ 완료 |
| 2 | Strava OAuth 인증 | 미시작 |
| 3 | Webhook + 활동 자동 저장 | 미시작 |
| 4 | 활동 조회 API + 지도 UI | 미시작 |
| 5 | LLM 조언 연동 (SSE 스트리밍) | 미시작 |
| 6 | Railway/Render 배포 | 미시작 |

## 환경 변수

루트의 `.env.example`과 `frontend/.env.example`을 참고하세요. 백엔드 `.env`는 `backend/` 디렉토리에 위치합니다.

```env
STRAVA_CLIENT_ID=
STRAVA_CLIENT_SECRET=
STRAVA_WEBHOOK_VERIFY_TOKEN=jog-post-webhook
DATABASE_URL=postgresql+asyncpg://jogpost:jogpost@localhost:5432/jogpost
JWT_SECRET_KEY=change-me-in-production
LLM_PROVIDER=          # openai | anthropic | ollama
LLM_API_KEY=
LLM_MODEL=
FRONTEND_URL=http://localhost:5173
```
