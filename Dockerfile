# syntax=docker/dockerfile:1.6

# --- Frontend builder -------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /fe

COPY web/app/package.json web/app/package-lock.json ./
RUN npm ci

COPY web/app/ ./
RUN npm run build

# --- Backend runtime --------------------------------------------------------
FROM python:3.11-slim AS runtime
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Install Python dependencies first (cached layer)
COPY pyproject.toml ./
COPY pipeline/ ./pipeline/
COPY web/__init__.py ./web/__init__.py
COPY web/api/ ./web/api/
RUN pip install -e .[web]

# Bring in the built React SPA. FastAPI mounts this when web/app/dist exists.
COPY --from=frontend-builder /fe/dist ./web/app/dist

# Hardcode 8000 to match Railway's auto-detected port from EXPOSE.
# The $PORT interpolation pattern is finicky; matches what works in other
# Upwork projects deployed to Railway.
EXPOSE 8000

CMD ["uvicorn", "web.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
