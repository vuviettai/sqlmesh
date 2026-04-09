#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DEFAULT_REMOTE_HOST="${REMOTE_HOST:-beedu}"
if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  cat <<'EOF'
Usage: deploy.sh [remote_host] [docker compose up args...]

Sync the current SQLMesh repository to the remote host, remove any existing app
container, rebuild its image, and start it again from apps/.

Arguments:
  remote_host      SSH config host name (default: beedu)

Environment overrides:
  REMOTE_DIR       Remote repo directory (default: ~/byt-ioc/byt-ioc-sqlmesh)
  REMOTE_APPS_DIR  Remote apps directory (default: ${REMOTE_DIR}/apps)
  COMPOSE_FILE     Compose file name under apps/ (default: docker-compose.yml)
  COMPOSE_SERVICE  Compose service to redeploy (default: byt-ioc)

Examples:
  ./apps/deploy.sh
  ./apps/deploy.sh beedu
  ./apps/deploy.sh beedu --wait
  COMPOSE_SERVICE=my-service ./apps/deploy.sh staging --force-recreate
EOF
  exit 0
fi

if [ "$#" -gt 0 ]; then
  REMOTE_HOST="$1"
  shift
else
  REMOTE_HOST="$DEFAULT_REMOTE_HOST"
fi

REMOTE_DIR="${REMOTE_DIR:-~/byt-ioc/byt-ioc-sqlmesh}"
REMOTE_APPS_DIR="${REMOTE_APPS_DIR:-${REMOTE_DIR}/apps}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
COMPOSE_SERVICE="${COMPOSE_SERVICE:-byt-ioc}"

RSYNC_ARGS=(
  -az
  --delete
  --human-readable
  --exclude=.git/
  --exclude=.github/
  --exclude=.venv/
  --exclude=venv/
  --exclude=node_modules/
  --exclude=__pycache__/
  --exclude=.pytest_cache/
  --exclude=.mypy_cache/
  --exclude=.ruff_cache/
  --exclude=.cache/
  --exclude=.idea/
  --exclude=.vscode/
  --exclude=.DS_Store
  --exclude=dist/
  --exclude=build/
  --exclude=htmlcov/
  --exclude=.coverage
  --exclude=.coverage.*
)

if [ "$#" -gt 0 ]; then
  UP_ARGS=("$@")
else
  UP_ARGS=(-d)
fi

printf 'Syncing %s to %s:%s\n' "$REPO_ROOT" "$REMOTE_HOST" "$REMOTE_DIR"
ssh "$REMOTE_HOST" "mkdir -p $(printf '%q' "${REMOTE_APPS_DIR}")"
rsync "${RSYNC_ARGS[@]}" "${REPO_ROOT}/" "${REMOTE_HOST}:${REMOTE_DIR}/"

printf 'Deploying service %s on %s using %s\n' "$COMPOSE_SERVICE" "$REMOTE_HOST" "$COMPOSE_FILE"
ssh "$REMOTE_HOST" bash -s -- "$REMOTE_APPS_DIR" "$COMPOSE_FILE" "$COMPOSE_SERVICE" "${UP_ARGS[@]}" <<'EOF'
set -euo pipefail

remote_apps_dir="$1"
compose_file="$2"
compose_service="$3"
shift 3
up_args=("$@")

cd "$remote_apps_dir"

compose_cmd=(docker compose -f "$compose_file")
existing_container_id="$("${compose_cmd[@]}" ps -a -q "$compose_service" || true)"

if [ -n "$existing_container_id" ]; then
  printf 'Removing existing container for service %s (%s)\n' "$compose_service" "$existing_container_id"
  "${compose_cmd[@]}" rm -f -s "$compose_service"
else
  printf 'No existing container found for service %s\n' "$compose_service"
fi

printf 'Rebuilding image for service %s\n' "$compose_service"
"${compose_cmd[@]}" build "$compose_service"

printf 'Starting service %s\n' "$compose_service"
"${compose_cmd[@]}" up "${up_args[@]}" "$compose_service"
EOF
