# CreatorHub Sidecar 桥接器部署与运维说明

`tools/bridges/creatorhub_bridge.py` + `docker/creatorhub-bridge.Dockerfile` + `docker-compose.sidecars.yml` 组成一条**单向、只读**的社交线索同步通道：从内容创作工具 CreatorHub 的 SQLite 数据库读取新帖子，推送到主服务 `POST /api/v1/ingest/social` 入库为宁波房产待核实线索。

**安全模型（重要）**：桥接器对 CreatorHub 只读（SQLite URI `mode=ro`，永不取写锁、永不写 CreatorHub 数据）；对主服务只走 HTTP POST；**本进程内没有任何 PostgreSQL 连接或 SQL 写入**。数据入库统一由主服务完成（参数绑定 + 幂等去重）。

## 1. 拓扑

```
[CreatorHub 容器]                    [主项目栈（Codex 部署）]
  SQLite creatorhub.db <---只读挂载--- creatorhub-bridge ---HTTP POST--> app:8000
        |                              |                (POST /api/v1/ingest/social)
        +---------- sidecar-internal 网络 ----------+   +---- main-net（外部网络）----+
```

- 三个容器两两隔离：CreatorHub 与桥接器在 `sidecar-internal` 内网；桥接器同时加入主项目网络 `main-net`（默认 `ningbo-re-ai_private`，可用 `MAIN_COMPOSE_NETWORK` 覆盖）。主项目服务名为 `api`，默认目标为 `http://api:8000/api/v1/ingest/social`。
- 默认不发布主机端口；NAS Compose 仅把 UI 和扫码桌面绑定到主机 `127.0.0.1`，bridge 不发布端口。
- 桥接器对 CreatorHub 数据目录**只读挂载**（`:ro`），游标状态写在独立卷 `bridge-state`。

NAS 版本将 UI 与扫码桌面仅绑定到 NAS 回环地址的 `8001` 和 `5901`，不开放 LAN 或公网端口。CreatorHub 本身不提供登录/密码门禁，并通过中间件强制本机访问；不得直接把它放到未受保护的反向代理后。网页访问和二维码窗口都通过 SSH 隧道进入：

```sh
ssh -N -L 8789:127.0.0.1:8001 -L 5901:127.0.0.1:5901 <NAS别名>
```

浏览器打开 `http://127.0.0.1:8789`；用 macOS 屏幕共享/VNC 客户端连接 `vnc://127.0.0.1:5901`。二维码只显示在 VNC 桌面中的平台浏览器窗口。VNC 端口仅监听 NAS 回环并由 SSH 身份认证保护。

## 2. 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `MAIN_APP_INGEST_URL` | `http://app:8000/api/v1/ingest/social` | 主服务 ingest 端点；compose 内用容器名，主机直连用 `http://127.0.0.1:<端口>` |
| `MAIN_APP_API_KEY` | 空 | 主服务 `APP_API_KEY`；主端未配置密钥时留空（此时主端仅接受回环调用） |
| `CREATORHUB_DB_PATH` | `/data/creatorhub/creatorhub.db` | CreatorHub SQLite 文件在桥接容器内的路径（只读） |
| `SYNC_STATE_PATH` | `/data/bridge_state.json` | 游标状态文件（容器内写入独立卷） |
| `POLL_INTERVAL_SECONDS` | `60` | 轮询间隔（`--loop` 模式） |
| `SYNC_BATCH_SIZE` | `25` | 单批最多处理条数（上限 200） |

CLI：`python creatorhub_bridge.py --once`（单批后退出）或 `--loop`（默认，持续轮询）；`--batch-size N` 临时覆盖。

CreatorHub 应用的默认 SQLite 路径是 `./data/creatorhub.db`。应用挂载为 `/app/data` 时，桥接器对应路径应设为 `/data/creatorhub/creatorhub.db`。

## 3. CreatorHub 数据契约

桥接器以 SQLite `mode=ro` 打开 CreatorHub 数据库，支持两种结构：

1. `posts` 导出表：使用 `id`、`platform`、`post_id`、`source_url`、`title`、`content`、`author_name`、`publish_time`、`media_urls`、`tags`、`raw_html_snippet`。
2. CreatorHub 应用数据库：从 `contentrecord` 读取作品描述、平台 ID 与发布时间，并左连接 `monitortarget` 取得作者昵称和标签。抖音与小红书的公开 URL 按各自稳定的帖子 ID 形式生成；标题取作品描述前 300 字，正文保留原描述。桥接器不读取账号 Cookie、浏览器 Profile 或媒体文件，也不把本地媒体缓存路径作为 URL 发送。当前结构没有来源 URL 的其他平台记录会安全跳过。

两种结构均以单调递增的 `id` 作为游标。字段容忍度：

- `platform`：`xiaohongshu/小红书/xhs`→`xiaohongshu`；`douyin/抖音`→`douyin`；`channels/视频号/公众号/微信`→`channels`；其余→`other`；
- `media_urls`/`tags`：接受 JSON 数组或逗号分隔字符串（≤20 项，单项≤2000 字符）；
- **本地跳过规则**（游标照常推进，stderr 记警告）：`content` 为空，或 `source_url` 非 `https://`——这类记录重试永远不会成功。

CreatorHub `ContentRecord` 来源没有 `attestation` 字段，因此不会伪造授权说明；这些帖子按原始来源链接进入未核实线索流程。只在 CreatorHub 中设置你有权监控的账号/关键词，主系统仍不会把帖子自动升级为正式挂牌或成交记录。

## 3.1 Bark 与人工登录

1. 在「通知」页添加 Bark 渠道，填写设备 Key（服务器地址通常保留默认值），随后点击测试通知。密钥不会回传到页面读取接口。
2. 在「账号」页选择平台并启动扫码。切到同一 SSH 隧道内的 VNC 桌面，手动使用平台 App 扫码；登录窗口不可见或平台要求验证时，按页面提示人工操作，不绕过验证。

「设置 → 采集与运行」中建议将全局间隔设为 600 秒或更长；保持保守风险控制默认值，不配置代理或自动互动/发布任务。采集行为应遵守平台规则、账号授权和内容隐私要求。

## 4. 游标与失败语义

状态文件 `{"last_id": N, "version": 1, "updated_at": ...}`，原子写（tmp+rename）：

| 主端响应 | 行为 |
|---|---|
| 200/201 stored | 推进游标，计数 `stored` |
| 422 `not_ningbo_related` | 推进游标（永久安全跳过），计数 `skipped_not_ningbo` |
| 503 `storage_pending` | **游标保持**，批停止，下轮重试同一行 |
| 5xx / 网络错误 / 超时 | **游标保持**，批停止，下轮重试 |
| 其他 4xx | **游标保持**并在 stderr 报出行号与原因（防止静默丢失；修复 CreatorHub 数据后自动继续） |

幂等性由主端保证（`raw_sha256` 唯一去重），因此 200/201 语义下重复推送安全。

## 5. 部署命令

在已运行主项目的部署目录中浅克隆 CreatorHub 源码，并先创建独立数据目录：

```sh
git clone --depth=1 https://github.com/3441293738/creatorhub.git creatorhub-src
mkdir -p creatorhub-data bridge-data
cp creatorhub-src/config.example.yaml creatorhub-data/config.yaml
touch creatorhub-data/creatorhub.db
```

`creatorhub-data/config.yaml` 使用 `server.host: 127.0.0.1`、`server.port: 8000`、`storage.db_path: ./data/creatorhub.db`，并将 `engine.scan_interval_seconds` 调整为 600。保留应用默认的保守风险控制，不配置代理，也不开启自动评论、私信、发布或互动任务。

主项目网络名默认为 `ningbo-re-ai_private`，主项目 `.env` 必须包含 `APP_API_KEY`。桥接器只挂载 SQLite 数据库文件本身（`:ro`），不挂载账号 Profile/Cookie 目录。启动新项目时只操作自己的 Compose 文件：

```sh
docker compose -f docker-compose.sidecars.yml config --quiet
docker compose -f docker-compose.sidecars.yml up -d --build
docker compose -f docker-compose.sidecars.yml ps
```

该 Compose 不会重建主 `api`、`worker` 或 `db`。首次构建包含 Chromium、Node.js、中文字体和虚拟显示桌面，耗时与镜像体积会高于纯 API 容器。

验收检查：

```sh
curl -fsSI http://127.0.0.1:8001/health
docker logs creatorhub --tail 50
docker logs creatorhub-bridge --tail 20
docker inspect creatorhub-bridge --format '{{json .Mounts}}'
```

确认 bridge 的数据库挂载为只读单文件，状态文件写入独立的 `bridge-data` 目录。SSH 隧道命令和手动扫码步骤见本页「NAS 版本」和「Bark 与人工登录」。

UAT 冒烟（隔离网络内真实一次入库）：向 CreatorHub 插入一条含「宁波…189万」的测试帖 → 等一轮轮询 → `GET /api/videos|candidates` 或主服务日志确认 `stored`，且 `source_listings`/`price_history` 仍为 0 行。

## 6. 排查检查点

| 现象 | 检查 |
|---|---|
| `database unavailable` | `CREATORHUB_DB_PATH` 是否指向容器内只读路径；文件是否存在 |
| `config error: MAIN_APP_INGEST_URL…` | URL 必须 http/https、无凭据、无 query/fragment；容器名拼写 |
| summary 恒为 `failed: 1, hold_reason: storage_pending` | 主端 `app/social_store.py` 持久层未部署（见 Issue #30 合同）；部署后自动恢复 |
| `hold_reason: HTTP 422 not_...` 以外的 422 | 载荷校验失败（URL 域名与平台不符等）；修正 CreatorHub 行数据 |
| 游标卡死不动 | 查看 stderr 行级警告（本地跳过会推进；只有“可能恢复”的失败才保持）；必要时人工修正数据后桥接器自动续跑 |
| 回滚 | `docker compose -f docker-compose.sidecars.yml down`；不动主项目容器/卷/数据库 |
