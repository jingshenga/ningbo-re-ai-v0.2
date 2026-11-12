FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /srv
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd -r -u 10001 appuser
RUN mkdir -p /data && chown 10001 /data && chmod 700 /data
COPY app ./app
USER appuser
EXPOSE 8000
