#!/usr/bin/env bash
set -Eeuo pipefail

repo_root="$(git rev-parse --show-toplevel)"
commit_sha="$(git rev-parse HEAD)"
if [[ -n "$(git status --porcelain)" ]]; then
  echo "Refusing to run from a dirty checkout; use a clean disposable checkout." >&2
  exit 2
fi
command -v docker >/dev/null
docker compose version >/dev/null
command -v python3 >/dev/null
python3 -c 'import playwright' >/dev/null || {
  echo "Install requirements-uat.txt and Chromium before running this script." >&2
  exit 2
}

test_dir="$(mktemp -d "${TMPDIR:-/tmp}/ningbo-admin-uat.XXXXXX")"
artifact_dir="${ADMIN_UAT_ARTIFACT_DIR:-$repo_root/artifacts/admin-uat}"
mkdir -p "$artifact_dir"
project="ningbo-admin-uat-$(date +%s)-$$"
env_file="$test_dir/.env.uat"
override_file="$test_dir/compose.uat.yml"
compose_file="$test_dir/docker-compose.yml"
cleanup() {
  status=$?
  trap - EXIT
  set +e
  if [[ -f "$compose_file" && -f "$env_file" ]]; then
    docker compose -p "$project" --env-file "$env_file" -f "$compose_file" -f "$override_file" ps >"$artifact_dir/containers.txt" 2>&1
    docker compose -p "$project" --env-file "$env_file" -f "$compose_file" -f "$override_file" down --volumes --remove-orphans >/dev/null 2>&1
  fi
  rm -rf "$test_dir"
  exit "$status"
}
trap cleanup EXIT

git -C "$repo_root" archive "$commit_sha" | tar -x -C "$test_dir"
cat >"$env_file" <<EOF
POSTGRES_DB=rehouse
POSTGRES_USER=rehouse
POSTGRES_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_hex(24))')
APP_API_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
ENABLE_ONLINE_COLLECTION=false
DTK_BASE_URL=
DTK_API_KEY=
API_BIND_IP=127.0.0.1
API_PORT=${ADMIN_UAT_PORT:-18787}
EOF
cat >"$override_file" <<'EOF'
services:
  db:
    networks:
      - private
  api:
    networks:
      - private
networks:
  private:
    internal: true
EOF

if [[ -n "$(docker compose -p "$project" -f "$compose_file" ps -q 2>/dev/null || true)" ]]; then
  echo "Unique UAT compose project unexpectedly already exists; refusing to reuse it." >&2
  exit 3
fi

docker compose -p "$project" --env-file "$env_file" -f "$compose_file" -f "$override_file" up -d --build db api
base_url="http://127.0.0.1:${ADMIN_UAT_PORT:-18787}"
ready=false
for _ in $(seq 1 60); do
  if curl --fail --silent "$base_url/healthz" >/dev/null; then
    ready=true
    break
  fi
  sleep 2
done
if [[ "$ready" != true ]]; then
  echo "Isolated API did not become healthy." >&2
  docker compose -p "$project" --env-file "$env_file" -f "$compose_file" -f "$override_file" ps >&2 || true
  exit 4
fi

export ADMIN_UAT_BASE_URL="$base_url"
export ADMIN_UAT_API_KEY="$(sed -n 's/^APP_API_KEY=//p' "$env_file")"
export ADMIN_UAT_ARTIFACT_DIR="$artifact_dir"
export UAT_COMMIT_SHA="$commit_sha"
python3 "$test_dir/scripts/admin_uat_browser.py"
