# Home Assistant의 Python 베이스 이미지 사용
ARG BUILD_FROM=ghcr.io/home-assistant/aarch64-base-python:3.12-alpine3.22
FROM ${BUILD_FROM}

# 환경 설정
ENV PYTHONUNBUFFERED=1
ENV PDM_IGNORE_SAVED_PYTHON=1
ENV PDM_CHECK_UPDATE=0
ENV PDM_USE_VENV=false


# 작업 디렉터리
WORKDIR /app

# PDM 관련 파일만 먼저 복사해서 캐시 최적화
COPY pyproject.toml pdm.lock run.sh /app/
RUN chmod +x /app/run.sh

# PDM 설치 (Home Assistant base에는 기본 Python만 있음)
RUN pip install --no-cache-dir pdm

# 의존성 설치
RUN pdm install --check --prod --no-editable

# 실제 코드 복사
COPY src /app/src

# 포트 노출 (FastAPI 기본 포트)
EXPOSE 7070

# s6-overlay entrypoint 유지
ENTRYPOINT ["/init"]

# 컨테이너 실행 명령
CMD ["/app/run.sh"]
