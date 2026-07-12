# JOG-POST

Apple Health(Health Auto Export 앱)로 달리기 기록을 자동 수집하고, AI 코치에게 훈련 조언을 받는 멀티 사용자 서비스.

## 주요 기능

- **자동 기록 동기화** — Health Auto Export 앱이 운동 데이터를 webhook으로 전송하면 DB에 자동 저장
- **활동 상세 조회** — km 구간별 페이스(서버에서 GPS route로 계산), 경로 지도
- **AI 달리기 코치** — 활동 데이터를 LLM에 전달해 SSE 스트리밍으로 조언 수신
- **종합 훈련 조언** — 최근 N주 기록을 바탕으로 한 전반적인 훈련 분석
- **공개 프로필** — 프로필 공개 설정 시 인증 없이 내 달리기 통계를 URL로 공유 가능

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), Alembic, uv |
| DB | PostgreSQL (asyncpg) |
| Frontend | Vue 3 + TypeScript, Vuetify 3, Pinia, Vue Router, Axios |
| 인증 | Google OAuth2 + JWT (HttpOnly 쿠키) |
| 데이터 연동 | Apple Health — [Health Auto Export](https://apps.apple.com/us/app/health-auto-export-json-csv/id1115567069) 앱의 REST API 자동화(webhook) |
| LLM | OpenAI / Anthropic / Gemini / Groq (환경변수로 선택) |

## 프로젝트 구조

```
jog-post/
├── docker-compose.yml          # 로컬 PostgreSQL
├── backend/
│   ├── pyproject.toml
│   ├── alembic/                # DB 마이그레이션
│   └── app/
│       ├── api/v1/             # auth, activities, advice, webhook, statistics, public
│       ├── models/             # User, Activity, DataSource, LLMAdvice
│       ├── schemas/            # Pydantic 요청/응답 스키마
│       ├── services/           # google_auth, apple_health, llm
│       └── core/               # config, database, security
└── frontend/
    └── src/
        ├── views/              # HomeView, ActivityListView, ActivityDetailView, AdviceView, StatisticsView, ProfileView, PublicProfileView
        ├── components/         # ActivityCard, ActivityStats, SplitsTable, RouteMap, AdviceChat
        ├── stores/             # auth, activities, statistics (Pinia)
        └── api/                # client, activities, advice, statistics, appleHealth, public
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

## Apple Health(Health Auto Export) 연동 설정

운동 완료 시 자동 저장 기능을 쓰려면 [Health Auto Export](https://apps.apple.com/us/app/health-auto-export-json-csv/id1115567069) 앱(iOS, 유료 REST API 자동화 기능 필요)이 필요합니다.

1. jog-post 프로필 페이지에서 "Apple Health 연동" 클릭 → `webhook_secret`과 webhook URL 발급 (시크릿은 이때 1회만 표시됨)
2. Health Auto Export 앱 → Automations → New Automation → REST API 선택
   - URL: 발급받은 webhook URL (로컬 테스트 시 ngrok으로 노출한 URL, 예: `https://<ngrok-id>.ngrok.io/api/v1/webhook/apple-health`)
   - Data Type: **Workouts**
   - Headers: `X-Webhook-Secret: <발급받은 시크릿>`
3. 앱에서 수동 export를 실행하거나, iOS Shortcuts의 "Workout Ended" 트리거로 자동화를 연결해 반자동 동기화 구성

로컬 테스트 시 ngrok으로 로컬 서버를 노출해야 합니다:

```bash
ngrok http 8000
```

> Health Auto Export는 Strava webhook과 달리 진짜 실시간이 아니라, 기간 기준(오늘/최근7일/마지막 동기화 이후) 배치 전송이며 **폰이 잠금 해제된 상태에서만** 동작합니다. 같은 운동이 여러 번 재전송될 수 있어 서버는 `apple_health_id` 기준으로 멱등하게 처리합니다.

## API 엔드포인트

### 인증 필요

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/v1/auth/google/login` | Google 로그인 URL로 리디렉트 |
| GET | `/api/v1/auth/me` | 현재 사용자 정보 조회 (`is_public` 포함) |
| PATCH | `/api/v1/auth/me` | 프로필 공개 설정 변경 (`{ is_public: bool }`) |
| POST | `/api/v1/auth/apple-health/connect` | Apple Health 웹훅 시크릿 발급/재발급 |
| DELETE | `/api/v1/auth/apple-health/disconnect` | Apple Health 연동 해제 |
| GET | `/api/v1/activities` | 활동 목록 (페이지네이션) |
| GET | `/api/v1/activities/{id}` | 활동 상세 + km 구간 |
| POST | `/api/v1/advice/activity/{id}` | 활동별 AI 조언 (SSE 스트리밍) |
| POST | `/api/v1/advice/general` | 최근 N주 종합 조언 (SSE 스트리밍) |
| GET | `/api/v1/advice/history` | 과거 조언 목록 |
| GET | `/api/v1/statistics/weekly` | 주별 통계 (`?year=&month=`) |
| GET | `/api/v1/statistics/monthly` | 월별 통계 (`?year=`) |
| GET | `/api/v1/statistics/yearly` | 연별 통계 |

### 인증 불필요 (공개 API)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/v1/public/users/{user_id}` | 공개 사용자 기본 정보 조회 (`is_public=false`이면 404) |
| GET | `/api/v1/public/users/lookup` | 이메일로 공개 사용자 조회 (`?email=`) |
| GET | `/api/v1/public/users/{user_id}/statistics/yearly` | 공개 사용자 연별 통계 |
| GET | `/api/v1/public/users/{user_id}/statistics/monthly` | 공개 사용자 월별 통계 (`?year=`) |

### 웹훅 (X-Webhook-Secret 헤더로 인증, 쿠키 인증 아님)

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/webhook/apple-health` | Health Auto Export 앱의 운동 데이터 수신 |

## 라즈베리파이 자가호스팅 배포

FastAPI가 Vue 빌드 결과물을 직접 서빙하는 단일 서비스 구조를, 라즈베리파이5(Home Assistant OS) + Cloudflare Tunnel + `docker compose`로 자가호스팅합니다.

```
라즈베리파이5 (HAOS)
├── docker compose (docker-compose.prod.yml)
│   ├── app 컨테이너 (FastAPI + Vue 정적 파일, 127.0.0.1:8000)
│   └── db 컨테이너 (PostgreSQL, 내부 네트워크 전용)
└── Cloudflare Tunnel (cloudflared, HA와 동일 터널)
    └── jog.onlypearson.com → localhost:8000
```

### 배포 절차

1. **라즈베리파이에서 저장소 클론** (SSH 애드온으로 접근)
   ```bash
   git clone <repo-url>
   cd jog-post
   ```

2. **환경변수 배치**: 로컬에서 채운 `.env`를 `scp`로 전달 후 권한 제한
   ```bash
   scp .env <user>@<rpi-host>:/path/to/jog-post/.env
   ssh <user>@<rpi-host> chmod 600 /path/to/jog-post/.env
   ```
   프로덕션에서는 `FRONTEND_URL=https://jog.onlypearson.com`, `POSTGRES_PASSWORD`는 강한 값으로 설정합니다.

3. **빌드 및 기동**
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   docker compose -f docker-compose.prod.yml logs -f app   # 마이그레이션/기동 확인
   ```

4. **Cloudflare Tunnel에 서브도메인 추가**: Zero Trust 대시보드 → Networks → Tunnels → 기존 HA 터널 → Public Hostname 추가 (`jog.onlypearson.com` → `localhost:8000` 또는 라즈베리파이 LAN IP)

5. **Google OAuth 리디렉션 URI 업데이트**:
   - Google Cloud Console: `https://jog.onlypearson.com/api/v1/auth/google/callback`

6. **Apple Health 연동**: 프로필 페이지에서 연동 → 발급받은 시크릿/URL(`https://jog.onlypearson.com/api/v1/webhook/apple-health`)을 Health Auto Export 앱의 커스텀 헤더에 설정

7. **재배포 시**:
   ```bash
   git pull
   docker compose -f docker-compose.prod.yml build
   docker compose -f docker-compose.prod.yml up -d
   ```

자세한 절차와 트러블슈팅은 [`docs/deployment-rpi.md`](docs/deployment-rpi.md) 참고.
