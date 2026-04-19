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
