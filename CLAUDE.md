# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

**JOG-POST**는 Apple Health(Health Auto Export 앱)를 통해 사용자의 달리기 기록을 자동으로 수집·저장하고, 운동 데이터를 조회하며, LLM을 연동하여 기록 향상 조언을 제공하는 멀티 사용자 서비스입니다.

모노레포 구조로, `backend/`(FastAPI + PostgreSQL)와 `frontend/`(Vue 3 + Vuetify)가 단일 저장소에서 관리됩니다.

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), Alembic, uv |
| DB | PostgreSQL (asyncpg 드라이버, Alembic 마이그레이션은 psycopg2-binary 사용) |
| Frontend | Vue 3 + TypeScript, Vuetify 3, Pinia, Vue Router, Axios |
| 인증 | Google OAuth2 + JWT (HttpOnly 쿠키) |
| 데이터 연동 | Apple Health(Health Auto Export 앱 webhook push, `data_sources` 테이블에 시크릿 저장) |
| LLM | Protocol 기반 추상화 (`services/llm.py`) — OpenAI / Anthropic / Gemini / Groq 교체 가능 |

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

### Apple Health(Health Auto Export) 웹훅 로컬 테스트

```bash
ngrok http 8000
```
1. 프로필 페이지에서 Apple Health 연동 → 시크릿/URL 발급
2. Health Auto Export 앱의 REST API 자동화 설정에서 URL을 `https://<ngrok-id>.ngrok.io/api/v1/webhook/apple-health`로, 커스텀 헤더에 `X-Webhook-Secret: <발급받은 시크릿>` 추가
3. 앱에서 수동 export 실행 → 활동 목록에서 확인

## 프로젝트 구조

```
backend/app/
├── api/v1/
│   ├── auth.py          # Google OAuth + Apple Health 연동(시크릿 발급/해제) + PATCH /auth/me (is_public 설정)
│   ├── activities.py    # 활동 목록/상세/삭제
│   ├── advice.py        # LLM 조언 SSE 스트리밍
│   ├── statistics.py    # 주별/월별/연별 통계 (인증 필요)
│   ├── public.py        # 공개 사용자 정보 + 통계 (인증 불필요)
│   └── webhook.py       # Apple Health(Health Auto Export) Webhook 수신
├── models/
│   ├── user.py          # User (Google 로그인 정보)
│   ├── data_source.py   # DataSource (provider + webhook_secret)
│   ├── activity.py      # Activity (raw_json JSONB 포함)
│   └── llm_advice.py    # LLMAdvice (조언 이력)
├── schemas/
│   ├── activity.py      # ActivityResponse, ActivityDetailResponse, SplitMetricResponse
│   ├── advice.py        # AdviceHistoryResponse
│   ├── statistics.py    # WeeklyStatsResponse, MonthlyStatsResponse, YearlyStatsResponse
│   └── user.py          # UserResponse, MeResponse, MeUpdateRequest, PublicUserResponse, AppleHealthConnectResponse
├── services/
│   ├── google_auth.py   # Google OAuth 흐름
│   ├── apple_health.py  # 웹훅 시크릿 관리 + 워크아웃 매핑/upsert + 1km 구간 계산
│   └── llm.py           # LLMClient Protocol + AnthropicClient/OpenAIClient/GeminiClient/GroqClient
└── core/
    ├── config.py        # Pydantic Settings (환경변수 단일 진실 공급원)
    ├── database.py      # 비동기 SQLAlchemy 엔진/세션
    └── security.py      # JWT 발급/검증

frontend/src/
├── views/
│   ├── HomeView.vue           # 로그인/Apple Health 연동 랜딩
│   ├── ActivityListView.vue   # 활동 목록
│   ├── ActivityDetailView.vue # 활동 상세 (km 구간, 지도, AI조언)
│   ├── AdviceView.vue         # 종합 훈련 조언
│   ├── StatisticsView.vue     # 주별/월별/연별 통계 (인증 필요)
│   ├── ProfileView.vue        # 프로필 설정 + is_public 토글 + Apple Health 연동 (인증 필요)
│   └── PublicProfileView.vue  # 공개 프로필 + 통계 (인증 불필요, /public/:userId)
├── components/
│   ├── ActivityCard.vue      # 목록 카드
│   ├── ActivityStats.vue     # 핵심 통계 (거리/페이스/심박 등)
│   ├── SplitsTable.vue       # km 구간별 메트릭 테이블
│   ├── RouteMap.vue          # Leaflet.js 경로 지도
│   └── AdviceChat.vue        # SSE 스트리밍 AI 조언 표시
├── stores/
│   ├── auth.ts               # 인증 상태 + updatePublicSetting()/connectAppleHealth()/disconnectAppleHealth() (Pinia)
│   ├── activities.ts         # 활동 데이터 (Pinia)
│   └── statistics.ts         # 통계 데이터 (Pinia)
└── api/
    ├── client.ts             # Axios 인스턴스 (withCredentials)
    ├── activities.ts         # 활동 API
    ├── advice.ts             # 조언 API (SSE)
    ├── statistics.ts         # 통계 API (인증 필요)
    ├── appleHealth.ts        # Apple Health 연동/해제 API
    └── public.ts             # 공개 API (인증 불필요)
```

## 핵심 아키텍처

### Apple Health(Health Auto Export) 자동 저장 흐름

Health Auto Export는 OAuth가 없고, 기간 기준(오늘/최근7일/마지막 동기화 이후)으로 운동 데이터를 배치 push한다. 폰이 잠금 해제된 상태에서만 동작하므로 Strava webhook 같은 진짜 실시간은 아니다.

```
사용자 프로필 → POST /api/v1/auth/apple-health/connect
    → webhook_secret 발급 (data_sources에 저장, 1회만 노출)
    → 사용자가 Health Auto Export 앱의 커스텀 헤더(X-Webhook-Secret)에 붙여넣음

Health Auto Export 앱 → POST /api/v1/webhook/apple-health
    → X-Webhook-Secret 헤더로 data_sources 조회 → user_id 식별
    → payload["data"]["workouts"] 배열 순회 (한 요청에 여러 운동 포함 가능)
        1. name에 "run"이 포함되지 않으면 스킵
        2. 거리(mi/km)·칼로리(kJ/kcal) 단위 변환
        3. route 좌표를 polyline으로 인코딩 → summary_polyline
        4. route의 timestamp+거리로 1km 구간을 서버에서 직접 계산 → raw_json["computed_splits"]
        5. apple_health_id UNIQUE 기준으로 upsert (같은 운동 재전송 시 멱등)
    → {"saved": n, "skipped": m} 동기 응답 (Strava와 달리 응답시간 제약 없어 BackgroundTask 불필요)
```

### splits_metric 처리 방식

1km 구간 데이터는 Strava처럼 API가 내려주는 게 아니라 **서버에서 GPS route로부터 직접 계산**한다 (`apple_health.py::_compute_splits`). 별도 테이블 없이 `Activity.raw_json["computed_splits"]`에 보관.
- API 응답 시 `ActivityDetailResponse.splits_metric` computed_field가 `raw_json["computed_splits"]`를 파싱해 반환
- `raw_json` 자체는 `Field(exclude=True)`로 API 응답에서 제외
- AI 조언 컨텍스트 빌더(`advice.py::_build_activity_context`)도 `raw_json`에서 직접 추출해 LLM에 전달

### 인증 구조

- **Google OAuth** → 사용자 identity (로그인/회원가입), 완전히 별개 관심사
- **Apple Health 연동** → `data_sources` 테이블에 `(user_id, provider="apple_health", webhook_secret)` 저장. OAuth 토큰이 아니라 사용자가 직접 발급받아 Health Auto Export 앱에 붙여넣는 시크릿으로 웹훅 요청을 인증
- Google 로그인 성공 후 자체 JWT 발급 → HttpOnly 쿠키 전달
- `api/deps.py::get_current_user`로 모든 보호 라우터에서 사용자 확인
- 새 웹훅 기반 데이터 소스 추가 시 `data_sources`에 provider 행만 추가하면 됨

### LLM 추상화

```python
class LLMClient(Protocol):
    async def stream_completion(self, system: str, user: str) -> AsyncIterator[str]: ...
```

`config.py`의 `LLM_PROVIDER` 환경변수로 공급자 선택:

| `LLM_PROVIDER` | 클래스 | 기본 모델 | 비고 |
|----------------|--------|----------|------|
| `anthropic` | `AnthropicClient` | `claude-haiku-4-5-20251001` | `anthropic` 패키지 필요 |
| `openai` | `OpenAIClient` | `gpt-4o-mini` | `openai` 패키지 필요 |
| `gemini` | `GeminiClient` | `gemini-2.0-flash` | `openai` 패키지 재사용, base_url만 변경 |
| `groq` | `GroqClient` | `llama-3.3-70b-versatile` | `openai` 패키지 재사용, base_url만 변경. `temperature=0.4`, `top_p=0.9` 고정 (언어 혼용 방지) |

새 공급자 추가 시 `LLMClient` Protocol을 구현하는 클래스 작성 후 `get_llm_client()`에 분기 추가.

**LLM 관련 주의사항:**
- `ADVICE_ENABLED=false`면 `/advice/*` 라우터 전체가 404를 반환(router-level dependency `_require_advice_enabled`, `backend/app/api/v1/advice.py`) — 기능 자체를 끄는 킬스위치. 프론트도 `/auth/me`의 `advice_enabled` 값을 보고 네비게이션·활동 상세 카드·`/advice` 라우트 접근을 함께 숨김
- 스트리밍 시작 전 `get_llm_client()`로 설정 유효성 검사 → 실패 시 503 반환 (스트림 도중 연결 끊김 방지)
- 시스템 프롬프트에 "반드시 한국어로만 답변" 명시 — Llama 계열 모델의 언어 혼용(일본어 등) 억제
- Groq/Llama 사용 시 언어 혼용이 발생하면 `temperature`를 `0.2~0.3`으로 낮춰볼 것

## 배포 구조 (라즈베리파이5 자가호스팅)

단일 서비스로 FastAPI가 Vue 빌드 결과물을 직접 서빙합니다. 라즈베리파이5(Home Assistant OS) 위에서 `docker compose`로 앱+DB 컨테이너를 기동하고, 기존 HA용 Cloudflare Tunnel에 서브도메인(`jog.onlypearson.com`)을 추가해 외부에 노출합니다.

```
라즈베리파이5 (HAOS)
├── docker compose (docker-compose.prod.yml)
│   ├── app 컨테이너 (FastAPI + Vue 정적 파일, 127.0.0.1:8000)
│   │   ├── /api/v1/*  → FastAPI 라우터
│   │   └── /*         → Vue SPA (index.html 폴백)
│   └── db 컨테이너 (PostgreSQL, 내부 네트워크 전용)
└── Cloudflare Tunnel (cloudflared) → jog.onlypearson.com
```

### 핵심 파일

| 파일 | 역할 |
|------|------|
| `Dockerfile` | 멀티스테이지 빌드(프론트 빌드 → 백엔드 설치) + CMD로 마이그레이션·uvicorn 기동 |
| `docker-compose.prod.yml` | app + db 서비스, healthcheck, `restart: unless-stopped` |
| `.env` (git 미추적) | 라즈베리파이에 `scp`로 배치하는 실제 운영 환경변수 |
| `backend/app/main.py` | `frontend/dist` 존재 시 정적 파일 서빙 + SPA 폴백 라우트 |

### 배포 절차

1. 라즈베리파이에서 `git clone` (최초 1회) 또는 `git pull` (재배포)
2. `.env`를 `scp`로 배치 (`FRONTEND_URL=https://jog.onlypearson.com`, `POSTGRES_PASSWORD` 운영값 설정)
3. `docker compose -f docker-compose.prod.yml up -d --build`
4. Cloudflare Zero Trust 대시보드에서 기존 HA 터널에 Public Hostname 추가 (`jog.onlypearson.com` → 라즈베리파이 LAN IP:8000, `localhost`/`homeassistant.local`은 이 환경에서 동작하지 않음 — [`docs/deployment-rpi.md`](docs/deployment-rpi.md) 참고)
5. Google Cloud Console에서 리디렉션 URI를 `jog.onlypearson.com` 기준으로 업데이트
6. 프로필 페이지에서 Apple Health 연동 → 발급받은 시크릿/URL을 Health Auto Export 앱의 커스텀 헤더에 설정

자세한 절차는 [`docs/deployment-rpi.md`](docs/deployment-rpi.md) 참고.

### Home Assistant Add-on 배포 (대안)

`docker compose` 대신 HAOS Supervisor 애드온 스토어로도 배포 가능하다. repo 루트의 `repository.yaml` + `jogpost/`(add-on용 `config.yaml`, `Dockerfile`, `run.sh`)가 이를 위한 구성이다.

- `.github/workflows/docker-publish.yml`이 `main` push 시 앱 이미지를 `ghcr.io/bluewings109/jog-post`(amd64/arm64)로 publish
- `jogpost/Dockerfile`은 그 이미지를 `FROM`으로 가져와 HA add-on 옵션(`/data/options.json`)을 환경변수로 변환하는 `run.sh` 래퍼만 얹음 (Supervisor가 설치 시점에 라즈베리파이에서 이 얇은 레이어만 로컬 빌드)
- HA add-on은 단일 컨테이너 원칙이라 PostgreSQL은 별도의 공식 Postgres add-on(`a0d7b954/postgresql` 등)에 의존 — `docker-compose.prod.yml`의 `db` 서비스처럼 같이 묶을 수 없음

자세한 절차는 [`docs/deployment-rpi.md`](docs/deployment-rpi.md#home-assistant-add-on으로-배포-대안) 참고.

### 로컬 vs 프로덕션 API 경로

- **로컬 개발**: 프론트엔드(`localhost:5173`)가 백엔드(`localhost:8000`)로 프록시 없이 직접 요청 — `VITE_API_URL` 불필요
- **프로덕션**: 같은 도메인에서 서빙 → `VITE_API_URL` 미설정 시 상대 경로(`/api/v1`) 자동 사용
- `frontend/src/api/client.ts`와 `advice.ts` 모두 `import.meta.env.VITE_API_URL ?? ''` 패턴으로 동작

### CORS 허용 오리진

`backend/app/main.py`의 `CORSMiddleware.allow_origins`는 jog-post 자체 프론트(`settings.FRONTEND_URL`) 외에, jog-post API를 호출하는 **외부에 별도로 호스팅된 정적 페이지**들을 명시적으로 추가해둔 목록이다:

| 오리진 | 용도 |
|--------|------|
| `settings.FRONTEND_URL` | jog-post 자체 프론트엔드 (로컬/프로덕션 도메인) |
| `https://bluewings109.github.io` | GitHub Pages로 호스팅된 정적 페이지에서 jog-post API 호출 |
| `https://page.onlypearson.com` | 공개 프로필/통계 페이지를 별도 호스팅한 정적 사이트에서 jog-post API(`/api/v1/public/*` 등) 호출 |

새 외부 페이지에서 jog-post API를 호출해야 하면 이 목록에 오리진을 추가해야 한다(하드코딩 배열, 환경변수화되어 있지 않음).

## 주요 설계 결정

| 결정 | 이유 |
|------|------|
| `raw_json` JSONB 보관 | Apple Health 원본 payload 전체 저장 → 스키마 마이그레이션 없이 새 필드 활용 가능 |
| Webhook 멱등성 | `apple_health_id UNIQUE + upsert` → 같은 운동 재전송 시 안전 처리 |
| 인증/데이터 분리 | Google(identity) + Apple Health(webhook_secret)를 분리해 다중 데이터 소스 확장 용이 |
| 1km 구간 서버 계산 | Health Auto Export가 구간 데이터를 안 주므로 route로 직접 계산해 raw_json에 저장 → 마이그레이션 불필요 |
| Alembic sync 연결 | `env.py`에서 `postgresql+asyncpg://` → `postgresql://` 변환 (Alembic은 sync 엔진 사용) |
| 단일 서비스 배포 | FastAPI가 Vue 빌드 정적 파일 직접 서빙 → 컨테이너 하나로 운영 가능 |

## 환경 변수

`backend/.env` (`.env.example` 참고):

```env
# Google OAuth
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# DB
DATABASE_URL=postgresql+asyncpg://jogpost:jogpost@localhost:5432/jogpost

# JWT
JWT_SECRET_KEY=change-me-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080   # 7일

# LLM
LLM_PROVIDER=              # openai | anthropic | gemini | groq
LLM_API_KEY=
LLM_MODEL=                 # gpt-4o-mini | claude-haiku-4-5-20251001 | gemini-2.0-flash | llama-3.3-70b-versatile
ADVICE_ENABLED=true        # false로 두면 /advice/* API가 404, 프론트 UI(네비게이션·활동 상세 카드)도 숨겨짐

# App
FRONTEND_URL=http://localhost:5173
```

## 구현 현황

| Phase | 내용 | 상태 |
|-------|------|------|
| 1 | 기반 인프라 (uv, Vue, DB 모델, Alembic) | ✅ 완료 |
| 2 | Google OAuth 연동 | ✅ 완료 |
| 3 | Apple Health(Health Auto Export) Webhook + 활동 저장 | ✅ 완료 |
| 4 | 활동 조회 API + 프론트엔드 (지도, km구간) | ✅ 완료 |
| 5 | LLM 조언 연동 (SSE 스트리밍) | ✅ 완료 |
| 6 | 라즈베리파이5 자가호스팅 배포 (docker compose + Cloudflare Tunnel) | ✅ 완료 |
| 7 | Strava → Apple Health 데이터 소스 전환 (Strava API 유료화 대응) | ✅ 완료 |
