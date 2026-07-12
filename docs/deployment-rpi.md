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
| `STRAVA_CLIENT_ID` / `STRAVA_CLIENT_SECRET` | Strava Developers 발급값 |

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
   - URL: cloudflared가 호스트 네트워크에서 동작한다면 `localhost:8000`, 별도 네트워크 네임스페이스라면 라즈베리파이의 LAN IP(`http://<rpi-lan-ip>:8000`) — 실제 환경에서 어느 쪽인지 확인 후 선택
3. 저장하면 DNS CNAME(`jog.onlypearson.com → <tunnel-id>.cfargotunnel.com`)이 자동 생성됩니다.
4. 외부 접근 검증:

```bash
curl -I https://jog.onlypearson.com/health
```

## OAuth / Webhook 갱신

1. **Google Cloud Console**
   - 승인된 리디렉션 URI: `https://jog.onlypearson.com/api/v1/auth/google/callback`
   - 승인된 JavaScript 원본: `https://jog.onlypearson.com`
2. **Strava Developers** (`https://www.strava.com/settings/api`)
   - Authorization Callback Domain: `jog.onlypearson.com` (전체 URL이 아닌 도메인만 등록)
3. **Strava Webhook 재등록**

```bash
cd backend
uv run python scripts/register_webhook.py \
  --callback-url https://jog.onlypearson.com/api/v1/webhook/strava
```

`STRAVA_WEBHOOK_VERIFY_TOKEN`이 라즈베리파이 `.env`와 Strava 앱 설정에서 일치해야 구독이 성공합니다.

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
2. Strava 연동 → 활동 동기화 버튼으로 과거 기록 가져오기
3. 실제 러닝 완료 후 webhook이 도달하는지 `docker compose -f docker-compose.prod.yml logs -f app`에서 확인

## 트러블슈팅

| 증상 | 확인 순서 |
|------|-----------|
| `app` 컨테이너가 계속 재시작됨 | `docker compose -f docker-compose.prod.yml logs app`으로 alembic 마이그레이션 에러 확인 → `DATABASE_URL`이 `db` 서비스명을 가리키는지 확인 |
| healthcheck가 `unhealthy`로 유지 | `docker compose -f docker-compose.prod.yml exec app curl -f http://localhost:8000/health` (또는 python으로 동일 요청)으로 컨테이너 내부에서 직접 확인, `start_period`가 짧아 기동 중 오탐인지 확인 |
| `jog.onlypearson.com` 접속 시 502/523 | cloudflared가 가리키는 URL(`localhost:8000` vs LAN IP)이 실제 `app` 컨테이너 바인딩과 일치하는지 확인 (`docker compose -f docker-compose.prod.yml ps`로 포트 매핑 확인) |
| Strava Webhook 구독 실패 | `STRAVA_WEBHOOK_VERIFY_TOKEN` 일치 여부, `https://jog.onlypearson.com/api/v1/webhook/strava`가 외부에서 실제로 200을 반환하는지(`curl`) 확인 |
| alembic 마이그레이션 실패 후 롤백 필요 | `docker compose -f docker-compose.prod.yml run --rm app sh -c "cd /app/backend && uv run alembic downgrade -1"`로 직전 리비전으로 롤백 후 원인 조사 |
