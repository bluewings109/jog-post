# 라즈베리파이5(HAOS) 자가호스팅 배포 가이드

jog-post를 라즈베리파이5 + Home Assistant OS(HAOS) Supervisor 애드온 + Cloudflare Tunnel로 배포하는 상세 절차입니다. 요약은 [`CLAUDE.md`](../CLAUDE.md#배포-구조-라즈베리파이5-자가호스팅)와 [`README.md`](../README.md#라즈베리파이-자가호스팅-배포) 참고.

앱 자체는 `docker compose`가 아니라 **HAOS Supervisor 애드온 스토어**로 설치·관리합니다. repo 루트의 `repository.yaml` + `jogpost/`(add-on용 `config.yaml`, `Dockerfile`, `run.sh`)가 이를 위한 구성입니다. PostgreSQL은 HA add-on이 원칙적으로 단일 컨테이너라 앱과 묶을 수 없어 별도 add-on에 의존합니다.

## 사전 조건

- Cloudflare에서 도메인(`onlypearson.com`)을 관리 중이고, HA OS UI가 이미 Cloudflare Tunnel(Named Tunnel, Zero Trust 대시보드 관리, 공식 "Cloudflare Tunnel" add-on)로 `ha.onlypearson.com`에 연결되어 있음
- Supervisor 접근 권한 (설정 → 애드온), 필요 시 SSH & Web Terminal add-on

## 1. GHCR 이미지 준비

`.github/workflows/docker-publish.yml`이 `main` 브랜치 push마다 앱 이미지를 `ghcr.io/bluewings109/jog-post`(`linux/amd64` + `linux/arm64`)로 빌드/publish합니다. `jogpost/Dockerfile`은 이 이미지를 `FROM`으로 가져와 HA add-on 옵션(`/data/options.json`)을 환경변수로 변환하는 `run.sh` 래퍼만 얹습니다. 이 add-on 이미지 자체는 Supervisor가 설치/업데이트 시점에 라즈베리파이에서 이 얇은 레이어만 로컬 빌드하므로 별도 push는 필요 없습니다.

> **⚠️ `jogpost/config.yaml`의 `version`을 매번 올릴 것.** Supervisor는 이 값이 바뀌어야만 "업데이트 있음"으로 인식해 재빌드합니다. `jogpost/Dockerfile`이 `ghcr.io/bluewings109/jog-post:latest`를 태그 고정 없이 참조하므로, `backend/`나 `frontend/`만 고치고 `jogpost/`를 안 건드려도 **version을 안 올리면 새 앱 이미지가 절대 반영되지 않습니다.**

## 2. PostgreSQL add-on 설치

Home Assistant 공식(`hassio-addons/repository`) 저장소에는 PostgreSQL add-on이 없습니다. 커뮤니티 표준인 Expaso의 **"PostgreSQL + TimescaleDB"** add-on을 사용합니다.

1. Supervisor → 설정 → 애드온 → 애드온 스토어 → 저장소에 `https://github.com/expaso/hassos-addons` 추가
2. **PostgreSQL + TimescaleDB** add-on 설치 및 기동
3. 그 안에 `jogpost` 데이터베이스/사용자 생성
4. add-on의 **정보/네트워크** 탭에서 접속 호스트명 확인 (3단계 옵션에 필요)

## 3. jog-post add-on 설치 및 설정

1. Supervisor → 설정 → 애드온 → 애드온 스토어 → 저장소에 `https://github.com/bluewings109/jog-post` 추가 (repo 루트의 `repository.yaml`을 인식)
2. 목록에 나타난 "JOG-POST" add-on 설치
3. **설정** 탭에서 옵션 입력:

| 옵션 | 값 |
|------|-----|
| `google_client_id` / `google_client_secret` | Google Cloud Console 발급값 |
| `jwt_secret_key` | 운영용 랜덤 값 |
| `frontend_url` | `https://jog.onlypearson.com` |
| `db_host` / `db_port` / `db_name` / `db_user` / `db_password` | 2단계 Postgres add-on 접속 정보 (`db_name`/`db_user`는 `jogpost`) |
| `llm_provider` / `llm_api_key` / `llm_model` | 사용할 LLM 공급자 (비워두면 AI 조언 기능 비활성) |
| `advice_enabled` | AI 조언 기능 on/off |

4. **정보** 탭에서 시작 → **로그** 탭에서 `uv run alembic upgrade head` 완료와 `Uvicorn running on http://0.0.0.0:8000` 확인

## 4. Cloudflare Tunnel 연결

Cloudflare Tunnel(공식 "Cloudflare Tunnel" add-on)도 Supervisor 내부 도커 네트워크(`hassio`)에 있으므로, 라즈베리파이 LAN IP 대신 **컨테이너 alias**로 안정적으로 연결할 수 있습니다(LAN IP는 DHCP로 바뀌면 깨지는 문제가 있음).

1. jog-post add-on의 실제 컨테이너 alias 확인:
   ```bash
   docker ps --format '{{.Names}}' | grep -i jogpost
   # 예: addon_bf3a2436_jogpost
   docker inspect <위 이름> --format '{{json .NetworkSettings.Networks.hassio.Aliases}}'
   # 예: ["bf3a2436-jogpost"]
   ```
2. [one.dash.cloudflare.com](https://one.dash.cloudflare.com) → **Networks → Tunnels** → 기존 HA 터널 선택 → **Public Hostname** 탭 → **Add a public hostname**
   - Subdomain: `jog`
   - Domain: `onlypearson.com`
   - Service Type: `HTTP`
   - URL: `http://<alias>:8000` (예: `http://bf3a2436-jogpost:8000`)
3. 검증:
   ```bash
   docker exec <cloudflared-컨테이너명> wget -qO- http://<alias>:8000/health   # 내부
   curl -I https://jog.onlypearson.com/health                                 # 외부
   ```

**hostname 앞자리(`bf3a2436` 등)에 대한 주의사항**: 이 값은 add-on repository를 등록한 URL(`https://github.com/bluewings109/jog-post`)로부터 결정적(deterministic)으로 계산되는 해시이므로, add-on 재시작·업데이트·HA 재부팅으로는 바뀌지 않습니다. 다만 **저장소를 스토어에서 삭제 후 재등록**하거나(등록 시 입력한 URL 문자열이 조금이라도 다르면, 예: 끝에 `/` 유무), **GitHub repo 자체를 이전/개명**하면 새 해시가 나올 수 있습니다 — 그런 작업을 했다면 위 1번부터 다시 확인하고 Cloudflare Tunnel URL을 갱신해야 합니다.

공식(`core_*`) add-on과 달리, 커뮤니티/커스텀 저장소 add-on은 slug 단독(`jogpost`)으로는 resolve되지 않고 `<repo해시>-<slug>` 형태의 alias로만 통신 가능합니다.

## OAuth / Apple Health 연동

1. **Google Cloud Console**
   - 승인된 리디렉션 URI: `https://jog.onlypearson.com/api/v1/auth/google/callback`
   - 승인된 JavaScript 원본: `https://jog.onlypearson.com`
2. **Apple Health(Health Auto Export) 연동**
   - `https://jog.onlypearson.com`에 Google 로그인 후 프로필 페이지 → "Apple Health 연동" → `webhook_secret`과 webhook URL(`https://jog.onlypearson.com/api/v1/webhook/apple-health`) 발급 (시크릿은 이때 1회만 표시됨)
   - Health Auto Export 앱 → Automations → New Automation → REST API → URL/헤더(`X-Webhook-Secret`)에 위 값 입력, Data Type은 **Workouts**로 설정
   - 이 연동은 Google OAuth와 무관한 별도 흐름이며, 앱별 승인/유료 심사가 필요 없음(Strava와 달리 Apple의 공식 API가 아니라 우리가 직접 만든 webhook 수신 엔드포인트)

## 재배포 (업데이트)

1. `backend/`, `frontend/`, `jogpost/` 중 무엇을 바꿨든 `jogpost/config.yaml`의 `version`을 올리고 main에 push
2. GitHub Actions에서 GHCR 이미지 빌드 완료 확인 (`gh run list --repo bluewings109/jog-post --limit 3`)
3. HA → 애드온 스토어 → 우측 상단 메뉴 → **업데이트 확인** (UI에 안 뜨면 브라우저 강력 새로고침, 그래도 안 되면 SSH에서 `ha store update` 후 `ha addons update <slug>`)
4. JOG-POST add-on 페이지에서 업데이트 → 로그 확인

## 엔드투엔드 검증

1. 브라우저로 `https://jog.onlypearson.com` 접속 → Google 로그인
2. 프로필에서 Apple Health 연동 → Health Auto Export 앱에 시크릿/URL 설정 → 수동 export 1회 실행
3. 활동 목록에 나타나는지, 경로 지도·1km 구간이 정상 렌더링되는지 확인
4. 같은 기간을 다시 export해도 중복 저장되지 않는지(멱등성) 확인
5. 실제 러닝 완료 후(폰 잠금 해제 상태에서) webhook이 도달하는지 add-on 로그에서 확인

## 트러블슈팅

| 증상 | 확인 순서 |
|------|-----------|
| jog-post add-on이 계속 재시작됨 | add-on **로그** 탭에서 alembic 마이그레이션 에러 확인 → `db_host`/`db_port`/`db_password` 옵션이 Postgres add-on 정보와 일치하는지 확인 |
| add-on 옵션에 `false`를 넣은 boolean 값이 반영 안 됨(pydantic bool_parsing 에러) | `jogpost/run.sh`의 `get_option` 함수가 jq `//`로 falsy 값(`false`)을 빈 문자열로 치환하던 버그(1.0.1에서 수정됨) — add-on이 그 이전 버전이면 `version`을 올려 재빌드 |
| add-on 업데이트를 눌러도 버전이 그대로 | `ha addons info <slug>`로 `version_latest`가 실제로 올라갔는지 확인 → 다르면 `ha store update` 후 `ha addons update <slug>`. UI만 이전 버전으로 보이면 브라우저 강력 새로고침(`Ctrl+F5`)으로 해결되는 경우가 많음(프론트엔드 캐시) |
| `jog.onlypearson.com` 접속 시 502/523 | Cloudflare Tunnel Public Hostname의 URL이 실제 jog-post 컨테이너 alias와 일치하는지 확인 (`docker ps` + `docker inspect`로 재확인, 저장소 재등록 시 해시가 바뀌었을 수 있음) |
| Apple Health webhook이 401 반환 | Health Auto Export 앱의 `X-Webhook-Secret` 헤더 값이 프로필에서 발급받은 시크릿과 정확히 일치하는지 확인 (재연동 시 이전 시크릿은 자동 무효화됨) |
| Apple Health export 후 활동이 안 보임 | add-on 로그에서 `saved`/`skipped` 카운트 확인 — workout `name`에 "run"이 없으면 스킵됨(달리기 외 운동) |
| alembic 마이그레이션 실패 후 롤백 필요 | Postgres add-on에 직접 접속(DataGrip 등)해 `alembic_version` 테이블 확인 후 필요 시 이전 리비전으로 수동 조정, 원인 조사 |
