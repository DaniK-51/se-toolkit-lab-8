# Nanobot Dockerfile
# Multi-stage build with uv
# Build context is ./nanobot, additional_contexts: workspace: .

# ---
# Stage 1: Build the application
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy workspace files (from additional_contexts)
COPY --from=workspace pyproject.toml /app/pyproject.toml
COPY --from=workspace uv.lock /app/uv.lock
COPY --from=workspace nanobot/ /app/nanobot/
COPY --from=workspace mcp/ /app/mcp/
COPY --from=workspace nanobot-websocket-channel/ /app/nanobot-websocket-channel/
COPY --from=workspace backend/ /app/backend/
COPY --from=workspace qwen-code-api/ /app/qwen-code-api/

WORKDIR /app

# Install all workspace dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen

# ---
# Stage 2: Runtime image
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends gosu && rm -rf /var/lib/apt/lists/*

# Create non-root user matching host UID/GID for bind-mount compatibility
ARG APP_UID=1000
ARG APP_GID=1000
RUN if [ "$APP_UID" != "0" ]; then \
  groupadd --gid "$APP_GID" app || true && \
  useradd --system --gid "$APP_GID" --uid "$APP_UID" --create-home --shell /bin/bash app || true; \
  else \
  groupadd --system --gid 999 nonroot && \
  useradd --system --gid 999 --uid 999 --create-home nonroot; \
  fi

# Copy application from builder
COPY --from=builder --chown=app:app /app /app

# Create writable directories for cron and temp files
RUN mkdir -p /app/nanobot/workspace/cron /tmp/nanobot && chown -R app:app /app/nanobot/workspace/cron /tmp/nanobot

# Set PATH to include venv
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Switch to non-root user
USER app

ENTRYPOINT ["python", "/app/nanobot/entrypoint.py"]
