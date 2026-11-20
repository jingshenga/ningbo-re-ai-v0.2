# CreatorHub sidecar bridge: read-only SQLite poller that pushes posts to the
# main app's /api/v1/ingest/social. Built and run only in the isolated UAT
# compose project; no host ports, no production access.
FROM python:3.12-alpine

RUN addgroup -S bridge && adduser -S bridge -G bridge

WORKDIR /app
COPY tools/bridges/creatorhub_bridge.py /app/creatorhub_bridge.py
RUN pip install --no-cache-dir "httpx>=0.27,<1"

USER bridge

# Container-network defaults; override per environment in compose.
ENV MAIN_APP_INGEST_URL=http://api:8000/api/v1/ingest/social \
    CREATORHUB_DB_PATH=/data/creatorhub/data.db \
    SYNC_STATE_PATH=/state/bridge_state.json \
    POLL_INTERVAL_SECONDS=60 \
    SYNC_BATCH_SIZE=25

ENTRYPOINT ["python", "/app/creatorhub_bridge.py"]
CMD ["--loop"]
