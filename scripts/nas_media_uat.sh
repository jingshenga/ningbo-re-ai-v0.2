#!/usr/bin/env bash
set -euo pipefail

PROJECT="rehouse-ai-uat-20261113"
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/.env.uat"
COMPOSE_FILE="$ROOT/compose.uat.yml"

random_hex() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  else
    python3 -c 'import secrets; print(secrets.token_hex(32))'
  fi
}

ensure_env() {
  if [[ -f "$ENV_FILE" ]]; then
    return
  fi
  umask 077
  local db_password api_key
  db_password="$(random_hex)"
  api_key="$(random_hex)"
  cat >"$ENV_FILE" <<EOF
POSTGRES_DB=rehouse_uat
POSTGRES_USER=rehouse_uat
POSTGRES_PASSWORD=$db_password
APP_API_KEY=$api_key
API_BIND_IP=127.0.0.1
API_PORT=18788
ENABLE_ONLINE_COLLECTION=false
DTK_BASE_URL=
DTK_API_KEY=
EOF
  chmod 600 "$ENV_FILE"
}

dc() {
  docker compose --env-file "$ENV_FILE" -f "$ROOT/docker-compose.yml" \
    -f "$COMPOSE_FILE" --project-directory "$ROOT" -p "$PROJECT" "$@"
}

health_check() {
  for _ in $(seq 1 60); do
    if curl --fail --silent http://127.0.0.1:18788/healthz >/dev/null &&
       curl --fail --silent http://127.0.0.1:18788/admin/login >/dev/null; then
      return 0
    fi
    sleep 1
  done
  echo "API health or admin login did not become ready in 60 seconds" >&2
  return 1
}

run_video_roundtrip() {
  dc exec -T -u 0:0 api sh -lc \
    'mkdir -p /data/uat-media && chown 10001:10001 /data/uat-media'

  dc exec -T api ffmpeg -y -hide_banner -loglevel error \
    -f lavfi -i 'color=c=black:s=320x240:d=2:r=2' \
    -pix_fmt yuv420p /data/uat-media/synthetic.mp4

  local video_id
  video_id="$(dc exec -T api python - <<'PY'
import os
import secrets
import httpx

response = httpx.post(
    "http://127.0.0.1:8000/api/ingest/videos",
    headers={"X-API-Key": os.environ["APP_API_KEY"]},
    json={
        "platform": "douyin",
        "source_post_id": "uat-" + secrets.token_hex(8),
        "title": "隔离验收合成视频",
        "description": "synthetic-media-uat",
    },
    timeout=15,
)
response.raise_for_status()
print(response.json()["id"])
PY
)"
  if [[ ! "$video_id" =~ ^[[:xdigit:]-]{36}$ ]]; then
    echo "视频登记未返回有效 UUID" >&2
    return 1
  fi

  dc exec -T api python scripts/enrich_local_video.py \
    /data/uat-media/synthetic.mp4 --video-id "$video_id" --submit \
    --api-url http://127.0.0.1:8000 --asr mock --ocr mock \
    --ocr-text '东湖花园 建筑面积160㎡ 挂牌365万元'

  dc exec -T api python - "$video_id" <<'PY'
import os
import sys
import httpx

video_id = sys.argv[1]
response = httpx.get(
    "http://127.0.0.1:8000/api/videos",
    headers={"X-API-Key": os.environ["APP_API_KEY"]},
    timeout=15,
)
response.raise_for_status()
row = next((item for item in response.json() if str(item["id"]) == video_id), None)
assert row is not None, "视频记录不存在"
assert row["processing_status"] == "enriched", row["processing_status"]
assert "建筑面积160㎡" in row["ocr_text"]
assert "extracted_fields" in row and row["extracted_fields"]
print("视频OCR线索已写入 enrichment；挂牌/成交表未由该流程写入。")
PY

  dc exec -T db sh -lc \
    'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT (SELECT count(*) FROM source_listings), (SELECT count(*) FROM price_history)"'
}

run_failure_recovery_check() {
  dc exec -T api sh -lc "printf 'not a video' >/data/uat-media/invalid.mp4"
  if dc exec -T api python scripts/enrich_local_video.py \
      /data/uat-media/invalid.mp4 --asr mock --ocr mock --ocr-text '合成故障'; then
    echo "无效媒体应由处理命令报告失败" >&2
    return 1
  fi
  health_check
  dc exec -T db pg_isready -U rehouse_uat -d rehouse_uat >/dev/null
  echo "媒体处理异常已隔离；API 与 PostgreSQL 17 仍可用。"
}

check_runtime() {
  dc exec -T db pg_isready -U rehouse_uat -d rehouse_uat >/dev/null
  health_check
  dc exec -T api ffmpeg -hide_banner -version | head -n 1
  dc exec -T api python -c \
    'from rapidocr_onnxruntime import RapidOCR; engine=RapidOCR(); print("RapidOCR模型初始化成功:", type(engine).__name__)'
  dc exec -T db psql -v ON_ERROR_STOP=1 -U rehouse_uat -d rehouse_uat <<'SQL'
DO $uat$
BEGIN
  IF current_setting('server_version_num')::int < 170000 THEN RAISE EXCEPTION 'PostgreSQL 17 required'; END IF;
  IF to_regclass('public.videos') IS NULL THEN RAISE EXCEPTION 'migration 001 signature missing'; END IF;
  IF to_regclass('public.collection_runs') IS NULL THEN RAISE EXCEPTION 'migration 002 signature missing'; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public' AND indexname='idx_collection_candidates_source_review') THEN RAISE EXCEPTION 'migration 003 signature missing'; END IF;
  IF to_regclass('public.collection_health_metrics') IS NULL THEN RAISE EXCEPTION 'migration 004 signature missing'; END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='saved_searches' AND column_name='max_listing_age_days') THEN RAISE EXCEPTION 'migration 005 signature missing'; END IF;
  IF to_regclass('public.collection_discovery_states') IS NULL THEN RAISE EXCEPTION 'migration 006 signature missing'; END IF;
  IF to_regclass('public.collection_listing_observations') IS NULL THEN RAISE EXCEPTION 'migration 007 signature missing'; END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='collection_discovery_states' AND column_name='sweep_number') THEN RAISE EXCEPTION 'migration 008 signature missing'; END IF;
  IF to_regclass('public.collection_listing_reviews') IS NULL THEN RAISE EXCEPTION 'migration 009 signature missing'; END IF;
  IF to_regclass('public.collection_parse_attempts') IS NULL THEN RAISE EXCEPTION 'migration 010 signature missing'; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname='collection_parse_attempts_no_truncate' AND NOT tgisinternal) THEN RAISE EXCEPTION 'migration 011 signature missing'; END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='collection_discovery_staged_ids' AND column_name='last_seen_sweep') THEN RAISE EXCEPTION 'migration 012 signature missing'; END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='monitored_accounts' AND column_name='history_backfill_cursor') THEN RAISE EXCEPTION 'migration 013 signature missing'; END IF;
  IF to_regclass('public.collection_discovery_detail_queue') IS NULL THEN RAISE EXCEPTION 'migration 014 signature missing'; END IF;
END
$uat$;
SQL
  run_video_roundtrip
  run_failure_recovery_check
  echo "隔离 Docker UAT 完成；合成数据只在 rehouse-ai-uat-20261113 项目及其专属卷内。"
}

action="${1:-accept}"
case "$action" in
  accept)
    command -v docker >/dev/null
    command -v curl >/dev/null
    ensure_env
    dc config --quiet
    dc up -d --build db api worker
    for _ in $(seq 1 90); do
      if dc exec -T db pg_isready -U rehouse_uat -d rehouse_uat >/dev/null 2>&1; then
        check_runtime
        exit 0
      fi
      sleep 2
    done
    echo "PostgreSQL 17 未在 180 秒内就绪" >&2
    dc ps
    exit 1
    ;;
  status)
    ensure_env
    dc ps
    ;;
  stop)
    ensure_env
    dc stop
    ;;
  *)
    echo "用法: $0 [accept|status|stop]" >&2
    exit 2
    ;;
esac
