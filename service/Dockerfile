# syntax=docker/dockerfile:1.6
#
# Lean image: installs notebooklm-py (without browser extras) + FastAPI.
# Authentication is provided at runtime by mounting the host's storage_state
# at /data/storage_state.json (see docker-compose.yml).

FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NOTEBOOKLM_HOME=/data \
    NOTEBOOKLM_STORAGE_PATH=/data/storage_state.json

WORKDIR /app

# Install system deps. curl is here only so `docker exec` debugging is sane.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Copy only what's needed for installing the library first (better layer caching).
COPY pyproject.toml README.md SKILL.md AGENTS.md /app/
COPY src /app/src

# Install the library WITHOUT the [browser] extra — Playwright/Chromium are
# unnecessary inside the service. Auth happens on the host via `notebooklm login`.
RUN pip install /app

# Service deps.
COPY service/requirements.txt /app/service/requirements.txt
RUN pip install -r /app/service/requirements.txt

# Service code last — changes here don't bust the heavier layers above.
COPY service /app/service

# Non-root for safety. /data is the mount point for credentials.
RUN useradd --create-home --uid 10001 nlm \
 && mkdir -p /data \
 && chown -R nlm:nlm /data /app
USER nlm

EXPOSE 8000

# Default command. Override with `docker run … uvicorn …` if you need flags.
CMD ["uvicorn", "service.main:app", "--host", "0.0.0.0", "--port", "8000"]
