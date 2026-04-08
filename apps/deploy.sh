#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

DEFAULT_REMOTE_HOST="${REMOTE_HOST:-beedu}"
if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  cat <<'EOF'
Usage: deploy.sh [remote_host] [docker compose args...]

Sync the current SQLMesh repository to the remote host and run docker compose in apps/.

Arguments:
  remote_host      SSH config host name (default: beedu)

Environment overrides:
  REMOTE_DIR       Remote repo directory (default: ~/byt-ioc/byt-ioc-sqlmesh)
  REMOTE_APPS_DIR  Remote apps directory (default: ${REMOTE_DIR}/apps)
  COMPOSE_FILE     Compose file name under apps/ (default: docker-compose.yml)

Examples:
  ./apps/deploy.sh
  ./apps/deploy.sh beedu
  ./apps/deploy.sh beedu up -d --build
  ./apps/deploy.sh staging logs -f byt-ioc
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

RSYNC_ARGS=(
  -az
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
  COMPOSE_ARGS=("$@")
else
  COMPOSE_ARGS=(up -d --build)
fi

printf 'Syncing %s to %s:%s\n' "$REPO_ROOT" "$REMOTE_HOST" "$REMOTE_DIR"
ssh "$REMOTE_HOST" "mkdir -p $(printf '%q' "${REMOTE_APPS_DIR}")"
rsync "${RSYNC_ARGS[@]}" "${REPO_ROOT}/" "${REMOTE_HOST}:${REMOTE_DIR}/"

REMOTE_COMMAND="cd $(printf '%q' "${REMOTE_APPS_DIR}") && docker compose -f $(printf '%q' "${COMPOSE_FILE}")"
for arg in "${COMPOSE_ARGS[@]}"; do
  REMOTE_COMMAND+=" $(printf '%q' "${arg}")"
done

printf 'Running remote command on %s: %s\n' "$REMOTE_HOST" "$REMOTE_COMMAND"
ssh "$REMOTE_HOST" "$REMOTE_COMMAND"
