#!/usr/bin/env bash
set -euo pipefail

OPTIONS_FILE=/data/options.json

get_option() {
  jq -r ".$1 // empty" "$OPTIONS_FILE"
}

export GOOGLE_CLIENT_ID
export GOOGLE_CLIENT_SECRET
export JWT_SECRET_KEY
export FRONTEND_URL
export ADVICE_ENABLED
export LLM_PROVIDER
export LLM_API_KEY
export LLM_MODEL
export DATABASE_URL

GOOGLE_CLIENT_ID=$(get_option google_client_id)
GOOGLE_CLIENT_SECRET=$(get_option google_client_secret)
JWT_SECRET_KEY=$(get_option jwt_secret_key)
FRONTEND_URL=$(get_option frontend_url)
ADVICE_ENABLED=$(get_option advice_enabled)
LLM_PROVIDER=$(get_option llm_provider)
LLM_API_KEY=$(get_option llm_api_key)
LLM_MODEL=$(get_option llm_model)

DB_HOST=$(get_option db_host)
DB_PORT=$(get_option db_port)
DB_NAME=$(get_option db_name)
DB_USER=$(get_option db_user)
DB_PASSWORD=$(get_option db_password)
DATABASE_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo "[jogpost] Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."
attempt=0
max_attempts=30
until nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge "$max_attempts" ]; then
    echo "[jogpost] ERROR: PostgreSQL did not become reachable within $((max_attempts * 2))s." >&2
    exit 1
  fi
  sleep 2
done
echo "[jogpost] PostgreSQL is reachable."

cd /app/backend
uv run alembic upgrade head
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=*
