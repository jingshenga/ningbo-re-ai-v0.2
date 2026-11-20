FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    DISPLAY=:99

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
      bash curl ffmpeg fonts-noto-cjk nginx nodejs npm tini x11-utils x11vnc xvfb \
    && rm -rf /var/lib/apt/lists/*

COPY creatorhub-src/ /app/

RUN pip install --no-cache-dir -r requirements.txt \
    && python -m patchright install-deps chromium \
    && python -m patchright install chromium \
    && npm ci --no-audit --no-fund \
    && mkdir -p /app/data /tmp/nginx_client_body_temp /ms-playwright \
    && chmod -R a+rX /ms-playwright

COPY docker/creatorhub/entrypoint.sh /usr/local/bin/creatorhub-entrypoint
COPY docker/creatorhub/nginx.conf /etc/nginx/nginx.conf

RUN chmod 755 /usr/local/bin/creatorhub-entrypoint

EXPOSE 8001 5900
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/creatorhub-entrypoint"]
