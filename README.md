# JOG-POST

Strava API로 달리기 기록을 자동 수집하고, AI 코치에게 훈련 조언을 받는 멀티 사용자 서비스.

## 주요 기능

- **자동 기록 동기화** — 운동 완료 시 Strava Webhook을 통해 DB에 자동 저장
- **수동 동기화** — 버튼 한 번으로 과거 기록 일괄 가져오기
- **활동 상세 조회** — km 구간별 페이스/심박/고도, 사용자 랩, 경로 지도
- **AI 달리기 코치** — 활동 데이터를 LLM에 전달해 SSE 스트리밍으로 조언 수신
- **종합 훈련 조언** — 최근 N주 기록을 바탕으로 한 전반적인 훈련 분석

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), Alembic, uv |
| DB | PostgreSQL (asyncpg) |
| Frontend | Vue 3 + TypeScript, Vuetify 3, Pinia, Vue Router, Axios |
| 인증 | Google OAuth2 + JWT (HttpOnly 쿠키) |
| 데이터 연동 | Strava OAuth2 |
| LLM | OpenAI / Anthropic / Gemini / Groq (환경변수로 선택) |

## 프로젝트 구조

```
jog-post/
├── docker-compose.yml          # 로컬 PostgreSQL
├── backend/
│   ├── pyproject.toml
│   ├── alembic/                # DB 마이그레이션
│   └── app/
│       ├── api/v1/             # auth, activities, advice, webhook
│       ├── models/             # User, Activity, Lap, DataSource, LLMAdvice
│       ├── schemas/            # Pydantic 요청/응답 스키마
│       ├── services/           # strava_auth, strava_api, activity_sync, llm
│       └── core/               # config, database, security
└── frontend/
    └── src/
        ├── views/              # HomeView, ActivityListView, ActivityDetailView, AdviceView
        ├── components/         # ActivityCard, ActivityStats, LapTable, SplitsTable, RouteMap, AdviceChat
        ├── stores/             # auth, activities (Pinia)
        └── api/                # client, activities, advice
```

## 로컬 개발 환경 구성

### 사전 조건

- Python 3.12+
- Node.js 18+
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Docker (로컬 PostgreSQL용)

### 1. 저장소 클론

```bash
git clone <repo-url>
cd jog-post
```

### 2. 환경 변수 설정

```bash
cp .env.example backend/.env
```

`backend/.env`를 열어 아래 항목을 채웁니다:

| 변수 | 설명 | 발급처 |
|------|------|--------|
| `GOOGLE_CLIENT_ID` | Google OAuth 클라이언트 ID | [Google Cloud Console](https://console.cloud.google.com) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 클라이언트 시크릿 | Google Cloud Console |
| `STRAVA_CLIENT_ID` | Strava API 앱 ID | [Strava Developers](https://developers.strava.com) |
| `STRAVA_CLIENT_SECRET` | Strava API 시크릿 | Strava Developers |
| `JWT_SECRET_KEY` | JWT 서명 키 (임의 문자열) | 직접 생성 |
| `LLM_PROVIDER` | `openai`, `anthropic`, `gemini`, `groq` 중 선택 | — |
| `LLM_API_KEY` | LLM API 키 | 각 공급자 콘솔 |
| `LLM_MODEL` | 사용할 모델명 (아래 표 참고) | — |

**공급자별 API 키 발급처 및 추천 모델:**

| `LLM_PROVIDER` | API 키 발급 | 추천 `LLM_MODEL` | 비고 |
|----------------|------------|-----------------|------|
| `openai` | [platform.openai.com](https://platform.openai.com) | `gpt-4o-mini` | 유료 |
| `anthropic` | [console.anthropic.com](https://console.anthropic.com) | `claude-haiku-4-5-20251001` | 유료 |
| `gemini` | [aistudio.google.com](https://aistudio.google.com) | `gemini-2.0-flash` | 무료 티어 제공 |
| `groq` | [console.groq.com](https://console.groq.com) | `llama-3.3-70b-versatile` | 무료 티어 제공 (한국어 응답 최적화 적용) |

> Google Cloud Console에서 승인된 리디렉션 URI로 `http://localhost:8000/api/v1/auth/google/callback`을 추가해야 합니다.

### 3. DB 실행 및 마이그레이션

```bash
docker compose up -d

cd backend
uv sync
uv run alembic upgrade head
```

### 4. 백엔드 실행

```bash
cd backend
uv run uvicorn app.main:app --reload
# http://localhost:8000
# http://localhost:8000/docs  ← API 문서
```

### 5. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

## Strava Webhook 로컬 테스트

운동 완료 시 자동 저장 기능을 로컬에서 테스트하려면 ngrok으로 외부에 서버를 노출해야 합니다.

```bash
# 1. ngrok으로 로컬 서버 노출
ngrok http 8000

# 2. Webhook 구독 등록 (ngrok URL 사용)
cd backend
uv run python scripts/register_webhook.py \
  --callback-url https://<ngrok-id>.ngrok.io/api/v1/webhook/strava

# 3. Strava 앱에서 달리기 완료 → 자동으로 DB에 저장됨
```

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/v1/auth/google/login` | Google 로그인 URL로 리디렉트 |
| GET | `/api/v1/auth/strava/connect` | Strava 연동 URL로 리디렉트 |
| GET | `/api/v1/activities` | 활동 목록 (페이지네이션) |
| GET | `/api/v1/activities/{id}` | 활동 상세 + 랩 + km 구간 |
| POST | `/api/v1/activities/sync` | Strava 과거 기록 수동 동기화 |
| POST | `/api/v1/advice/activity/{id}` | 활동별 AI 조언 (SSE 스트리밍) |
| POST | `/api/v1/advice/general` | 최근 N주 종합 조언 (SSE 스트리밍) |
| GET | `/api/v1/advice/history` | 과거 조언 목록 |
