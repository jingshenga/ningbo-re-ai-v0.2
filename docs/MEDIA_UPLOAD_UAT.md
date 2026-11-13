# 视频上传后端：DXP4800隔离验收

本覆盖文件用于已有的隔离项目 `rehouse-ai-uat-20261113`，不引用生产Compose目录、生产卷或生产端口。隔离PG17卷仍为 `rehouse-ai-uat-20261113-pgdata`，API仅绑定 `127.0.0.1:18788`；视频与任务清单写入该项目独立 `data/media-uploads-uat` 目录，默认UAT上限25MiB/单文件、100MiB总配额。真实部署前先核对容器标签及挂载，禁止 `down -v`。

## 更新隔离API/Worker

在NAS项目目录 `/volume3/docker/rehouse-ai-uat-20261113` 中，保留现有权限为0600的 `.env.uat`。下列命令只重建API和应用Worker；不选择 `db` 服务，不重启PG容器，也不修改卷：

```sh
docker compose --env-file .env.uat -p rehouse-ai-uat-20261113 \
  -f docker-compose.yml -f compose.uat.yml -f compose.media-upload-uat.yml \
  config --services

mkdir -p data/media-uploads-uat
chown 10001:10001 data/media-uploads-uat
chmod 700 data/media-uploads-uat

docker compose --env-file .env.uat -p rehouse-ai-uat-20261113 \
  -f docker-compose.yml -f compose.uat.yml -f compose.media-upload-uat.yml \
  up -d --build --no-deps api worker
```

API容器使用 `Dockerfile.uat-media` 中的FFmpeg与RapidOCR 1.4.4；UAT固定单个Uvicorn worker。服务启动后运行真实OCR隔离验收：

```sh
docker exec rehouse-ai-uat-20261113-api-1 \
  python /srv/scripts/media_upload_uat.py
```

该脚本由容器内FFmpeg生成合成MP4，经HTTP上传到API，再等待真实RapidOCR完成；核对OCR文本/字段/帧证据、价格保持 `not_calibrated`，并在只读事务中确认 `videos`、`source_listings`、`price_history` 行数前后不变。它不删除已完成任务或证据。

## 用户电脑访问现有后台

在用户电脑开启本地SSH隧道：

```sh
ssh -N -L 18788:127.0.0.1:18788 notedock-nas
```

浏览器打开 `http://127.0.0.1:18788/admin/`，登录密码使用该UAT实例的 `APP_API_KEY`。可通过SSH在NAS终端查看该隔离实例的密钥：

```sh
ssh notedock-nas 'grep "^APP_API_KEY=" /volume3/docker/rehouse-ai-uat-20261113/.env.uat'
```

此命令只读取UAT密钥；不要将其粘贴到网页脚本、URL、截图或日志。停止隧道即可撤销该电脑的临时访问；不要直接访问NAS公网映射，也不要把UAT回环端口改为 `0.0.0.0`。

截至本说明编写时，现有 `/admin/` 可以通过该隧道浏览；真实视频上传页面由ZCode Issue #29交付后才能在浏览器操作。后端验收脚本证明API的真实文件/OCR链路，不冒充页面验收。
