# mixmatch — imaginea pentru server. Construită de compose.yaml; testele: --target test.

# Interfața compilată (frontend/dist).
FROM node:22-bookworm-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run lint && npm test && npm run build

# Python + ffmpeg + dependențele backendului.
FROM python:3.12-slim-bookworm AS base
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app/backend
# Întâi doar dependențele (strat refolosit cât timp pyproject.toml nu se schimbă).
COPY backend/pyproject.toml ./
RUN mkdir mixmatch && touch mixmatch/__init__.py && pip install -e .
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY backend/mixmatch ./mixmatch

# Lint + testele backendului, în același mediu ca aplicația.
FROM base AS test
RUN pip install -e ".[dev]"
COPY backend/tests ./tests
COPY backend/tools ./tools
RUN ruff check . && ruff format --diff . && pytest -q

# Aplicația.
FROM base
COPY --from=frontend /app/frontend/dist /app/frontend/dist
ENV MIXMATCH_DATA_DIR=/data \
    MIXMATCH_EXPORT_DIR=/music/mixmatch \
    MIXMATCH_UPLOAD_DIR=/music/mixmatch/Importate \
    MIXMATCH_FRONTEND_DIR=/app/frontend/dist \
    HOME=/tmp
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)"
CMD ["uvicorn", "mixmatch.main:app", "--host", "0.0.0.0", "--port", "8000"]
