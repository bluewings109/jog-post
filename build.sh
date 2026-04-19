#!/usr/bin/env bash
set -e

# 1. 프론트엔드 빌드
echo "▶ Building frontend..."
cd frontend
npm ci
npm run build
cd ..

# 2. 백엔드 의존성 설치
echo "▶ Installing backend dependencies..."
cd backend
pip install uv
uv sync --no-dev

# 3. DB 마이그레이션
echo "▶ Running database migrations..."
uv run alembic upgrade head

echo "✓ Build complete."
