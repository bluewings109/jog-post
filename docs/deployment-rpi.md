# 라즈베리파이5(HAOS) 자가호스팅 배포 가이드

jog-post를 라즈베리파이5 + Home Assistant OS(HAOS) + Cloudflare Tunnel + `docker compose`로 배포하는 상세 절차입니다. 요약은 [`CLAUDE.md`](../CLAUDE.md#배포-구조-라즈베리파이5-자가호스팅)와 [`README.md`](../README.md#라즈베리파이-자가호스팅-배포) 참고.

## 사전 조건

- HAOS에 SSH & Web Terminal 애드온이 설치되어 있고 `docker`, `docker compose`(v2 플러그인)에 접근 가능
- Cloudflare에서 도메인(`onlypearson.com`)을 관리 중이고, HA OS UI가 이미 Cloudflare Tunnel(Named Tunnel, Zero Trust 대시보드 관리)로 `ha.onlypearson.com`에 연결되어 있음

SSH 애드온으로 접속 후 확인:

```bash
docker compose version
```

## 최초 배포

### 1. 저장소 클론

```bash
git clone <repo-url> jog-post
cd jog-post
```

### 2. `.env` 배치

로컬 개발 머신에서 채워둔 `.env`(또는 `.env.example`을 복사해 운영값으로 채운 파일)를 `scp`로 전달합니다.

```bash
scp .env <user>@<rpi-host>:/path/to/jog-post/.env
ssh <user>@<rpi-host> chmod 600 /path/to/jog-post/.env
```

프로덕션에서 반드시 확인/수정할 값:

| 변수 | 값 |
|------|-----|
| `FRONTEND_URL` | `https://jog.onlypearson.com` |
| `POSTGRES_PASSWORD` | 로컬 개발용 기본값(`jogpost`) 대신 강한 비밀번호로 교체 |
| `JWT_SECRET_KEY` | 운영용 랜덤 값 |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google Cloud Console 발급값 |

`.env`는 `.gitignore`에 의해 git에 커밋되지 않으므로 반드시 별도 경로(scp 등)로만 전달합니다.

### 3. 빌드 및 기동

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f app
```

`app` 컨테이너의 `CMD`가 `alembic upgrade head` 실행 후 `uvicorn`을 기동하므로, 로그에서 마이그레이션 완료와 `Uvicorn running on http://0.0.0.0:8000`을 확인합니다. `db` 서비스는 `pg_isready` healthcheck를 통과해야 `app`이 기동을 시작합니다(`depends_on: condition: service_healthy`).

### 4. 로컬 검증

```bash
curl http://127.0.0.1:8000/health
# {"status":"ok"}
```

## Cloudflare Tunnel에 서브도메인 추가

1. [one.dash.cloudflare.com](https://one.dash.cloudflare.com) → **Networks → Tunnels** → 기존 HA 터널 선택 → **Public Hostname** 탭
2. **Add a public hostname** 클릭
   - Subdomain: `jog`
   - Domain: `onlypearson.com`
   - Service Type: `HTTP`
   - URL: 라즈베리파이의 LAN IP (`http://<rpi-lan-ip>:8000`, 예: `192.168.0.56:8000`)

   > `localhost:8000`이나 `homeassistant.local:8000`은 이 환경(HAOS 커뮤니티 SSH/cloudflared 애드온, 브리지 네트워크)에서 동작하지 않는 것으로 실측 확인됨. `homeassistant.local`은 HA Supervisor 내부 DNS가 호스트의 모든 인터페이스 IP(도커 브리지 게이트웨이 포함)를 무작위 순서로 반환하는 특수 케이스라 신뢰할 수 없다. 반드시 LAN IP를 명시할 것. 이에 따라 `docker-compose.prod.yml`의 앱 포트는 `0.0.0.0:8000:8000`으로 바인딩되어 있다(LAN 내 다른 기기에서도 포트 8000 직접 접근 가능 — 인터넷에는 노출 안 됨, 홈 네트워크 신뢰 전제).
   >
   > 라즈베리파이 IP가 DHCP로 바뀌면 이 설정이 깨지므로, 공유기에서 라즈베리파이에 고정 IP(DHCP 예약)를 걸어둘 것.
3. 저장하면 DNS CNAME(`jog.onlypearson.com → <tunnel-id>.cfargotunnel.com`)이 자동 생성됩니다.
4. 외부 접근 검증:

```bash
curl -I https://jog.onlypearson.com/health
```

## OAuth / Apple Health 연동

1. **Google Cloud Console**
   - 승인된 리디렉션 URI: `https://jog.onlypearson.com/api/v1/auth/google/callback`
   - 승인된 JavaScript 원본: `https://jog.onlypearson.com`
2. **Apple Health(Health Auto Export) 연동**
   - `https://jog.onlypearson.com`에 Google 로그인 후 프로필 페이지 → "Apple Health 연동" → `webhook_secret`과 webhook URL(`https://jog.onlypearson.com/api/v1/webhook/apple-health`) 발급 (시크릿은 이때 1회만 표시됨)
   - Health Auto Export 앱 → Automations → New Automation → REST API → URL/헤더(`X-Webhook-Secret`)에 위 값 입력, Data Type은 **Workouts**로 설정
   - 이 연동은 Google OAuth와 무관한 별도 흐름이며, 앱별 승인/유료 심사가 필요 없음(Strava와 달리 Apple의 공식 API가 아니라 우리가 직접 만든 webhook 수신 엔드포인트)

## 재배포 (업데이트)

```bash
cd jog-post
git pull origin main
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml logs -f app
```

## 엔드투엔드 검증

1. 브라우저로 `https://jog.onlypearson.com` 접속 → Google 로그인
2. 프로필에서 Apple Health 연동 → Health Auto Export 앱에 시크릿/URL 설정 → 수동 export 1회 실행
3. 활동 목록에 나타나는지, 경로 지도·1km 구간이 정상 렌더링되는지 확인
4. 같은 기간을 다시 export해도 중복 저장되지 않는지(멱등성) 확인
5. 실제 러닝 완료 후(폰 잠금 해제 상태에서) webhook이 도달하는지 `docker compose -f docker-compose.prod.yml logs -f app`에서 확인

## Home Assistant Add-on으로 배포 (대안)

`docker compose` 대신 HAOS의 Supervisor 애드온 스토어를 통해 배포할 수도 있습니다. 이 방식은 앱 컨테이너만 add-on으로 관리하고, PostgreSQL은 별도의 공식 Postgres add-on(예: `a0d7b954/postgresql`)에 의존합니다 — HA add-on은 원칙적으로 단일 컨테이너이므로 `docker-compose.prod.yml`의 `db` 서비스를 그대로 옮길 수 없습니다.

### 사전 조건

- Supervisor 애드온 스토어에서 공식 **PostgreSQL** add-on 설치 및 기동, 그 안에 `jogpost` 데이터베이스/사용자 생성
- Postgres add-on의 접속 호스트명(보통 add-on 슬러그 기반, 예: `core-postgresql` — 실제 값은 설치한 add-on의 정보 화면에서 확인) 확인

### 1. GHCR 이미지 준비

`.github/workflows/docker-publish.yml`이 `main` 브랜치 push마다 `ghcr.io/bluewings109/jog-post`(`linux/amd64` + `linux/arm64`)로 이미지를 빌드/publish합니다. `jogpost/Dockerfile`은 이 이미지를 `FROM`으로 가져와 HA add-on 옵션(`/data/options.json`)을 환경변수로 변환하는 `run.sh` 래퍼만 얹습니다. 이 add-on 이미지 자체는 Supervisor가 설치 시점에 로컬(라즈베리파이) 빌드하므로 별도 push는 필요 없습니다.

### 2. 저장소를 add-on repository로 등록

1. HA → **설정 → 애드온 → 애드온 스토어** → 우측 상단 메뉴 → **저장소**
2. `https://github.com/bluewings109/jog-post` 입력 후 추가 (repo 루트의 `repository.yaml`을 인식)
3. 목록에 "JOG-POST" add-on이 나타나면 설치

### 3. 옵션 설정

설치 후 **설정** 탭에서 다음 값을 입력합니다.

| 옵션 | 값 |
|------|-----|
| `google_client_id` / `google_client_secret` | Google Cloud Console 발급값 |
| `jwt_secret_key` | 운영용 랜덤 값 |
| `frontend_url` | `https://jog.onlypearson.com` |
| `db_host` / `db_port` / `db_name` / `db_user` / `db_password` | Postgres add-on 접속 정보 |
| `llm_provider` / `llm_api_key` / `llm_model` | 사용할 LLM 공급자 (비워두면 AI 조언 기능 비활성) |
| `advice_enabled` | AI 조언 기능 on/off |

### 4. 기동 및 확인

**정보** 탭에서 시작 → **로그** 탭에서 `uv run alembic upgrade head` 완료와 `Uvicorn running on http://0.0.0.0:8000` 로그를 확인합니다. 이후 Cloudflare Tunnel 설정(위 섹션과 동일하게 라즈베리파이 LAN IP:8000)과 Google OAuth 리디렉션 URI 설정은 `docker compose` 배포 때와 동일합니다.

### `docker compose` 방식과의 차이

| 항목 | `docker compose` | HA Add-on |
|------|-------------------|-----------|
| DB 관리 | `db` 서비스로 같이 관리 | 별도 Postgres add-on 필요 |
| 설정 방법 | `.env` 파일 | Supervisor 애드온 설정 UI |
| 업데이트 | `git pull` + `docker compose up -d --build` | Supervisor 스토어에서 업데이트 알림 → 클릭 한 번 |
| 이미지 빌드 위치 | 라즈베리파이에서 직접 | GHCR(멀티스테이지 앱 이미지)는 CI, add-on 래퍼는 로컬 |

## 트러블슈팅

| 증상 | 확인 순서 |
|------|-----------|
| `app` 컨테이너가 계속 재시작됨 | `docker compose -f docker-compose.prod.yml logs app`으로 alembic 마이그레이션 에러 확인 → `DATABASE_URL`이 `db` 서비스명을 가리키는지 확인 |
| healthcheck가 `unhealthy`로 유지 | `docker compose -f docker-compose.prod.yml exec app curl -f http://localhost:8000/health` (또는 python으로 동일 요청)으로 컨테이너 내부에서 직접 확인, `start_period`가 짧아 기동 중 오탐인지 확인 |
| `jog.onlypearson.com` 접속 시 502/523 | cloudflared가 가리키는 URL(`localhost:8000` vs LAN IP)이 실제 `app` 컨테이너 바인딩과 일치하는지 확인 (`docker compose -f docker-compose.prod.yml ps`로 포트 매핑 확인) |
| Apple Health webhook이 401 반환 | Health Auto Export 앱의 `X-Webhook-Secret` 헤더 값이 프로필에서 발급받은 시크릿과 정확히 일치하는지 확인 (재연동 시 이전 시크릿은 자동 무효화됨) |
| Apple Health export 후 활동이 안 보임 | `docker compose -f docker-compose.prod.yml logs app`에서 `saved`/`skipped` 카운트 확인 — workout `name`에 "run"이 없으면 스킵됨(달리기 외 운동) |
| alembic 마이그레이션 실패 후 롤백 필요 | `docker compose -f docker-compose.prod.yml run --rm app sh -c "cd /app/backend && uv run alembic downgrade -1"`로 직전 리비전으로 롤백 후 원인 조사 |
