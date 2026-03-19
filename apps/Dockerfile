# =============================================================================
# Stage 1: Build the React UI
# =============================================================================
FROM node:20-slim AS ui-builder

WORKDIR /build

# Install pnpm
RUN npm install -g pnpm@latest

# Copy workspace manifests first (better layer caching)
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY web/client/package.json ./web/client/

# Install all dependencies
RUN pnpm install --frozen-lockfile

# Copy the frontend source (openapi.json is already committed so generate:api works offline)
COPY web/client/ ./web/client/

# Build the frontend (generate:api → tsc → vite build)
WORKDIR /build/web/client
RUN pnpm run build


# =============================================================================
# Stage 2: Python SQLMesh engine + FastAPI server
# =============================================================================
FROM python:3.11-slim AS runtime

# System dependencies needed by compiled Python packages such as psycopg2.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the full Python source before installing.
# setuptools_scm generates _version.py from git tags; since .git is not in the
# build context we use SETUPTOOLS_SCM_PRETEND_VERSION so it falls back cleanly.
COPY pyproject.toml MANIFEST.in ./
COPY sqlmesh/ sqlmesh/
COPY sqlmesh_dbt/ sqlmesh_dbt/
COPY web/server/ web/server/
COPY web/__init__.py web/__init__.py

# Install SQLMesh with extras needed by the bundled sushi example and postgres state backend.
RUN SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 pip install --no-cache-dir ".[web,postgres,bigquery,mysql]"

# Copy the compiled frontend produced in Stage 1
COPY --from=ui-builder /build/web/client/dist/ web/client/dist/

# Optional: copy the example sushi project so the image is usable out-of-the-box
# COPY examples/ examples/

# SQLMesh project that will be loaded at startup.
# Override with -e PROJECT_PATH=/your/project or a bind-mount + env var.
ENV PROJECT_PATH=/app/project

# UI mode: ide | oss (controls which modules are enabled)
ENV UI_MODE=ide

# FastAPI / uvicorn settings
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

# Health-check mirrors the /health endpoint defined in main.py
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')"

CMD uvicorn web.server.app:app \
    --host "$HOST" \
    --port "$PORT" \
    --timeout-keep-alive 300 \
    --timeout-graceful-shutdown 5
