# CreatorHub Sidecar 桥接器部署与运维说明

`tools/bridges/creatorhub_bridge.py` + `docker/creatorhub-bridge.Dockerfile` + `docker-compose.sidecars.yml` 组成一条**单向、只读**的社交线索同步通道：从内容创作工具 CreatorHub 的 SQLite 数据库读取新帖子，推送到主服务 `POST /api/v1/ingest/social` 入库为宁波房产待核实线索。

**安全模型（重要）**：桥接器对 CreatorHub 只读（SQLite URI `mode=ro`，永不取写锁、永不写 CreatorHub 数据）；对主服务只走 HTTP POST；**本进程内没有任何 PostgreSQL 连接或 SQL 写入**。数据入库统一由主服务完成（参数绑定 + 幂等去重）。

## 1. 拓扑

```
[CreatorHub 容器]                    [主项目栈（Codex 部署)]
  SQLite data.db  <---只读挂载--- creatorhub-bridge ---HTTP POST--> app:8000
        |                              |                (POST /api/v1/ingest/social)
        +---------- sidecar-internal 网络 ----------+   +---- main-net（外部网络）----+
```

- 三个容器两两隔离：CreatorHub 与桥接器在 `sidecar-internal` 内网；桥接器同时加入主项目网络 `main-net`（默认 `ningbo-re-ai_private`，可用 `MAIN_COMPOSE_NETWORK` 覆盖）。主项目服务名为 `api`，默认目标为 `http://api:8000/api/v1/ingest/social`。
- **零宿主机端口**：creatorhub 与 bridge 都不发布端口；主服务也保持既有回环/内网绑定不变。
- 桥接器对 CreatorHub 数据目录**只读挂载**（`:ro`），游标状态写在独立卷 `bridge-state`。

## 2. 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `MAIN_APP_INGEST_URL` | `http://app:8000/api/v1/ingest/social` | 主服务 ingest 端点；compose 内用容器名，主机直连用 `http://127.0.0.1:<端口>` |
| `MAIN_APP_API_KEY` | 空 | 主服务 `APP_API_KEY`；主端未配置密钥时留空（此时主端仅接受回环调用） |
| `CREATORHUB_DB_PATH` | `/data/creatorhub/data.db` | CreatorHub SQLite 文件在桥接容器内的路径（只读） |
| `SYNC_STATE_PATH` | `/data/bridge_state.json` | 游标状态文件（容器内写入独立卷） |
| `POLL_INTERVAL_SECONDS` | `60` | 轮询间隔（`--loop` 模式） |
| `SYNC_BATCH_SIZE` | `25` | 单批最多处理条数（上限 200） |

CLI：`python creatorhub_bridge.py --once`（单批后退出）或 `--loop`（默认，持续轮询）；`--batch-size N` 临时覆盖。

## 3. CreatorHub 数据契约

桥接器读取 CreatorHub 库的 `posts` 表，要求列：`id`（整数主键，单调递增=游标）、`platform`、`post_id`、`source_url`、`title`、`content`、`author_name`、`publish_time`、`media_urls`、`tags`、`raw_html_snippet`。字段容忍度：

- `platform`：`xiaohongshu/小红书/xhs`→`xiaohongshu`；`douyin/抖音`→`douyin`；`channels/视频号/公众号/微信`→`channels`；其余→`other`；
- `media_urls`/`tags`：接受 JSON 数组或逗号分隔字符串（≤20 项，单项≤2000 字符）；
- **本地跳过规则**（游标照常推进，stderr 记警告）：`content` 为空，或 `source_url` 非 `https://`——这类记录重试永远不会成功。

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

## 5. 部署命令清单（交 Codex 执行）

前置：主项目 compose 已运行且 social ingest 路由可用；确认主项目网络名：

```sh
docker network ls | grep ningbo   # 找到默认网络名（通常 <project>_default）
```

启动（仓库根目录）：

```sh
MAIN_COMPOSE_NETWORK=ningbo-re-ai_private \
CREATORHUB_IMAGE=<your-creatorhub-image> \
MAIN_APP_API_KEY=<主服务APP_API_KEY> \
  docker compose -f docker-compose.sidecars.yml up -d --build creatorhub-bridge
```

（CreatorHub 已另行部署时可省略 `creatorhub` 服务，只 `up -d --build creatorhub-bridge`。）

验收检查：

```sh
docker logs creatorhub-bridge --tail 20          # 应看到每轮 JSON summary
docker exec creatorhub-bridge sh -c 'ls -la /data/creatorhub'   # 只读挂载就位
cat <bridge-state 卷>/bridge_state.json          # 游标推进情况
```

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
