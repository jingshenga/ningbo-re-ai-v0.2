# 视频上传后端：DXP4800隔离验收

本覆盖文件只用于隔离项目 `rehouse-ai-uat-20261113`；不引用生产Compose目录、数据库卷或端口。PG17使用命名卷 `rehouse-ai-uat-20261113-pgdata`。API回环端口为 `127.0.0.1:18788`；当前NAS UAT另以私有IP `10.10.10.7:18789` 提供浏览器访问，应用来源白名单仅允许当前Mac的 `10.10.10.89/32`。无公网绑定或端口转发。UAT上传目录为独立的 `data/media-uploads-uat`，单文件限制25MiB、总配额100MiB、处理临时空间预留50MiB。运行命令前先核对容器项目标签和挂载，禁止 `down -v`。

此验收配置依赖PR #25的隔离PG17 Compose文件；PR #31选择本PR跟踪的 `Dockerfile.media-upload-uat`，其中安装FFmpeg/RapidOCR并复制验收脚本。字体不需在NAS安装，验收视频由本机预先生成。

## 准备合成视频

把获准的纯合成MP4复制到NAS UAT数据目录，不要放进数据库卷：

```sh
mkdir -p data/uat-media
install -m 600 /path/to/nbre-nas-uat-zh-listing.mp4 data/uat-media/nbre-nas-uat-zh-listing.mp4
sha256sum data/uat-media/nbre-nas-uat-zh-listing.mp4
```

标准样本SHA-256为 `3459916d8dadd12ab6056ac22ee47b3ef99a94cbfaf0ce56042d3363cbe1fe53`，内容为东湖花园、建筑面积160平方米、3室2厅、报价365万元。可通过 `NBRE_MEDIA_UAT_VIDEO` 和 `NBRE_MEDIA_UAT_VIDEO_SHA256` 指定其他经授权的合成MP4及其摘要。

## 更新隔离API/Worker

在NAS项目目录 `/volume3/docker/rehouse-ai-uat-20261113` 中保留原有权限为0600的 `.env.uat`。下列命令只重建API和应用Worker；不选择 `db` 服务，不重启PG容器，也不修改卷：

```sh
docker compose --env-file .env.uat -p rehouse-ai-uat-20261113 \
  -f docker-compose.yml -f compose.uat.yml -f compose.media-upload-uat.yml \
  config --services

docker compose --env-file .env.uat -p rehouse-ai-uat-20261113 \
  -f docker-compose.yml -f compose.uat.yml -f compose.media-upload-uat.yml \
  up -d --build --no-deps api worker
```

API/Worker使用FFmpeg、RapidOCR 1.4.4；单个Uvicorn worker处理队列任务。样本放好后执行：

```sh
docker exec rehouse-ai-uat-20261113-api-1 \
  python /srv/scripts/media_upload_uat.py
```

该脚本用FFmpeg对样本做无损重封装以生成唯一SHA-256，再经真实上传API排队并运行RapidOCR。它检查小区、价格、面积、户型线索、帧证据、重复上传409以及 `not_calibrated` 边界；并以只读查询确认隔离数据库中的 `videos`、`source_listings`、`price_history` 行数前后不变。该脚本只读确认数据库名为 `rehouse_uat`，不创建挂牌或成交记录。成功任务与帧证据保留在隔离上传目录。

## 用户电脑访问后台

在可信LAN中，打开配置的NAS私有IP和白名单端口，例如：

```text
http://10.10.10.7:18789/admin/
```

登录口令是该隔离实例的 `APP_API_KEY`（保存在NAS项目目录的 `.env.uat`，不要发给浏览器脚本、URL或截图）。更换电脑时，应先把该电脑单独加入 `NBRE_UAT_ALLOWED_CLIENTS`，不得放宽为公网地址或通配CIDR。当前经NAS SSH隧道访问时，容器看到的是Docker桥接来源地址；若不在白名单中会返回403，因此当前UAT使用上面的单机LAN白名单访问。不要改SSH服务配置，也不要把API端口绑定到 `0.0.0.0`。
