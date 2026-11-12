# 宁波房产 AI 情报与智能选房平台 · V0.2 目标驱动开发包

> **目标设备**：绿联 DXP4800 / Intel N100 / 16GB RAM / Docker。**类型**：单操作者后端原型 + 长期研发工作区；还不是可公开上线的成品。虚构的房价和HTML页面只用于测试。

## 1. 本次最重要的修正

**贝壳、安居客当前按网页采集技术路线设计，授权API是未来的替代方案，而不是当前前置条件。**

但是，能技术性获取到网页不代表有权自动化抓取或商业使用。贝壳现行服务协议对自动化访问、robots和商业使用有限制，安居客需单独审核。项目**不包含绕过验证码/账号限制/反爬风控**的功能。在线采集默认关闭，只有取得相应权限并完成robots核验后才可显式启用。

## 2. V0.2 实际具备的功能

| 业务能力 | 当前状态 | 备注 |
|---|---|---|
| 指定抖音账号监控/历史补采 | **已有V0.1接口与DTK适配器** | 需独立部署DTK并在NAS联调，未真实验证 |
| 指定视频号 | **账号登记+JSON导入** | 未实现自动连续监控 |
| 贝壳/安居客HTML样本解析 | **可在本地运行** | 通用保守解析器，尚未用真实宁波页面校准 |
| 公开网页在线抓取框架 | **已写入代码，但默认禁用** | 来源审查+全局开关+robots+阻断日志；并非网站已可抓 |
| 网页候选审核 | **已实现API** | 人工纠错/审批后才能进入正式挂牌库 |
| 原始证据 | **已实现** | HTML gzip + SHA256 + 来源URL +时间 |
| 小区/来源挂牌/同来源价格历史 | **已有V0.1功能，V0.2增加证据链** | SQL迁移需NAS实测 |
| 跨平台挂牌价差机会 | **已有候选API** | 同小区、同户型、面积差≤5%、挂牌单价差`(高单价−低单价)/低单价≥10%`；只提示待核实候选，不自动认定同套或合并。面积差按`abs(a-b)/min(a,b)≤5%`计算（用户已确认较小面积为分母） |
| 条件单、降价信号、通知outbox | **已有基础版** | 仅记录站内事件，无实际微信/邮件发送 |
| 逐字稿/OCR | **只接收外部文本** | 尚未自动下载视频并调用ASR/OCR |
| 公众AI问答/多用户/管理前端 | **未实现** | 属后续P1—P3 |

**验证状态（2026-11-12）**：当前解析器为`generic-labelled-v0.2.158`；解析器测试文件 **783 passed**；解析器/API/样本集/评估器四个相关文件 **1259 passed**，覆盖近似/上下限面积同义表达及证据暂存；最新全量离线pytest **1649 passed、28 skipped、27 subtests passed**，其中28项PostgreSQL集成因未设置`TEST_DATABASE_URL`而跳过。Python 3.12 `compileall`通过；P0-09已覆盖UTF-8字节上限、跨页回环、详情/页数上限及策略阻断后的多轮续跑。解析尝试明细由迁移011拒绝UPDATE、DELETE和TRUNCATE；该迁移已在隔离PostgreSQL 17.11按001–011运行并重复执行，运行时保护及1/1/1汇总保持回归通过。重复样式缓存单次解析最多保留1,024项并在返回/异常时清理；520个唯一样式后接2,000个重复样式的合成页由12,602次扫描降至2,085次。近1 MB唯一样式压力样本缓存中位数493.7 ms、未缓存472.8 ms，说明收益集中在重复样式页面。2026-11-12候选根评分与字段值接受的千分位格式一致，畸形分组不会压过有效字段根。样本清单的非空来源挂牌ID现要求匹配对应来源的ASCII数字格式；missing_fields场景不会再由multiple_prices单独导致的挂牌价空值凑数。面积与挂牌价解析下限现与模型/样本清单统一为大于0；float下溢为0.0时不输出，零值仍拒绝；“挂牌价：2万/㎡”及全角斜杠及“万元/㎡”及括号单位写法等单位面积报价不会误作挂牌总价；建筑面积识别“平/平方”单位并保留完整证据，近似/上下限面积（含“100㎡起”）留空待审并保留证据，范围报价仍完整留证且留空待审；“200万左右/以上/以下”等非精确价不会作为精确挂牌总价，有明确总价时保留总价。内容根按证据分数惰性搜索，满分main使重叠根查询/文本化由3次降至1次；证据不足时仍检查后续根。折叠details摘要前置空白改为切片批量裁剪，32,000个合成节点的文本化由约94ms降至40ms。2026-11-12选中的候选文本不再重复空白归一化，计数回归由2次降至1次。长前缀候选根评分限制到字段提取实际使用的35,000字符窗口，避免截断后的字段丢失。精确边界回归确认35,000字符恰好到上限不警告，多1字符触发截断告警并阻止审核就绪。字段证据偏移不越过窗口，窗口后的冲突报价不被当作已扫描。混合main/推荐卡/article含冲突字段时留空并告警，优先保留精确率。有界候选根归一化在800,144字节合成页中位耗时低16.5%，tracemalloc峰值低1.53 MiB。body回退路径也覆盖窗口内字段、窗口外未扫描冲突和证据偏移边界。有界归一化另有1,000组固定种子的Unicode差分回归，并穷举正则表达式识别的全部Unicode空白码点及各截断位置；DOM文本、可见性与隐藏节点处理复用已有子节点列表，样式表CSS片段改为按需流式扫描，注释/字符串筛除与内联CSS声明扫描均按片段惰性处理，避免再次物化冗余引用或片段列表。2026-11-12将同一样式的缓存键从(style,属性集合)收敛为style并缓存受审属性集合，普通样式的底层声明扫描由3次降至1次；合成300种唯一style页面中位耗时9.41 ms，旧行为13.25 ms，重复style页面耗时近似持平，不代表真实页面性能。健康率迁移010和API曾在临时PostgreSQL 16上通过全量 **741 passed、0 skipped、17 subtests passed**（含数据库集成）；另将当前工作区只读挂载到NAS隔离PostgreSQL **17**执行完整`tests/test_db_integration.py`，**24 passed**（含迁移011账本保护），清理后schema残留为0。另在NAS隔离PostgreSQL **17.11**（`--network none`、tmpfs、无端口/持久卷）执行001–010全部迁移、重复执行010，并以合成解析事件核对计数触发器`2/1/1`；这验证迁移兼容性；当前工作区完整`tests/test_db_integration.py`已在NAS隔离PG17.11运行**29 passed**，覆盖迁移001–014、详情队列API和外键级联；测试资源已清理，但不代表工作区代码已部署到生产。2026-11-12只读复核确认生产API/Worker仍运行、PostgreSQL healthy及`/healthz`=200；NAS API解析器为`generic-labelled-v0.2.5`，工作区为`generic-labelled-v0.2.158`，四个核心源码文件哈希均不一致，未部署。未携认证调用`/api/collection/health`返回401，指标正文未验证；本轮只读检查生产schema元数据、未查业务行；确认生产缺失006–014关键对象，工作区当前API/Worker未部署。健康API按用户确认口径返回采集成功率`success/(success+failed)`（排除`blocked_*`）、解析成功率（成功解析/成功获取且进入解析器）、四关键字段完整率（来源挂牌ID、小区、总价、面积均非空/解析成功）和人工审核通过率`approved/(approved+rejected)`（排除`pending`）；零分母返回null。解析尝试和字段完整统计从迁移010启用后开始，旧记录无法可靠重建解析阶段，不能据此声称解析率覆盖010之前的历史；采集与审核率沿用其现有累计记录。人工核验API只将观察队列标记为reviewed，不改变正式挂牌。挂牌连续2次完整分页遍历未见后进入pending_review，不自动下架。在线采集保持关闭，未访问来源网站；只读生产核验未修改业务数据，未部署。P0-01仍缺真实V0.1备份；P0-02/P0-03仍缺每站20份获准页面及人工标签；同页外层article与嵌套.content报价冲突现留空待审；P0-04许可和P0-07当前生产版本/迁移验收待完成；P0-09仍待获准来源/真实样本及生产版本差异验收。虚构fixture和合成数据不代表真实页面准确率、授权或生产SLO。详情见[docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)和[docs/TEST_REPORT.md](docs/TEST_REPORT.md)。

## 3. 最简部署

```bash
cp .env.example .env
# 修改.env的POSTGRES_PASSWORD、APP_API_KEY；保持ENABLE_ONLINE_COLLECTION=false
docker compose config
docker compose up -d --build
docker compose ps
```

默认仅NAS本机可访问：`http://127.0.0.1:8787/docs`，填写 `X-API-Key` 使用接口。若局域网访问需把 `.env` 的 `API_BIND_IP` 改为NAS的局域网IP，不要直接映射公网。

**已有V0.1数据库卷时不可只执行 `up`**：必须先备份并运行 `sql/002_collection_pipeline.sql`。操作顺序见 [`docs/NAS_DEPLOYMENT.md`](docs/NAS_DEPLOYMENT.md)。**禁止通过删卷完成迁移。**

## 4. 离线网页采集实验：贝壳、安居客

测试包中的 `fixtures/beike_demo.html`、`fixtures/anjuke_demo.html` 是**虚构演示网页**，用于验证数据抽取和待审核机制，并非站点真实页面或实际房价。

在能访问NAS API的电脑（已安装Python和httpx）执行：

```bash
export APP_API_KEY='填写你自己的APP_API_KEY'
python scripts/submit_html_snapshot.py fixtures/beike_demo.html \
  --source beike \
  --source-url https://nb.ke.com/ershoufang/109900001234.html \
  --api-url http://127.0.0.1:8787
```

然后在API `/api/collection/candidates` 查看 `pending` 条目；未审核时正式 `/api/listings` **不会增加房源**。对真实、有权使用的页面样本，先确认解析出来的小区、面积、总价、来源ID是否与网页相同，然后使用 `PATCH .../candidates/{id}` 更正，最后 `POST .../candidates/{id}/review?decision=approve&note=人工核对字段与原始页面一致`。

即使某页被解析为 `ready_for_review=true` 也**不是自动批准**。如果来源ID或关键字段缺失，必须补正后才能审批。

## 5. 在线目标采集为什么默认关闭

`POST /api/collection/targets` 支持登记目标URL、24小时检查周期等；但新目标默认 `enabled=false`，`source_registry` 的贝壳/安居客默认不允许在线操作，`.env` 的 `ENABLE_ONLINE_COLLECTION=false` 是第二道全局门。任何一层不满足，Worker只记录 `blocked_policy`；**绝不静默伪装成采集成功**。

只有经过实际的条款、robots、使用范围及许可核查，才由运营者在 `POST /api/collection/sources/{source}/policy-review` 中记录审核证据并明确开启对应来源；网站禁止访问或返回403/429将直接停止。此框架还未接受真实站点联调，**不能宣称已经能每天稳定采到贝壳/安居客房源**。

## 6. 用“目标驱动模式”持续开发

建议把本工程作为长期项目/仓库存档：

1. 把 [`AGENTS.md`](AGENTS.md) 设为编码助手的仓库规则；把 [`docs/MASTER_DEVELOPMENT_PROMPT.md`](docs/MASTER_DEVELOPMENT_PROMPT.md) 作为项目级开发总提示词；如果项目指令有长度限制，用 [`prompts/PROJECT_INSTRUCTIONS_SHORT.md`](prompts/PROJECT_INSTRUCTIONS_SHORT.md)。
2. 每轮开始用 [`prompts/NEXT_ITERATION.md`](prompts/NEXT_ITERATION.md)，按 [`docs/ROADMAP.md`](docs/ROADMAP.md) 和 [`docs/GOAL_STATE.json`](docs/GOAL_STATE.json) 的未完成最高优先级推进。
3. 每轮结束要更新 [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) 和 [`CHANGELOG.md`](CHANGELOG.md)，记录真实测试/未测试状态，避免跨会话重复讨论或错把计划当完成。
4. 初次迭代任务建议用 [`prompts/SPRINT_01.md`](prompts/SPRINT_01.md)：真实网页解析器校准、NAS迁移测试和抖音联调。
5. 每轮交付包用`python scripts/package_dev.py --output ../ningbo-re-ai-v0.2-dev-<iteration>.zip`生成；脚本会刷新SHA-256清单、校验ZIP及包内哈希，并排除秘密、备份、运行数据、缓存和旧ZIP。

## 7. 文件导航

- `AGENTS.md`：长期开发中不得违背的技术和商业约束。
- `docs/MASTER_DEVELOPMENT_PROMPT.md`：完整开发总提示词。
- `prompts/NEXT_ITERATION.md`：每轮续接一句话/一段话可复制指令。
- `docs/PRODUCT_REQUIREMENTS.md`：PRD、场景、功能边界。
- `docs/DATA_SOURCE_MATRIX.md`：每个数据源的当前方式、实际进度和未来授权方向。
- `docs/COLLECTION_SPEC.md`：采集流程、阻断、安全与解析器开发规格。
- `docs/ARCHITECTURE.md` / `docs/DATA_MODEL.md`：组件及数据库信息流。
- `docs/ROADMAP.md` / `docs/ACCEPTANCE.md`：任务池和验收条件。
- `docs/PROJECT_STATUS.md` / `docs/GOAL_STATE.json` / `docs/DECISIONS.md`：跨会话交接的真实状态、机器可读目标与决策记录。
- `docs/NAS_DEPLOYMENT.md`：绿联Docker部署/旧数据库升级。
- `docs/API.md`：全部API与采集调用说明。
- `app/collectors/`：贝壳/安居客解析入口、通用保守解析基线、保守线上HTTP客户端；入口尚未用获准真实页面校准。
- `sql/001_init.sql`–`sql/014_collection_detail_queue.sql`：基础表及幂等迁移；006–009保存分页发现、挂牌观察/扫轮和人工核验，010–011记录解析阶段并维护追加式健康率账本，012规范化长期发现去重ID，013保存DTK历史补采游标，014持久化待抓详情URL。
- `fixtures/`：虚构网页测试样本；`examples/`：原V0.1模拟请求数据。
- `data/raw-pages/`：HTML证据（运行后为实际采样数据；被Git忽略）。

## 8. 合规与数据真实性

平台规则、视频版权、个人信息、网站内容二次传播和商业使用必须单独审核。采集成本、识别准确率、每条房源更新频率需要真实小规模试点数据评估。单纯爬到了网页不等于有真实房源、成交价或可公开商业使用的数据集。

贝壳官方协议：https://www.ke.com/zhuanti/serviceProtocol 。详细风险及备选数据路径见 `docs/DATA_SOURCE_MATRIX.md`。
