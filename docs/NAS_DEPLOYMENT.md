# 绿联 DXP4800 16GB 部署与V0.1升级指南

**2026-11-12只读复核**：通过已授权`notedock-nas`确认主机为`DXP4800/sheng`；`/volume3/docker/ningbo-re-ai/docker-compose.yml`仍为登记路径，API/Worker运行、PostgreSQL 17 healthy，NAS本机`127.0.0.1:8788/healthz`返回`ok=true`。当前Compose仅挂载001–005迁移；工作区006–012未部署。本轮未查询业务行/schema/凭据，未传输文件或改动NAS。

**运行设备**：绿联NAS / Docker Compose；推荐内网访问。2026-11-10已将工作区V0.2版本部署到DXP4800，并验证API/DB/Worker、003/004迁移及备份隔离恢复；随后备份并在生产执行005条件单筛选迁移，更新API/Worker。NAS不存在可升级的旧V0.1项目/数据库，因此旧库升级仍待验证。

2026-11-10经授权OpenSSH只读复核：API/Worker运行、PostgreSQL 17 healthy，API `/healthz`=200；贝壳和安居客均在线关闭，候选/挂牌/条件单为0行。`backups/ningbo-re-ai-20261110T063944Z-1816930`中数据库与raw-pages文件的`SHA256SUMS`通过。该备份不等于V0.1旧库备份。NAS运行中的API仍缺工作区最新`beike.py`/`anjuke.py`/`url_policy.py`且解析器/候选服务哈希较旧；尚未传输、备份或部署这些本地更新。若后续授权API-only更新，先制作新的数据库/raw-pages备份并在隔离PostgreSQL 17栈验证，再仅替换API，保持Worker/DB/卷、Compose登记路径及在线OFF不变。

同日续核留存策略：主机侧只读元数据扫描显示90天外备份0个/0字节；API服务UID下`data/raw-pages`仅有`.gitkeep`与`._.gitkeep`占位文件（2个/249字节），候选表0行。NAS现有`storage_report.py` SHA-256 `54b39480b8b2a2f6b3f45b19ede649c5ba1f8e29c033bd4253c1db4727f648ac`，不含工作区逐文件超期路径列报实现；工作区版SHA-256 `7f491af1e55532040b31f67438057ee1ad6a4ba0db4079c3f50649b162245f74`。普通SSH用户运行NAS脚本时raw-pages权限不足而显式报错；没有调整权限或创建临时容器。当前无自动清理。

## 当前 DXP4800 实例

- Compose目录：`/volume3/docker/ningbo-re-ai`；UGREEN登记名：`ningbo-re-ai`。
- 2026-11-10 NAS项目ACL审计发现源码/Compose等原有`other::rwx`，已收紧项目源码/配置目录至755、普通文件644并保留属主；`.env`=600、`data/`=700、`backups/`=700未改。调整前96条路径权限清单存于`backups/source-snapshots/permissions-before-20261110.txt`（SHA-256 `c24a855275c2ffcdafa26b1ca7ce0c7650e02a9b9e0b00bf88f1837872e9b8a9`）。仅改权限元数据，Compose配置和服务健康核对通过，未重启容器。
- API只绑定NAS本机 `127.0.0.1:8788`：主机8787已由 `nas-image-manager` 使用。访问Swagger可通过SSH本地转发到NAS的8788端口。
- PostgreSQL命名卷：`ningbo-re-ai_pgdata`。`.env`只保存在NAS项目目录，权限600，含随机 `POSTGRES_PASSWORD` 和 `APP_API_KEY`；不要覆盖或提交该文件。
- 工作区`Dockerfile`已为镜像内`/data`预置UID 10001、权限700，便于新建命名卷继承写入权限；NAS隔离派生镜像已验证该权限和证据写入。生产当前仍使用宿主机bind mount，未为此修复重建或重启生产服务。
- 贝壳/安居客在线采集总开关和来源开关均保持关闭；数据库目前没有房源/候选/运行记录。
- 2026-11-10已在当前实例先备份，再部署工作区版本并执行003/004；生产数据库仍为0条采集运行、候选与挂牌，健康指标中两个来源均为0且在线OFF。API/Worker镜像已更新，DB healthy。
- 2026-11-10随后仅更新Worker日志安全：原`app/worker.py`备份为`backups/source-snapshots/worker.py.pre-log-fields-20261110`；通过`docker compose build worker`及`up -d --no-deps worker`更新。活动账号/采集目标为0，API/DB/卷未动；容器内源码SHA-256与工作区一致，Worker启动、API `/healthz`=200、DB healthy。
- 2026-11-10再以Worker-only方式部署HTTP 200验证码/反爬挑战阻断修复：旧`app/collectors/http_client.py`备份为`backups/source-snapshots/http_client.py.pre-challenge-guard-20261110`（权限600），新文件SHA-256 `f82033dc6242a0dba48e94cf0795dd1c54e450a438c303143fb3d7befdea723a`。仅重建Worker镜像`sha256:72dbb681920a74590bd543a7d317714fb5cf307fb0af606f02ca25dad8db345d`；容器内文件哈希一致、挑战识别通过，Worker启动，API/DB健康、`/healthz`=200、来源OFF、启用采集目标0。没有访问房源页或变更API、数据库、数据卷和Compose登记。
- 2026-11-10生产部署条件单筛选扩展：先备份DB/raw-pages至`backups/ningbo-re-ai-20261109T224647Z-1242652`并验SHA256；旧源码/Compose快照为`backups/source-snapshots/workspace-before-p1-07-20261110.tar.gz`（600）。同路径Compose加入005迁移挂载，执行幂等加列迁移（部署前saved_searches=0，新增4列及约束）；API/Worker镜像分别为`sha256:6f64ce8135164e8d9c96efb129df1d7f15562be4c46a08d45769430fa59c0022`、`sha256:b478d80d565c1eaf75d78a7d317714fb5cf307fb0af606f02ca25dad8dbce0726`。部署后认证GET `/api/saved-searches`=200且0条，DB healthy，`/healthz`=200，两来源OFF、启用目标0；DB和数据卷未重启或重建。
- 2026-11-10部署P1-08条件单匹配GET API：先备份DB/raw-pages至`backups/ningbo-re-ai-20261109T232953Z-1351503`并验证SHA256；旧API源码/Compose/状态快照`backups/source-snapshots/api-before-matches-20261109T232952Z.tar.gz`（600）。NAS隔离PostgreSQL 17集成9 passed；仅构建/替换API镜像`sha256:b2e24f878bbd24b0b62130c4bc02e29fed8ac9336e30f8b22afba9ef19f9a794`，Worker、DB、卷、Docker引擎和Compose登记路径未改。`/healthz`=200、OpenAPI含GET匹配路由、未认证请求401；DB healthy、来源OFF、saved_searches/source_listings均0行。
- 2026-11-10源码快照权限复核发现旧`worker.py.pre-log-fields-20261110`为777，已设600；当前源码快照文件600、父目录700，数据库备份文件/目录分别600/700。
- 最近部署前备份：backups/ningbo-re-ai-20261109T191510Z-837029/，含database.dump、raw-pages.tar.gz与source-before.tar.gz，SHA256校验通过；目录700、文件600。
- 2026-11-10另在隔离NAS栈完成5分钟4并发候选/审批/挂牌/健康指标负载，2,175流程、10,876请求0错误；DB单核CPU峰值约108%。测试资源已清理，结果不代表生产容量。
- 2026-11-10迁移后备份 `backups/ningbo-re-ai-20261109T194304Z-884213` 已在隔离PostgreSQL 17栈恢复；dump/证据包SHA256、pg_restore目录、tar结构、权限700/600通过，恢复库业务表0行、两来源在线OFF，隔离API健康接口实读恢复库成功。生产raw-pages与归档摘要一致（2文件/249字节）；恢复栈/卷/网络/临时文件已清理，生产服务仍运行。
- 2026-11-10只读库存：`backups/`共532KiB、3个子目录、15个文件；`/volume3`约406GiB可用（55%已用）。用户确认备份保留90天、原始页面证据随关联记录保留；当前无自动删除。
- 2026-11-10用户解锁Mac后已在UGREEN项目详情页确认运行中、登记路径正确，API/PostgreSQL 17/Worker均运行。
- UGREEN登记库修改前备份：`ugreen-docker-info-log-pre-change.db`，权限600，完整性检查通过。登记行及项目页运行状态已视觉核验。

## 数据库与原始证据备份

从 Compose 项目目录运行 `bash scripts/backup.sh`。脚本将数据库导出为 PostgreSQL custom 格式、打包 `data/raw-pages`，校验两份归档并写入 `SHA256SUMS`；备份目录和文件权限分别为700/600，输出位于 `./backups/`。备份不包含 `.env`。如需设置`BACKUP_ROOT`，使用不含`..`路径组件的专用目录；脚本会在任何目录或权限修改前拒绝父目录遍历路径。API要求`data/raw-pages`是实际目录而不是符号链接，避免证据写入备份/盘点范围之外；脚本不会清理旧备份。当前策略为备份保留90天、原始页面证据随关联记录保留；工作区`backup.sh`会在容器内确认`/data/raw-pages`为真实目录，且目录树内只有普通文件和目录后才打包；`storage_report.py`可运行`python scripts/storage_report.py --backup-retention-days 90`只读查看超期候选并输出相对路径。由`backup.sh`生成的`ningbo-re-ai-...`目录按完整备份集列报，且仅当目录和其中全部普通文件均严格早于保留期限时才列出；旧式散落备份仍按文件列报。该工作区版本尚未同步到NAS；NAS旧版可能仅汇总候选数量/字节。报告忽略符号链接，只统计指定真实目录中的普通文件；报告不删除文件，清理前须核对备份集恢复能力和回滚依赖。

检查归档后，在**单独的临时数据库**演练恢复；不要把测试转储覆盖到正在使用的 `rehouse` 数据库：

```bash
BACKUP_DIR=/volume3/docker/ningbo-re-ai/backups/备份目录名
cd "$BACKUP_DIR"
sha256sum -c SHA256SUMS
cd /volume3/docker/ningbo-re-ai
RESTORE_DB="rehouse_restore_test_$(date -u +%Y%m%d%H%M%S)"
docker compose exec -T db sh -c "createdb -U \"\$POSTGRES_USER\" \"$RESTORE_DB\""
docker compose exec -T db sh -c "pg_restore --exit-on-error -U \"\$POSTGRES_USER\" -d \"$RESTORE_DB\"" < "$BACKUP_DIR/database.dump"
docker compose exec -T db sh -c "psql -v ON_ERROR_STOP=1 -U \"\$POSTGRES_USER\" -d \"$RESTORE_DB\" -Atc 'SELECT count(*) FROM source_registry'"
mkdir -p /tmp/ningbo-re-ai-restore-check
tar -xzf "$BACKUP_DIR/raw-pages.tar.gz" -C /tmp/ningbo-re-ai-restore-check
docker compose exec -T db sh -c "dropdb -U \"\$POSTGRES_USER\" \"$RESTORE_DB\""
rm -r /tmp/ningbo-re-ai-restore-check
```

核对恢复库的表和预期记录数、原始文件哈希后，只删除这次命名的 `RESTORE_DB` 和 `/tmp/ningbo-re-ai-restore-check`。若中途失败，保留备份并先查明原因；不要删生产卷或执行 Compose 全局清理。

## 一、从V0.1升级（务必保留数据）

1. **不要执行 `docker compose down -v` 或删除数据库volume。**
2. 对旧工程执行数据库备份（在旧项目目录运行，以下仅示例）：

```bash
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > backup-before-v0.2.sql
```

3. 把新工程文件部署在原Compose工程目录或确保仍使用旧项目的**同一个 PostgreSQL 数据卷**。旧Compose项目名与新项目名都设为 `ningbo-re-ai`，检查 `docker volume ls` 及 `docker compose config`，确认不会误切新数据库。
4. 替换/新增代码、`sql/002_collection_pipeline.sql`、`data/raw-pages`，修改 `.env` 新增：

```env
ENABLE_ONLINE_COLLECTION=false
COLLECTION_MIN_DELAY_SECONDS=30
```

5. 先迁移已有数据库（新SQL文件已挂载到 `db` 容器）——启动数据库后依次执行：

```bash
docker compose up -d db
docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/002_collection_pipeline.sql'
docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/003_collection_health_indexes.sql'
docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/004_collection_health_metrics.sql'
docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/005_saved_search_filters.sql'
docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/006_collection_discovery_state.sql'
docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/007_collection_listing_observations.sql'
docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/008_collection_discovery_sweeps.sql'
docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/009_collection_listing_reviews.sql'
docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/010_collection_parse_metrics.sql'
docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/011_parse_attempts_append_only.sql'
docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/012_collection_discovery_staged_ids.sql'
docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/013_account_history_backfill_cursor.sql'
docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/014_collection_detail_queue.sql'
```

`005_saved_search_filters.sql` 仅为条件单添加区域数组、偏好/排除小区和最近挂牌天数列；`006_collection_discovery_state.sql`新增目标级游标状态表；`007_collection_listing_observations.sql`按目标记录列表页中出现的来源挂牌ID、首次/最近观察时间、观察次数，以及首末列表页证据哈希和存储路径；`008_collection_discovery_sweeps.sql`为目标分页状态增加完整遍历轮次及本轮已见ID。连续2次完整分页遍历未见的记录进入`pending_review`，分页中断/失败/阻断/上限或歧义不计为完整遍历；重新观察会清零缺失次数，但不会自动清除已进入的人工核验状态。`009_collection_listing_reviews.sql`扩展观察队列状态为`reviewed`并创建追加式核验记录表，固定结论为`still_listed`、`confirmed_withdrawn`、`inconclusive`，备注可选；人工核验只记录结论，不修改正式`source_listings.status`。复核历史通过关联约束保留，不能单独删除观察行。`010_collection_parse_metrics.sql`增加每次解析的追加记录和汇总触发器；解析成功指解析器返回结果，字段完整要求来源挂牌ID、小区、总价、面积均有非空解析值。`011_parse_attempts_append_only.sql`拒绝解析记录的UPDATE、DELETE和TRUNCATE，避免插入触发器维护的累计计数与解析明细脱节。`012_collection_discovery_staged_ids.sql`将目标级成功暂存ID从游标JSON迁入独立表并回填旧值，降低长期分页状态体积；游标JSON中的`seen_listing_ids`清空后由API从规范化表读取，默认最多返回100,000项且报告截断标记。升级前必须完成数据库/raw-pages备份。013为DTK账号保存历史补采分页游标和固定30/90天截止时间，使每轮最多5页的补采可续跑；切换历史模式或显式重新补采会清除旧进度，只有读到末页才标记首次同步完成。014新增目标级持久化详情URL队列；临时详情失败会保留并记录错误类别，同时继续列表分页及其他详情，后续轮询重试。详情抓取仍受全局许可与Robots门禁约束，403/429/验证码等阻断会停止目标，不会规避限制。GET发现状态最多返回100条待抓URL并报告总量/截断。新空库按001–014顺序初始化。
`001`–`014`每份SQL文件都自行执行`BEGIN`/`COMMIT`，因此镜像新库初始化与以上手动升级命令采用相同事务边界。手动执行时保留`ON_ERROR_STOP=1`，避免SQL出错后继续；不要再添加`psql --single-transaction`，以免与文件内事务嵌套。若需回退数据迁移，应从迁移前备份恢复；不要直接删除核验/解析阶段记录表，以免丢失审核历史和指标来源。

**迁移012的回退边界**：迁移本身是单事务；执行失败时该迁移的DDL、ID回填和游标清空会整体回滚。迁移已提交后，不支持仅回滚应用代码或直接删除`collection_discovery_staged_ids`：新版允许该表累计超过旧`seen_listing_ids` JSON可承载的数量/2,000,000字节，反向聚合可能截断或拒绝写入并破坏详情去重。若必须恢复旧版本，应停止API和Worker写入，在确认迁移前数据库备份可恢复后，将该数据库与匹配的迁移前源码快照整体恢复到迁移前时间点；这会丢弃该备份之后的数据库写入。保留迁移后的raw-pages证据副本，避免恢复数据库时丢失或误删证据文件。恢复后检查表结构、目标游标/分页进度和业务行数，再启动旧版并核验健康状态。若无法接受迁移后写入损失，保持当前版本并向前修复；不要用手工SQL压缩或截断ID来回退。

`003_collection_health_indexes.sql` 使用普通 `CREATE INDEX`，构建时会暂时阻塞这两张表的写入、查询可继续。现有库应在低写入时段执行；不需要停数据库或重建数据卷。

`004_collection_health_metrics.sql` 在一个事务内回填汇总并创建维护触发器；迁移期间会锁定`source_registry`、`collection_runs`、`collection_candidates`和`source_listings`以避免回填与并发写入丢失计数。先完成备份，在低写入时段执行；读操作可继续，相关写入会等待迁移提交。迁移后通过`GET /api/collection/health`核对各来源计数。010后接口还返回累计采集成功率、解析成功率、字段完整率和审核通过率。

2026-11-10在NAS临时PostgreSQL 17库做过001–003基线的合成数据演练（250k run、250k candidate、10k listing；1核/512MiB）：004首次回填墙钟约0.74秒、重复执行约0.74秒，来源汇总与原表聚合逐字段一致。该测试没有并发写事务，未验证生产锁等待时间；它不替代生产备份、低写入时段安排或执行后核对。

另一次隔离演练在同规模库中让一个写事务提交前持锁3秒，004约0.4秒后开始并在`LOCK TABLE`上等待2.608秒；取得锁后至提交约0.631秒，回填约0.597秒，含锁等待的PostgreSQL语句耗时合计约3.239秒，包含等待期间提交的run后仍逐字段对账0差异。这只是一个受控长事务样例，不代表生产长事务分布或未来业务写请求的精确延迟。

另经NAS隔离基准发现，旧版004的挂牌更新触发器对每次`last_observed_at`前进都扫描挂牌表重算最大值：101k条挂牌下1,000次更新耗时约13.04秒。当前工作区004已调整为时间前进直接维护最大值，仅回退/来源变化时重算；同负载约146毫秒。2026-11-10已在生产数据库执行当前004，迁移前业务表均为空；汇总API和来源开关已核验。此前隔离基准仍仅用于说明合成负载性能，不外推生产容量。

6. 第一次使用新的原始页面卷，确保容器内 UID 10001 可以写入 `./data`（例如通过SSH执行 `sudo chown -R 10001:10001 ./data`，**只修改本项目的data目录**）。确认迁移返回成功，再启动其余组件：

```bash
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 api
docker compose logs --tail=100 worker
```

7. 用原有 `APP_API_KEY` 调用 `/api/collection/sources`，预期 `beike/anjuke` 两条记录且在线开关为false；测试保存HTML样本进候选池。
8. 若升级失败，保留容器日志和备份，先停止新服务，恢复匹配版本代码，**不要随意覆盖生产DB或删卷**。恢复数据库应在隔离环境先演练。

## 二、新安装

```bash
cp .env.example .env
# 编辑.env中两个不同的高强度密码，建议 openssl rand -hex 24
docker compose config
docker compose up -d --build
docker compose ps
```

首次启动前，需确保 ./data/raw-pages 对容器内UID 10001可写（例如通过SSH仅调整本工程data目录权限）。新建空数据库卷时按001_init.sql至012_collection_discovery_staged_ids.sql顺序初始化；API_BIND_IP=127.0.0.1 意味着仅NAS本机可访问。当前DXP4800实例使用127.0.0.1:8788；可通过SSH本地端口转发访问Swagger。若确需局域网访问，改为NAS所在内网IP并限制防火墙。Swagger仅为后端测试界面，不是公众产品。

## 三、离线HTML导入演示（虚构页面）

在有Python3/httpx的管理电脑执行：

```bash
APP_API_KEY='你的APP_API_KEY' python scripts/submit_html_snapshot.py fixtures/beike_demo.html \
  --source beike \
  --source-url https://nb.ke.com/ershoufang/109900001234.html \
  --api-url http://127.0.0.1:8787
```

本地提交脚本只接受不超过1,000,000字节的UTF-8 HTML；超限文件在请求API前拒绝。它不会访问贝壳或安居客来源页。

检查 `/api/collection/candidates`：必须是 `pending`。审核后才会写入正式 `source_listings`。**fixture仅是格式演示，不是宁波真实房源。不要用测试数据污染正式数据库。**

## 四、控制资源
- Worker单任务串行；日常网页目标可设置≥6小时频率，默认24小时。
- 限制原始HTML为1MB；原始页面证据随关联记录保留，并纳入90天备份；只有确认关联记录已按其保留政策删除后才能清理证据。管理密钥不得写入项目代码。
- 备份按用户确认的90天期限保留；原始页面证据在关联数据库记录保留期间必须可用，不按90天备份周期删除。同步新版脚本后，运行工作区最新版`python scripts/storage_report.py --backup-retention-days 90`可只读盘点文件占用、时间范围与超期候选路径，不会自动清理；路径列报更新同步到NAS前，其报告可能只显示数量/体积。人工清理前核实恢复能力、数据库引用及回滚依赖。
- 不建议同时在N100上高并发运行DTK全功能、ASR和OCR；先监控 CPU、RAM、磁盘占用。
- DTK服务需要单独部署并设置 `DTK_BASE_URL`/`DTK_API_KEY`；微信视频号继续独立客户端导入。

## 五、已知缺口
- 2026-11-09已在DXP4800完成V0.2空库新装、API/Worker/DB启动、健康接口PostgreSQL验收及数据库容器重启持久化验证；该NAS没有旧V0.1项目或数据库卷，因此V0.1备份升级仍未验证。
- NAS迁移后备份已在独立PostgreSQL 17中恢复，并核对数据库行数、健康API、raw-pages归档摘要及权限；临时恢复资源已清理。`/volume3`容量与备份目录已只读盘点。备份留存期限已由用户确认为90天，原始页面证据随关联记录保留；当前无自动清理。
- 默认禁止网站在线抓取；是否能够合法/稳定采集两个网站的真实页面需完成来源权限与页面样本验证。


## 2026-11-10 API上传上限 API-only更新
- 部署前备份：`backups/ningbo-re-ai-20261110T063944Z-1816930`；源码回滚快照：`backups/source-snapshots/api-before-body-limit-20261110T063944Z.tar.gz`（SHA-256 `c42280a44e0a115d8f4b3d0048df02a2209cfc6774b7c23be2642c27ed0b56cb`）。
- 使用验证过的开发包同步源码清单文件；不覆盖`.env`、`data/`、`backups/`，保留Compose登记路径。仅执行`docker compose build api`与`docker compose up -d --no-deps api`，无SQL迁移。
- 新API镜像SHA-256 `c7d12ea6f745583224b2fa937b30bb58203036dc93b85109e44c491c3083daaf`。健康接口200，未认证业务请求401，超6,100,000字节上传413；全局和来源在线开关均关闭，业务表为空。
- Worker、PostgreSQL容器ID及`ningbo-re-ai_pgdata`卷保持不变；`.env` 600、`data/`和`backups/` 700。隔离测试资源已清理，备份及源码快照保留。


## 2026-11-10 P0-08只读留存盘点
- NAS上raw-pages目录属主UID 10001，backups目录属主UID 1006:10，均700。为读取受保护目录，分别使用匹配UID、禁网且只读挂载的临时容器运行报告；未读取`.env`。
- 实测raw-pages 2文件/249字节；backups 34文件/1,056,619字节；90天超期候选0文件/0字节；`/volume3`可用约406.9GiB。无清理。
- 发现旧版报告在目录权限不足时可能静默显示0；本机修复后`tests/test_storage_report.py` 8 passed。新版脚本尚待同步并复核。
## 2026-11-10 P0-03本地SQL修复的部署状态
- 只读复核确认NAS项目仍运行API/Worker、PostgreSQL 17 healthy、`/healthz`=200，Compose文件仍登记在`/volume3/docker/ningbo-re-ai/docker-compose.yml`。业务候选/挂牌/价格历史/条件单为0，两来源OFF、启用目标0。
- NAS `app/collection_service.py` SHA-256=`479c191f67d413ad388aaa75993fc07c94115dacf19e58cd4478c33e41f36ffd`，本地修复版SHA-256=`d9d040a372f23cfa6bd05919e012f8adea7ada3565f3a07c174abef736856a39`；本地PG16隔离测试通过不代表NAS已更新。此次仅只读，未备份、传输或重建API。

## 2026-11-11 P0-08只读连接续核
- 经授权的`notedock-nas`首次SSH只读命令确认主机身份`DXP4800/sheng`、Compose服务db/api/worker、PG数据卷`ningbo-re-ai_pgdata`，以及`backups/`根目录700和顶层7个归档文件。该查询没有展开子目录，不能据此判断数据库备份是否存在。普通宿主机身份不能读取`data/raw-pages`。
- 随后的SSH复用连接被本机控制套接字权限拒绝，公网主机名解析失败；未继续远端操作，没有备份、传输或部署。新版`backup.sh`和`storage_report.py`仍待NAS实机复验。


## 2026-11-11 DXP4800只读运行态复核
- `notedock-nas`连接后确认API/Worker/PostgreSQL 17容器均运行，PG17 health=`healthy`；容器内API `/healthz`返回200，schema=`v0.2`。
- Beike在线开关关闭且策略`not_authorized`；Anjuke在线开关关闭且策略`not_reviewed`。`collection_runs`、`collection_candidates`、`source_listings`、`collection_targets`均为0行。`backups/`共34个普通文件、`du`约1.2MiB。此处未读取备份内容、校验SHA或执行恢复。
- 生产API容器的`/srv/app/collection_service.py`与工作区哈希不同，生产容器无`/srv/app/collectors/discovery.py`和`url_policy.py`；因此本轮工作区分页代码的PG17隔离测试不构成生产代码部署验收。未修改或重启任何容器、卷、Compose登记或数据库。

## 2026-11-11 当前版备份与隔离恢复验收（P0-08）
- 使用当前工作区`scripts/backup.sh`在NAS生成`/volume3/docker/ningbo-re-ai/backups/ningbo-re-ai-20261111T030737Z-3584908`。目录权限700、文件权限600；database.dump SHA-256 `4555836d9f002dafb1d516f411bf9fea5ca62281dde334983ad332e9f729e46a`，raw-pages.tar.gz SHA-256 `edf08bd9e0cdce5c638164daf3e08a376d3089e3c19654c5ec116b6a09daaf8a`。
- 用Docker `--network none`、tmpfs、无宿主端口/挂载的临时PostgreSQL 17恢复库执行完整`pg_restore`，成功；`source_registry=2`，collection_runs/candidates/source_listings/collection_targets均0。raw-pages归档解压成功。恢复容器及辅助脚本已清理，未创建持久卷。
- 当前脚本SHA-256 `5353fc94ce3ae356e1f67c9aba78be46487a24f3542b826061219440a3ddcc43`；`bash -n`和备份脚本专项9 passed。此项完成P0-08当前脚本的NAS实机备份/隔离恢复验收。
- 操作只向备份目录写入新归档；未改生产数据库/卷/API/Worker/Compose、未部署工作区代码、未清理文件、未访问房源网站。生产API与工作区代码差异仍在，不能视为已更新。
- 用户确认备份保留90天、原始页面证据随关联数据库记录保留。工作区新版`storage_report.py`的超期路径列报尚未同步到NAS，因此本次未盘点90天超期候选；当前没有自动清理。
- 该备份属于V0.2现状，不替代P0-01真实V0.1旧库迁移验收。

**迁移014应用顺序**：先完成数据库与raw-pages备份，在隔离PostgreSQL 17按001–014验证后，生产升级评估中必须先执行014再启用依赖队列表的新Worker/API。014只新增队列表和索引，队列行级联依赖挂牌观察记录；旧版程序会忽略该表，但回退后未完成URL不会由旧Worker继续处理。不得删除表来回退。
