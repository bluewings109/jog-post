# ---- Stage 1: Frontend build ----
FROM node:20-slim AS frontend-build
WORKDIR /app
COPY frontend/package*.json frontend/
RUN cd frontend && npm ci
COPY frontend/ frontend/
RUN cd frontend && npm run build

# ---- Stage 2: Python runtime ----
FROM python:3.12-slim
WORKDIR /app

RUN pip install uv

COPY backend/ backend/
RUN cd backend && uv sync --no-dev

COPY --from=frontend-build /app/frontend/dist frontend/dist

WORKDIR /app/backend

EXPOSE 8000

CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips=*"]
