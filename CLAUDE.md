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
| Frontend | Vue 3 + TypeScript, Vuetify 3, Pinia, Vue Router, Axios |
| 인증 | Google OAuth2 + JWT (HttpOnly 쿠키) |
| 데이터 연동 | Strava OAuth2 (`data_sources` 테이블로 관리, 향후 Apple Health 등 확장 가능) |
| LLM | Protocol 기반 추상화 (`services/llm.py`) — OpenAI / Anthropic 교체 가능 |

## 개발 명령어

### Backend (`backend/` 디렉토리에서)

```bash
uv sync                                                # 의존성 설치
uv run uvicorn app.main:app --reload                  # 개발 서버
uv run pytest                                         # 전체 테스트
uv run pytest tests/test_activities.py -v             # 단일 파일
uv run alembic revision --autogenerate -m "desc"      # 마이그레이션 생성
uv run alembic upgrade head                           # 마이그레이션 적용
```

### Frontend (`frontend/` 디렉토리에서)

```bash
npm install          # 의존성 설치
npm run dev          # 개발 서버 (http://localhost:5173)
npm run build        # 프로덕션 빌드
npm run type-check   # TypeScript 타입 체크
```

### 로컬 DB

```bash
docker compose up -d   # PostgreSQL 컨테이너 시작 (Docker Desktop WSL 통합 활성화 필요)
```

### Strava Webhook 로컬 테스트

```bash
ngrok http 8000
cd backend
uv run python scripts/register_webhook.py \
  --callback-url https://<ngrok-id>.ngrok.io/api/v1/webhook/strava
```

## 프로젝트 구조

```
backend/app/
├── api/v1/
│   ├── auth.py          # Google/Strava OAuth 엔드포인트
│   ├── activities.py    # 활동 목록/상세/동기화/삭제
│   ├── advice.py        # LLM 조언 SSE 스트리밍
│   └── webhook.py       # Strava Webhook 수신
├── models/
│   ├── user.py          # User (Google 로그인 정보)
│   ├── data_source.py   # DataSource (Strava 토큰, 향후 확장용)
│   ├── activity.py      # Activity (raw_json JSONB 포함)
│   ├── lap.py           # Lap (사용자 정의 랩)
│   └── llm_advice.py    # LLMAdvice (조언 이력)
├── schemas/
│   ├── activity.py      # ActivityResponse, ActivityDetailResponse, SplitMetricResponse
│   └── advice.py        # AdviceHistoryResponse
├── services/
│   ├── google_auth.py   # Google OAuth 흐름
│   ├── strava_auth.py   # Strava OAuth + 토큰 갱신
│   ├── strava_api.py    # Strava REST API 호출
│   ├── activity_sync.py # Webhook/수동 동기화 비즈니스 로직
│   └── llm.py           # LLMClient Protocol + AnthropicClient/OpenAIClient
└── core/
    ├── config.py        # Pydantic Settings (환경변수 단일 진실 공급원)
    ├── database.py      # 비동기 SQLAlchemy 엔진/세션
    └── security.py      # JWT 발급/검증

frontend/src/
├── views/
│   ├── HomeView.vue          # 로그인/Strava 연동 랜딩
│   ├── ActivityListView.vue  # 활동 목록 + 동기화 버튼
│   ├── ActivityDetailView.vue # 활동 상세 (탭: km구간/랩, 지도, AI조언)
│   └── AdviceView.vue        # 종합 훈련 조언
├── components/
│   ├── ActivityCard.vue      # 목록 카드
│   ├── ActivityStats.vue     # 핵심 통계 (거리/페이스/심박 등)
│   ├── SplitsTable.vue       # km 구간별 메트릭 테이블
│   ├── LapTable.vue          # 사용자 랩 테이블
│   ├── RouteMap.vue          # Leaflet.js 경로 지도
│   └── AdviceChat.vue        # SSE 스트리밍 AI 조언 표시
├── stores/
│   ├── auth.ts               # 인증 상태 (Pinia)
│   └── activities.ts         # 활동 데이터 (Pinia)
└── lib/
    └── format.ts             # formatTime, formatPace, formatDistance, hrColor 등 공유 유틸
```

## 핵심 아키텍처

### Strava Webhook 자동 저장 흐름

```
Strava → POST /api/v1/webhook/strava
    → 200 OK 즉시 응답
    → FastAPI BackgroundTask:
        1. strava_athlete_id로 data_source 조회
        2. access_token 만료 시 refresh → DB 업데이트
        3. GET strava.com/api/v3/activities/{id} (laps, splits_metric 포함)
        4. sport_type ∈ {Run, TrailRun, VirtualRun, Treadmill} 만 저장
        5. activities + laps upsert (strava_id UNIQUE → 멱등성 보장)
```

### splits_metric 처리 방식

Strava 응답의 `splits_metric`(1km 구간 자동 분할)은 별도 테이블 없이 `Activity.raw_json` JSONB에 보관.
- API 응답 시 `ActivityDetailResponse.splits_metric` computed_field가 `raw_json`에서 파싱해 반환
- `raw_json` 자체는 `Field(exclude=True)`로 API 응답에서 제외
- AI 조언 컨텍스트 빌더(`advice.py::_build_activity_context`)도 `raw_json`에서 직접 추출해 LLM에 전달

### 인증 구조

- **Google OAuth** → 사용자 identity (로그인/회원가입)
- **Strava OAuth** → `data_sources` 테이블에 별도 저장 (access_token, refresh_token)
- Google 로그인 성공 후 자체 JWT 발급 → HttpOnly 쿠키 전달
- `api/deps.py::get_current_user`로 모든 보호 라우터에서 사용자 확인
- 향후 Apple Health·Samsung Health 추가 시 `data_sources`에 행만 추가하면 됨

### LLM 추상화

```python
class LLMClient(Protocol):
    async def stream_completion(self, system: str, user: str) -> AsyncIterator[str]: ...
```

`config.py`의 `LLM_PROVIDER` 환경변수로 `AnthropicClient` / `OpenAIClient` 선택.
새 공급자 추가 시 Protocol을 구현하는 클래스만 작성하면 됨.

## 주요 설계 결정

| 결정 | 이유 |
|------|------|
| `raw_json` JSONB 보관 | Strava 원본 응답 전체 저장 → 스키마 마이그레이션 없이 새 필드 활용 가능 |
| Webhook 멱등성 | `strava_id UNIQUE + upsert` → 중복 이벤트 안전 처리 |
| 인증/데이터 분리 | Google(identity) + Strava(data)를 분리해 다중 데이터 소스 확장 용이 |
| splits_metric 별도 테이블 없음 | raw_json에서 computed_field로 파싱 → 마이그레이션 불필요 |
| Alembic sync 연결 | `env.py`에서 `postgresql+asyncpg://` → `postgresql://` 변환 (Alembic은 sync 엔진 사용) |

## 환경 변수

`backend/.env` (`.env.example` 참고):

```env
# Google OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Strava OAuth
STRAVA_CLIENT_ID=
STRAVA_CLIENT_SECRET=
STRAVA_WEBHOOK_VERIFY_TOKEN=jog-post-webhook

# DB
DATABASE_URL=postgresql+asyncpg://jogpost:jogpost@localhost:5432/jogpost

# JWT
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080   # 7일

# LLM
LLM_PROVIDER=              # openai | anthropic
LLM_API_KEY=
LLM_MODEL=                 # gpt-4o-mini | claude-haiku-4-5-20251001

# App
FRONTEND_URL=http://localhost:5173
```

## 구현 현황

| Phase | 내용 | 상태 |
|-------|------|------|
| 1 | 기반 인프라 (uv, Vue, DB 모델, Alembic) | ✅ 완료 |
| 2 | Google OAuth + Strava OAuth 연동 | ✅ 완료 |
| 3 | Strava Webhook + 활동 자동 저장 | ✅ 완료 |
| 4 | 활동 조회 API + 프론트엔드 (지도, km구간, 랩) | ✅ 완료 |
| 5 | LLM 조언 연동 (SSE 스트리밍) | ✅ 완료 |
| 6 | Railway/Render 배포 | 미시작 |
