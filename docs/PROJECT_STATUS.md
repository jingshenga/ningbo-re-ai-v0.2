## 2026-11-20 CreatorHub Sidecar 集成（PR #37）
- PR #37 基于 main `646e83c` 添加 CreatorHub SQLite 只读桥接、sidecar Compose、离线测试和部署说明；对齐主项目服务/网络、修复 ingest URL 拼接，并要求显式提供 API key。Sidecar 专项 16 passed；完整本地快速套件 2141 passed、2 skipped；PR CI与合并后main CI均通过。Squash merge提交 `4585a15`。
- 本记录仅覆盖代码集成和自动化验证；实际运行态验收属于单独的后续环节。

## 2026-11-20 Issue #30 社交线索人工采集合并（PR #35）
- ZCode补丁 `nbre-social-ingest-2d91c74-d468bc5.patch`（SHA-256 `5d1d1fb2e582893353974d6ba151ab531aa6f235d8d107cef84c2b8610af6431`）基于main `31b3d66`审查并经PR #35 Squash Merge，main提交 `1454c98`。
- 新增单条人工采集API、社交线索表015、Tampermonkey脚本及文档。持久层按参数绑定写入，`raw_sha256`冲突使用DO NOTHING；重复内容返回原记录，不覆盖原始证据或状态。线索不进入正式挂牌、成交价或价格历史。
- 同步新库Compose挂载、请求体限制、未知字段拒绝，以及脚本目标仅允许loopback/私网HTTP(S)。已有数据库卷不会自动执行015，须独立备份并按迁移流程应用；本轮没有NAS或生产数据库操作。
- PR CI：Quick **2123 passed、4 skipped、27 subtests passed**；隔离PostgreSQL 17 **35 passed**；Admin Browser UAT workflow通过并上传24项验收产物。本机完整快速套件 **2125 passed、2 skipped、27 subtests passed**；本机Docker不可用，PG17验收由GitHub Actions完成。
- Mimosa不在Codex执行环境中；使用普通git push，没有跳过本地钩子。未验证ZCode本机扫描器状态；未做NAS迁移或真实平台页面采集。

## 2026-11-13 Issue #4 migration preflight synchronized with main
- PR #10 synchronized with latest main `054786c`; P2 schema-signature review was resolved. After synchronization, GitHub Actions passed: quick suite 1962 passed, 0 skipped, 27 subtests; PostgreSQL 17 integration 31 passed, 0 skipped.
- Isolated synthetic rehearsal applied migrations 001–014, reran 006–014, checked selected legacy business fields and transaction rollback. Migration 012 sweep-only ID risk is tracked independently in Issue #13.
- No NAS production database, volume, Compose file, or container was modified. Real production schema and V0.1 backup remain unverified.

## 2026-11-13 P0-03/P0-06 双代理PR集成与真实联调边界
- ZCode Bundle的解析器修复经PR #8合并：`generic-labelled-v0.2.168`，排除评估/租金/原总价及单位周期报价；新增独立“每月还贷/每年物业费”上下文回归，保证正常300万挂牌价不会被误排。Issue #1完成关闭。
- ZCode DTK worker状态契约及回归经PR #7合并：`blocked_config`、`guest_fallback→partial`、失败计数/后续轮询及首次基线单页行为经离线测试验证。已纠正文档：DTK收到403/429当前记普通`failed`，没有专用blocked状态/退避；仍待后续安全改造和获准账号实测，Issue #3继续开放。
- 在包含上述两项功能的PR #7合并预检中，GitHub Actions快速测试 **1963 passed**、隔离PostgreSQL 17集成 **31 passed**，均成功，审查线程已解决。合并后的main功能基线为`a26ad49`。无NAS部署、数据库迁移、真实网站采集或24小时监控验收。
- 后续：Codex执行Issue #4隔离PG17迁移预演、Issue #5管理后台；Issue #9处理Mimosa Push扫描超时和SQL参数化误报（不能关闭安全门）。P0-02真实合法页面样本与P0-06真实联调仍由外部条件阻塞。

## 2026-11-12 P0-02直接采集请求的许可核验
- 用户要求直接采集贝壳及安居客挂牌样本。重新读取贝壳官方服务协议，页面标示2026-11-11更新、2026-11-12生效；第七条限制未经书面许可读取/复制及机器人或蜘蛛获取内容，获许可后仍须遵守许可范围和Robots。依据项目当天NAS实读Robots记录，贝壳示例详情路径被禁止。
- 安居客官方消费者协议当前正文/版本仍无法确认，且缺少本项目书面许可；其Robots允许示例路径不能代替内容使用授权。
- 未请求任一房源页面、未采集数据、未绕过访问限制；两来源在线开关保持OFF。P0-02从`todo`改为`blocked`，解除条件是取得覆盖目标域名/路径、字段、频率、用途、展示/分发和留存的书面许可，并复核目标Robots。
- 无代码、迁移、配置、NAS或生产环境变化。下一步：等待平台许可或用户提供获准样本；随后按P0-02清单逐站收集并人工标注，才可进行P0-03真实准确率评估。

## 2026-11-12 P0-03在隔离PostgreSQL 17验证不等式挂牌价证据留存
- 新增数据库集成回归覆盖`挂牌价：>=200万`与`总价：≤200万`。API候选保持pending、`asking_price_wan`为空且未就绪；数据库JSONB持久化数值候选、完整quote、`is_non_exact=true`及`non_exact_asking_price`警告，原始HTML SHA-256及gzip字节逐项核对。
- NAS隔离PostgreSQL 17完整数据库集成文件 **31 passed**；当前本机全量离线pytest **1850 passed、30 skipped、27 subtests passed**。30项本机PostgreSQL用例未连接本机，均已在NAS隔离PG17环境实跑通过。保留1条既有Starlette/httpx弃用警告。
- NAS运行使用仅internal网络、512 MiB数据目录tmpfs、无宿主端口及无持久卷；源码和测试依赖只读挂载。测试容器、数据库容器、网络、NAS暂存文件均已清理。复核时生产DB healthy、API/Worker运行；未修改生产schema、数据、卷、Compose或容器。
- 验证源码快照：`ningbo-re-ai-v0.2-dev-2026-11-12-pg17-price-inequality-evidence.zip`（129文件，SHA-256 `6391dcbfcb961f0ec6a58cd1fc8c79c50b1f269dc8996feacb6d191d8ba196c7`）。真实页面准确率仍待许可样本及人工标注。

## 2026-11-12 P0-03将挂牌价不等式符号作为非精确报价
- 回归复现`挂牌价：>=200万`、`总价：≤200万`等写法没有挂牌价数值证据及`non_exact_asking_price`警告。解析器现识别`>=`、`<=`、`>`、`<`及常见Unicode不等式符号；报价金额保留为候选证据，`asking_price_wan`留空并待人工核验。评估器与提交API回归同步验证。解析器版本升至`generic-labelled-v0.2.166`。
- 两来源解析、评估和API回归修复后通过；相关五个测试文件 **1495 passed**；全量离线pytest **1850 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有Starlette/httpx弃用警告。
- Python 3.12 compileall、目标JSON、文档尾随空白与diff检查通过。仅合成HTML/离线验证；未访问网站、NAS或生产数据库，无迁移/部署；真实页面准确率未验证。

## 2026-11-12 P0-03将面积不等式符号作为非精确边界
- 合成反例复现`100㎡+`/`100㎡＋`和`≥100㎡`、`<=100㎡`、`>100㎡`等不等式会被误解析为精确面积或丢失候选。解析器现识别ASCII/全角加号、常见大小于/大于符号，保留数字候选和完整quote，面积留空并添加`non_exact_area_sqm`进入待审；评估器的限定证据识别同步这些符号。解析器升至`generic-labelled-v0.2.165`。
- 新增两来源解析器、评估和提交API回归；符号边界回归先失败后通过。相关五个测试文件 **1477 passed**；全量离线pytest **1832 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有Starlette/httpx弃用警告。
- Python 3.12 compileall、目标JSON、文档尾随空白和diff检查通过。只用合成HTML与离线测试，未访问网站、NAS或生产数据库，无迁移/部署；真实页面准确率未验证。

## 2026-11-12 P0-03保留位于面积字段名前的近似限定证据
- 新增两来源回归复现“约建筑面积：100㎡”“估算建面：100㎡”会被写成精确面积，以及“参考建筑面积：100㎡-120㎡”虽识别范围却漏掉非精确告警。现在面积字段名前的近似/估算/参考限定词也纳入完整匹配、候选证据与`is_non_exact`；面积留空、添加`non_exact_area_sqm`并保持待审。解析器版本升至`generic-labelled-v0.2.164`。
- 修复前新增6项均失败，修复后通过；解析器/评估器/样本校验/提交API相关测试 **1453 passed**；全量离线pytest **1808 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有Starlette/httpx弃用警告。
- Python 3.12 compileall、目标JSON、文档空白和diff检查通过。仅合成页面/离线测试；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率未验证。

## 2026-11-12 P0-03核验限定范围与其他精确值共存
- 新增混合样本回归：同页同时包含带限定词的面积/挂牌价区间，以及另一条精确面积/挂牌价单值。评估器分别校验范围非精确标记、专用告警和限定quote，同时对账所有精确/非精确候选集合，四个场景均通过。
- 定向 **1 passed**；全量离线pytest **1788 passed、28 skipped、27 subtests passed**。28项本机PostgreSQL集成未连接，保留1条既有Starlette/httpx弃用警告。仅增加测试，解析器保持`generic-labelled-v0.2.163`。
- 使用合成HTML和本地清单；未访问网站、NAS或生产数据库，无迁移/部署。真实页面准确率未验证。

## 2026-11-12 P0-03闭环近似面积区间的API证据留存
- 为`POST /api/collection/pages`新增两来源面积范围往返回归，覆盖“建筑面积：100㎡-120㎡左右”“建筑面积约：100㎡-120㎡”“建筑面积估算：100㎡-120㎡”。候选保持pending且未就绪，`area_sqm`为空；完整范围候选、完整quote、`is_non_exact=true`及`multiple_area_mentions`/`non_exact_area_sqm`在响应和JSONB写入中一致，gzip原始HTML逐字节保持。
- API定向 **6 passed**；全量离线pytest **1787 passed、28 skipped、27 subtests passed**。28项本机PostgreSQL集成未连接，保留1条既有Starlette/httpx弃用警告。仅测试变更，解析器保持`generic-labelled-v0.2.163`。
- 使用合成HTML和Mock数据库；未访问网站、NAS或生产数据库，无迁移/部署。真实页面准确率未验证。
- 开发包：`ningbo-re-ai-v0.2-dev-2026-11-12-area-range-api-evidence.zip`（129个项目文件）。

## 2026-11-12 P0-03验证限定词后冒号的近似面积/挂牌价区间端到端证据
- 扩展两来源解析器回归，覆盖`建筑面积约：100㎡-120㎡`、`建筑面积估算：100㎡-120㎡`、`挂牌价约：300-320万`及`总价估算：300万-320万`，确认完整区间候选、完整quote、非精确标记和对应告警均保留。校验器/评估器正向场景同时覆盖冒号式限定区间；`POST /api/collection/pages`新增挂牌价区间例，核对响应、JSONB证据和gzip原始页面一致。
- 限定词冒号的解析器/评估器回归 **26 passed**；API证据回归 **6 passed**；全量离线pytest **1781 passed、28 skipped、27 subtests passed**。28项本机PostgreSQL集成未连接，保留1条既有Starlette/httpx弃用警告。解析器版本`generic-labelled-v0.2.163`。
- 仅使用合成HTML和Mock API；未访问网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍未验证。
- 开发包：`ningbo-re-ai-v0.2-dev-2026-11-12-qualified-range-colon-roundtrip.zip`（129个项目文件）。

## 2026-11-12 P0-03识别限定词后置冒号的近似面积与挂牌价
- 两来源回归复现`建筑面积约：100㎡`、`建筑面积估算：100㎡`、`挂牌价约：200万`、`总价估算：200万`漏掉候选证据/专用告警；其中总价估算漏标时还会被写成精确挂牌价。现允许近似词后跟冒号，并确保挂牌价非精确检测同步识别该限定形式。
- 修复前两来源8项解析回归均失败，修复后通过；解析器专项 **827 passed**，API候选响应/JSONB证据/ gzip原始HTML定向 **140 passed**，全量离线pytest **1767 passed、28 skipped、27 subtests passed**。28项本机PostgreSQL集成未连接，保留1条既有Starlette/httpx弃用警告。解析器升级为`generic-labelled-v0.2.163`。
- 仅合成HTML和Mock API验证；未访问网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍未验证。
- 开发包：`ningbo-re-ai-v0.2-dev-2026-11-12-qualified-colon-v0163.zip`（129个项目文件）。

## 2026-11-12 P0-03加固近似/上下限区间评估
- 覆核样本标签后发现同类缺口也存在于面积：解析器会将带限定词范围置空、保留证据并发出`non_exact_area_sqm`，但`area_ranges`场景不强制校验。新增可选`non_exact_area_ranges`标签；它与前一轮的`non_exact_price_ranges`一致，由人工标注独立启用严格门禁。精确`area_ranges`/`price_ranges`维持原有行为。
- 两类显式标签均要求挂牌/面积字段留空、范围候选匹配且证据未截断；相应范围mention逐条验证`is_non_exact=true`、专用告警及同时包含候选值和限定词的quote。面积覆盖前置约/估算与后置左右/以上；三项信号同时丢失的负向回归也失败。校验器+评估器 **393 passed**；全量离线pytest **1751 passed、28 skipped、27 subtests passed**。28项本机PostgreSQL集成未连接，保留1条既有Starlette/httpx弃用警告。
- 仅离线合成HTML/模拟解析结果验证，真实页面准确率未验证；未访问网站、NAS或生产数据库，无迁移/部署。解析器版本保持`generic-labelled-v0.2.162`。
- 开发包：`ningbo-re-ai-v0.2-dev-2026-11-12-non-exact-range-eval.zip`（129个项目文件）。

## 2026-11-12 P0-03为限定价区间增加独立人工标注场景
- 上轮评估器仍有盲点：当限定区间的`is_non_exact`、告警和quote限定词同时丢失时，`price_ranges`无法从解析结果判断原页面是否为近似报价。新增可选清单标签`non_exact_price_ranges`，由人工标注独立启用门禁；要求范围字段留空，候选至少含一个范围，解析候选未截断且对应区间证据全部带非精确标记、告警及完整候选值/限定词quote。普通精确`price_ranges`保持兼容。
- 校验器/评估器与正向样本、标记/告警/引用单项损坏和三项同时损坏回归已同步；相关两个测试文件 **384 passed**，全量离线pytest **1742 passed、28 skipped、27 subtests passed**。28项本机PostgreSQL集成未连接，保留1条既有Starlette/httpx弃用警告。
- 仅离线合成HTML/模拟解析结果验证；无真实页面准确率结论，未访问网站、NAS或生产数据库，无迁移/部署。解析器版本保持`generic-labelled-v0.2.162`。
- 开发包：`ningbo-re-ai-v0.2-dev-2026-11-12-explicit-qualified-range-scenario.zip`（129个项目文件）。

## 2026-11-12 P0-03评估限定挂牌价区间的非精确证据
- 负向回归复现：`price_ranges`只核对候选集合、字段留空和`multiple_price_mentions`，限定区间即使丢失`is_non_exact`、`non_exact_asking_price`或quote限定词仍会误通过。现对检测到非精确标记/限定词的区间要求三项证据契约齐全；普通精确区间路径保持不变。
- 覆盖`300-320万左右`、`300万-320万以上`正常样本，以及标记、告警、quote三类损坏注入。旧逻辑下3项负向用例先失败，修复后评估器专项 **277 passed**；全量离线pytest **1740 passed、28 skipped、27 subtests passed**。28项PostgreSQL测试未连接本机，另保留1条既有Starlette/httpx弃用警告。
- 仅离线合成HTML和模拟解析结果验证；未访问网站、NAS或生产数据库，无迁移/部署。解析器版本保持`generic-labelled-v0.2.162`，真实页面准确率仍未验证。

- 安全开发包由`scripts/package_dev.py`构建，包含129个文件；交付包：`ningbo-re-ai-v0.2-dev-2026-11-12-range-evaluation-evidence.zip`。
## 2026-11-12 P0-03端到端核验限定挂牌价区间证据
- 补齐`POST /api/collection/pages`对近似挂牌价区间的两来源回归，覆盖`300-320万左右`与`300万-320万以上`。API候选保持pending、挂牌价为空、同时携带`multiple_price_mentions`和`non_exact_asking_price`；完整区间/限定词quote和`is_non_exact=true`均透传到响应及JSONB写入参数，原始HTML gzip逐字节保留。
- API端到端定向 **4 passed**；全量离线pytest **1735 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有Starlette/httpx弃用警告。解析器保持`generic-labelled-v0.2.162`。
- 仅Mock数据库/合成HTML验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率未验证。

## 2026-11-12 P0-03评估器拒绝缺少限定词的非精确证据
- 负向回归模拟解析证据`is_non_exact=true`但`quote`截掉“左右”等限定词，旧评估器仍会通过非精确价场景。现在面积和挂牌价的非精确评估都要求每条证据引用同时包含候选数值及限定表达；缺少限定词或数值都判失败。
- 相关评估器非精确场景 **43 passed**；全量离线pytest **1731 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有Starlette/httpx弃用警告。解析器保持`generic-labelled-v0.2.162`。
- Python 3.12 compileall、GOAL_STATE JSON、文档空白检查和129文件开发包校验通过。仅合成HTML和模拟解析结果验证；未访问来源网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-03处理挂牌价连接词并保留完整限定证据
- 失败回归复现“挂牌价为约200万”“挂牌价约为200万”“挂牌价在200万左右”此前没有挂牌价证据；精确写法“挂牌价为200万”也漏解析。现支持“为/在”连接及限定词前后位置；精确“为”不改变精确语义，“在”作为非精确限定留空待审。
- 近似/上下限报价单值和区间证据的`quote`现在包含完整后缀限定词（如“200万元左右”“300-320万以上”）；限定区间也追加`non_exact_asking_price`。解析器升至`generic-labelled-v0.2.162`。
- 相关解析器/API/评估器价格契约回归 **327 passed**；全量离线pytest **1729 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有Starlette/httpx弃用警告。Python 3.12 compileall、GOAL_STATE JSON、文档空白检查和129文件开发包校验通过。
- 仅合成HTML/Mock验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准页面和人工标签。

## 2026-11-12 P0-03保留面积“在”限定证据并识别精确连接词
- 失败回归复现“建筑面积在100㎡左右”只报缺字段而不保留候选；现将“在”按非精确面积限定处理。新增“建筑面积为100㎡”精确值回归；标签可选“为”连接词后仍正确提取，不置空、不告警。
- 解析器升至`generic-labelled-v0.2.160`。相关解析器/API/评估器回归 **119 passed**；全量离线pytest **1705 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、文档空白检查和129文件开发包校验通过。仅合成HTML/Mock验证；未访问来源网站、NAS或生产数据库，无迁移/部署；真实页面准确率仍未验证。

## 2026-11-12 P0-03识别估算/参考面积限定
- 失败回归复现“建筑面积：参考/估算/预估100㎡”缺少候选证据和`non_exact_area_sqm`告警，以及“100㎡参考/估算/预估”会被作为精确面积。现在两种位置均按非精确面积处理；另覆盖“估计”。字段留空，保留完整引用和数值候选，告警且禁止审核就绪。
- 解析器升至`generic-labelled-v0.2.159`。两来源解析器/API/评估器非精确面积回归 **111 passed**；全量离线pytest **1697 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、文档空白检查和129文件开发包校验通过。只使用合成HTML/Mock；未访问来源网站、NAS或生产数据库，无迁移/部署，真实页面准确率未验证。

## 2026-11-12 P0-03确认近似/上下限面积留空待审
- 用户确认“100㎡左右”“100㎡以上”等近似或边界面积不得写成精确面积：字段留空，保留候选证据、告警并待人工审核。现有解析器/API和评估器已符合此口径，本轮无需改动应用逻辑。
- 定向解析器/API/样本校验/评估器用例 **69 passed**；全量离线pytest **1649 passed、28 skipped、27 subtests passed**。28项本机PostgreSQL集成测试未连接；保留1条既有Starlette/httpx弃用警告。
- 仅验证现有离线实现；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站获准页面和人工标签。

## 2026-11-12 P0-03评估器阻止核心字段缺失却审核就绪
- 失败回归复现：评估器仅核对“字段留空+歧义警告”，即使来源ID/小区/面积/挂牌价等核心必需字段冲突或缺失、解析器却给出`ready_for_review=true`，仍会把样本判为通过。
- 对会使核心必需字段无值的场景，评估器现同时要求`ready_for_review=false`：来源ID冲突/未知、社区/面积/价格冲突及范围、多值价格、核心字段缺失和没有挂牌价的口播价格。可选字段（户型/区域/楼层/装修）歧义仍只按其字段为空、警告和证据集合核验，不强制该候选整体未就绪。
- 负向回归在旧逻辑下7项先失败；扩展来源ID冲突和口播价格后共9项通过。评估器文件 **248 passed**；解析器/API/样本集/评估器相关四文件 **1259 passed**；全量离线pytest **1649 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有Starlette/httpx弃用警告。
- 仅离线模拟解析结果和合成清单，无数据库/运行配置变更；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本与人工标签。 Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及129文件开发包校验通过；包为`../ningbo-re-ai-v0.2-dev-2026-11-12-required-field-review-gate.zip`。

## 2026-11-12 P0-03评估器拒绝非精确值审核就绪
- 新增负向回归发现：模拟解析器把`ready_for_review`错误设为true时，旧评估器仍会将`non_exact_areas`和`non_exact_prices`样本判为通过，只检查了空字段与告警。
- 两类非精确场景现要求解析结果明确处于待人工审核状态；样本说明同步该验收条件。异常模拟先通过旧逻辑、修复后均判失败。
- 评估器测试文件 **239 passed**；全量离线pytest **1640 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有Starlette/httpx弃用警告。解析器版本仍为`generic-labelled-v0.2.158`。
- 本轮只改离线评估器、回归和说明，无数据库/运行配置变化；未访问网站、NAS或生产数据库，无迁移/部署。真实样本准确率仍未验证。

## 2026-11-12 P0-03补齐面积下限“起”的标点边界
- 反向回归发现仅在句末/空白/部分标点后识别“起”，导致`100㎡起、采光好`和`100㎡起（含赠送面积）`被当作精确面积；两来源修复前均失败。
- 现将顿号及中英文括号纳入“起”的合法结束边界，同时保留“100㎡起居室”作为精确面积、“100㎡起步”作为下限的区分。面积仍留空、保留证据、发出警告并待人工审核。
- 解析器升至`generic-labelled-v0.2.158`。解析器/API/样本集/评估器四个相关测试文件 **1248 passed**，解析器文件 **783 passed**；全量离线pytest **1638 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`和129文件开发包校验通过。仅使用合成HTML/模拟API；未访问来源网站、NAS或生产数据库，无迁移/部署。真实准确率未验证。

## 2026-11-12 P0-03避免“起居室”误判为面积下限
- 新增贝壳/安居客反向回归，先复现精确“建筑面积：100㎡起居室宽敞”被当作非精确值；原因是限定词`起`没有结束边界。
- `起`现在要求句末、空白或标点等边界；“起步”优先完整匹配，仍留空待审且证据不截短。原有近似/上下限词及完整范围行为保持。
- 修复后解析器/API/样本集/评估器四个相关测试文件 **1244 passed**，解析器文件 **779 passed**；全量离线pytest **1634 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`与129文件开发包校验通过。仅使用合成HTML和模拟API；未访问来源网站、NAS或生产数据库，无迁移/部署。真实准确率未验证。

## 2026-11-12 P0-03补齐面积上下限同义表达
- 回归复现“面积大于/超过/高于/多于100㎡”“小于/低于/不满100㎡”“100㎡封顶/起步”未触发非精确告警；另发现“100㎡起步”证据quote被短匹配截为“100㎡起”。
- 面积限定词现覆盖这些前置/后置表达，并优先完整匹配“起步”。字段保持为空，保留完整候选证据，发出`non_exact_area_sqm`并进入人工审核；API暂存和评估器同样覆盖。
- 解析器升至`generic-labelled-v0.2.156`。解析器/API/样本集/评估器四个相关测试文件 **1242 passed**；全量离线pytest **1632 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有Starlette/httpx弃用警告。
- 解析器文件 **777 passed**；Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`通过。129文件开发包通过包内SHA清单及ZIP完整性校验。仅合成HTML/模拟API验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率未验证，在线采集保持关闭。

## 2026-11-12 P0-03建筑面积下限“起”留空待审
- 将“建筑面积：100㎡起”纳入非精确面积口径。两来源解析器回归先失败，修复后建筑面积字段留空、保留候选与完整证据、添加`non_exact_area_sqm`并阻止审核就绪；API暂存和评估器也覆盖该表达。
- 解析器版本升至`generic-labelled-v0.2.155`。解析器/API/样本集/评估器相关四个测试文件 **1212 passed**；全量离线pytest **1602 passed、28 skipped、27 subtests passed**。28项本机PostgreSQL集成未连接，既有Starlette/httpx弃用警告1条。
- 本轮无数据库/运行配置变化；未访问来源网站、NAS或生产数据库，无迁移或部署。全部验证使用合成页面/模拟API；真实页面准确率仍未验证，在线采集保持关闭。

## 2026-11-12 P0-03保留“平方”完整字段证据
- 失败回归发现`建筑面积：100平方`数值虽正确但证据quote被截成`100平`；`120平方-130平方`还会将不完整单值和完整范围同时计入，导致范围待审行为异常。
- 面积单位正则现避免把`平方/平方米/平米`回溯匹配成较短的`平`前缀；单值证据保留完整单位，范围只保留完整范围。解析器版本升至`generic-labelled-v0.2.153`。
- `平方`证据及面积范围定向 **9 passed**；解析器测试文件 **759 passed**，全量离线pytest **1562 passed、28 skipped、27 subtests passed**。28项数据库集成未连接本机PostgreSQL；隔离PG17最近一次完整集成29 passed。compileall、JSON、diff和129文件开发包校验通过。仅合成HTML验证，真实准确率未验证。

## 2026-11-12 P0-03识别“建筑面积：100平”并保留面积范围
- 新增两来源回归后先复现失败：`建筑面积：100平`此前漏提面积。面积单位现包含`平`；同步扩展现有范围检测，`120平-130平`和`120-130平`仍完整留证、置空并待审，不从范围抽取端点。解析器版本升至`generic-labelled-v0.2.152`。
- 面积单值及范围定向 **6 passed**（含修复前两来源失败复现、修复后单值与范围边界）；全量离线pytest **1559 passed、28 skipped、27 subtests passed**。28项数据库集成未连接本机PostgreSQL；最近一次隔离PG17完整数据库集成29 passed。Python 3.12编译、GOAL_STATE JSON及diff检查通过。仅合成HTML验证，无真实页面准确率结论，保留1条既有弃用警告。

## 2026-11-12 P0-07生产schema迁移边界只读核验
- 按NAS连接技能尝试局域网后，使用此前已获准的`notedock-nas`确认`DXP4800/sheng`；生产API/Worker运行、PostgreSQL容器healthy。查询范围仅为PostgreSQL `information_schema`，没有读取业务行、凭据或环境变量值。
- 关键基础表和条件单字段可见，`saved_searches`包含005新增筛选列及其约束。生产库未发现迁移006–014的核心对象：分页发现状态、挂牌观察/复核记录、解析尝试账本、暂存去重ID、详情队列；发现扫轮与历史回填游标列也缺失，解析健康计数列不存在。此结果更新了此前只核验到006–011的边界，未逐项证明001–005所有对象完整。
- P0-07保持`in_progress`。生产schema不具备工作区当前API/Worker所需迁移对象，不能只部署API；本轮未创建备份、运行迁移、修改Compose/容器/卷或部署。生产升级仍须新鲜备份、恢复验证、隔离测试和部署评估。
- P0-03：用户再次确认面积与挂牌价下限为大于0。工作区解析器、模型和样本校验器已一致允许正数并拒绝零值，本轮无需重复改代码。
- `PYTHONPATH=. /private/tmp/ningbo-re-ai-venv312/bin/pytest -q`：**1555 passed、28 skipped、27 subtests passed**；28项本机数据库集成测试需隔离PostgreSQL，不能由本次离线运行覆盖。`compileall`、目标JSON解析和`git diff --check`通过；保留1条既有Starlette/httpx弃用警告。

## 2026-11-12 P0-03核验限定价证据穿过API暂存
- 扩展`POST /api/collection/pages`回归，确认近似价场景中每条挂牌价mention的`is_non_exact`既保留于待审响应，也保留在数据库写入参数的`extracted_fields` JSONB对象中。
- `tests/test_collection_api.py` **108 passed**；全量pytest **1554 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未连接，保留1条既有Starlette/httpx弃用警告。
- 仅mock数据库与合成HTML验证；未访问网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-03补齐价格区间逐条限定标记
- 失败回归发现：挂牌价证据契约已新增`is_non_exact`，但合并区间扫描路径漏写该标记，导致区间mention缺字段。
- 单值与区间证据现一致携带`is_non_exact`；普通范围为false，带近似/上下限限定的范围为true。同分根冲突证据扫描也保留标记，解析器版本升至`generic-labelled-v0.2.151`。
- 区间、限定区间和同分根冲突定向 **19 passed**；全量pytest **1554 passed、27 skipped、27 subtests passed**，27项数据库集成未连接。仅合成HTML验证，未访问网站、NAS或生产数据库。

## 2026-11-12 P0-03将非精确限定关联到逐条价格证据
- 失败回归复现：同页“挂牌价约200万 总价200万”时，解析器将字段留空并发出非精确报价警告，但评估器只比较去重数值集合，误将该样本判为通过。
- 挂牌价证据mention现带`is_non_exact`，评估器要求场景中的每条报价证据都带限定词；页面同时含精确报价、缺少标记或证据截断都会失败。解析器升至`generic-labelled-v0.2.150`。
- 误通过回归修复前失败、修复后通过；限定价相关定向 **54 passed**，全量离线pytest **1554 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未连接，保留1条既有Starlette/httpx弃用警告。
- 仅合成HTML/清单验证；无真实页面准确率结论，无网站、NAS或生产数据库访问、迁移或部署。

## 2026-11-12 P0-03 将非精确挂牌价纳入人工样本评估
- 新增可选样本场景`non_exact_prices`：挂牌价必须留空，`price_candidates_wan`恰好一个正数；与冲突价及范围场景互斥。评估器逐样本检查`non_exact_asking_price`警告、完整证据及候选集合与人工标签一致，精确挂牌价或缺警告均判失败。
- 定向样本校验/评估 **323 passed**（含证据截断边界回归1 passed）；全量离线pytest **1553 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未连接；保留1条既有Starlette/httpx弃用警告。未访问网站、NAS或生产数据库，无部署。
- 仅使用虚构HTML/清单测试。P0-02/P0-03真实获准页面及人工标签仍缺，不能据此报告真实准确率。

## 2026-11-12 P0-03识别数字前的近似/上下限挂牌价
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-12-leading-price-qualifiers.zip`；项目打包器、包内清单哈希及ZIP完整性检查通过。
- 新回归复现“挂牌价约200万”“总价不超过200万”等前置限定词此前未进入价格命中：字段虽为空，但缺少`non_exact_asking_price`且没有数值证据。现于挂牌标签后识别金额前限定词；候选评分排除该金额，最终字段留空并保留命中证据。价格范围也接受前置限定词并保留完整范围，不提升端点。
- 首次全量运行还发现新增警告检查多扫描整段价格文本一次；现把判断合并进既有证据扫描，重复价格扫描次数维持原契约。两来源前置限定词/范围解析专项 **50 passed**，API前后置限定词与摘要专项 **98 passed**，评估器前后置限定词专项 **96 passed**；解析器测试文件 **732 passed**。
- 全量离线pytest **1539 passed、27 skipped、27 subtests passed**；27项PostgreSQL集成未连接。解析器版本`generic-labelled-v0.2.149`。仅合成HTML/mock离线验证；未访问网站、NAS或生产数据库，无迁移/部署。真实准确率仍待每站20份获准页面和人工标签。

## 2026-11-12 P0-03 API保留折叠摘要前的精确挂牌价
- 新增两来源`POST /api/collection/pages`回归：精确总价后紧邻折叠`<summary>起始摘要</summary>`时，API仍返回精确挂牌价及其证据，不产生`non_exact_asking_price`或`multiple_price_mentions`，原始HTML gzip内容保持一致。
- 定向 **2 passed**；全量离线pytest **1396 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未连接；保留1条既有Starlette/httpx弃用警告。
- 仅合成HTML/mock离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标签。

## 2026-11-12 P0-07 NAS生产版本与健康只读复核
- 按NAS连接技能尝试LAN：`nas-lan`超时；Tailscale CLI无法载入偏好且本机未安装Tailscale App。使用此前获准的`notedock-nas`后确认宿主为`DXP4800/sheng`，只执行只读检查。
- UGREEN Compose项目`ningbo-re-ai`显示运行3个容器：API/Worker运行、PostgreSQL healthy；`http://127.0.0.1:8788/healthz`返回`ok=true`及schema v0.2。容器登记的Compose路径为`/volume3/docker/ningbo-re-ai/docker-compose.yml`，当前容器仅将SQL 001–004作为初始化脚本挂载。
- NAS API容器解析器为`generic-labelled-v0.2.5`，与工作区`generic-labelled-v0.2.148`不一致；parser、collection_service、main、worker四个源码SHA-256均与工作区不一致。`/api/collection/health`未携认证请求返回401；本轮未读取凭据，也未验证认证后的指标正文。未查询生产业务行或迁移目录表，因此不能据此断言生产库迁移状态。
- P0-07仍`in_progress`：运行态健康已确认，但健康指标契约及工作区新代码仍未在生产验证/部署。全程只读，无配置、容器、卷、数据库或代码写入。

## 2026-11-12 P0-03端到端验证限定挂牌价不进入候选精确总价
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-12-price-e2e-guard.zip`；打包器与独立`sha256sum -c MANIFEST.sha256`、`unzip -t`均通过。
- 页面提交API此前只对“左右”覆盖单一近似价；现将两来源端到端回归扩展为25种报价限定后缀，检查API候选保持pending、asking_price_wan为空、保留`non_exact_asking_price`及原始HTML压缩证据逐字节一致。
- API定向 **50 passed**；完整离线pytest **1394 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成因未配置本机隔离数据库跳过；保留1条既有Starlette/httpx弃用警告。
- 仅合成HTML/mock验证；无来源网站、NAS或生产数据库访问，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标签。

## 2026-11-12 P0-03扩展挂牌价语义评估门禁
- 评估器回归原先只覆盖“200万左右”，未覆盖其余已支持的近似/上下限后缀，也没有锁定折叠摘要“起始”不得清空精确价格。现新增两来源评估矩阵，覆盖约、大约、大概、左右、上下、出头、以上、以下、以内、附近、不到、不足、不超过、不高于、不低于、起、起价、起售、起售房源、起步、起步价、起始价、封顶及ASCII/全角加号，并新增折叠摘要精确总价评估回归。
- 评估器定向 **52 passed**；全量离线pytest **1346 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未连接；仅合成HTML和清单验证。
- 无来源网站、NAS或生产数据库访问，无迁移/部署。真实字段准确率仍待每站20份获准页面和人工标签。

## 2026-11-12 P0-03避免“起始摘要”误伤精确挂牌价
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-12-approx-price-summary.zip`；打包器已校验ZIP完整性及包内SHA-256清单。
- 全量回归复现精确`总价：300万`后紧邻折叠`<summary>起始...`时，之前新增的独立“起始”限定词会错误清空挂牌价。移除过宽的独立匹配，仅保留明确的“起始价”；对应限定价测试不再把单独“起始”当作报价修饰语。
- 精确挂牌价与折叠摘要回归及限定价矩阵定向 **51 passed**；全量离线pytest **1296 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成测试未连接。
- 仅合成HTML/mock离线验证；无来源网站、NAS或生产数据库访问，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标签。

## 2026-11-12 P0-03户型边界回归补齐
- 对照样本规则与API模型确认`bedrooms`允许0（开间/无独立卧室），上限20。解析器行为一致；新增贝壳/安居客两来源的0与20边界回归，验证字段证据保持且不报越界。
- 户型边界专项 **4 passed**；解析器专项 **669 passed**，评估器专项 **120 passed**，API专项 **12 passed**；全量pytest **1284 passed、27 skipped、27 subtests passed**。27项为未连接PostgreSQL集成测试。
- Python 3.12 compileall、GOAL_STATE JSON、diff检查通过。仅合成HTML/mock离线验证；未访问网站、NAS或生产数据库，无迁移/部署。
- 文件：`tests/test_collection_parser.py`、`docs/PROJECT_STATUS.md`、`docs/ROADMAP.md`、`docs/TEST_REPORT.md`、`docs/GOAL_STATE.json`、`README.md`、`CHANGELOG.md`。无运行配置或数据库变化。
- 下一步：继续P0-03离线语义边界回归；获准材料到位后完成真实样本准确率验收；取得真实V0.1备份后推进P0-01旧库升级。

## 2026-11-12 P0-03保留挂牌价近似/上下限语义
- 复现“挂牌价：200万左右/以上/以下/起”等被当作精确总价且候选就绪。对挂牌金额后接近似或上下限词的情况，解析器现将`asking_price_wan`置空并追加`non_exact_asking_price`；字段证据仍保留数值命中，独立精确总价根优先于带限定词的候选根。
- 回归覆盖两来源19种“左右/上下/以上/以下/以内/起/约/大约/大概/不超过”等后缀、精确值冲突和候选根评分。解析器版本`generic-labelled-v0.2.146`；解析器专项 **665 passed**，评估器专项 **120 passed**，API专项 **12 passed**；全量pytest **1280 passed、27 skipped、27 subtests passed**。27项为未连接PostgreSQL集成测试。
- Python 3.12 compileall、GOAL_STATE JSON、diff检查通过。仅合成HTML/mock离线验证；未访问网站、NAS或生产数据库，无迁移/部署。
- 文件：`app/collectors/parser.py`、`tests/test_collection_parser.py`、`tests/test_collection_api.py`、`tests/test_parser_evaluation.py`、`docs/API.md`、`docs/PROJECT_STATUS.md`、`docs/ROADMAP.md`、`docs/TEST_REPORT.md`、`docs/GOAL_STATE.json`、`README.md`、`CHANGELOG.md`。无配置变化。
- 下一步：继续P0-03离线边界回归；获准材料到位后完成真实样本准确率验收；取得真实V0.1备份后推进P0-01旧库升级。

## 2026-11-12 P0-03挂牌单价不能充当挂牌总价
- 离线复现贝壳/安居客“挂牌价：2万/㎡”会将单价写入`asking_price_wan`；扩展回归也覆盖`/m²`、`/平米`、`/平方米`、`/平`、`每平方米`及每面积范围值。
- 解析器在总价标签后排除单位面积后缀；同页明确总价保留，单位价格不造成第二个挂牌价冲突。解析器升至`generic-labelled-v0.2.142`。
- 单价专项 **26 passed**；全量离线pytest **1162 passed、27 skipped、27 subtests passed**。跳过项为未连接PostgreSQL的集成测试；仅合成HTML验证，未访问来源网站、NAS或生产数据库，无迁移/部署。涉及文件：`app/collectors/parser.py`、`tests/test_collection_parser.py`、`docs/API.md`、`docs/PROJECT_STATUS.md`、`docs/ROADMAP.md`、`docs/TEST_REPORT.md`、`docs/GOAL_STATE.json`、`README.md`、`CHANGELOG.md`。无配置/迁移变化，未访问网站、NAS或生产库。
- 下一步：继续P0-03离线边界回归；获准材料到位后完成每站20份真实样本与字段精确率/覆盖率验收；取得真实V0.1备份后推进P0-01旧库升级。

## 2026-11-12 P0-02统一missing_fields场景判定
- 样本校验器此前允许某行仅因`multiple_prices`而挂牌价留空时，同时标记`missing_fields`；评估器会排除该挂牌价，不认为缺失字段场景成立，造成清单校验通过但场景评估失败。现在校验器与评估器一致：此组合必须另有一个可计入missing_fields的空标签。
- 新增失败回归；样本集专项 **93 passed**，全量离线pytest **1136 passed、27 skipped、27 subtests passed**。
- 跳过为未连接PostgreSQL的集成测试。仅合成清单验证；真实获准页面和人工标注仍缺，P0-02保持todo。未访问网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-02校验样本挂牌ID来源格式
- 样本清单对无可识别ID的列表URL仅检查`source_listing_id`长度，可能接受`listing-123`或Unicode全角数字，造成不符合平台ID格式的人工真值进入评估。校验器现对普通ID和冲突候选共用来源格式：贝壳8–220位、安居客7–220位ASCII数字；`unknown_id`/`source_id_conflict`仍要求标签ID留空。
- 5项两来源回归覆盖非数字、过短数字及全角数字，旧逻辑失败，修复后通过；样本集专项 **92 passed**，全量离线pytest **1135 passed、27 skipped、27 subtests passed**。
- 27项跳过为未连接PostgreSQL的集成测试。仅合成清单验证；真实获准页面与人工标注仍缺，P0-02保持todo。未访问网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-03统一面积与挂牌价正数下限
- 对照模型、样本校验器和解析器后发现：模型及清单允许面积/挂牌价大于0，但解析器分别要求至少10㎡/1万元。用户确认统一为大于0；解析与候选根评分现使用同一正数边界，0仍拒绝。
- 新增两来源面积/挂牌价正值、零值及小数下溢回归。Decimal正数转float若下溢为`0.0`，现在留空并待审，避免违反正值约束。解析器版本`generic-labelled-v0.2.141`；解析器专项 **529 passed**，全量离线pytest **1130 passed、27 skipped、27 subtests passed**。
- 27项跳过为未连接PostgreSQL的集成测试。仅合成HTML验证，真实准确率仍待每站20份获准页面和人工标签；未访问来源网站、NAS或生产数据库，无迁移/部署。
- 下一步继续P0-03离线边界复核；获准页面到位后按人工标签评估。

## 2026-11-12 P0-03候选根评分拒绝畸形千分位
- 失败回归复现：候选根评分将`12,34㎡`/`12,34万`直接移除逗号转成有效Decimal，导致含畸形数字的后续根压过先前有效根，最终丢失有效面积或挂牌价。
- `_number_str`现在先按解析器共享数值格式校验，再做Decimal范围判断；候选根评分与字段值接受的千分位格式一致。贝壳/安居客面积、挂牌价共4项回归由失败转通过；解析器版本`generic-labelled-v0.2.140`。
- 全量离线pytest **1117 passed、27 skipped、27 subtests passed**；27项PostgreSQL集成未连接数据库。仅合成HTML验证；真实页面准确率仍待每站20份获准页面和人工标签。未访问来源网站、NAS或生产数据库，无迁移/部署。
- 下一步继续P0-03离线解析边界复核；获准页面材料到位后再按人工标注集报告精确率与覆盖率。

## 2026-11-12 P0-04安居客消费者协议入口复核
- 官方`faqId=104`本轮重定向到协议中心`/helpcenter/policy?id=44`；协议中心显示消费者/经营者协议和历史版本目录，但当前文本提取仍未返回消费者协议正文或版本标识。官方`faqId=155`新三网协议将安居客用户服务协议指向该入口。
- 只确认当前入口链路，没有确认具体适用文本；官方静态PDF仍只能作为风险条款证据。安居客无本项目书面许可，在线采集继续OFF。未访问房源页或执行采集。

## 2026-11-12 P0-03独立同分候选根冲突留空待审
- 用户确认独立候选根同分且字段互相矛盾时，冲突字段留空待审。此前首根优先会静默保留冲突值；现仅比较同分且互不嵌套的根，逐字段检测冲突，保留无冲突字段，不拼接跨根缺失字段。
- 贝壳/安居客覆盖小区、面积、挂牌价、区域、户型、楼层和装修冲突；冲突字段保留双方证据引用偏移。等值数值格式（120/120.0㎡、320/320.00万）不会误报，嵌套根不当作独立根。
- 解析器版本`generic-labelled-v0.2.140`；解析器专项 **516 passed**，全量离线pytest **1117 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未连接数据库。
- 仅合成HTML离线验证；真实准确率仍待获准页面和人工标签。未访问网站、NAS或生产数据库，无迁移/部署。

## 当前状态摘要（2026-11-12）

- 工作区解析器版本为`generic-labelled-v0.2.152`；解析器测试文件736 passed，最新全量离线pytest为1559 passed、28 skipped、27 subtests passed；本轮新增“平”建筑面积单值/范围专项6 passed。28项PostgreSQL集成测试在本机未连接数据库；当前工作区此前在隔离PostgreSQL 17.11完整运行数据库集成文件为29 passed，覆盖迁移001–014及详情队列相关数据库行为，但这不代表工作区已部署到生产。
- 挂牌价限定词已覆盖近似价、上下限、单位面积价和价格范围；“起始价”按非精确报价处理，折叠摘要中的独立“起始”不会清空紧邻的精确价格。同页嵌套报价及独立同分根的冲突字段按用户确认留空待审。面积、挂牌价下限均为大于0；跨平台面积差以较小面积作分母，挂牌价差以低价作分母。
- P0-01仍缺真实V0.1数据库备份；P0-02/P0-03仍缺每站20份获准页面及人工标签，真实解析准确率未验证。P0-04的许可证据仍不足，P0-06等待获准DTK账号联调；P0-07生产健康率正文及工作区代码未部署，/api/collection/health认证后内容未验证；P0-09仍需真实来源验收。所有网站在线采集开关继续关闭。
- 最近开发包`../ningbo-re-ai-v0.2-dev-2026-11-12-qualified-price-range-api.zip`通过项目打包器的ZIP完整性和包内SHA-256清单校验。当前迭代只做离线代码、测试与文档更新；没有访问网站、NAS或生产数据库，也没有迁移或部署。
## 2026-11-12 P0-03阻止“挂牌售价”限定价后缀绕过
- 对`售价`标签增加“不能从`挂牌`后缀起始”的边界。失败回归证明`折后挂牌售价：300万`此前会从“售价”子串匹配并污染真实挂牌价；现在完整`挂牌售价`作为一个标签处理，限定语仍被排除。
- 将“售价/挂牌售价”加入全部非挂牌前缀与分隔符组合回归，确认其与已支持挂牌价标签一致。该组合定向 **82 passed**，解析器专项 **496 passed**，全量pytest **1097 passed、27 skipped、27 subtests passed**。
- 解析器升至`generic-labelled-v0.2.137`；compileall、JSON和diff空白检查通过。仅合成HTML离线验证，无真实页面准确率结论、数据库变化或部署。

## 2026-11-12 P0-03支持“售价/挂牌售价”并排除成交合同售价
- 目标：接受“售价”“挂牌售价”作为挂牌总价字段标签，同时确保成交/合同售价不会被误当挂牌价。
- 两来源回归修复前显示4个合法标签场景漏解析；新增限定价回归验证`成交售价`和`合同售价`不填挂牌价、不会与真实挂牌价冲突。解析器现支持两个别名，保留非挂牌限定词规则，版本升至`generic-labelled-v0.2.136`。
- 价签/限定词专项 **82 passed**；解析器专项 **496 passed**；全量pytest **1097 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未设置`TEST_DATABASE_URL`而跳过；compileall、GOAL_STATE JSON和diff空白检查通过。
- 仅合成HTML离线验证，真实页面准确率未验证；未访问来源网站、NAS或生产数据库，无数据库/配置/迁移/部署变化。

## 2026-11-12 P0-03补齐扩展装修标签
- 目标：识别`装修情况`和`装修状况`标签，不把标签后缀误当值或漏掉真实装修字段。
- 两来源4个合成回归修复前均失败；现扩展装修字段标签并将完整标签用于前字段终止识别；回归还验证原文quote和字符偏移能从证据摘录还原。解析器版本升至`generic-labelled-v0.2.135`。
- 装修/楼层新回归定向 **8 passed**；解析器专项 **488 passed**；全量离线pytest **1089 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未设置`TEST_DATABASE_URL`而跳过；compileall、GOAL_STATE JSON及diff空白检查通过。
- 仅合成HTML离线验证；无来源网站、NAS、生产数据库、配置或迁移变化，也未部署。真实准确率仍需每站20份获准样本及人工标签。

## 2026-11-12 P0-03排除“总楼层”对挂牌楼层的污染
- 成功标准：单独“总楼层”不填入挂牌`floor_text`；同时有所在楼层和总楼层时保留所在楼层，不能把总楼层作为第二个冲突候选。
- 贝壳/安居客4个合成回归修复前均失败：只出现“总楼层：18层”会抽出`18层`；与“所在楼层：中楼层”并列会触发`multiple_floor_mentions`并清空字段。现排除`总楼层`标签，并将其作为前一楼层值的终止边界，解析器升至`generic-labelled-v0.2.134`。保留“楼层：高楼层 14/18层”既有格式。
- 定向 **4 passed**；`tests/test_collection_parser.py` **484 passed**；全量离线pytest **1085 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未设置`TEST_DATABASE_URL`而跳过；compileall、GOAL_STATE JSON和`git diff --check`通过。
- 仅合成HTML离线验证，无真实准确率结论；未访问来源网站、NAS或生产数据库，无迁移/部署。P0-03仍待每站20份获准样本及人工标签。

## 2026-11-12 P0-03排除“实用面积”误报为建筑面积
- 目标：建筑面积字段不把“实用面积”误当成建筑面积，并在同页另有建筑面积时保留正确值。
- 贝壳和安居客4个合成回归先失败：单独“实用面积100㎡”被错误抽取；与“建筑面积120㎡”并列时误报多值并清空。现将“实用”加入面积排除限定词，解析器版本升至`generic-labelled-v0.2.133`；未改变建筑面积标签或字段模型。
- `tests/test_collection_parser.py` **480 passed**；全量离线pytest **1081 passed、27 skipped、27 subtests passed**。27项跳过均需`TEST_DATABASE_URL`；Python 3.12 compileall、GOAL_STATE JSON和`git diff --check`通过。
- 仅合成HTML离线验证，没有获准真实样本、来源准确率结论、数据库/配置/迁移变化；未访问网站、NAS或生产环境，未部署。P0-03仍需每站20份获准页面及人工标签。下一步继续可复现的离线解析边界审查，并在样本到位后运行准确率/覆盖率评估。

## 2026-11-12 P0-03同页嵌套挂牌价冲突留空待审
- 用户确认同一HTML外层`article`与嵌套`.content`给出不同挂牌价时按冲突处理，留空并待人工审核。
- 新增贝壳/安居客失败回归：旧解析器均选中嵌套320万且无冲突告警；现若已选内层类根位于含多个不同挂牌价的`article`中，则用该article文本保留两条报价证据，`asking_price_wan=null`、追加`multiple_price_mentions`并保持待审核。同价重复仍可正常审核；不拼接兄弟根字段。解析器版本升至`generic-labelled-v0.2.132`。
- 解析器专项 **476 passed**；全量离线pytest **1077 passed、27 skipped、27 subtests passed**。27项为默认未连接PostgreSQL的数据库集成。compileall、GOAL_STATE JSON及`git diff --check`通过。
- 仅合成HTML离线验证，没有真实许可样本准确率结论；本轮不访问来源网站、NAS或生产数据库，不部署。下一步：取得每站至少20份获准页面及人工标签后运行样本评估；材料未到前继续做可复现的离线解析边界审查。

## 2026-11-12 P0-04贝壳当前协议正文复核
- 直接复核贝壳官方协议页面：最新更新日期2026-11-11、生效日期2026-11-12；第七条第2/3款明确未经书面许可不得读取或自动化抓取平台内容，许可后仍须限定用途并遵守Robots。该条款没有授予本项目许可。
- 安居客官方协议中心仍只展示消费者/经营者协议目录和历史版本入口，当前消费者协议正文/版本映射未能核实；官方PDF继续仅作为风险条款证据。来源政策矩阵已记录证据和版本不确定性。
- 两站无本项目书面许可，在线采集保持OFF。只读取官方协议资料，未请求Robots、房源页或执行采集；未访问NAS/生产数据库，无部署。

## 2026-11-12 P0-06 DTK/Worker离线边界续审
- 复核DTK响应envelope、普通/嵌套任务页、页大小与游标类型、任务ID/状态、分享链接主机校验、不可持久化文本、任务轮询截止时间，以及Worker历史补采跨轮进度保存与恢复路径；未发现新的可复现缺陷，因此不改应用逻辑。
- 定向`tests/test_dtk.py tests/test_worker.py tests/test_account_history_backfill.py`：**85 passed**；同一版本的全量离线pytest为**1073 passed、27 skipped、27 subtests passed**。数据库集成另外在隔离PG17.11运行28 passed；此PG结果不验证真实DTK。
- P0-06仍需核对运行中DTK版本/接口权限，并由用户提供至少3个获准账号连续运行24小时，记录发现率与阻断。未连接DTK或访问平台，未部署。

## 2026-11-12 P0-09迁移014 NAS隔离PG17验收
- 使用PG17.11隔离库运行完整`tests/test_db_integration.py`：**28 passed**，覆盖001–014初始化、迁移重放幂等、迁移旧数据保留、详情队列表/API查询及观察记录删除时级联清理。测试只使用临时schema与合成数据；结束后业务schema仅剩`public`。
- PG17首次运行发现集成测试文件缺少`json`导入；修复后，持久详情队列的恢复顺序回归断言也由旧的“重抓列表后取详情”更新为实际契约：先排空已持久化详情队列，再重读列表页完成扫轮。没有修改应用运行代码。
- NAS隔离资源为本轮专用Docker internal网络、512 MiB tmpfs PG17、无宿主端口/持久卷；源码和pytest纯Python依赖只读挂载。测试容器、网络、源码/依赖暂存与压缩包已清理，复核生产API/Worker仍运行且DB healthy。
- 本机全量pytest **1073 passed、27 skipped、27 subtests passed**；27项PostgreSQL集成在默认离线运行中跳过，随后已全部在隔离PG17运行。保留1条既有Starlette/httpx弃用警告。Python 3.12 compileall、GOAL_STATE JSON和`git diff --check`通过。
- 本轮没有生产数据库/卷/Compose/API/Worker变更、迁移或部署，也未访问房源网站。P0-09继续`in_progress`：真实来源许可、获准页面和真实分页准确性仍缺；任何生产更新仍需新鲜备份、恢复验收与单独部署评估。


## 2026-11-12 P0-04安居客消费者协议入口再核验
- 官方协议中心仍列消费者“用户服务协议”和历史版本入口；官方帮助FAQ `faqId=104`重定向回该目录，未提供正文或版本标识。官方静态PDF适用于平台注册/非注册服务用户，含Robots、未经书面同意商业利用、未经明确特别书面许可抓取/使用等限制，但PDF没有可读版本日期，不能证明其与当前协议中心版本对应。
- 将该PDF维持为官方风险条款证据，不标成现行协议。安居客当前适用版本映射及项目书面许可仍缺，两站在线采集继续OFF；本次只读官方协议资料，未请求房源页面或执行采集。

## 2026-11-12 P0-03离线解析器边界复核
- 复核当前内容根评分、显式挂牌价格标签/非挂牌价格排除、面积范围、ID来源及35,000字符截断边界；未找到不依赖未决跨根价格冲突口径的新可复现缺陷，因此不修改解析行为。
- Python 3.12解析器专项 `tests/test_collection_parser.py`：**472 passed**。这是虚构/合成HTML回归，不代表真实页面准确率或覆盖率。
- P0-03仍需贝壳、安居客各20份获准页面及人工标签；外层`article`和内层`.content`价格冲突已由用户确认留空待审并在v0.2.132实现。未访问来源网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-02样本校验与评估工具复核
- 对照样本模板、校验器和评估器：必填列/场景门槛一致；工具覆盖样本身份与内容去重、源状态与异常场景覆盖、许可范围元数据、字段标签、冲突候选/范围证据和截断失败门禁。
- Python 3.12专项`tests/test_sample_set.py tests/test_parser_evaluation.py`：**203 passed**。这些回归使用临时合成样本，只证明工具逻辑；目前仍无获准真实页面，不形成准确率/覆盖率结论，也不验证许可效力。未发现可复现缺陷，未修改代码。
- 未访问来源网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-09迁移014隔离验收续查
- 当前Python 3.12环境重新运行全量离线pytest：**1073 passed、27 skipped、27 subtests passed**；27项均为未连接PostgreSQL的集成测试。`tests/test_migration_transactions_stdlib.py`另有**3 passed**，确认001–014事务边界、部署命令和Compose挂载顺序。
- 尝试用本机PostgreSQL 16建立一次性隔离库；`initdb`即使指定`shared_memory_type=mmap`和`dynamic_shared_memory_type=mmap`仍因System V `shmget`失败，临时目录已清理，未启动数据库或执行迁移。Docker daemon返回permission denied。
- 迁移014的PG运行验收仍未完成；已向用户请求授权，通过`notedock-nas`传输源码并创建/清理不挂生产卷的PG17临时隔离资源。当前没有远端写入或部署。
- README文件导航同步至迁移001–014，简述011–014各自维护的追加式解析账本、发现去重ID、DTK补采游标和详情URL队列。
- 最新NAS只读复核：`nas-lan`连接超时、Tailscale CLI偏好加载失败，故使用此前获准的`notedock-nas`并确认宿主机`DXP4800/sheng`。API/Worker运行、生产PG17 healthy；`postgres:17-alpine`和`python:3.12-slim`镜像存在，未发现`nbrei-p009`测试容器。未查询业务数据/schema、传输源码、创建远端资源或改动生产服务。
- P0-09代码边界复核：列表提取仅接受本来源HTTPS主机的详情URL，详情抓取重新校验URL并经过全局/来源许可及Robots门禁；403/429停止队列处理，普通失败留队重试。相同来源URL/原始HTML哈希由候选唯一约束处理重复提交，约束的PostgreSQL运行行为仍待隔离PG17验收。定向发现/队列/状态测试**55 passed、7 subtests passed**；未发现新的可复现缺陷。

## 2026-11-12 P0-07健康指标文档口径同步
- README验证摘要更新为当前解析器`generic-labelled-v0.2.131`、解析器专项472 passed、评估器专项116 passed及全量离线pytest 1073 passed/27 skipped/27 subtests；27项PostgreSQL集成未连接数据库。
- API健康比率说明补充：解析成功率和字段完整率只统计迁移010启用后的事件；旧运行记录无法可靠区分网络失败与解析失败，不回填迁移前历史。
- 本轮仅同步文档，没有修改应用代码、数据库或NAS部署；P0-07生产升级仍需备份、恢复验证与单独部署评估。

## 2026-11-12 P0-03评分后续 article 根
- 失败回归证明：当页面第一个`article`仅含“推荐阅读”、后续独立`article`含完整挂牌字段时，旧实现只评分第一个节点，贝壳和安居客均漏掉小区、面积和挂牌价。现评分所有未嵌套于其他`article`的候选，保留文档顺序/最高分选择、不跨根拼接；嵌套`.content`冲突策略保持待确认。解析器升至`generic-labelled-v0.2.131`。
- 新增两来源回归，解析器专项 **472 passed**；全量离线pytest **1073 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过。Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`通过。
- 仅本机合成HTML验证；未访问来源网站、NAS或生产数据库，无迁移或部署。P0-03真实页面准确率仍待两站各20份获准样本及人工标签。

## 2026-11-12 P0-03将非挂牌价格场景缺失值纳入字段指标
- 失败回归显示，`oral_prices`/`transaction_prices`标注挂牌价为空时，专门场景能检出非挂牌金额被误抽，但该样本未进入挂牌价字段准确率/精确率分母；错误输出因而未降低字段指标。现将这两类显式空挂牌价作为空真值计分，误报会同时反映在字段指标和专门场景指标；未解析的`multiple_prices`继续只在独立场景计分。
- 两来源promotion回归修复前均失败，修复后通过。评估器专项 **116 passed**；全量离线pytest **1073 passed、27 skipped、27 subtests passed**。27项均需PostgreSQL集成库，未运行。Python 3.12 compileall和`git diff --check`通过。
- 更新`docs/SAMPLE_DATASET.md`与`docs/ACCEPTANCE.md`分母说明。仅使用合成HTML/Mock，没有真实样本准确率结论；未访问来源网站、NAS或生产数据库，无迁移或部署。

## 2026-11-12 P0-09独立持久化详情URL队列
- 本轮目标：详情页临时失败不再卡住整个列表页/扫轮；完成工作区实现与离线验证。迁移014按目标+挂牌ID持久化详情URL、尝试次数和错误类别，外键关联挂牌观察记录；Worker每轮最多尝试20个详情，失败项保留供后续轮询重试，继续其他URL和列表分页。成功后删除队列行，已暂存ID账本保障崩溃后幂等恢复。
- 已认证的discovery-state响应新增待抓URL列表（最多100条）及总数/截断标记。在线许可、robots、403/429阻断仍优先停止目标；没有增加重试绕过路径。
- 新增回归证明首个详情失败时后续详情仍处理、列表扫轮继续完成、失败URL保留并在下一轮优先恢复；更新页数/详情上限与许可撤回回归。发现/服务/状态专项65 passed，新增403/429限制响应专项2 passed；全量pytest **1060 passed、26 skipped、27 subtests passed**。26项跳过均需TEST_DATABASE_URL，故迁移014 PostgreSQL实际执行/API真实数据库查询未验证。本机Docker socket返回permission denied；PostgreSQL 16在shared_memory_type与dynamic_shared_memory_type均设为mmap后仍因系统shmget限额启动失败，临时数据目录已清理；迁移事务、Compose顺序静态回归已纳入全量套件。Python编译、目标JSON与diff空白检查通过。
- 变更包括迁移014、Compose初始化挂载、发现Worker、认证状态API响应及API/部署文档。仅本机离线验证，未访问网站、NAS或生产数据库，未执行迁移或部署；现有NAS不包含本轮改动。
- 下一步：①隔离PostgreSQL 17按001–014初始化并重放014，验证队列表/API和外键级联；验收迁移幂等、pending URL可读、观察记录删除时队列清理；②取得获准真实列表/详情样本后再做站点专用列表选择器校准；③通过备份与恢复门槛后单独评估NAS更新，不与生产迁移混做。

## 2026-11-12 P0-06历史补采页数上限后续跑
- 复现并修复DTK 30/90天首次历史补采超过每轮5页会被误标完成的问题。迁移013保存补采游标和固定截止时间；每页提交后推进游标，只有读完末页才标记首次同步完成。切换历史模式和显式重新补采会清除旧进度。
- 新增Worker续跑/截止时间回归、增量轮询不污染补采游标、服务模式重置回归、迁移事务/Compose顺序契约。Worker定向4 passed；完整定向8 passed、13 subtests passed；全量pytest **1057 passed、26 skipped、26 subtests passed**，26项因本机未设置TEST_DATABASE_URL跳过。迁移013通过静态事务/顺序检查，PostgreSQL执行未验证；compileall、GOAL_STATE JSON和git diff --check通过。
- 仅本机离线验证；无NAS、DTK或生产库访问，未执行迁移/部署。P0-06仍需确认真实DTK接口、获准账号和24小时联调；P0-01真实V0.1备份、P0-02获准真实样本仍缺。
- 下一步：①有TEST_DATABASE_URL时在隔离PostgreSQL 17验证001–013与013重放幂等；②取得获准DTK账号后做至少3账号连续24小时联调；③收到每站20份获准HTML及标注后评估解析准确率。验收以迁移可重放且数据保留、分页跨轮不漏/不重、解析指标按标注集报告为准。

## 2026-11-12 P0离线回归套件重新验证
- 使用已有离线依赖缓存和临时Python 3.12环境重新运行全量pytest：**855 passed、26 skipped、25 subtests passed**；仅有1条Starlette/httpx弃用警告。26项跳过全部为PostgreSQL集成，因为本机未配置`TEST_DATABASE_URL`且`pg_isready`无服务响应。
- Python 3.12 compileall、`docs/GOAL_STATE.json`解析及文档尾随空白检查通过。未改应用代码、未执行迁移、未访问房源网站/NAS或生产数据库。
- 按项目迭代流程生成`../ningbo-re-ai-v0.2-dev-2026-11-12-offline-regression.zip`；开发包包含124个源码/文档文件，ZIP完整性与包内SHA-256清单校验通过。
- P0-09迁移012运行回归仍需PostgreSQL 17隔离库；跨区域解析字段行为继续等待用户选择。

## 2026-11-12 更新P0-09路线图主清单的验证范围
- 主清单原列的PostgreSQL 17 `17 passed`和离线套件`670 passed`是早期历史数据，容易误代表当前状态。现更新为最新离线套件855 passed/26 skipped/25 subtests；明确24项PG17结果先于迁移012新增回归。
- 另外同步当前NAS只读证据：生产Compose仅挂载001–005，工作区006–012未部署。历史各轮记录保留；未将旧数据库测试结果外推到迁移012。
- 仅更新路线图与本记录，无代码、数据库或NAS变更。

## 2026-11-12 P0-01/P0-07 NAS运行态与迁移挂载只读复核
- 按NAS连接技能依次尝试`nas-lan`、Tailscale，再使用用户此前授权的`notedock-nas`；LAN连接超时、Tailscale CLI无法读取偏好。公网别名通过严格主机校验后连接到`DXP4800/sheng`，Docker权限正常。
- UGREEN Compose路径仍为`/volume3/docker/ningbo-re-ai/docker-compose.yml`；API与Worker运行，PostgreSQL 17 healthy，NAS本机`http://127.0.0.1:8788/healthz`返回`ok=true`。当前Compose仅挂载001–005迁移；工作区006–012没有部署。该只读检查未查询业务行、数据库schema或秘密。
- 未传输文件、创建容器、执行迁移或改动Compose/卷/服务；未部署。P0-01仍缺真实V0.1备份；P0-07仍需经过备份和隔离验证后评估生产更新；P0-09迁移012仍待允许的隔离PG17回归。不得将此运行态检查表述为工作区版本已部署。

## 2026-11-12 P0-09同步挂牌失联主清单规则
- 路线图主清单仍写“失效判定次数与自动下架规则不得自行猜测”，与用户已确认的规则冲突。现明确连续2次完整分页遍历未见后转`pending_review`、不自动下架；人工结论只记录，不修改正式挂牌状态。
- 同步注明对应回归已覆盖，迁移012新增测试仍待隔离PostgreSQL 17复测；站点专用列表选择器和独立待发现URL队列仍未完成。另有解析器跨区域字段合并口径待用户选择，答复前保持现状。
- 仅更新路线图和目标状态，无应用代码、数据库或部署变更。

## 2026-11-12 P0-09明确迁移012的安全回退边界
- 迁移012将成功暂存挂牌ID从有界JSON迁到可累计增长的规范化表；旧版应用依赖JSON去重，因此仅回滚代码或删除新表会导致漏去重，盲目聚合还可能超过旧版数量/2,000,000字节上限并截断。
- 部署手册现明确迁移事务失败时自动整体回滚；迁移提交后不支持原地降级。必须回退时，停API/Worker写入并把数据库与匹配源码恢复到迁移前备份时间点，说明会丢弃备份后的数据库写入，同时保留迁移后raw-pages证据副本。若不能接受该损失，保持当前版本向前修复。
- 新库初始化事务说明与顺序同步至迁移012。只更新文档，未执行迁移、NAS/生产访问或部署。

## 2026-11-12 P0-09确认迁移期间活动扫描状态来源
- 核对`_finish_discovery_sweep`后确认失联计数和本轮已见集合以`collection_listing_observations`为权威；迁移012清空冗余`sweep_seen_listing_ids`后，发现状态API从观察表重建本轮ID，Worker恢复活动扫描仍使用持久化页游标与`sweep_number`。
- 新增PG集成回归：构造活动扫描和匹配观察记录、重放迁移012，再断言扫描仍active且API返回本轮已见ID。本机全量离线pytest **855 passed、26 skipped、25 subtests passed**；26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过。本机PostgreSQL 16隔离启动也未成功：即使将`dynamic_shared_memory_type=mmap`设为initdb参数，bootstrap仍因系统`shmget`资源限制失败；失败后数据目录自动清理。
- Python 3.12 compileall、目标JSON及变更文件尾随空白扫描通过。未执行SQL迁移、未访问来源/NAS生产库、未部署。P0-09仍需隔离PG17数据库回归、获准来源样本与生产升级评估。

## 2026-11-12 P0-04官方来源协议时点复核
- 贝壳官方协议标示2026-11-11更新、2026-11-12生效；继续要求书面许可，限制自动化抓取，并要求遵守许可范围及Robots。安居客官方中心目录可见，协议正文未能读取；经纪人协议不代替消费者协议。
- 本轮未访问房源页、未采集或申请许可；目标主机robots正文未能从网页工具取得，2026-11-10 NAS结果仅作历史记录。无本项目书面许可，来源和全局在线采集继续OFF，P0-04保持`in_progress`。
- 下一步：取得平台书面授权并明确用途范围；确认安居客当前协议版本；有授权后再从目标origin复核robots和允许路径。

## 2026-11-12 P0-09规范化长期分页去重ID
- 新增迁移`012_collection_discovery_staged_ids.sql`，将目标级成功暂存ID从游标JSON迁入独立表，并回填已有`seen_listing_ids`；游标状态保存不再随累计ID数增长。Worker从该表检查详情去重；扫轮已见ID由挂牌观察记录派生，避免重复累积。
- 发现状态API保留旧字段语义，并返回累计ID数及截断标记；`seen_ids`按挂牌ID字典序返回，直接利用主键索引并避免时间戳并列时的不确定顺序。新增100,001条历史ID后仍能发现并暂存新挂牌及稳定返回顺序的PG集成回归。
- 本机完整离线pytest **855 passed、25 skipped、25 subtests passed**；Python 3.12 compileall、GOAL_STATE JSON及变更文件尾随空白扫描通过。25项数据库集成因本机未设置`TEST_DATABASE_URL`跳过。NAS PG17复测未运行：自动审核拒绝将源码包/测试运行时写入NAS临时目录，指出当前授权未覆盖源码外传或远端文件写入；未绕过该拒绝。
- 仅离线测试；没有执行迁移、访问来源网站、改变生产数据库/Compose/卷/服务或部署。在线采集保持关闭。P0-09继续等待许可范围、两站获准真实页面样本及生产升级评估。

## 2026-11-12 P0-09发现页遍历复用DOM子节点
- `_visible_anchors`原对每个节点执行`list(parent.children)`复制直接子节点；闭合`details`的`Tag.find()`也会间接访问`.children`。现对普通节点反向读取已有`contents`，闭合`details`直接在`contents`中选取`summary`，保持其余折叠内容不进入发现结果。
- 新增回归禁止发现过程访问`Tag.children`，同时确认普通详情链接和折叠摘要保留、折叠正文排除。回归先失败后通过；发现/URL/状态专项 **57 passed、7 subtests passed**。
- 全量离线pytest **855 passed、23 skipped、24 subtests passed**；23项数据库集成因未配置`TEST_DATABASE_URL`跳过。Python 3.12 `compileall`、GOAL_STATE JSON及`git diff --check`通过，保留1条Starlette/httpx弃用警告。
- 仅本地合成HTML验证；无数据库迁移、配置变化、来源访问、NAS/生产库访问或部署。P0-09仍`in_progress`，真实页面及许可范围仍未验收。当时发现发现状态`seen_ids`有100,000项和2 MB序列化上限；该问题已由后续迁移012将成功暂存ID规范化存储，保留详情失败可重试与跨轮去重语义。

## 2026-11-12 P0-07生产schema与API差异只读复核
- NAS连接技能按 LAN→Tailscale→已授权 `notedock-nas` 路由核验；LAN SSH 超时、Tailscale CLI 无法加载偏好，公网别名连接确认主机为 `DXP4800/sheng`。
- 生产API/Worker运行、PostgreSQL 17 healthy；Compose登记路径为 `/volume3/docker/ningbo-re-ai/docker-compose.yml`。数据库挂载初始化脚本仅001–004，schema具有基础挂牌/采集/健康表，但缺少006–011的分页发现状态、挂牌观测/复核、扫轮、解析尝试结构及健康解析计数列；生产OpenAPI缺少工作区的发现观测、复核历史和发现状态读写路由。
- 此轮只读查询容器元信息、表/列目录和API路径，没有读取业务行、凭据或环境秘密；未创建备份、迁移、修改Compose/卷/服务或部署。P0-07仍`in_progress`，需要生产升级前的新鲜备份、完整恢复验证及单独部署评估。
- 用户确认跨平台同套候选面积差≤5%按较小面积作分母；与现有公式及两方向边界测试一致，无需代码变更。

## 2026-11-12 P0-07在隔离PostgreSQL 17运行完整数据库集成
- 为NAS一次性Python测试运行器临时提供离线pytest及依赖，当前工作区源码以只读方式挂载；完整`tests/test_db_integration.py`在PostgreSQL 17.11运行 **24 passed**，包括迁移011幂等、UPDATE/DELETE/TRUNCATE拒绝及解析账本/健康汇总一致性检查。
- 数据库仅使用Docker internal网络和512 MiB tmpfs，无宿主端口、无持久卷；测试API容器自动退出。测试容器、网络、pytest依赖和源码暂存目录均已清理。复查生产API/Worker为running、生产PostgreSQL为healthy，生产数据库、卷、Compose及服务未变；没有生产查询写入、迁移或部署。
- 本机全量离线pytest仍为 **854 passed、23 skipped、24 subtests passed**；23项数据库集成跳过是本机环境未配置`TEST_DATABASE_URL`，其数据库集成文件现已单独在NAS隔离PG17完整通过。

## 2026-11-12 P0-07在隔离PostgreSQL 17验证解析账本保护
- NAS LAN路径超时、Tailscale应用不存在后，使用已授权的`notedock-nas` OpenSSH别名确认主机为`DXP4800/sheng`。传输开发包SHA-256一致。
- 创建本轮专用Docker internal网络和PostgreSQL 17.11容器：512 MiB tmpfs、无宿主端口、无数据库持久卷；只读挂载源包。001–011全部按序成功，011重复执行成功。运行时DO回归确认UPDATE、DELETE、TRUNCATE均被拒绝；解析明细保留1行，健康汇总保持`parse_attempt/success/complete=1/1/1`。
- 测试容器、网络和NAS临时目录已清理；生产API、Worker仍running，生产PostgreSQL healthy。未查询生产业务表、未改生产Compose/代码/卷或执行迁移，未部署。
- 本轮数据库运行时烟测通过；完整离线pytest仍为 **854 passed、23 skipped、24 subtests passed**，其中新增PostgreSQL集成用例因本机没有`TEST_DATABASE_URL`而跳过。

## 2026-11-12 P0-07保持解析审计与累计健康指标一致
- 发现迁移010的解析尝试明细虽声明为追加式，数据库实际只在INSERT时递增汇总，仍允许UPDATE、DELETE和TRUNCATE，可能令健康计数与审计记录脱节。新增迁移011拒绝三类修改，并保持累计指标仅由追加插入维护。
- 同步Compose初始化顺序、NAS升级命令、API说明及迁移契约检查；新增PostgreSQL集成回归核对明细和三项汇总保持不变。失败契约回归先失败后通过。
- 定向迁移/健康测试 **7 passed、1 skipped、11 subtests passed**；全量离线pytest **854 passed、23 skipped、24 subtests passed**。新增数据库行为用例随其他数据库集成测试因未设置`TEST_DATABASE_URL`跳过；本机PostgreSQL无响应、Docker socket拒绝访问，因此SQL运行时行为未验证。Python 3.12编译、GOAL_STATE JSON、`git diff --check`及开发包校验通过。
- 未访问NAS、生产数据库或房源网站，无迁移/部署。P0-07仍待隔离PG17及生产差异验收；P0-03真实获准页面与人工标签仍缺。

## 2026-11-12 P0-03恶意式字段文本的有界耗时复核
- 用重复的长“装修”字段值构造合成页面，预热后各解析5次：9,933字符/29,613 UTF-8字节中位5.6ms；49,985字符/149,123字节20.1ms；149,929字符/447,343字节21.1ms；299,969字符/895,043字节22.0ms。未观察到输入增大时超线性增长；35,000字符字段扫描窗口和1 MB输入字节上限均生效。
- 该探针只覆盖特定合成文本和本机环境，不是生产性能SLO或真实页面准确率证据；无应用代码变更。未访问房源网站、NAS或生产数据库，无部署。
- 跨语义区域小区名与详情字段能否组合仍待用户答复；获准真实页面和人工标签仍缺。

## 2026-11-12 P2-02面积边界复核与P0-03口径待答
- 用户确认跨平台疑似同套面积差以较小面积为分母；重新运行`tests/test_opportunities.py`，**21 passed**，覆盖两种面积方向及5%边界。
- P0-03尚有跨语义区域字段是否可组合的产品口径未答。具体场景已提交用户选择；答复前维持现有解析行为，不改变代码。
- 本轮无应用逻辑修改。真实获准网页/人工标签仍缺；没有访问来源网站、NAS或生产数据库，也未部署。

## 2026-11-12 P0-03解析器内存边界复核与口径确认
- 复核剩余的两处`get_text()`：内嵌样式扫描受1 MB输入页面上限约束；标题候选最终裁剪至500字符。没有发现可复现的无界内存或重复DOM遍历问题，因此不增加实现复杂度。
- 用户确认跨平台同套候选的面积差≤5%以较小面积作分母；`abs(a-b)/min(a,b)≤0.05`与现有实现一致，无需业务代码改动。
- Python 3.12离线全量pytest **853 passed、22 skipped、23 subtests passed**；22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 未访问来源网站、NAS或生产数据库，无迁移/部署。P0-03真实页面准确率仍待两站各20份获准页面及人工标签。下一步：样本到位后运行标注集评估；期间继续有计数证据的离线缺陷审查。

## 2026-11-12 P0-03流式处理内联CSS声明
- 将内联样式解析与opacity歧义检查中的`split(';')`改为惰性声明迭代。75,000声明内存回归修改前均失败，峰值3.76/3.75 MiB；修改后为0.0067/0.0020 MiB。
- 解析器专项 **340 passed**，全量离线pytest **853 passed、22 skipped、23 subtests passed**；22项数据库集成因未设置`TEST_DATABASE_URL`跳过。CSS/可见性定向70 passed。
- Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。仅合成CSS离线验证，未访问网站、NAS或生产数据库，无迁移/部署；真实页面评测样本仍缺。

## 2026-11-12 P0-03避免CSS可见文本逐字符分配
- `_css_without_comments_or_strings`改为在注释/字符串边界按片段写入，避免每个普通CSS字符产生一个列表引用。失败回归复现300 KB输入额外分配2,901,577字节，修改后峰值低于1,000,000字节。
- 同类600 KB合成输入的tracemalloc峰值从5.60 MiB降至1.29 MiB。CSS/可见性定向70 passed、解析器338 passed；全量离线pytest851 passed、22 skipped、23 subtests passed。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`通过。未联网、未访问NAS/生产数据库、未部署；该合成测量不构成生产SLO。

## 2026-11-12 P0-03按需生成CSS规则片段
- CSS分段器改为流式yield，避免在解析可见性声明前构造整份片段列表；命中首个风险规则时可立即停止扫描。失败回归先证明旧实现会在取首片段前产生1,001次切片，现为1次。
- 600 KB/200,000段合成CSS的分段函数峰值内存由列表版9.75 MiB降至流式完整消费的0.0008 MiB；该数字不含输入字符串/DOM，也不是生产SLO。CSS专项23 passed，解析器专项337 passed；全量离线pytest850 passed、22 skipped、23 subtests passed。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`通过。未访问网站、NAS或生产数据库，无迁移/部署。真实页面/人工标签仍缺。

## 2026-11-12 P0-03复核DOM遍历和样本库存
- `app/collectors/parser.py`只剩H1包装链处直接迭代`Tag.children`；该处没有`list()`物化。`data/`仅有1个占位文件、`fixtures/`有4份演示HTML，未发现真实页面样本或标注清单。
- 项目要求形式的Python模块运行定向DOM回归 **1 passed**；解析器专项最近一次336 passed、全量离线pytest最近一次849 passed/22 skipped/23 subtests passed。此盘点没有改变代码。
- 真实页面准确率不可由演示fixture推断；P0-03继续等待每站20份获准真实页面与人工标签。未访问网站、NAS或生产数据库，无部署。

## 2026-11-12 P0-03避免复制DOM子节点列表
- 新增失败回归，禁止DOM遍历通过`Tag.children`重新物化已有子节点；此前隐藏节点/文本裁剪、内联可见性检查、文本布局与run-in布局会复制子节点列表。实现改为复用`Tag.contents`并在需要删除时逆序迭代，测试覆盖连续隐藏兄弟节点及多段隐藏文本，确认前后可见文本顺序不变。
- 解析器专项 **336 passed**；全量离线pytest **849 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 先后顺序相反的两批各9次合成基准（600,098字节、25,000个span，含DOM解析及tracemalloc）中，上一版中位数1,224.24/1,230.99ms，当前版1,122.29/1,138.92ms；峰值均30.02MiB。耗时低约7.5–8.3%，仅代表该合成页面，不构成真实网页性能SLO。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`通过。仅离线验证，未访问网站、NAS或生产数据库，无迁移/部署；真实页面样本和跨语义根策略仍待落实/确认。

## 2026-11-12 P0-03穷举Unicode空白归一化边界
- 新增测试枚举正则表达式识别的每个Unicode空白码点，并对每个规范化输出截断位置逐项比对完整`re.sub`的前缀及截断标志；没有修改解析器行为。
- 归一化专项 **8 passed**，解析器专项 **335 passed**；全量离线pytest **848 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`通过；仅离线验证，未访问网站、NAS或生产数据库，无迁移/部署。跨根字段合并策略待用户确认；真实页面样本和人工标签仍缺。

## 2026-11-12 P0-03恢复Python 3.12离线测试并完成复验
- 系统Python未安装pytest；改用`uv`和任务临时目录中的离线缓存提供Python 3.12测试依赖，不修改项目依赖或联网安装。解析器专项 **334 passed**；全量离线pytest **847 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过；出现1条Starlette/httpx弃用警告。
- Python 3.12 `compileall`、GOAL_STATE JSON、`git diff --check`通过。测试含1,000组固定种子Unicode空白差分，不构成真实网页准确率验收。
- 仅离线测试，未访问来源网站、NAS或生产数据库，也未部署。跨语义根字段合并策略待用户确认；获准真实页面与人工标签仍缺。

## 2026-11-12 P0-03 Unicode 差分交付包复核
- 固定种子Unicode空白差分测试和正文回退边界仍由上一轮解析器专项334 passed、全量847 passed/22 skipped/23 subtests passed覆盖；本轮尝试复跑时，Python 3.12与系统Python 3.9均未安装pytest，因此不能声称本轮复验通过。
- 本轮Python 3.12 compileall、`docs/GOAL_STATE.json` JSON解析、`git diff --check`通过。开发包首次生成及脚本内ZIP/manifest SHA256逐文件核验通过；更新本状态记录后会重新生成最终包。
- 仍仅限离线验证；未访问来源网站、NAS、生产数据库或部署。跨语义根字段合并策略待用户确认；获准真实页面和人工标签仍缺。

## 2026-11-11 P0-09组合验证页数/详情上限与策略恢复
- 新增多轮Worker mock：第一页同时达到每轮页数上限和详情上限并保留第二页游标；第二轮在第二页暂存一条后模拟策略撤销，保存当前页游标与已完成ID；第三轮恢复后重读第二页、跳过已暂存ID，只暂存剩余挂牌并完成同一轮扫轮。验证无重复暂存、无漏抓，完成计数仅增加一次。
- 组合回归通过；全量离线pytest **831 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过；Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。
- 仅使用合成HTML和mock，未联网采集、未访问NAS或生产数据库，也未部署。生产数据库/PG17验收仍待做。

## 2026-11-11 P0-09验证详情上限命中时保留跨页游标
- 新增多轮Worker mock：第一页刚好包含20条详情并指向第二页时，首轮只暂存20条、保存第二页游标且保持扫轮活动；第二轮从第二页继续，仅暂存新挂牌，完成后扫轮计数增加一次。确认没有重抓或漏抓；现有实现符合约定。
- 新回归通过；全量离线pytest **830 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过；Python 3.12 compileall、GOAL_STATE JSON及变更文件尾随空白扫描通过。
- 仅mock HTML与本地状态模拟，未联网采集、访问NAS或修改生产数据库；未部署。

## 2026-11-11 P0-09补齐发现器字节上限与跨页回环回归
- 新增UTF-8字符数低于1,000,000、编码后超过1,000,000字节的页面拒绝用例，确认门禁按实际字节数执行。新增Worker两页互相回链用例，确认第二页后停止，不再请求已访问页，清空下一页游标并将该轮保持为不完整扫描；现有实现符合约定，无需改状态机。
- 两项定向回归 **2 passed**；全量离线pytest **829 passed、22 skipped、23 subtests passed**。22项数据库集成因未配置`TEST_DATABASE_URL`跳过；Python 3.12 compileall、目标状态JSON与`git diff --check`通过。
- 仅本地合成HTML和mock验证，未联网采集、未访问NAS或生产数据库、未部署。真实来源授权和页面样本仍待提供。

## 2026-11-11 修复内联CSS缓存饱和后的热点丢失
- 混合页先出现520个唯一样式、后跟2,000个重复样式（278,079字节）时，原“缓存满后停止写入”使后段重复style扫描4,001次。改为有界FIFO替换后，重复style扫描降至4次，总扫描由真正不缓存时的12,602次降至2,085次；配对解析中位数由122.09 ms降至62.01 ms。
- 对接近1 MB的989,918字节页面（9,165个span）压力核验：重复样式扫描4次、缓存峰值3项；唯一样式扫描45,826次、缓存封顶1,024项。解析返回后ContextVar为空。tracemalloc记录的解析峰值分别19.3 MB和20.3 MB（包含DOM与测量开销）。唯一样式无缓存中位数472.8 ms，缓存中位数493.7 ms，约4.4%额外开销；该缓存主要改善重复样式页面。
- 解析器测试 **318 passed**；全量离线pytest **827 passed、22 skipped、23 subtests passed**。22项数据库集成因缺少`TEST_DATABASE_URL`跳过；Python 3.12 compileall、GOAL_STATE JSON与`git diff --check`通过。
- 测量仅使用合成HTML、未访问来源网站、NAS或生产数据库，也未部署。压力探针不代表真实页面耗时或生产SLO；获准页面和人工标签仍缺。

## 2026-11-11 P0-03为重复内联样式加入有界解析期缓存
- 同一包含17项声明的style用于500个span时，完整解析重复扫描**2,502次**；缓存原型降至**4次**。在135,489字节合成页的配对测试中，解析中位数由30.86 ms降至10.63 ms，P95由31.29 ms降至11.48 ms。500个色值各异的样式用例扫描由2,502次降至1,502次，中位数31.94 ms降至25.33 ms；该用例未触及1,024项上限。解析器升至`generic-labelled-v0.2.113`。
- 加入仅在单次解析ContextVar作用域内生效的缓存，按(style, property set)去重，最多保存1,024项；`finally`重置上下文，直接调用小型样式辅助函数仍走原扫描。回归覆盖重复样式命中、两次解析不共享缓存、错误退出时清理和缓存容量上限。
- 解析器测试 **317 passed**；全量离线pytest **826 passed、22 skipped、23 subtests passed**。22项数据库集成因缺少`TEST_DATABASE_URL`跳过；Python 3.12 compileall、GOAL_STATE JSON与`git diff --check`通过。
- 仅合成HTML离线验证，未访问来源网站、NAS或生产数据库，也未部署。计时不代表真实页面耗时或生产SLO；获准页面和人工标签仍缺。

## 2026-11-11 P0-03评估跨阶段内联CSS缓存
- 用含30个文本节点及一个多声明`span style`的合成页面测得同一style每次解析扫描5次；100次解析中位数0.764 ms、P95 0.826 ms。为减少这5次扫描而引入跨过滤、可见性检查和文本布局阶段的缓存状态，复杂度高于当前实测收益，因此保留现状，不增加全局或跨请求缓存。解析器版本保持`generic-labelled-v0.2.112`。
- 同一style扫描计数回归1 passed；全量离线pytest **824 passed、22 skipped、23 subtests passed**，22项数据库集成因缺少`TEST_DATABASE_URL`跳过。Python 3.12 compileall和`git diff --check`通过。
- 本轮仅做离线合成页面性能评估；没有访问来源网站、NAS或生产数据库，也未部署。短基准不代表真实页面耗时或生产性能；真实准确率仍待获准页面和人工标签。

## 2026-11-11 P0-03合并明确排除节点的DOM扫描
- 失败回归统计到文档根节点11次完整后代遍历，其中脚本/样式/导航等排除、dialog、`[hidden]`和`style`隐藏内容分别触发整树查询。现用一次迭代树遍历判定并移除这些子树；跨层联动规则不变。相同合成文档的根级完整遍历降到7次上限。
- 回归同时检查可见挂牌价不被hidden/dialog/details广告污染，样式表可见性告警仍保留；解析器/采集服务 **339 passed**，全量pytest **818 passed、22 skipped、23 subtests passed**。22项数据库集成因缺少`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包完整性/manifest校验通过。仅合成HTML离线验证；未访问网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标签。

## 2026-11-11 P0-03复用重叠列表根的可见文本
- 失败回归复现：嵌套`main`、`article`、`.content`候选会各自生成评分文本，选中的根随后再被完整提取一次；80层嵌套内联节点中选中的`main`被遍历2次。现每个唯一候选根只抽取一次，候选评分和最终字段解析复用该规范化文本；相同Tag只评分一次，候选优先级与信号分数不变。解析器升至`generic-labelled-v0.2.110`。
- 回归确认80层嵌套候选根的文本提取调用各为1次，社区/面积/总价与原来一致。解析器/采集服务 **338 passed**；全量pytest **817 passed、22 skipped、23 subtests passed**。22项数据库集成因缺少`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`与开发包完整性/manifest校验通过。仅合成HTML离线验证；未访问网站、NAS或生产数据库，无迁移/部署；真实页面准确率仍待获准样本与人工标签。

## 2026-11-11 P0-03合并挂牌字段判定与证据匹配扫描
- 失败回归复现同一挂牌价pattern被`_first_unique_numeric`与证据构造各扫描一次；1,002条相同挂牌价触发2次完整匹配遍历。现单遍同时计算冲突唯一值、完整`mention_count`和最多20条证据；字段值、Decimal等值判定、冲突状态与证据内容保持原语义。解析器升至`generic-labelled-v0.2.109`。
- 新回归确认1,002次命中时只调用一次该字段pattern，价格保留365万元、完整计数1002、证据20条且截断标志正确。解析器/采集服务 **337 passed**；全量pytest **816 passed、22 skipped、23 subtests passed**。22项数据库集成因缺少`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 证据序列化压力探针：36,025字节合成HTML产生74,790字节fields JSON；可见文本按35,000字符截断，价格/面积各保留最多20条证据。本探针记录实际输出规模，不代表真实页面或全输入极限。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包完整性/manifest校验通过。仅合成HTML离线验证；未访问网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本与人工标签。

## 2026-11-11 P0-03流式处理页面身份与标题元数据
- 失败回归覆盖1,002个canonical链接和1,002个`og:url`标签：原实现通过多个BeautifulSoup结果列表及URL/ID列表暂存整组命中，再截断最终证据。现对样式链接、canonical/og URL及标题元数据直接迭代DOM；不同ID检测最多保留两个代表值，但逐项检查所有命中。解析器升至`generic-labelled-v0.2.108`。
- 新回归确认2,005条挂牌ID提及完整计数、证据仅保留20条且截断标志正确；重复匹配ID之后出现的冲突ID仍阻止审核。collection parser/service **336 passed**；全量离线pytest **815 passed、22 skipped、23 subtests passed**。22项数据库集成因缺少`TEST_DATABASE_URL`跳过；保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包完整性/manifest校验通过。仅合成HTML离线验证；未访问网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本与人工标签；P0-01真实V0.1备份和P0-02样本/许可/标签仍缺。

## 2026-11-11 P0-03 H1候选按需遍历
- 80层嵌套H1回归先失败：当前解析器对每个标题反复展开其子树，共访问13,306个子节点。现将H1文本候选改为惰性生成，并在找到第二个不同标题后停止；保留冲突告警、head:title回退和标题文本规则。解析器升至`generic-labelled-v0.2.107`。
- 解析器/采集服务 **334 passed**；全量离线pytest **813 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。新回归要求80层输入总子节点访问≤1,280。
- 仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实解析准确率仍待获准页面及人工标签；P0-01真实V0.1备份和P0-02样本/许可/标签仍缺。

## 2026-11-11 P0-03流式判定字段值歧义并保留完整证据计数
- 失败回归复现：`_first_unique`与`_first_unique_numeric`先物化全部正则匹配，再决定是否存在冲突；前两项已不同的字段仍继续生成并保存后续候选列表。现在改为流式归一化，发现第二个不同值即停止核心歧义判定，候选集合最多保留2项；field_evidence仍单独遍历全文，准确统计全部命中数并仅保留前20条。解析器升至`generic-labelled-v0.2.106`。
- 1,002条报价回归确认解析字段被冲突阻断、`mention_count=1002`、证据保留20条；歧义扫描调用计数回归确认在第二个不同值处停止。collection parser/service **333 passed**，全量离线pytest **812 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。配置无变化；真实页面准确率仍待获准样本和人工标注。
- 下一轮继续P0-03检查H1/title候选提取和字段证据序列化的输入放大/重复文本处理；用确定性节点或匹配计数回归验收。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。

## 2026-11-11 P0-03避免可见性检查反复展开嵌套文本子树
- 复杂度回归复现：80层嵌套、每层均含文字的样式节点让`_has_unresolved_inline_visibility`反复调用`get_text(strip=True)`，累计遍历 **3,240个后代字符串**。现改为一次迭代后序遍历汇总子树文本状态，只扫描直接子节点并在有文本的样式节点上检查声明；空文本节点仍不触发告警。解析器升至`generic-labelled-v0.2.105`。
- 后代字符串访问与直接子节点访问均有确定性规模上限回归；解析器/采集服务 **331 passed**，全量离线pytest **810 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。配置无变化；真实页面准确率仍待获准样本与人工标注。
- 下一轮继续P0-03在1 MB上限下审计证据提取的重复正则扫描和内存放大；用确定性匹配/节点计数回归验证并修复。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。

## 2026-11-11 P0-03缓存同级run-in分析避免超线性扫描
- 复杂度回归复现：80个连续`display:run-in`兄弟节点调用`_text_with_inline_boundaries`时，重复向前/向后扫描产生 **183,763次display查询**。现按父节点一次性构建同级run-in布局，文本边界结果保持不变；解析器升至`generic-labelled-v0.2.104`。
- 新增确定性规模回归要求80节点不超过 **350次display查询**；run-in/显示边界专项 **19 passed**，collection parser/service **330 passed**，全量离线pytest **809 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。配置无变化；真实页面解析准确率仍待获准样本和人工标注。
- 下一轮继续P0-03按1 MB输入上限审计树遍历/证据提取复杂度，优先寻找确定性二次方或重复子树扫描；用调用次数/处理节点数回归验收。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。

## 2026-11-11 P0-03避免CSS自定义属性嵌套块重复解码前缀
- 性能回归复现：100层自定义属性花括号块让扫描器重复解码不断增长的同一前缀 **101次**，可通过小于1 MB的输入造成二次方工作。现仅在进入自定义属性值块时解码并判型一次，内层花括号只更新深度；解析器升至`generic-labelled-v0.2.103`。
- 调用次数回归先失败后通过，解码次数降为 **1**；性能/词法定向 **8 passed**，collection parser/service **329 passed**，全量离线pytest **808 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。配置无变化。
- 下一轮继续P0-03对有界HTML输入下的解析时间/内存热点审计；用确定性复杂度回归证明线性或有界增长，并跑定向及全量离线测试。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。

## 2026-11-11 P0-03覆盖嵌套CSS与转义属性组合
- 扩展样式表门禁回归，验证嵌套`@media`中的转义`display`属性，以及自定义属性花括号块之后继续出现的嵌套真实隐藏规则；前者必须识别为可见性未决，后者不能被自定义属性块状态吞掉。应用实现与解析器版本`generic-labelled-v0.2.102`不变。
- CSS词法组合定向 **16 passed**，collection parser/service **328 passed**，全量离线pytest **807 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。配置无变化。下一轮继续P0-03词法边界验证；真实页面准确率仍待获准样本与人工标注，P0-01真实V0.1备份及P0-02来源材料仍缺。

## 2026-11-11 P0-03区分嵌套自定义属性块与样式规则
- 失败回归复现：CSS自定义属性允许花括号块值；`--label:{display:none;}`中的`display:none`不是实际声明，却被规则分段器误报。现在自定义属性值花括号块内不再按声明分段；另加嵌套`@media`与`@supports`正例，确保其中真实可见性声明仍触发复核。解析器升至`generic-labelled-v0.2.102`。
- 自定义属性与嵌套规则词法回归 **14 passed**；collection parser/service **326 passed**；全量离线pytest **805 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。配置无变化。
- 下一轮继续P0-03 CSS转义token与嵌套声明边界审计；验收要求具体漏报/误报先由回归复现，再通过定向和全量离线测试。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。

## 2026-11-11 P0-03区分CSS声明与自定义属性文本
- 失败回归复现：样式表扫描把自定义属性`--display:none`及`--label:display:none`中的词元误识别为实际`display`声明，即使这些变量未使用也会阻止有效候选审核。现仅按规则块内声明起始位置识别可见性属性和`@import`，并避开注释、引号字符串及函数/属性选择器内部的分隔符。
- 两项自定义属性误报回归先失败后通过；CSS词法/样式表定向 **18 passed**，collection parser/service **323 passed**，全量离线pytest **802 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。配置无变化。
- 下一轮继续P0-03 CSS词法边界审计；验收要求新增漏报/误报回归先证明问题，再通过定向与全量离线测试。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。

## 2026-11-11 P0-03忽略CSS字符串中的伪可见性声明
- 失败回归复现：样式表扫描直接对CSS原文做正则搜索，会把`content:"display:none"`和`content:"@import"`中的字符串误判为样式规则/外部导入，造成无需人工复核的候选被拦截。现扫描前跳过CSS注释与引号字符串，再解码并检查真实声明；解析器升至`generic-labelled-v0.2.101`。
- 两种字符串误报回归先失败后通过，且既有转义属性、活动`@import`、遮罩及惰性内容用例通过；CSS字符串/样式表定向 **13 passed**，collection parser/service **321 passed**，全量离线pytest **800 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。配置无变化。
- 下一轮继续P0-03 CSS token/selector边界审计，寻找会把有效声明漏掉或误报的具体输入；验收要求回归先复现、再通过定向和全量离线测试。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。

## 2026-11-11 P0-03识别CSS遮罩造成的未知文本可见性
- 失败回归复现：`mask-image:linear-gradient(transparent,transparent)`及`-webkit-mask`可使推荐报价完全透明，但解析器此前未添加可见性告警。现在内联标准/WebKit mask及活动样式表mask声明触发人工复核；解析器升至`generic-labelled-v0.2.99`。
- 三项遮罩回归先失败后通过；遮罩/样式表定向 **10 passed**，collection parser/service **319 passed**，全量离线pytest **798 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。配置无变化。
- 下一轮继续P0-03视觉裁剪/遮罩类属性边界审计；验收要求先由失败回归证明漏判，再使定向与全量离线测试通过。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。

## 2026-11-11 P0-03识别CSS裁剪造成的未知文本可见性
- 失败回归复现：`clip-path:inset(100%)`可将推荐报价完整裁出视口，但解析器既未移除该文本，也未给候选可见性告警。现在内联`clip`/`clip-path`声明及活动`<style>`中的同类规则触发人工复核告警；解析器升至`generic-labelled-v0.2.98`。
- 两项裁剪回归先失败后通过；裁剪/样式表定向 **7 passed**，collection parser/service **316 passed**，全量离线pytest **795 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。配置无变化。
- 下一轮优先继续P0-03对CSS裁剪/遮罩类可见性属性的离线边界审计；以复现测试和定向、全量离线测试通过作为验收。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。

## 2026-11-11 P0-03排除noscript惰性样式表
- 失败回归复现：`<noscript>`内的`<style>`和`rel="stylesheet"`会触发`unresolved_stylesheet_visibility`，尽管当前解析器随后移除整个noscript子树。样式表门禁现与文本提取的惰性内容处理一致，跳过template及noscript后代；解析器升至`generic-labelled-v0.2.97`。
- 新增两种noscript回归均先失败后通过；样式表/noscript定向 **9 passed**，collection parser/service **314 passed**，全量离线pytest **793 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。
- 配置/迁移：无变化。下一轮优先继续P0-03惰性/非文档节点的字段证据边界回归；验收标准为新增用例先复现差异、定向及全量离线套件通过，并继续保持在线采集关闭。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。

## 2026-11-11 P0-03忽略惰性template中的样式表
- 失败回归复现：样式表门禁在移除`<template>`前扫描整棵DOM，模板中的`<style>`和`rel="stylesheet"`属于惰性内容，却让当前文档候选误报可见性未决。现在忽略template后代中的样式块与链接，仅对当前文档样式表生效；解析器升至`generic-labelled-v0.2.96`。
- 两项模板误报回归先失败后通过，仍覆盖活动`<style>`、转义属性、`@import`和外部样式链接；样式表门禁定向 **7 passed**，collection parser/service **312 passed**，全量离线pytest **791 passed、22 skipped、23 subtests passed**，1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。

## 2026-11-11 P0-03覆盖转义形式的CSS @import
- 扩展样式表可见性回归，新增转义at-rule`@\69 mport`案例，确认解码后仍触发`unresolved_stylesheet_visibility`并阻止审核就绪；解析器实现及版本`generic-labelled-v0.2.95`不变。
- 样式表可见性定向 **5 passed**，collection parser/service **310 passed**，全量离线pytest **789 passed、22 skipped、23 subtests passed**，1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。

## 2026-11-11 P0-03将CSS @import纳入样式表可见性门禁
- 失败回归复现：内嵌`<style>@import url(...)</style>`可加载外部规则，当前样式表扫描只识别直接可见性声明，忽略`@import`，因此隐藏推荐报价仍可能让候选误报ready。现识别`@import`并追加`unresolved_stylesheet_visibility`；解析器升至`generic-labelled-v0.2.95`。
- @import失败回归先失败后通过；collection parser/service **309 passed**，全量离线pytest **788 passed、22 skipped、23 subtests passed**，1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。

## 2026-11-11 P0-03识别内嵌样式表中的CSS转义可见性属性
- 失败回归复现：上一轮样式表门禁只查字面属性名，漏掉合法转义写法`d\69 splay:none`，隐藏推荐报价仍可能让候选误报ready。现在先移除CSS注释并解码样式块内属性名，再检查`display`、`opacity`、`visibility`与`content-visibility`；解析器升至`generic-labelled-v0.2.94`。
- 转义属性样式块回归先失败后通过；collection parser/service **308 passed**，全量离线pytest **787 passed、22 skipped、23 subtests passed**，1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。

## 2026-11-11 P0-03标记样式表可见性未知的候选
- 失败回归复现：`<style>`规则或`rel="stylesheet"`外部样式表可隐藏推荐报价，但静态解析器只看内联样式；同价隐藏报价不产生冲突，候选可能误报ready。现在检查样式表来源：内嵌CSS含`display`/`opacity`/`visibility`/`content-visibility`声明，或HTML引用任一外部样式表时，添加`unresolved_stylesheet_visibility`、保留文本证据并阻止ready；外部样式不会联网获取。解析器升至`generic-labelled-v0.2.93`。
- 两种样式表失败回归先失败后通过；collection parser/service **307 passed**，全量离线pytest **786 passed、22 skipped、23 subtests passed**，1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。

## 2026-11-11 P0-03避免将opacity中的转义符号重解释为CSS语法
- 失败回归复现：CSS转义括号`opacity:calc\(0\)`属于标识符内容，不构成`calc()`函数；统一解码转义后却把它错误当作透明函数并移除可见文本。现将opacity中的转义数学运算符/分隔符视为不确定声明，不以其计算隐藏，并输出`unresolved_inline_visibility`。解析器升至`generic-labelled-v0.2.92`。
- 新增失败回归先失败后通过；CSS/可见性定向 **14 passed**，collection parser/service **304 passed**，全量离线pytest **783 passed、22 skipped、23 subtests passed**，1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。

## 2026-11-11 P0-03将content-visibility:auto标为需人工复核
- 失败回归复现：`content-visibility:auto`会随用户相关性动态跳过或显示子树；从静态HTML无法得知页面视口/跳过状态。旧解析器保留其文字却未发告警，同价推荐内容可让候选保持可审核。现保留文本证据、增加`unresolved_inline_visibility`告警并阻止ready；解析器升至`generic-labelled-v0.2.91`。参考[W3C CSS Containment Level 2](https://www.w3.org/TR/css-contain-2/#propdef-content-visibility)。
- 新增回归先失败后通过；content-visibility/变量定向 **9 passed**，collection parser/service **303 passed**，全量离线pytest **782 passed、22 skipped、23 subtests passed**，1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。

## 2026-11-11 P0-03避免把转义数字标识符当作opacity数值
- 失败回归复现：`opacity:\30`与`opacity:calc(\30)`中的CSS转义数字在CSS tokenization中是标识符，不是数值；解码后直接按opacity求值会误判为0并移除可见内容。现对带转义十六进制数字且无`var()`的opacity声明保守忽略，不将其作为隐藏条件；解析器升至`generic-labelled-v0.2.90`。
- 两种裸值/`calc()`失败回归先失败后通过；CSS转义/变量/优先级定向 **14 passed**，collection parser/service **302 passed**，全量离线pytest **781 passed、22 skipped、23 subtests passed**，1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。

## 2026-11-11 P0-03仅在CSS顶层识别!important
- 失败回归复现：`display:var(--hidden, none!important)`中的`!important`位于函数参数内，不应作为声明优先级；旧解析器按字符串首个`!`截断，漏掉未解析的`var()`并让候选保持可审核。现按函数/块括号层级和引号识别顶层`!`，并跳过转义字符；解析器升至`generic-labelled-v0.2.89`。
- 新增失败回归先失败后通过；可见性/级联定向 **17 passed**，collection parser/service **300 passed**，全量离线pytest **779 passed、22 skipped、23 subtests passed**，1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。

## 2026-11-11 P0-03识别转义的CSS重要优先级
- 失败回归复现：`!important`关键字本身也可含CSS转义；旧解析器将`display:none !impor\74 ant`当成无效优先级，错误保留前序`display:block`，隐藏推荐报价会进入挂牌文本。现在对`!`后的优先级标记也解码CSS转义；解析器升至`generic-labelled-v0.2.88`。
- 新增优先级失败回归先失败后通过；CSS转义专项 **6 passed**，collection parser/service **299 passed**，全量离线pytest **778 passed、22 skipped、23 subtests passed**，1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。

## 2026-11-11 P0-03解码CSS转义后的可见性声明
- 失败回归复现：CSS转义可写隐藏属性/值及`var()`函数名，如`d\69 splay:none`、`display:n\6f ne`、`v\69 sibility:hidden`和`v\61 r(...)`。旧解析器忽略转义后仍可能把隐藏推荐报价读入文本，或未给未解析可见性告警。现先解码CSS标识符转义，再识别属性、隐藏值与变量函数；解析器升至`generic-labelled-v0.2.87`。
- 三项失败回归先失败后通过，新增五种转义声明/函数覆盖；collection parser/service定向 **298 passed**，全量离线pytest **777 passed、22 skipped、23 subtests passed**，1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。

## 2026-11-11 P0-03服务层持久化未解析可见性告警
- 增加`stage_html`回归，确认`unresolved_inline_visibility`写入候选告警，候选仍为`pending`且`ready_for_review=false`；实现逻辑和解析器版本`generic-labelled-v0.2.86`不变。
- 定向collection service/parser **293 passed**；全量离线pytest **772 passed、22 skipped、23 subtests passed**，1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- 仅合成HTML、Mock持久化与离线测试；未连接来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标签。下一轮继续P0-03离线回归；真实样本到位后执行标注集评估。

## 2026-11-11 P0-03标记未解析的内联CSS变量可见性
- 失败回归复现：内联`display`、`opacity`、`visibility`、`content-visibility`中的`var()`可能计算为隐藏，但解析器会把未知计算结果静默当作可见；即使隐藏推荐价格与挂牌价相同、未产生冲突，也可能错误标记候选可审核。现在保留原文及证据，追加`unresolved_inline_visibility`警告，并阻止`ready_for_review`。解析器升至`generic-labelled-v0.2.86`。
- 五种普通/嵌套`var()`可见性场景回归先失败后通过；解析器专项 **264 passed**，全量离线pytest **771 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标注。

## 2026-11-11 P0-03核验复合楼层值的证据契约
- 为`楼层：高楼层 14/18层`增加字段证据断言：解析字段值、`field_evidence.value`、首条候选值均完整保留复合楼层，证据摘录与`楼层：高楼层 14/18层`逐字一致；未改解析器实现或版本。
- 解析器定向1 passed；完整离线pytest **766 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅离线合成HTML；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标签。

## 2026-11-11 P0-03将顿号作为楼层/装修终止符
- 失败回归复现：楼层/装修自由文本捕获已改为跨空格读取，但漏掉顿号`、`终止符，导致`楼层：高楼层、装修：精装`把顿号保留在楼层值内。现将顿号加入捕获字符排除集及结束边界。解析器升至`generic-labelled-v0.2.85`。
- 顿号边界端到端回归先失败后通过；解析器专项 **259 passed**，全量离线pytest **766 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML与离线测试；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标签；下轮继续P0-03离线缺陷复现。

## 2026-11-11 P0-03保留楼层值中的比例与空格
- 失败回归复现：`楼层：高楼层 14/18层 装修：精装`被按第一个空格截成“高楼层”，丢失所在/总楼层信息。楼层和装修值现保留内部空格与比例斜杠，仅在标点、下一个已识别字段标签或文本末尾结束；捕获上限与API模型一致为120字符。解析器升至`generic-labelled-v0.2.84`。
- 复合楼层值、紧邻装修标签和超过20字符值回归通过；解析器专项 **258 passed**，全量离线pytest **765 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML与离线测试；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标签；下轮继续P0-03离线缺陷复现。

## 2026-11-11 P0-03分隔相邻楼层与装修字段
- 失败回归复现：行内标签紧贴时`楼层：高楼层装修：精装`会把“装修”并进楼层值。楼层/装修提取现于已识别的后续标签处停止，并将捕获上限从20对齐到API模型允许的120字符，避免截断合法较长描述。解析器升至`generic-labelled-v0.2.83`。
- 相邻标签和超过20字符的楼层/装修值回归通过；解析器专项 **257 passed**，全量离线pytest **764 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML与离线测试；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标签；下轮继续P0-03离线缺陷复现。

## 2026-11-11 P0-03识别相邻的重复小区标签
- 失败回归复现：`小区：东湖花园<span>小区：</span><span>锦港府</span>`行内文本紧贴时，社区正则要求标签前有空格/标点，漏掉第二个显式社区值并错误采用第一个。社区标签现可在连续文本中识别；多个不同社区值按歧义规则留空并告警。与上一轮相邻字段标签修复一起，解析器升至`generic-labelled-v0.2.82`。
- 两个相邻标签场景及29/181字符边界专项 **4 passed**；解析器专项 **255 passed**，全量离线pytest **762 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML与离线测试；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标签；下轮继续P0-03离线缺陷复现。

## 2026-11-11 P0-03分开相邻行内小区名与字段标签
- 失败回归复现：行内标签跨`span`紧贴时，`小区：东湖花园建筑面积：160㎡`被解析成小区名“东湖花园建筑面积”。现在社区字段捕获在已识别的后续挂牌字段标签处停止；同时保留最多180字符的完整名称，并要求名称在分隔符/字段标签处闭合，超限时不截断。解析器升至`generic-labelled-v0.2.81`。
- 相邻行内标签、29字符名称完整保留、181字符名称拒绝截断的回归先失败后通过；解析器专项 **254 passed**，全量离线pytest **761 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML与离线测试；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标签；下轮继续P0-03离线缺陷复现。

## 2026-11-11 P0-03按模型上限完整提取小区名
- 失败回归复现：小区名正则最多保留28个字符，会把更长但有效的名称静默截断；接口模型允许`community_name`最多180字符。现提取上限对齐到180，并要求字段值在明确分隔符或文本结束处闭合，超过模型上限时留空而不接受前缀。解析器升至`generic-labelled-v0.2.80`。
- 29字符名称完整保留、181字符名称不截断的边界回归先失败后通过；解析器专项 **253 passed**，全量离线pytest **760 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML与离线测试；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标签；下轮继续P0-03离线缺陷复现。

## 2026-11-11 P0-03识别opacity尾随小数点
- 失败回归复现：CSS opacity数值允许`0.`形式；裸值校验器却拒绝`opacity:0.`和`opacity:0.%`，导致透明广告报价进入挂牌字段冲突。数值语法现与受限`calc()`求值语法一致，接受数字后有小数点但小数部分为空的有效数值。解析器升至`generic-labelled-v0.2.79`。
- 两条端到端可见性回归先失败后通过；解析器专项 **251 passed**，全量离线pytest **758 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML与离线测试；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标签；下轮继续P0-03离线缺陷复现。

## 2026-11-11 P0-03严格识别opacity百分比token
- 失败回归复现：`opacity:0;opacity:1 %`中的数字与`%`之间有空格，CSS不构成有效百分比token；旧校验器去掉`%`并再次trim，错误地用无效声明覆盖透明值，隐藏广告总价进入候选。现在opacity接受百分比时要求数字紧邻`%`。解析器升至`generic-labelled-v0.2.78`。
- 端到端回归先失败后通过；解析器专项 **249 passed**，全量离线pytest **756 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML与离线测试；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标签；下轮继续P0-03离线缺陷复现。

## 2026-11-11 P0-03忽略畸形!important级联声明
- 失败回归复现：`display:block;display:none!important bogus`和`opacity:1;opacity:0!important bogus`把前一条合法声明错误覆盖，导致实际挂牌字段丢失。CSS优先级标记若包含`!`但后续不是完整`important`，现整条声明在进入属性值校验与级联前忽略。解析器升至`generic-labelled-v0.2.77`。
- 两条端到端回归先失败后通过；解析器专项 **248 passed**，全量离线pytest **755 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标状态JSON、空白检查和开发包清单校验通过。仅合成HTML与离线测试；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标签；下轮继续P0-03离线缺陷复现。

## 2026-11-11 P0-03忽略无效内联CSS级联声明
- 失败回归复现：`display:none;display:bogus`让隐藏报价变为可见，`opacity:0;opacity:bogus`也会覆盖透明声明。级联现在先按所用属性校验内联值，只让有效声明参与顺序与`!important`选择；覆盖`display`、`opacity`、`visibility`和`content-visibility`。解析器升至`generic-labelled-v0.2.76`。
- 回归先失败后通过；解析器专项 **246 passed**，全量离线pytest **753 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未配置`TEST_DATABASE_URL`跳过。
- 仅合成样式/HTML与离线测试；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标签。下轮继续P0-03离线缺陷复现；实页面样本到位后再按验收指标评估。

## 2026-11-11 P0-03识别opacity的CSS min/max/clamp函数
- 失败回归复现：合法的`opacity:min(0, 1)`、`max(0, 0)`、`clamp(0, 0, 1)`仍让透明内容参与挂牌字段抽取。受限AST求值器现加入这三个函数的定参求值，并允许它们嵌套在`calc()`算术中；仅计算纯数值，不调用任意函数。未知函数、单位、错误参数和超长表达式仍拒绝推断。解析器升至`generic-labelled-v0.2.75`。
- 失败先复现后通过；opacity级联/表达式专项**24 passed**。完整离线pytest **748 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告；22项数据库集成需`TEST_DATABASE_URL`而跳过。
- Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。仅合成HTML验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标签。

## 2026-11-11 P0-03安全计算opacity的CSS calc()表达式
- 延续上一轮发现的缺口：透明度表达式`calc(1 - 1)`和`calc(0% + 0%)`仍让隐藏报价进入可见文本。现在以Python AST解析算术语法，但仅求值十进制常量、百分比、括号、单目正负及加减乘除；不执行表达式。表达式限256字符/128 AST节点；未知CSS函数、单位及除零不推断。解析器升至`generic-labelled-v0.2.74`。
- 回归先失败后通过，覆盖零结果/正结果、百分比、嵌套括号、四则运算、未知函数、除零和超长输入。opacity/边界专项**19 passed**；完整离线pytest **743 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成需`TEST_DATABASE_URL`而跳过。
- Python 3.12 compileall、GOAL_STATE JSON与`git diff --check`通过。仅合成HTML，未访问来源网站/NAS或生产数据库，无迁移/部署；真实页面准确率仍待许可样本和人工标注。

## 2026-11-11 P0-03识别CSS opacity的calc数值字面量
- 失败回归复现：可见性过滤器只接受裸数值/百分比，`opacity:calc(0)`会把浏览器实际完全透明的挂牌价当可见文本，污染总价并产生错误冲突。现在识别`calc(...)`中的单个数值字面量，再复用原有十进制与百分比判断；不把算术表达式猜成数值。解析器版本升至`generic-labelled-v0.2.73`。
- 新增零值/百分比隐藏与正值保留回归；失败先复现后修复。opacity级联专项**11 passed**；完整离线pytest **735 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成需`TEST_DATABASE_URL`而跳过。
- Python 3.12 compileall、GOAL_STATE JSON与`git diff --check`通过。只用合成HTML；未访问网站、NAS或生产数据库，无迁移/部署。真实页面字段准确率仍待获准样本与人工标注。

## 2026-11-11 P0-03/P0-04恢复Python 3.12完整离线回归
- 使用已有uv离线wheel缓存，并显式指定Python 3.12：`uv run --offline --cache-dir /private/tmp/ningbo-uv-cache --python 3.12 --with-requirements requirements-dev.txt -- python -m pytest -q`，当前工作区**732 passed、22 skipped、23 subtests passed**，1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- 首次不指定解释器时uv选择系统Python 3.9，测试收集因`X | None`语法报错；固定3.12后全套通过。许可门禁重写为unittest后仍由完整pytest发现，六种条件在23个subtests统计中覆盖。
- Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。此为离线合成/Mock测试，不代表真实来源准确率、NAS PG17当前快照或生产验收。

## 2026-11-11 P0-03解析器复验环境可用性检查
- 为在本机无pytest环境补做解析器回归，检查NAS `ningbo-re-ai-api:latest`运行镜像：FastAPI、Pydantic、psycopg、BeautifulSoup和httpx可导入，但pytest不存在；因此该运行镜像不能直接执行项目pytest套件。
- 用户此前授权的`notedock-nas`身份和Compose只读盘点已成功，但后续SSH复用socket不可用、直连别名DNS解析失败；源码包传输在建立连接前失败，没有创建远程文件或测试容器。未切换未经验证的IP/通道。
- 本轮无代码或生产状态修改；未读取业务数据/凭据、未连接生产数据库、未部署。解析器专项和完整数据库集成待恢复可用测试环境后执行；真实样本缺口仍在。

## 2026-11-11 P0-07 NAS当前运行态只读复核
- 按`nas-ssh-connect`技能优先试`nas-lan`，连接`10.10.10.7:22222`超时；Tailscale CLI无法读取偏好且本机没有Tailscale App；复用此前授权的`notedock-nas`完成SSH身份核验，返回`DXP4800`、用户`sheng`、属于`docker`组。
- `docker compose ps`只读显示API与Worker容器运行、PostgreSQL 17 healthy；API端口仍仅绑定`127.0.0.1:8788`。尝试读取迁移schema时SSH复用套接字权限受限，禁用复用后的别名解析`300858.xyz`失败，未获得schema核验结果；没有继续切换通道。
- 未读取业务行、环境变量/凭据、未创建备份、运行迁移、改容器/Compose/数据卷或部署。现有生产schema差异结论仍以此前成功查询为准，本轮未能更新其状态。

## 2026-11-11 P0-04许可门禁回归可脱离pytest运行
- `may_fetch_online`为纯标准库权限门禁；将原pytest参数化测试改为标准库`unittest`，保留六种组合（总开关关闭、来源开关关闭、状态未批准、许可引用缺失/空白及完整批准），以便在当前无pytest/业务依赖环境中直接复验。未改权限逻辑。
- 专项**1 passed、6 subtests passed**；标准库套件42 passed，Python 3.12 compileall与`git diff --check`通过。完整pytest仍因未安装pytest未运行，数据库集成仍因本地依赖和Docker daemon不可用未运行。
- 没有开启在线采集、访问NAS/来源网站/生产数据库或部署。此门禁单测不替代平台书面许可和端到端网络阻断验收。

## 2026-11-11 P0-03当前离线回归可复验范围
- 按目标续开发流程复核当前工作区。`python3.12 -m pytest -q`无法启动（Python 3.12未安装pytest）；`uv run --offline`初始化用户缓存时被系统拒绝访问；Docker daemon不可用，故本轮不能重跑完整pytest或数据库集成。
- 当前快照可复验项：`python3.12 -m unittest discover -s tests -p '*_stdlib.py' -v` **42 passed**；Python 3.12 `compileall`通过。上轮完整离线pytest737 passed/22 skipped/17 subtests属于上一快照，不作为本轮重跑结果。
- 未改应用代码、未访问NAS/生产数据库/来源网站、未部署。继续P0-03离线开发；真实获准页面与人工标注仍缺。

## 2026-11-11 P0-03锁定缺失字段误报对精确率的影响
- 审计`evaluate_parser.py`对准确率、覆盖率和精确率的分母：标注为缺失的字段仍计入标注数；解析器若输出非空值，会作为错误覆盖计入精确率分母，缺字段场景也判失败。新增回归注入一个错误面积值，确认5条标注中4条正确、覆盖率100%、精确率80%，且缺字段场景未通过。
- 定向测试**1 passed**；完整离线pytest：**737 passed、22 skipped、17 subtests passed**，22项数据库集成因未配置`TEST_DATABASE_URL`跳过。仅评估器逻辑回归，没有实现改动或数据库变化。
- compileall、GOAL_STATE JSON及变更文件尾随空白扫描通过。仅虚构样本与桩化结果验证，不产生真实页面准确率；来源网页、许可和人工标签仍待补齐。

## 2026-11-11 P0-03修复折叠摘要内联字段文本断裂
- 失败回归复现：折叠`details`中的`summary`含多个内联`span`时，`get_text(' ')`会在每个节点间插入空格，破坏“小区/总价”等标签和值。现摘要文本改用解析器已有的行内/块级边界遍历后折叠空白，保留相邻行内片段，同时仍排除折叠详情主体与隐藏摘要文本；解析器版本升至`generic-labelled-v0.2.72`。
- 回归先失败后通过；摘要/隐藏内容定向测试**8 passed**。完整离线pytest：**736 passed、22 skipped、17 subtests passed**，22项数据库集成因未配置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON与`git diff --check`通过。仅合成HTML验证；未读取来源网站或NAS、无数据库迁移/部署。P0-03真实准确率仍待获准样本与人工标注。
- 下一步：继续在合成样本上覆盖解析边界；收到真实授权页面后再评估字段准确率与覆盖率。

## 2026-11-11 P0-07补齐V0.2基线升级回归
- 新增`test_v02_baseline_migration_preserves_collection_data_and_parse_metrics`：以001–005和合成挂牌、采集目标/运行/候选、条件单作为起点，执行006–010；写入发现游标、挂牌观察/核验结论及解析事件后再次执行006–010，并逐字段核对旧数据、新记录与健康计数`2/1/1`均保留且不重复。
- NAS隔离PostgreSQL 17上的完整`tests/test_db_integration.py`：**23 passed**，保留1条Starlette/httpx测试客户端弃用警告。测试schema残留0；临时数据库容器、网络及传输目录已清理。
- 当前工作区完整离线pytest：**735 passed、22 skipped、17 subtests passed**；22项数据库集成因未配置`TEST_DATABASE_URL`跳过。Python 3.12 compileall、GOAL_STATE JSON及变更文件尾随空白扫描通过。
- 测试仅用合成数据，在独立临时Docker网络和tmpfs PostgreSQL中运行；源码只读挂载。未连接生产数据库、未读取业务行、未备份/迁移/部署或改动生产服务、Compose和数据卷。P0-07继续`in_progress`：生产缺迁移006–010，且当前生产代码与工作区不一致；生产变更仍须新鲜备份及单独授权评估。
- 下一步：继续无需真实页面/许可/旧备份的离线P0工作；不将该合成PG17回归等同生产升级或V0.1恢复验收。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-pg17-v02-baseline-regression.zip`。

## 2026-11-11 P0-09策略撤销前置时保留空详情进度
- 失败回归复现：列表页已存档并识别挂牌后、首个详情请求前来源许可撤销，旧分支仅在已有详情候选成功暂存时才保存状态，导致零暂存路径丢失活动遍历号和重试游标。现任何详情级策略阻断均保存当前列表页游标、扫描轮次/活动状态及列表页已观察ID；详情仍未暂存，不计为成功详情或完整遍历。
- 定向分页/发现/状态测试 **78 passed、7 subtests passed**；全量离线pytest **734 passed、21 skipped、17 subtests passed**；标准库42 passed，compileall通过。新增PG集成回归验证数据库状态保存，但因未设置`TEST_DATABASE_URL`跳过。
- 无迁移、无API契约变化。仅Mock/离线验证；未访问NAS、生产数据库或房源网站，未部署。P0-09仍待许可、获准真实分页样本及NAS PG17/生产差异验收。

## 2026-11-11 P2-02精确比较跨平台10%单价门槛
- 失败回归复现：挂牌价100/110万元、面积均7㎡时，两个单价分别为循环小数；逐个除面积后再求百分比在Decimal上下文中得到略低于10%，误漏掉用户确认应纳入的边界候选。现在用原始Decimal价格和面积交叉相乘精确比较门槛，通过后再计算展示比例。
- 回归先失败后通过；`tests/test_opportunities.py` **21 passed**，全量离线pytest **734 passed、20 skipped、17 subtests passed**；标准库42 passed、compileall通过。数据库集成20项因未设置`TEST_DATABASE_URL`跳过。
- 面积≤5%现仍沿用代码中的对称较小面积作分母；该公式尚未由用户明确确认，已提出澄清，收到回复前不更改。无数据库迁移；未访问NAS、生产数据库或房源网站，未部署。

## 2026-11-11 P0-03按CSS相邻盒规则解析 `display: run-in`
- 上轮将run-in一律按块级边界处理，虽阻止误拼接，却会漏掉run-in应并入后继块级内容的有效标签。现按相邻同级run-in序列及后继普通块判断；遇到行内内容或建立独立格式上下文的块则保留边界。解析器升至`generic-labelled-v0.2.71`。
- 回归覆盖单个/连续run-in、后继普通块、前置行内文本和`flow-root`；显示边界专项17 passed，全量离线pytest **733 passed、20 skipped、17 subtests passed**；标准库42 passed，compileall通过。20项DB集成未设置`TEST_DATABASE_URL`而跳过。
- 依据CSS Display 3的run-in布局规则；仅合成HTML验证。NAS LAN、已授权`notedock-nas`公网连接均超时，本机未安装Tailscale应用，P0-07的NAS PG17核验未执行；未访问生产数据库或房源网站，未部署。

## 2026-11-11 P0-03将CSS `display: run-in`作为保守文本边界
- 失败回归复现：`display:run-in`被解析为行内文本，`<div>/<span>小</...><span>区：东湖花园</span>`误拼成小区名。因run-in的CSS排版取决于相邻盒子，通用HTML解析器没有布局树，现对文本提取保守按块级边界处理；不更改用于可见性级联的显示值分类。解析器升至`generic-labelled-v0.2.70`。
- 显示边界专项13 passed；全量离线pytest **729 passed、20 skipped、17 subtests passed**；标准库42 passed，compileall、备份脚本语法通过。20项数据库集成因未设置`TEST_DATABASE_URL`跳过；保留1条Starlette/httpx弃用警告。
- 仅合成HTML验证，未访问NAS、数据库或房源网站，未部署。真实页面准确率仍待每站获准样本及人工标注；P0-07健康率口径已按用户确认并通过离线PG16验证，NAS PG17验收仍待执行。

## 2026-11-11 P0-03修正CSS `display: flow`文本边界
- 失败回归复现：解析器把`display:flow`误归为行内显示，将`小`和后续`区：东湖花园`跨块拼接成社区字段。现在把单关键字`flow`归入块级文本显示；`inline flow`仍按行内显示，解析器版本升至`generic-labelled-v0.2.69`。
- 回归先失败后通过：显示边界专项26 passed、解析器专项218 passed；全量离线pytest **727 passed、20 skipped、17 subtests passed**。标准库42 passed，compileall、备份脚本语法、GOAL_STATE JSON及`git diff --check`通过；保留1条Starlette/httpx弃用警告。20项数据库集成因未配置`TEST_DATABASE_URL`跳过。
- 仅合成HTML验证；真实页面准确率仍需获准样本与人工标注。未访问NAS、数据库或房源网站，未部署。

## 2026-11-11 P0-02防止样本HTML跨来源重复计数
- 失败回归复现：5份贝壳HTML逐份复制到安居客路径并更换清单URL/哈希后，旧校验器仍分别计数5份，导致同一批内容可虚增两站样本覆盖。现按解压后的HTML内容在整个样本清单内去重；gzip头不同不影响内容身份，跨源重复一律拒绝。
- 样本集/解析评估定向 **131 passed**；全量离线pytest **726 passed、20 skipped、17 subtests passed**。标准库42 passed、compileall及备份脚本语法通过，保留1条Starlette/httpx弃用警告；20项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- 仅本地合成样本验证。未访问NAS、生产数据库或房源网站，未部署；P0-02仍缺真实获准页面、许可范围及人工标注。

## 2026-11-11 P0-03修复H1内联节点标题空格污染
- 失败回归复现：`<h1>东湖<span>花</span><em>园</em> 3室</h1>`被`get_text(' ')`解析为“东湖 花 园 3室”，低估标题字段准确度。H1现复用解析器的行内连续/块级分隔文本遍历，再折叠空白；标题变为“东湖花园 3室”。解析器版本升至`generic-labelled-v0.2.68`。
- 标题专项10 passed，解析器专项217 passed；全量离线pytest **725 passed、20 skipped、17 subtests passed**。标准库42 passed，compileall及备份脚本语法通过，保留1条Starlette/httpx弃用警告。数据库集成20项因未设置`TEST_DATABASE_URL`跳过。
- 仅合成HTML回归；真实页面准确率仍需每站获准样本和人工标注。未访问NAS、数据库或房源网站，未部署。

## 2026-11-11 P0-02重复CSV表头检测改为线性
- 受2 MB清单上限保护后，仍发现重复列诊断对每个字段调用`list.count`，复杂度为O(n²)。失败路径微基准：20万字节、10万个重复列名耗时3.565秒；现单次遍历收集重复列，结果排序和诊断内容保持一致，同输入耗时0.0036秒。
- 新增回归确保重复检测不调用全表扫描，保持重复列集合诊断。全量离线pytest **724 passed、20 skipped、17 subtests passed**；标准库42 passed，compileall和备份脚本语法通过。20项数据库集成缺`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 未访问NAS、生产数据库或房源网站，未部署。P0-02仍缺真实获准页面、许可和标注。

## 2026-11-11 P0-02为样本清单校验器增加有界读取
- 失败回归复现独立校验CLI无清单大小上限：超过评估器既定2,000,000字节的CSV（以空白行填充）仍被接受。现在`validate_sample_set.py`在解析前最多读取上限+1字节并拒绝超限；边界测试确认恰好2,000,000字节有效、超限明确报错。评估器和校验器共用同一常量。
- 清单/评估定向 **48 passed**；全量离线pytest **723 passed、20 skipped、17 subtests passed**，20项数据库集成因未设置`TEST_DATABASE_URL`跳过。标准库42 passed；compileall及`bash -n scripts/backup.sh`通过，保留1条Starlette/httpx弃用警告。
- 未连接NAS、生产数据库或房源网站，未部署。P0-02仍缺真实获准页面/许可范围/人工标签，工具通过不代表样本验收。

## 2026-11-11 P0-03来源身份边界复核与当前离线套件复验
- 复核`canonical`/`og:url`来源ID路径：解析时已调用来源专用ID提取器，而提取器先通过共享URL策略校验HTTPS及宁波白名单主机；跨域链接被拒绝，原先怀疑的问题无法复现，因此没有保留无效测试或改动解析器。
- 当前完整离线`pytest -q`：**721 passed、20 skipped、17 subtests passed**；20项数据库集成测试因`TEST_DATABASE_URL`未设置而跳过。Docker API socket返回permission denied，未运行PG集成。
- 标准库测试**42 passed**；Python 3.12 `compileall`、备份脚本`bash -n`、GOAL_STATE JSON解析与`git diff --check`通过。保留1条Starlette/httpx弃用警告。
- 未访问NAS、生产数据库或房源网站，未部署；P0-03仍需获准真实样本与人工标签，不能由合成套件证明真实页面准确率。下轮仅在离线输入上先复现实际缺陷再改解析器。

## 2026-11-11 P0-07落实四项健康率与解析阶段记录
- 按用户确认的累计口径实现：采集成功率=success/(success+failed)，blocked排除；解析成功率=解析器成功返回/成功获取且进入解析器的页面；字段完整率=来源挂牌ID、小区、总价、面积均非空的成功解析结果/成功解析结果；审核通过率=approved/(approved+rejected)，pending排除。百分比保留两位小数，分母为0返回null。
- 新增迁移010、collection_parse_attempts追加记录及触发器计数；记录manual_html_snapshot和public_page_collection采集方式。健康API按来源返回四项累计比率和阶段计数。解析警告/字段缺失不算解析失败；完整率按解析初始结果计算。
- 变更文件：app/collection_service.py、sql/010_collection_parse_metrics.sql、docker-compose.yml、tests/test_collection_health.py、tests/test_collection_service.py、tests/test_db_integration.py、迁移静态测试及API/验收/部署文档。
- PG16全量pytest 741 passed、0 skipped、17 subtests passed；含21项数据库集成。健康/服务定向30 passed，标准库42 passed。Python 3.12 compileall、GOAL_STATE JSON、备份脚本语法、迁移顺序静态检查、git diff --check和安全开发包校验通过；保留1条Starlette/httpx弃用警告。
- 临时PG16使用tmpfs和127.0.0.1绑定，已清理。仅离线源码、文档和迁移修改；未访问NAS、生产数据库或房源网站，未部署。P0-07仍需隔离NAS PG17及生产版本差异验收。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-07-health-rates-pg16.zip`。

## 2026-11-11 P0-09复核历史跨失联周期留存回归
- 扩展`tests/test_db_integration.py`：挂牌记录经首次人工结论后重新出现，再连续两轮完整遍历缺失并追加第二条复核结论；分页历史返回两条记录，正式挂牌状态仍为`available`。
- PostgreSQL 16数据库集成 **20 passed**；全量pytest **739 passed、0 skipped、16 subtests passed**，保留1条Starlette/httpx弃用警告。`compileall`、标准库42项、GOAL_STATE JSON、备份脚本语法和`git diff --check`均通过；开发包已重新生成并通过包内SHA-256与ZIP完整性校验。
- 临时PG16容器使用tmpfs且仅绑定127.0.0.1，结束后清理；没有NAS、网站或生产数据库访问与部署。真实许可/样本和NAS PG17/生产验收仍待完成。

## 2026-11-11 P0-09人工核验结论API
- 按用户确认的固定结论`still_listed`（仍在列表）、`confirmed_withdrawn`（已确认撤牌）、`inconclusive`（无法确认）和可选备注新增认证POST记录接口及GET历史接口。记录仅将观察队列状态设为`reviewed`；正式挂牌`source_listings.status`不变。重复处理非待核验记录返回409，非法挂牌ID返回422。
- 变更文件：`app/collection_models.py`、`app/collection_service.py`、`app/main.py`、`sql/009_collection_listing_reviews.sql`、`tests/test_db_integration.py`，并同步`docs/API.md`、`docs/DATA_MODEL.md`、`docs/DISCOVERY.md`、`docs/NAS_DEPLOYMENT.md`及状态记录。迁移009扩展观察状态并追加保存结论，外键保留关联观察记录。
- 本机一次性PostgreSQL 16全量`pytest -q`：**739 passed、0 skipped、16 subtests passed**；包括20项数据库集成。`compileall`、标准库测试42 passed、GOAL_STATE JSON、备份脚本语法和`git diff --check`均通过；开发包已由安全打包器生成并校验包内SHA-256清单。保留1条Starlette/httpx弃用警告。
- 迁移/风险：新库按001–009初始化，现有库须先完成数据库与raw-pages备份再单独执行009；本轮没有迁移NAS或生产数据库。临时PG16数据库使用tmpfs，仅绑定127.0.0.1；测试完成后容器已清理。未连接NAS、生产数据库或房源网站，未部署。
- 下一步：继续离线处理不依赖缺失材料的P0事项；P0-09仅在取得许可及每站获准分页样本后做真实选择器校准，并在部署窗口前做NAS PG17隔离差异回归。当前无许可样本，禁止启用在线采集。

## 2026-11-11 P0-09恢复列表DOM顺序并完成PG16回归
- 失败回归发现列表发现器在反向压入遍历栈时先追加锚点，导致返回顺序与页面DOM顺序相反；现改为节点出栈时追加锚点，保持页面顺序，也让详情上限优先处理页面前部挂牌。相关Mock与数据库策略撤销夹具已调整为“先处理首条、再阻断第二条”。
- 连续2次完整分页遍历未见后进入`pending_review`、不自动下架的规则已由用户确认。集成回归现在预置正式`available`挂牌并核对状态保持；另验证页数上限、请求超时和许可阻断不计入缺失扫描，恢复后完成遍历才计数。
- 使用本机一次性PostgreSQL 16（tmpfs、临时网络、仅127.0.0.1端口、无持久卷）运行`tests/test_db_integration.py`：**20 passed**；全量pytest：**739 passed、0 skipped、15 subtests passed**。保留1条Starlette/httpx弃用警告。发现器专项19 passed，采集服务+发现器专项47 passed；标准库42 passed，compileall、GOAL_STATE JSON、备份脚本语法和`git diff --check`通过。
- 临时容器、网络和数据库已清理。未访问房源网站、NAS或生产数据库，未部署；PG16合成环境结果不替代NAS PG17/生产代码验收。在线采集仍关闭，真实许可及分页样本仍缺。
- 安全开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-09-dom-order-pg16.zip`。

## 2026-11-11 P0-09确认连续缺失阈值并实现人工核验状态
- 用户确认：同一采集目标连续 **2 次完整分页遍历**未见挂牌后转为`pending_review`；不自动下架。列表/详情请求失败、许可/robots阻断、页数或详情数上限、分页回环或歧义均不构成完整遍历。
- 迁移007记录目标级挂牌观察和列表页原始证据引用；迁移008保存遍历轮次。完整遍历结束时才递增缺失次数；重新观察清零连续缺失次数，但已经进入`pending_review`的记录不自动恢复，正式挂牌状态不变。
- 验证：Python 3.12标准库套件 **42 passed**；`compileall`、备份脚本语法、GOAL_STATE JSON和Compose迁移挂载静态检查通过。pytest未运行（模块未安装）；007/008 SQL与Worker/API数据库集成未运行（PG16启动受shmget限制，Docker socket permission denied）。未访问网站/NAS/数据库，未部署；在线采集仍关闭。
- 当前实现为离线代码完成、数据库运行验证待补。P0-09仍需许可范围、真实获准分页样本及隔离PG17/生产差异验收；当前轮不自动下架任何正式挂牌。

## 2026-11-11 P0-09记录跨周期挂牌出现时间
- 分页`seen_ids`会过滤已经见过的详情链接，导致后续重新扫描无法刷新最近观察时间。发现器现分开返回本页唯一可识别挂牌ID与待入队的新详情；Worker按每个成功解析的列表页写入跨目标观察表，记录首次/最近时间、观察次数和最后目标/列表页。新增认证只读分页接口`GET /api/collection/discovery-observations`。
- `python3.12 -m unittest discover -s tests -p '*_stdlib.py' -v` **42 passed**；其中迁移事务/Compose顺序专项3 passed；`compileall`通过。定向pytest因无pytest模块无法启动；uv缓存目录不可访问。Homebrew PostgreSQL 16 `initdb`在bootstrap阶段因`shmget`共享内存限制失败，尚未执行SQL；Docker API socket也拒绝访问，故Worker与PostgreSQL集成未运行。临时目录已清理。没有连接网站/NAS或部署。
- 本轮功能实现完成，数据库运行验证未完成。迁移007仅加表与索引，不改现有业务记录；首次NAS升级仍需先备份并在隔离PG17验证。列表页出现不代表详情有效或仍在售，不执行下架判断。
- 安全开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-09-observation-tracking.zip`（打包器将执行内容清单SHA-256校验）。

## 2026-11-11 P0-03统一解析器文本候选身份
- 失败回归复现：社区标签两次命中`Café`/`Café`时，解析器将同一规范等价值视为两个小区候选并置空；标题来源也使用原始字符串判重。解析器现复用统一文本比较键（空白折叠+Unicode NFC）判重，字段值及证据仍保留页面的首个原始写法；版本升至`generic-labelled-v0.2.65`。
- `tests/test_collection_parser.py`候选字段/标题辅助函数专项 **2 passed**；样本集 **63 passed**；评估器清单/NFC/CLI子集 **10 passed**；标准库测试 **42 passed**（含3项无依赖Unicode文本比较测试）。pytest使用临时运行时和占位BeautifulSoup类型，解析器测试只直接覆盖候选归一辅助函数；真实HTML端到端解析回归及全量pytest因宿主缺少BeautifulSoup和项目依赖未运行。
- 编译、GOAL_STATE JSON、差异检查通过；仅本地离线代码/测试/文档变更，未访问来源网站、NAS或数据库，未部署。开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-03-shared-text-identity.zip`。

## 2026-11-11 P0-03核验评估器CLI错误诊断
- 对无效UTF-8和畸形CSV清单执行CLI级回归：两者均返回状态码1，stdout包含对应拒绝原因，stderr为空，不泄漏堆栈。
- 样本清单套件 **63 passed**；评估器清单/大小/NFC/CLI错误诊断子集 **10 passed**。测试使用临时pytest运行时和仅满足依赖导入的BeautifulSoup占位类型；这些用例不执行HTML解析，标题计分用替身解析结果。
- 全量pytest因宿主缺少项目依赖未运行；未访问来源网站、NAS或数据库，未部署。开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-03-evaluator-cli-diagnostics.zip`。

## 2026-11-11 P0-03统一文本指标的Unicode规范化
- 失败回归复现：人工标签和解析结果只在Unicode规范形式上不同（例如`Café`与`Café`）时，严格文本匹配会错误拉低解析准确率；歧义文本候选去重也会把规范等价字符串误计为不同候选。
- 评估器文本字段与样本校验器歧义候选现先折叠空白，再统一到Unicode NFC；数字字段不变，仍按Decimal精确比较。新增评估、候选归一和完整清单拒绝规范等价重复候选三项回归。
- 两项失败回归先复现后通过；完整`tests/test_sample_set.py` **63 passed**，评估器清单/大小/NFC/CLI错误诊断子集（含替身解析结果端到端计分）**10 passed**（临时pytest运行时与占位BeautifulSoup类型，所测路径不解析HTML）。全量pytest因宿主缺项目依赖未运行；没有真实人工样本，未报告准确率。
- 仅本地离线评估/清单验证变更；未访问来源网站、NAS或数据库，未部署。开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-03-evaluator-cli-diagnostics.zip`。

## 2026-11-11 P0-03锁定评估器损坏CSV诊断
- 定向检查确认`validate_sample_set.validate_manifest`已经将无效UTF-8和畸形CSV分别映射为清晰的验证错误；评估器再将该错误转为`ValueError`。上一轮新增转换代码冗余且测试期望写错，现已撤销实现改动，保留两项回归锁定现有诊断。
- 定向pytest **6 passed**：无效UTF-8/CSV诊断、初始超限拒绝、恰好2,000,000字节哈希通过、哈希超限拒绝，以及超限时只多读取1字节的计数流验证（使用临时pytest运行时；占位BeautifulSoup类型仅满足导入，所测用例不调用HTML解析器）。标准库套件**39 passed**，`compileall`、GOAL_STATE JSON、`git diff --check`及开发包校验通过。宿主仍缺完整项目依赖，本轮未运行全量pytest。
- 仅本地离线测试/文档变更；未访问真实样本、来源网站、NAS或数据库，未部署。开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-03-evaluator-hash-read-cap.zip`。
## 2026-11-11 P0-08同时限制证据压缩输入和解压内容
- 复核发现，仅限制gzip解压内容仍允许完整性扫描读取任意大的压缩文件。现在先检查压缩文件最大2,000,000字节，再最多解压1,000,000字节；超过任一界限即报告无效，不继续解压。CLI帮助同步说明该限制。上限与样本校验器一致。
- 新增回归确认>2MB压缩文件在创建gzip解压器前拒绝、恰好1MB解压内容通过、超1MB解压内容拒绝。存储报告专项**21 passed**；全量离线pytest **669 passed、16 skipped、13 subtests passed**，16项数据库集成缺`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- `compileall`、`bash -n scripts/backup.sh`及GOAL_STATE JSON校验通过。仅本机合成文件验证，未扫描/删除NAS证据，未连接数据库/网站或部署。

## 2026-11-11 P0-08完整性盘点限制gzip解压总量
- 失败回归复现：`storage_report.py --check-evidence-integrity`会分块读取gzip，但无解压总量上限；虽不累积全文，超大证据仍可消耗无界CPU。现完整性扫描最多解压1,000,000字节，超限即报告证据无效并停止读取；恰好1MB仍按SHA-256验证通过，与采集/样本HTML边界一致。
- 超限回归先失败后通过，恰好1MB边界通过；存储报告专项**20 passed**。全量离线pytest **668 passed、16 skipped、13 subtests passed**，16项数据库集成因缺少`TEST_DATABASE_URL`跳过；保留1条既有Starlette/httpx弃用警告。`compileall`、`bash -n scripts/backup.sh`通过。
- 仅本机合成gzip文件验证；未扫描/删除NAS文件，未连接数据库或网站，也未部署。P0-08仍待NAS当前版本备份恢复与实机复验。

## 2026-11-11 P0-04在robots验证后、房源页请求前再次核验许可
- 进一步检查发现，首次许可核验虽在请求robots前完成，但权限若在robots响应期间撤销，仍会继续请求房源页面。`fetch_public_html`现支持页面请求前回调，采集服务在robots许可通过后再次核验全局开关与来源许可；失败则在房源页请求发出前以`blocked_policy`结束。
- 回归确认许可在robots阶段撤销时只请求robots、不请求房源页；P0-04权限/HTTP及采集服务专项**45 passed**。全量离线pytest **666 passed、16 skipped、13 subtests passed**；16项数据库集成因无`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 本地MockTransport/假数据库验证；没有真实DB并发、站点或NAS验收，无迁移、无部署。在线采集保持关闭。

## 2026-11-11 P0-04/P0-09避免抓取期间长持有来源许可锁
- 失败回归复现：Worker原先在一个`FOR SHARE`数据库事务中执行整轮抓取，最长可能横跨5个列表页和20个详情页；来源许可撤销/更新会等待网络请求结束。现改为每个列表页和详情页请求前单独复核全局开关与来源许可，并在发起HTTP前关闭数据库事务；运行中撤销时阻断下一请求。
- `tests/test_collection_service.py`先失败后通过；采集服务专项**27 passed**。全量离线pytest **665 passed、16 skipped、13 subtests passed**，16项数据库集成因未设置`TEST_DATABASE_URL`跳过；保留1条Starlette/httpx弃用警告。`compileall`与备份脚本语法检查通过。
- 仅模拟连接和合成列表页验证；没有真实数据库、网站许可或来源页面验收。本轮无SQL迁移、NAS操作或部署；在线采集仍默认关闭。

## 2026-11-11 当前工作区完整离线pytest复验
- 从本机uv缓存创建临时Python 3.12环境（未联网），运行全量`pytest -q`：**664 passed、16 skipped、13 subtests passed**，有1条Starlette/httpx测试客户端弃用警告。
- `tests/test_db_integration.py`专项确认16项因未设置`TEST_DATABASE_URL`跳过；Docker API socket仍permission denied。Worker分页的数据库端到端验收未完成。
- `python3.12 -m compileall -q app scripts`、`bash -n scripts/backup.sh`及GOAL_STATE JSON校验通过。临时虚拟环境随后清理；未连接网站、数据库或NAS，未部署。

## 2026-11-11 P0-09路线图主清单与验收状态校正
- ROADMAP主清单此前仍将P0-09标为未开始，并称持久游标/重试和Worker分页尚未实现；现改为`in_progress`，列出当前通用发现、分页游标、每轮限额、候选隔离与暂停行为，并保留真实许可/页面、PostgreSQL集成和下架追踪等未验收项。
- `python3.12 -m unittest discover -s tests -p '*_stdlib.py' -v`：38 passed；GOAL_STATE JSON和主清单状态检查通过。`python3.12 -m compileall -q app scripts`、`bash -n scripts/backup.sh`通过。
- 当前Python 3.12环境没有pytest及FastAPI/Pydantic/psycopg/BeautifulSoup/httpx，Docker daemon不可用且未配置`TEST_DATABASE_URL`；Worker/API及隔离PostgreSQL用例未运行。未连接网站、数据库或NAS，未部署。

## 2026-11-11 P0-09同步Worker分页文档
- 修正文档将Worker列表分页误写为未实现的状态，明确当前每轮页数/详情数上限、详情候选隔离、游标续跑及robots/来源阻断后的操作员处理要求。
- 标注仍未实现的失效/下架跟踪、独立待发现队列及真实站点模板；在线采集开关与权限策略未改变。
- 文档与代码核对完成；GOAL_STATE JSON校验通过。未运行测试，本轮无代码、数据库、NAS或部署变更。

## 2026-11-11 P0-03继承display文本遍历改为线性
- 复杂度回归复现：400层`display:inherit`页面调用块级状态判定 **161,202次**，源于每个节点重复向祖先查找计算后的显示类型。文本遍历现沿树传递父节点块级状态，每个节点仅判定一次，起始节点只解析一次外部祖先状态；输出边界语义不变，解析器版本升至`generic-labelled-v0.2.63`。
- 新回归与解析器显示/文本边界专项 **31 passed**；当前工作区全量套件在临时PG16 internal网络运行 **661 passed、0 skipped、13 subtests passed**，有1条FastAPI/Starlette httpx测试客户端弃用警告。
- 临时镜像、PG16容器、internal网络和构建目录均已清理；只读挂载当前代码，未访问房源网站/NAS。仅合成HTML验证，不代表真实页面解析准确率；P0-03仍等待每站20份获准页面与人工标签。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-03-inherited-display-linear.zip`；项目打包器将校验ZIP与包内SHA-256清单。

## 2026-11-11 当前工作区 PG16 全量回归
- 以 `requirements-dev.txt` 构建一次性 Python 3.12 测试镜像，在仅有临时 PostgreSQL 16 的 Docker internal 网络中执行全量 `pytest -q`；当前工作区只读挂载。结果 **660 passed、0 skipped、13 subtests passed**，保留1条FastAPI/Starlette关于httpx测试客户端的弃用警告。
- 测试期间数据库未映射宿主端口，未连接NAS/房源站点；测试容器、PG16容器、internal网络、临时镜像和构建目录均已清理。
- 这验证当前工作区在合成 PostgreSQL 16 上的API/迁移/数据库套件，不替代NAS PostgreSQL 17部署验收或真实V0.1备份迁移；P0-01仍缺用户提供的真实备份。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-pg16-full-suite.zip`；项目打包器将校验ZIP与包内SHA-256清单。

## 2026-11-11 P0-08备份前拒绝raw-pages特殊文件
- 失败回归复现：raw-pages内的FIFO会被旧脚本打包并返回成功，造成备份混入无法作为普通证据读取的特殊节点。备份前现用find拒绝整棵树中任何非目录/非普通文件条目，因此也覆盖符号链接、socket和设备节点；普通文件与目录仍可打包。
- 失败回归先失败后通过；`python3.12 -m unittest discover -s tests -p '*_stdlib.py' -v` **29 passed**，`bash -n scripts/backup.sh`、Python语法编译与`git diff --check`通过。完整pytest本轮未运行：系统Python 3.9和项目Python 3.12均未安装pytest。
- 仅本地临时目录与假Docker命令验证，未连接NAS、未打包真实证据、未同步或部署；P0-08仍待NAS复验。用户暂时没有V0.1备份、获准真实网页或标注，继续离线开发。
- 本机沙箱禁止创建Unix socket测试节点，未能直接验证socket条目；脚本统一文件类型过滤会拒绝非目录/非普通文件，本轮真实节点回归覆盖FIFO与符号链接。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-08-reject-special-files.zip`；由项目打包器生成并校验ZIP与包内SHA-256清单。

## 2026-11-11 README验证摘要与目标状态对齐
- 复核发现README仍写639 passed，而当前工作区全量套件和`GOAL_STATE.json`记录为644 passed、15 skipped、13 subtests passed；现已统一摘要，并保留15项数据库集成跳过的说明。
- 文档/目标状态一致性复核通过；未改代码，未重跑测试。

## 2026-11-11 P0-03为标题来源冲突增加独立评估场景
- 解析器已能在同来源标题冲突时回退，但样本清单/评估器没有场景标签，无法单独验收。新增可选`title_source_conflict`标签：评估须同时见到标题来源歧义警告、选中来源避开歧义来源，且标题等于人工真值；标题真值为空时现有标签校验会拒绝。
- 两项评估回归验证正确/错误标题分别通过/失败；解析评估器+样本集专项**104 passed**；全量离线pytest **644 passed、15 skipped、13 subtests passed**。15项为未配置隔离数据库的集成测试。
- 清单模板列结构无变化。仅本地合成样本验证，未访问网站/NAS或部署；真实标题准确率和该场景覆盖仍待获准真实页面及人工标注。

## 2026-11-11 P0-08深层目录库存扫描改为迭代遍历
- 深层目录树回归复现递归库存扫描在Python递归上限处抛`RecursionError`并中断报告；目录遍历现使用显式栈，不跟随符号链接，并在目录扫描竞争中忽略已消失路径，与原有缺失目录处理一致。
- 深层目录失败回归先失败后通过；留存报告专项**18 passed**。全量离线pytest **642 passed、15 skipped、13 subtests passed**；Python AST语法检查通过。15项为未配置隔离数据库的集成测试。
- 仅本机临时目录验证，未读取/删除NAS文件、未连接网站或部署；P0-08仍待NAS复验。

## 2026-11-11 P0-03冲突标题来源回退到下一可靠字段
- 失败回归复现：HTML中存在不同的多个`og:title`时旧解析器静默使用第一条广告标题，忽略唯一的房源`h1`；多个不同`h1`也会静默选择第一个。
- 同一标题来源的非空值现先去重并检查一致性；冲突来源记录`ambiguous_title_source:<source>`并回退到下一来源（`og:title`→`h1`→`head:title`），避免静默选值。解析器版本升至`generic-labelled-v0.2.62`。
- 两项冲突回退回归先失败后通过。解析器/评估器/样本集专项**294 passed**；全量离线pytest **641 passed、15 skipped、13 subtests passed**。15项为未配置隔离数据库的集成测试。仅合成HTML验证，未访问网站/NAS或部署；真实标题准确率仍需获准页面和人工标签。

## 2026-11-11 P0-08留存盘点错误改为明确CLI诊断
- 失败回归复现：`storage_report.py`的`--raw-pages`或`--backups`路径指向普通文件时抛`NotADirectoryError`堆栈；目录权限不足时也直接回显Python异常堆栈。
- CLI现对非目录路径明确失败，对盘点、过期备份扫描和证据文件扫描的OS读取错误返回对应路径类别的诊断；只读盘点行为不变。失败回归先复现3项失败后通过，留存报告专项**17 passed**。
- 全量离线pytest **639 passed、15 skipped、13 subtests passed**，15项为未配置隔离数据库的集成测试；Python AST语法检查和`bash -n scripts/backup.sh`通过。仅本机合成目录验证，未连接NAS/网站、未删除文件或部署；P0-08 NAS复验仍待连接恢复。

## 2026-11-11 P0-03限定词与数值标签之间空白仍排除优惠价/套内面积
- 合成回归复现：房价标签限定词和总价之间经HTML块级分隔后归一成空格（如`折后 总价`），旧负向前缀检查失效，把优惠总价当挂牌价；面积也有相同问题，并且`使用 建筑面积`可退化匹配其子串`面积`。
- 现为限定词和单个归一空格同时生成负向前缀约束；面积规则另覆盖`限定词 + 建筑 + 面积`子串路径，防止同一标签从短后缀绕过。贝壳/安居客限定总价及套内/使用面积合成回归先失败后通过；解析器升至`generic-labelled-v0.2.61`。
- 解析器/评估器/样本集专项 **292 passed**；全量离线pytest **636 passed、15 skipped、13 subtests passed**。仅合成HTML验证，未访问网站/NAS或部署；P0-03真实准确率仍等待每站20份获准页面及人工标签。

## 2026-11-11 P0-08复验连接路径仍不可达
- 按`nas-ssh-connect`技能依次只读尝试：LAN `nas-lan`至`10.10.10.7:22222`超时；Tailscale CLI仍无法加载偏好且`open -a Tailscale`确认本机未安装该App；使用用户已授权的`notedock-nas`连接`300858.xyz:5005`也超时。
- 所有连接均未建立，未执行任何远端身份命令、文件读取/传输、备份或Docker操作。当前代码和留存报告仍仅在本地；P0-08 NAS同步/复验待连接恢复。

## 2026-11-11 P0-09覆盖Unicode分页别名的API与本地游标入口
- 在Unicode IRI页身份规范后，补充跨入口回归：API分页状态模型拒绝当前页/下一页的Unicode与UTF-8编码别名；本地state拒绝下一页指向Unicode写法的已访问页。
- 模型/发现器专项 **44 passed**，标准库状态/CLI **19 passed**；全量离线pytest **630 passed、15 skipped、13 subtests passed**。本轮仅补回归，不触及数据库/NAS或房源网站；P0-09验收仍待授权、真实分页样本与自动Worker。

## 2026-11-11 P0-09统一Unicode IRI与UTF-8分页页身份
- HTTPX本地URL规范化检查确认：裸中文路径会转换成UTF-8百分号路径。旧`source_page_key`未编码裸Unicode，导致分页指向同一请求路径时可能漏掉回环，或把两个等价`rel=next`误报冲突。
- 页身份键现将裸Unicode路径字符编码为大写UTF-8百分号序列；已有百分号转义仍按ASCII未保留/保留字符规则处理。路径大小写和`%2F`/`/`差异保持不变，孤立Unicode surrogate明确拒绝。新增等价下一页去重、编码别名回环及非法Unicode回归。
- `tests/test_collection_discovery.py` **18 passed**；全量离线pytest **628 passed、15 skipped、13 subtests passed**。仅本地HTTPX URL对象与合成HTML验证，未访问房源网站/NAS或部署；P0-09仍待授权、真实分页样本和自动Worker。

## 2026-11-11 P0-03按CSS计算结果排除负透明度文本
- 合成回归复现：浏览器将负数`opacity`按规范钳制为0；旧逻辑只把数值恰为0的元素当作透明，可能将负透明度广告挂牌价拼入主挂牌字段。该可见性函数也由离线链接发现器复用。
- 现按CSS数值语法识别有限数字/百分比/指数形式，并把小于等于0的值视为透明；无效值如`-Infinity`不误判隐藏。新增负小数、百分比、指数和无效值回归，解析器版本升至`generic-labelled-v0.2.60`。
- 解析器/链接发现器专项 **195 passed**；全量离线pytest **625 passed、15 skipped、13 subtests passed**。仅合成HTML验证，未访问网站/NAS或部署；P0-03真实准确率仍需每站20份获准页面及人工标签。

## 2026-11-11 P0-08拒绝符号链接库存根目录的零值误报
- 回归复现`storage_report.py`对符号链接形式的`--raw-pages`或`--backups`根目录拒绝遍历，却把结果输出为0文件/0字节；备份路径还会显示0个超期候选，无法区分空目录与未检查。
- CLI现在对这两个根目录显式报错并退出，库函数仍保留“不跟随符号链接”的行为。两类失败回归先失败后通过；`tests/test_storage_report.py` **14 passed**。
- 全量离线pytest **621 passed、15 skipped、13 subtests passed**，15项为数据库集成测试。仅本地临时目录验证，未扫描NAS或删除文件；NAS当前库存仍待恢复连接后复核。

## 2026-11-11 P0-08拒绝符号链接备份根目录
- 假Docker端到端回归复现`BACKUP_ROOT`指向目录符号链接时，`backup.sh`会跟随链接并将目标目录权限改为`700`，然后在目标目录发布备份。
- 脚本现在在创建/修改备份根目录前拒绝符号链接，并去除末尾斜杠后检查；目标目录原权限与内容保持不变。失败回归先失败后通过，原有raw-pages根及嵌套符号链接保护、正常临时目录/权限/哈希发布流程仍通过。
- `tests/test_backup_script_stdlib.py` **6 passed**，标准库全套 **27 passed**；`bash -n`通过。全量离线pytest **619 passed、15 skipped、13 subtests passed**，15项跳过为数据库集成测试。仅本机假Docker/合成文件离线验证，未连接NAS、未执行真实备份或部署；P0-08仍待NAS同步复验。

## 2026-11-11 P0-09避免重放已访问页的失败污染分页游标
- 新增回归复现：操作者显式重放已成功页，但本地HTML读取失败时，错误处理会将该页设为`next_page_url`，与`visited_page_urls`冲突，导致下次读取状态被误判为分页回环。
- 修复后，失败页未访问时仍保存为重试游标；失败页已访问时记录最近尝试页、错误类型和失败次数，同时保留现有游标。新增回归先失败后通过。
- 标准库状态/CLI专项 **18 passed**；全量离线pytest **618 passed、15 skipped、13 subtests passed**，15项跳过为数据库集成测试。仅本地离线验证，未访问房源网站或NAS，未部署。

## 2026-11-11 P0-09规范未保留字符百分号编码以阻断分页别名
- 新增回归发现`/page%31`与`/page1`是同一资源，但字符串比较会漏掉分页回环。`source_page_key`现将路径中百分号编码的ASCII未保留字符解码，并将保留字符编码统一为大写；路径大小写仍敏感，`%2F`仍不等于路径分隔符`/`。
- 发现器、数据库状态模型/保存服务、本地state/CLI沿用同一页身份。发现器/状态/CLI定向测试 **40 passed、7 subtests passed**；全量离线pytest **617 passed、15 skipped、13 subtests passed**，15项跳过为数据库集成测试。
- 仅使用合成输入离线验证，未访问房源网站、NAS或部署。P0-09仍缺来源许可、获准真实分页样本及自动Worker分页/重试/失效标记。

## 2026-11-11 P0-09按同源URL身份阻断分页别名回环
- 合成快照复现分页`rel=next`通过主机名大小写、显式默认`:443`或DNS尾点变化，可绕过字符串回环检测。新增`source_page_key`：在来源URL校验后统一scheme/host大小写、尾点、默认端口，并将空路径视作`/`；路径仍区分大小写。
- 发现器合并等价next链接并检测自环；数据库状态模型/服务和本地state/CLI按相同身份拒绝别名回环。新增5项回归；数据库API集成回归因当前未配置隔离数据库而跳过。
- 全量离线pytest **617 passed、15 skipped、13 subtests passed**，保留1条既有弃用警告；发现器/状态/CLI定向测试 **40 passed、7 subtests passed**。未访问网站/NAS或部署；P0-09仍缺P0-04许可、真实分页样本和自动Worker流程。

## 2026-11-11 P0-03只按CSS ASCII空白解析display多关键字
- `str.split()`会把NBSP也当空白，导致无效的`display:inline flow`被误认作合法`inline flow`、让块级div漏分隔。声明值现仅折叠CSS ASCII空格/Tab/换行/回车/换页，合法多空格值继续支持；解析器升至`generic-labelled-v0.2.59`。
- NBSP失败回归修复后通过。解析器/评估器/样本集 **282 passed**；全量离线pytest **609 passed、15 skipped、13 subtests passed**，保留1条既有弃用警告。15项跳过为数据库集成测试。
- 仅本地合成HTML验证，未访问网站/NAS或部署。

## 2026-11-11 P0-03规范内联CSS声明空白
- 等价的多关键字`display:inline   flow list-item`因声明值内部空白未归一化而被当作未知值，导致行内`div`被错误分隔。CSS属性值现折叠连续空白，解析器升至`generic-labelled-v0.2.58`。
- 参数化失败回归通过。解析器/评估器/样本集 **281 passed**；全量离线pytest **608 passed、15 skipped、13 subtests passed**，保留1条既有弃用警告；15项数据库集成跳过。
- 仅合成HTML验证，未访问网站/NAS或部署。

## 2026-11-11 P0-03解析display继承边界
- 合成回归复现块级父元素内`display:inherit`的子span被误判为行内，导致跨元素拼接“小区”标签。文本遍历现在沿父节点解析显式继承display，遵守最近祖先可判定的内联显示值；解析器升至`generic-labelled-v0.2.57`。
- 回归先失败后通过。解析器/评估器/样本集 **280 passed**；全量离线pytest **607 passed、15 skipped、13 subtests passed**，保留1条既有Starlette/httpx弃用警告。15项跳过为数据库集成测试。
- 仅本地合成HTML验证，未访问网站/NAS或部署；真实字段准确率仍待每站20份获准页面及人工标签。

## 2026-11-11 P0-03识别inline flow list-item显示值
- 新增合成回归发现`display:inline flow list-item`未列入行内显示分类，会错误分隔跨节点字段标签并漏提小区。将该合法多关键字值加入行内集合，解析器升至`generic-labelled-v0.2.56`。
- 回归先失败后通过。解析器/评估器/样本集 **279 passed**；全量离线pytest **606 passed、15 skipped、13 subtests passed**，保留1条既有Starlette/httpx弃用警告。15项跳过为数据库集成测试。
- 仅合成HTML离线验证，未访问网站/NAS或部署；真实准确率仍待获准样本和人工标签。

## 2026-11-11 P0-03统一CSS显示边界与语义根评分文本
- 合成回归复现三种错判：内联`display:block`的`span`把“小区”标签跨块粘连；内联`display:inline`的`div`被无条件拆分；语义根评分用`get_text(' ')`插入额外空格，导致真实正文标签拆分后得分为0而误选推荐`article`。
- 文本遍历现按可识别的内联`display`值决定块边界；语义根评分复用相同遍历和空白归一化，避免评分/解析的文本不一致。解析器升至`generic-labelled-v0.2.55`。
- 三类回归均先失败后通过。另将显示分类覆盖扩至大小写、`!important`顺序、`table-caption`和`inline flow`多关键字；7种display场景通过。解析器/评估器/样本集 **278 passed**；全量离线pytest **605 passed、15 skipped、13 subtests passed**，保留1条既有Starlette/httpx弃用警告。15项跳过为数据库集成测试。
- README验证摘要已同步到当前`v0.2.55`和最新测试数，并明确先前PG16全量测试早于近期解析器改动。
- 仅本地合成HTML验证，未访问网站/NAS或部署。真实字段准确率仍待每站20份获准页面和人工标签。

## 2026-11-11 P0-03阻止块级CENTER跨节点拼接字段标签
- 合成HTML复现旧遍历器把块级`<center>`内部“`小`”与后续行内“`区：`”直接拼接，伪造“小区：”标签并错误提取社区名。将`center`加入块级分隔集合，解析器升至`generic-labelled-v0.2.54`。
- 回归先失败后通过。解析器/评估器/样本集专项 **270 passed**；全量离线pytest **597 passed、15 skipped、13 subtests passed**，保留1条既有Starlette/httpx弃用警告。15项跳过为数据库集成。
- 仅本地合成HTML验证；未访问网站/NAS、未部署。P0-03仍等待每站20份获准页面及人工标签，未报告真实准确率。

## 2026-11-11 P0-03保留行内字段文本并忽略HTML注释
- 合成页面复现：`<span>小</span><span>区：</span>`、分拆的建筑面积/挂牌价标签和数字会被旧的`stripped_strings`以空格连接，导致标签无法匹配、字段漏提。
- 新增迭代式文本遍历：行内节点相邻文本保持连续，块级标签之间增加换行后再统一空白；HTML注释不进入可见文本，以免注释里的推荐价污染字段。解析器升至`generic-labelled-v0.2.53`。
- 行内分割和注释报价回归先复现后通过。解析器/评估器/样本集专项 **268 passed**；全量离线pytest **595 passed、15 skipped、13 subtests passed**；保留1条既有Starlette/httpx弃用警告。15项数据库集成跳过，未访问网站或NAS，未部署；真实准确率仍待获准页面。

## 2026-11-11 P0-03混合HTML文本与证据偏移复核
- 静态审阅`_text_with_inline_boundaries`确认遍历时跳过HTML注释、行内后代直接拼接、已知块级标签前后插入分隔；字段命中与偏移在空白归一化及35,000字符截断后的同一文本上计算。`field_evidence`命中片段保留原文和偏移，`evidence_excerpt`只保留前1,000字符，故较后命中的偏移按API契约相对完整归一化文本，不保证可在短摘录中直接切片。
- 补充跨越1,000字符摘录边界的回归，并在API文档说明偏移与摘录关系；确认较后字段的offset能从完整归一化文本定位，独立quote仍保留原文。解析器/评估器/样本集 **269 passed**；全量离线pytest **596 passed、15 skipped、13 subtests passed**，保留1条既有Starlette/httpx弃用警告。15项跳过为数据库集成测试。
- 未改解析器实现和版本；Docker socket拒绝访问，未运行PG集成、NAS或部署。P0-03仍`in_progress`；20+20获准页面与人工标签到位前不报告真实准确率。

## 2026-11-11 P0-03隔离折扣/参考总价
- 合成页面复现：`折后总价：300万`会被当作挂牌价；若同时出现`挂牌价：365万`则被误判为多个报价并阻断审核。
- 价格标签解析现在排除带折后、优惠、折扣、降价后、参考、估算、成交、历史、原始、预估、网签限定词的总价，只将明确挂牌标签或未限定的总价作为候选。解析器升至`generic-labelled-v0.2.52`，使待审核重复候选可识别并重新解析。
- 贝壳、安居客各覆盖12种限定词及仅有折后价的场景；回归先失败后通过。解析器/评估器/样本集专项 **266 passed**。全量离线pytest **593 passed、15 skipped、13 subtests passed**；15项数据库集成跳过。真实获准页面未提供，因此不报告准确率；没有联网、NAS访问或部署。
- 下一步：继续用合成页面检验混合价签和可见区域边界；获准20+20真实页面到位后再据标注评估准确率/覆盖率。

## 2026-11-11 PostgreSQL 16全量回归完成
- 将项目源码与依赖放入断网的 ARM64 临时测试容器，在内部网络中的临时 PostgreSQL 16上运行：`TEST_DATABASE_URL=... pytest -q`，**582 passed、0 skipped、13 subtests passed**。覆盖本地迁移、API、Worker和全部离线测试；保留1条既有Starlette/httpx弃用警告。
- P0-09数据库状态集成覆盖迁移重复执行、状态保存/读取、ID去重、revision陈旧写入冲突、非法URL拒绝和失败游标保存。测试schema列表复核为空。
- 临时PostgreSQL、测试容器、内部网络、上一轮遗留的同名PG16测试容器及本地临时依赖均已清理。未连接NAS生产数据库或网站；没有部署。
- 目标仍按真实外部条件保持：P0-01缺V0.1备份，P0-02缺获准页面和标注，P0-04缺书面许可；P0-09虽有本地数据库状态API/006迁移，但仍缺获准真实分页样本及自动Worker流程。

## 2026-11-11 P0-09数据库分页状态自环校验
- `DiscoveryStateIn`现在拒绝`next_page_url`重复`last_page_url`，避免遗漏`visited_page_urls`时数据库游标原地循环；上一页失败后把其作为待重试游标仍可通过。
- 新增自环拒绝和失败重试接受回归。全量离线pytest **567 passed、15 skipped、13 subtests passed**；数据库集成因没有安全的本机隔离数据库而跳过。标准库迁移检查3 passed、分页状态/CLI检查16 passed；compileall、GOAL_STATE JSON、CLI帮助和diff检查通过。
- NAS只读核验已连接：当前部署Compose仅含迁移001–005，API/Worker/DB仍在运行；未触碰容器、数据或项目登记。Mac Docker socket不可用，未运行PG集成测试或部署。
- P0-09仍为`todo`：数据库状态代码及006迁移仅在本地；缺P0-04批准和获准真实列表页样本，自动分页Worker/重试/失效标记未实现。用户暂无样本和真实V0.1备份，继续离线开发。

## 2026-11-11 P0-09区分网页快照与ID清单错误
- 本轮目标：修正CLI把状态文件、网页快照和`--seen-ids`辅助文件错误统一报成HTML读取失败的问题。目标状态：诊断已修复，分页发现整体仍待真实来源验证。
- 将状态读取、HTML读取/UTF-8解码、seen-ID文件校验和HTML发现分别处理；状态/清单输入错误不再被写成页面失败，HTML不可读与非法UTF-8有明确且不回显样本内容的错误信息。
- 新增缺失seen-ID文件和非法ID清单回归；`python3.12 -m unittest discover -s tests -p 'test_discovery_state_stdlib.py' -v`：16 passed。现有首页失败重试、stdout中断保留状态回归仍通过。
- 复核参数组确认`--state-file`与`--seen-ids`互斥，因此该问题影响错误诊断，不会污染分页状态。无数据库迁移、网络请求或NAS改动；完整pytest/真实HTML解析未运行。
- 下一步仍需获准列表页样本和P0-04许可范围，之后才能验收站点解析与数据库游标。

## 2026-11-11 P0-01迁移失败原子回滚验证
- 本轮目标：验证002–005在DDL执行后遇到SQL错误会整体回滚，避免留下部分迁移结构。目标状态：本机PG16故障注入通过；真实V0.1备份升级仍待材料。
- 在断网、无端口/宿主挂载的临时PG16库上，以001建立空V0.1 schema。对002–005分别生成仅供测试的SQL副本，在文件内`COMMIT`前注入`SELECT 1/0`；每份失败后核查该迁移新增的表/列/索引/触发器均未留下，再运行原版迁移确认正常完成。
- 002–005四份回滚断言全部通过，后续原版迁移也全部成功；容器已定向删除。该验证不覆盖NAS PG17、真实备份或API/Worker运行。
- NAS本轮只读连接仍无法建立：`nas-lan`超时、Tailscale CLI无法加载偏好、已授权`notedock-nas`超时。未改NAS配置或数据。
- 下一步：材料到位后以真实V0.1备份做隔离升级；NAS通道恢复后复验当前备份脚本。当前P0-01仍`blocked`。

## 2026-11-11 P0-09分页发现stdout中断保护
- 本轮目标：避免本地分页CLI在结果未交付时先把挂牌ID记为已发现，造成续跑静默丢失。目标状态：修复完成；数据库端分页、真实站点页面及P0-04许可仍未完成。
- `scripts/discover_listing_urls.py`现在先输出并刷新结果JSON，再原子保存分页状态；stdout写入/刷新失败时以非零退出且不推进游标或seen IDs。这样将输出与状态保存的故障窗口从可能丢失改为可重试/可能重复，符合至少一次交付。
- 新增BrokenPipe回归：先完成第一页，再模拟第二页输出管道断开，确认state文件逐字段未变；重跑同页后链接正常输出并更新状态。`python3.12 -m unittest discover -s tests -p 'test_discovery_state_stdlib.py' -v`：15 passed。
- 无数据库迁移、API或网络请求；未访问NAS。真实HTML解析依赖BeautifulSoup的完整测试仍未在当前环境运行；P0-09保持`todo`。
- 下一步：等待来源许可范围和获准列表页样本，再把经验证的分页行为接入数据库端；不将本地操作状态当作Worker游标验收。

## 2026-11-11 P0-08真实PostgreSQL 16备份恢复往返
- 本轮目标：验证当前`backup.sh`生成的数据库与raw-pages备份可校验并恢复。目标状态：本机隔离往返通过；NAS当前脚本版本尚未复验。
- 用两个断网、无端口映射的临时`postgres:16-alpine`容器和合成数据运行；通过临时Docker命令适配器将脚本的Compose调用映射到测试容器，实际执行PostgreSQL custom `pg_dump`、源端`pg_restore --list`及raw-pages容器内tar归档。将dump恢复到第二个PG16容器后，3条含中文/JSONB合成行逐字段一致。
- `SHA256SUMS`、归档内证据文件内容及目录700/文件600权限检查通过。PG容器、临时命令适配器和合成证据目录已清理；未连接NAS、生产库或项目Compose栈。
- 该结果验证当前脚本与PG16/临时容器执行路径，不证明UGREEN/NAS实际Compose容器兼容、PostgreSQL 17行为或生产数据恢复；P0-08仍`in_progress`，需在NAS对当前脚本版本重新验收。
- 下一步验收：NAS连接恢复后，同步/复核当前`backup.sh`并对生产备份做独立隔离恢复，核对数据库清单、raw-pages引用和哈希；不得据本机合成结果清除NAS待复验状态。

## 2026-11-11 P0-01 PostgreSQL 16合成旧库全迁移保真
- 本轮目标：在离线隔离环境验证合成V0.1旧数据经002–005升级和重复执行后仍保留。目标状态：本机数据库层验证完成；真实V0.1备份升级仍未完成。
- 以`postgres:16-alpine`在临时Docker容器运行；容器使用`--network none`，未映射端口、未挂载主机目录。基于001建立旧schema，写入账号/同步、视频、社区/房源/挂牌、报价历史、同套关系、条件单及通知等12张表各1条合成记录；002–005依次执行后再全部重复执行。
- SQL断言核对12张旧表行数及代表性业务字段；确认004健康汇总回填为贝壳挂牌1条、安居客0条，005三组数组字段默认为空数组、最大挂牌天数为NULL，来源在线开关仍关闭。全部断言通过。容器已定向删除。
- `python3 -m unittest discover -s tests -p 'test_migration_transactions_stdlib.py' -v`：3 passed。打包器自检生成113个源文件并核对ZIP内SHA256；`zipfile.testzip()`无损坏。`test_package_dev.py`依赖pytest，而本机未安装pytest，未能执行该pytest风格用例。
- 这是PostgreSQL 16合成schema迁移与重复执行证据；未执行应用/API/Worker集成，也不证明PostgreSQL 17或真实旧库备份升级。用户目前没有V0.1备份，P0-01继续`blocked`。未访问NAS或业务数据；无部署。
- 下一步：材料到位后在隔离环境对真实V0.1备份执行迁移并核对备份恢复；离线阶段可继续推进P0-07指标或P0-09本地流程。验收边界见本轮说明。

## 2026-11-11 README验证状态与部署边界同步
- README原验证摘要仍写本机267 passed、13 skipped，且旧NAS验收与当前源码状态并列，无法准确反映最近工作区回归。
- 已同步当前离线pytest **542 passed、14 skipped**、DTK/Worker **75 passed**，并明确NAS的144 passed为此前部署源码验收，不代表当前工作区最新代码已部署；同时列出P0-01/02/04/06/07仍未完成的外部条件。
- 文档口径检查、目标JSON解析及空白检查通过；未运行测试、连接NAS/数据库或部署。本轮只校正证据时效和边界，不改变运行状态。

## 2026-11-11 P0-06拦截DTK不可持久化或超限字段
- 复核发现DTK规范化结果绕过API请求模型直达视频数据库写入；帖子ID、标题、作者名和位置此前可超过API模型长度限制；NUL/孤立Unicode surrogate也会令写入失败，分享URL的孤立surrogate可能原样保存。
- `normalize_post`现在拒绝不可存储文本及超限帖子ID/标题/作者/位置并抛出明确`DtkError`；超过2000字符或含不可存储字符的分享URL回退为帖子ID规范链接。合法Unicode内容继续保留。
- DTK/Worker专项**80 passed**；全量离线pytest **547 passed、14 skipped**（PostgreSQL集成需`TEST_DATABASE_URL`），另有3个subtests通过和1条既有弃用警告。仅模拟响应离线验证，真实DTK及账号联调仍未完成，P0-06保持`todo`。

## 2026-11-11 P0 API拒绝NUL文本输入
- 复现HTML中的NUL字符进入`evidence_excerpt`后会被写入JSONB，而PostgreSQL文本/JSONB不接受NUL，可能造成保存页面接口返回未处理数据库错误；样本清单校验此前也会接受NUL，随后评估器才失败。挂牌、视频、条件单和审核文本等API字段同样可携带NUL并触发数据库错误。
- 请求模型统一继承`DatabaseTextSafeModel`，递归拒绝所有字段及嵌套数组中的NUL；页面解析器和样本校验器保留各自前置拒绝，普通/gzip HTML在清单阶段即失败。页面提交API返回422，且不会访问数据库或创建原始证据目录。解析器版本为`generic-labelled-v0.2.51`。
- 模型/采集模型/解析器/API专项**233 passed**；全量离线pytest **534 passed、14 skipped**（PostgreSQL集成需`TEST_DATABASE_URL`），另有3个subtests通过及1条既有Starlette/httpx弃用警告。仅离线验证，真实样本与授权仍未验证。

## 2026-11-11 P0-04严格校验所有API布尔输入
- 复现来源审批`online_enabled`、采集目标创建/PATCH、账号PATCH的`enabled`、小区`verified`及条件单通知开关会将数字`1`强转为`true`。所有API布尔字段现在使用严格布尔类型；只接受JSON`true`/`false`，DTK响应解析不在本次范围。
- 新增来源审批、采集目标、账号启停、小区校验标记和通知偏好回归，数字`0`和`1`均被拒绝；严格布尔模型/API/policy专项**89 passed**，全量离线pytest **521 passed、14 skipped**（PostgreSQL集成需`TEST_DATABASE_URL`），另有3个subtests通过及1条Starlette/httpx弃用警告。
- 仅本地输入/API契约验证，未更改来源许可状态、未发出网络请求、未连接NAS/业务数据库或部署。

## 2026-11-11 P0-03拒绝布尔值伪装整数筛选条件
- 复现Pydantic将挂牌/候选纠正/条件单户型`true`转换为整数1；条件单`max_listing_age_days=true`也会转为1天并被接受。现户型及最大挂牌时效字段均在类型转换前拒绝布尔值；轮询间隔的布尔值已由原有最小值约束拒绝。API文档已同步。
- 新增挂牌、候选纠正、最小户型及最大挂牌时效4种回归；模型/采集模型专项**71 passed**，全量离线pytest **509 passed、14 skipped**（PostgreSQL集成需`TEST_DATABASE_URL`），保留1条既有弃用警告。
- 仅本地输入校验验证，未连接真实数据库、NAS或来源网站，未部署。

## 2026-11-11 P2-02强化跨平台价差边界回归
- 已确认规则的测试扩展为两个挂牌面积方向：均以较小面积为分母核验5%边界；单价差恰好10%两种挂牌高低方向均进入候选。新增单价差9.999%排除回归。
- `tests/test_opportunities.py`定向测试**20 passed**；全量离线pytest **505 passed、14 skipped**（PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过），保留1条既有弃用警告。
- 本轮仅补充边界回归，机会计算实现未改；未连接数据库、NAS或房源网站，未部署。

## 2026-11-11 P0-03阻止三位数户型截断误解析
- 户型匹配此前未约束数字左右边界，`户型：102室`会从后缀误提取为2室；现使用数字边界拒绝部分匹配，并升级解析器为`generic-labelled-v0.2.50`。
- 新增102/123室合成HTML回归，确认不输出户型字段或伪造字段证据。解析器与评估器专项：**178 passed**。
- 仅合成HTML离线验证，未连接来源网站、数据库或NAS，未部署；真实字段准确率仍等待每站20份获准页面与人工标注。

## 2026-11-11 P0-09阻止状态文件覆盖HTML快照
- `--state-file`与`--html`指向同一文件或硬链接别名时，CLI此前会成功解析后用JSON状态覆盖原始HTML；现于读取前检测同文件身份并拒绝。
- 新增硬链接覆盖回归；修正延迟导入测试，将断言放入独立子进程，避免测试模块自身预加载解析器后产生错误失败。
- 全量离线pytest：**501 passed、14 skipped**（PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过），保留1条Starlette/httpx弃用警告；定向发现器测试**11 passed**。
- 仅本地代码与测试，无网站、数据库、NAS访问或部署；P0-09仍待来源许可、获准真实分页样本及数据库端实现。

## 2026-11-11 P0-09拒绝非普通状态文件
- 状态加载/保存统一拒绝目录等非普通文件，避免对目录报不清晰错误或从特殊文件读取阻塞；继续拒绝状态软链接。
- 新增目录路径读写拒绝测试；标准库状态与CLI集成测试：**11 passed**。compileall、JSON、差异/空白和ZIP校验通过；网页解析/完整pytest未运行。
- 仅本地离线状态文件处理，无网站、数据库、NAS操作或部署。

## 2026-11-11 P0-09标准库CLI状态集成测试
- 扩展无外部依赖的`unittest`：在替身发现器下实际调用CLI，覆盖两页续接/ID去重、首页失败后恢复和跨页回环阻断；另覆盖状态schema、URL/ID边界、软链接、文件上限和原子写入。
- `python3.12 -m unittest discover -s tests -p 'test_discovery_state_stdlib.py' -v`：**10 passed**；CLI`--help`、compileall、目标JSON、diff/空白及ZIP校验通过。替身不验证BeautifulSoup实际HTML解析，pytest网页解析套件仍未运行。
- 仅离线测试，无网站、数据库、NAS访问或部署。

## 2026-11-11 P0-09分页状态拆分并实现无依赖单测
- 将有界状态校验、原子写入和失败游标记录移到`app.collectors.discovery_state`；采集器包改为按需导入重解析器，状态逻辑不再因BeautifulSoup缺失而无法加载。保持`PARSERS`/`SOURCE_ID_EXTRACTORS`分发接口并延迟解析器加载。
- 新增标准库`unittest`覆盖兼容状态、同源/ID校验、软链接保护、2MB上限、失败游标和轻量导入：**7 passed**。另`discover_listing_urls.py --help`通过；`compileall`与目标JSON解析通过。完整网页解析及pytest套件仍未运行。
- 测试说明见`docs/DISCOVERY.md`；未连接网站、数据库或NAS，未部署。

## 2026-11-11 P0-09恢复首页失败后的无参数重试
- 失败页现成为待重试游标；解决首个列表页在还没有next游标时失败，导致状态文件无法续接的问题。非法/不允许的URL不会写入状态。
- 改写回归为“首页快照缺失→记录首页游标→补齐快照→省略`--page-url`重试成功”。pytest/BeautifulSoup不可用，未运行测试；依赖桩CLI smoke通过。编译、JSON、差异/空白和ZIP校验通过。

## 2026-11-11 P0-09状态文件软链接保护回归
- 新增CLI回归：状态路径为软链接时必须拒绝，并验证链接目标内容保持不变。
- 本机缺少pytest/BeautifulSoup，未执行完整用例；用标准库临时文件 smoke 验证状态读取拒绝软链接且目标SHA前后相同。compileall、JSON、差异/空白与包完整性校验通过。
- 不访问网站、数据库或NAS；本轮无部署。

## 2026-11-11 P0-09记录离线分页失败并保留重试游标
- state-file现在记录最后尝试页、累计失败次数和最近错误类型。输入读取、UTF-8解码、体积或URL校验失败时游标保持不变；错误记录不含本地路径、HTML正文或异常原文；成功重试后清除最近错误。
- 新增“缺失快照→失败留存→补文件重试成功”回归。pytest/BeautifulSoup依赖不可用，未运行pytest；依赖桩CLI smoke通过。compileall、JSON、diff/空白和包校验通过。
- 仅本地手动分页状态，不等于Worker自动重试；线上采集仍受P0-04授权门控。

## 2026-11-11 P0-09阻断分页自环
- 通用链接发现器现在拒绝指向当前列表页本身的安全`rel=next`地址，返回`pagination_loop`并清空下一页游标；不依赖本地state文件。
- 新增无状态自环回归；本机缺少pytest/BeautifulSoup，测试未运行。compileall、JSON、diff及包校验结果见本轮记录。
- 仅本地快照解析，无网络访问；跨多页回环保护依赖`--state-file`历史页记录。

## 2026-11-11 P0-09阻断分页回环
- 本地状态现记录已访问分页URL；下一页若回到任一已访问URL，CLI清空下一页游标并输出`pagination_loop`，避免操作员按游标重复处理循环快照。旧版状态兼容：从`last_page_url`初始化访问记录。
- 新增A→B→A回环回归。pytest/BeautifulSoup依赖缺失，未运行pytest；依赖桩CLI smoke确认回环被阻断并记录。compileall、目标JSON、差异/空白检查及ZIP哈希校验通过。
- 仅保护本地逐页快照工作流；不代表数据库采集Worker具备分页循环保护或P0-09验收完成。

## 2026-11-11 P0-09本地分页状态续接
- 离线发现CLI新增`--state-file`：原子保存来源、已发现ID、上一页与安全的下一页URL；后续本地HTML快照可从已保存游标续接并过滤已发现ID。限制2MB、拒绝软链接、跨来源/非法ID和不安全URL，不联网。
- 新增两页续接/去重及跨来源状态拒绝回归。pytest和BeautifulSoup依赖当前不可用，未运行测试；依赖桩CLI状态smoke通过（含游标清空和非法ID拒绝），静态编译、JSON、差异和包校验通过。
- 这是本地操作状态，不是数据库端任务游标；真实页面验证、自动重试、失效标记和P0-04批准仍缺，P0-09保持todo。

## 2026-11-11 P0-09本地分页状态续接
- 离线发现CLI新增`--state-file`：原子保存来源、已发现ID、上一页与安全的下一页URL；后续本地HTML快照可从已保存游标续接并过滤已发现ID。限制2MB并拒绝状态文件软链接，不联网。
- 新增两页续接/去重及跨来源状态拒绝回归。pytest和BeautifulSoup依赖当前不可用，未运行测试；依赖桩的CLI状态smoke通过，静态编译、JSON、差异和包校验通过。
- 这是本地操作状态，不是数据库端任务游标；真实页面验证、自动重试、失效标记和P0-04批准仍缺，P0-09保持todo。

## 2026-11-11 P0-09识别head中的rel=next分页链接
- 离线发现器新增标准`head link[rel~=next]`支持，与可见分页锚点共用来源主机、query/fragment和冲突校验；不新增网络请求或激活采集。
- 新增安全同源路径接受及外站地址拒绝回归。当前pytest及BeautifulSoup依赖不可用，测试未运行；compileall、目标JSON、差异检查和ZIP校验见本轮交付。
- 仍需获准列表样本验证站点行为；持久游标、重试与失效标记未实现，P0-09保持todo。

## 2026-11-11 P2-02减少机会计算的重复工作
- 机会接口先按小区和户型分组候选挂牌，再只遍历可比较的分组；历史报价查询移出挂牌循环，每次请求只执行一次。
- 新增多挂牌仅加载一次历史报价及跨平台不同小区排除的回归用例。当前环境没有pytest，系统Python也未安装pytest；uv离线缓存也缺少依赖，未执行pytest。用依赖桩直接调用机会函数验证：挂牌查询/历史查询各一次，符合阈值的两条跨平台信号保留，其他小区候选排除。`compileall`（临时字节码目录）、目标JSON解析、差异/空白检查通过；交付ZIP由打包脚本核验109个文件及包内SHA，最终SHA见交付信息。
- 仅离线代码修改，未连接NAS、数据库或房源网站，未部署；真实规模性能尚未测量。

## 2026-11-11 P0-03防止空挂牌文本覆盖已有字段
- `ListingIn`可选文本原样接收空格字符串；upsert以`COALESCE`更新时，空字符串会替换数据库中的既有标题/URL/区域等值，而不是按缺省保留。
- 标题、挂牌URL、区域、楼层、装修、备注现先裁剪，纯空白归一为`None`，有效值保留规范化文本。新增回归先失败后通过。
- 模型/条件单/机会专项 **72 passed**；全量`pytest -q -rs` **479 passed、14 skipped**（DB集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。数据库集成未运行，真实持久化未验收；仅离线验证，未部署。
- API文档、GOAL_STATE、路线图与变更记录同步。

## 2026-11-11 P0-03清除抖音账户链接空query/fragment分隔符
- `AccountIn`已清除非空query/fragment，但空`?`或`#`分隔符此前会保留在规范化后的账户资料URL。
- 现在按原始URL中分隔符是否存在执行清理；回归覆盖有值和空的query/fragment五种组合。
- `tests/test_models.py -k douyin_profile_url_drops` **5 passed**；全量`pytest -q -rs` **478 passed、14 skipped**（DB集成需`TEST_DATABASE_URL`），保留1条既有弃用警告。离线验证，未连接抖音/NAS或真实数据库。
- API文档和GOAL_STATE已同步，未部署。

## 2026-11-11 P0-03规范条件单可选文本筛选
- 复现条件单区域/小区传纯空格时仍被视为有效筛选条件，运行匹配时会意外排除所有挂牌。
- `SavedSearchIn`现裁剪`district`、`community_name`首尾空白，并将纯空白归一为`None`；新增回归通过。
- 模型/条件单专项 **51 passed**；全量`pytest -q -rs` **474 passed、14 skipped**（PostgreSQL集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。离线验证，未部署。

## 2026-11-11 P0-03规范账户、视频及条件单必填文本
- 复现`AccountIn`裁剪后才检查长度导致单字符账户引用可过校验，`VideoIn.source_post_id`及`SavedSearchIn.name`接受空白值。
- 现在账号标识、视频作品ID与条件单名称均在字段长度验证前裁剪首尾空格并拒绝纯空白；新增9条回归先失败后通过。
- 全量`pytest -q -rs`：**473 passed、14 skipped**（PostgreSQL集成需`TEST_DATABASE_URL`），保留1条既有Starlette/httpx弃用警告。仅离线模型/API验证，无真实DB/NAS/平台连接或部署。
- API文档与GOAL_STATE同步；P0-07四项运营比率口径待用户确认。

## 2026-11-11 P0-03对齐来源ID数据库集成fixture
- 复核`tests/test_db_integration.py`发现4个跨平台挂牌API样本仍用`beike-...`/`anjuke-...`非数字ID，与当前正式模型约束冲突；改为随机十进制ID，避免数据库集成恢复后在API校验处提前失败。
- 全量默认`pytest -q -rs`仍为 **464 passed、14 skipped**；跳过均为需`TEST_DATABASE_URL`的PostgreSQL集成用例，因此这4个fixture本轮未实际连库运行。其他直接SQL插入的V0.1历史挂牌值故意保留为旧格式，以验证迁移不篡改既有数据。
- 未连接数据库、NAS或来源网站；无运行数据/迁移变化。

## 2026-11-11 P0-09离线挂牌链接发现基础
- 新增`discover_listing_links`及本地HTML CLI：只识别允许的宁波来源主机与站点详情ID，按ID去重，可排除既有ID；仅接受无查询/片段的安全`rel="next"`地址。跳过导航、推荐、表单、脚本、hidden/display:none、透明、折叠区，保留可见ARIA-hidden链接和visibility显式可见后代。1MB输入上限，未发出网络请求。
- 对来源URL策略补齐空`?`/`#`分隔符拒绝，避免空查询/片段绕过“不含query/fragment”边界。
- 发现器/CLI与来源URL/解析专项 **146 passed**；全量`pytest -q -rs` **464 passed、14 skipped**（PostgreSQL集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。CLI实测本地快照和超限拒绝；编译、GOAL_STATE JSON及变更文件尾随空白扫描通过。
- CLI说明见`docs/DISCOVERY.md`。P0-09仍未完成：游标持久化、失败重试、失效标记和站点专用列表页选择器尚缺；需先有P0-04允许范围与真实页面/分页样本。未连接来源网站、NAS或业务数据库，未部署。

## 2026-11-11 P0-03规范正式挂牌与小区名称输入
- 复现正式挂牌入口接受`agent`/`other`纯空格ID、不裁剪有效ID首尾空格，以及挂牌/新建小区接受纯空白名称；这些字段在人工纠正中已有空白拒绝规范。
- `ListingIn`现对所有来源ID、小区名裁剪首尾空白并拒绝纯空白；`CommunityIn`小区名执行相同规范化。贝壳/安居客仍按ASCII数字及8/7–220位校验，`agent`/`other`自有ID格式保持兼容。新增12条回归先复现失败后通过。
- 定向模型/服务测试 **73 passed**；全量`pytest -q -rs` **451 passed、14 skipped**（PostgreSQL集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。仅离线验证，未连接真实数据库、NAS或来源网站，未部署。
- API契约、GOAL_STATE、路线图与变更记录已更新；P0-01真实V0.1备份、P0-02获准页面样本等外部验收仍待材料。

## 2026-11-11 P0-03挂牌来源ID边界回归复核
- 新增`ListingIn`贝壳8位、安居客7位最小长度，以及`agent`/`other`自有ID格式兼容的参数化回归。
- 全量`pytest -q -rs`：**439 passed、14 skipped**（均需`TEST_DATABASE_URL`的PostgreSQL集成），保留1条Starlette/httpx弃用警告。跳过数据库集成不构成迁移验收。
- `compileall`、GOAL_STATE JSON、`git diff --check`及开发ZIP包内哈希/ZIP完整性校验通过。
- 仅离线验证，未连接真实数据库、NAS或来源网站，未部署；P0-01真实V0.1备份及P0-02获准页面样本仍缺。

## 2026-11-11 P0-03在挂牌入口和审批入口校验来源ID
- 本轮目标与状态：完成。此前source-specific数字ID校验仅覆盖人工纠正入口，直接`ListingIn`写入及历史遗留待审候选批准仍可能使用非平台ID。
- `ListingIn`现在对贝壳/安居客按8/7–220位ASCII数字校验；`agent`/`other`自有ID格式保持兼容。无效历史候选审批返回409并明确`source_listing_id`字段。
- 新增来源格式正反边界和旧候选批准阻断回归；全量pytest **435 passed、14 skipped**（需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。`compileall`、GOAL_STATE JSON及`git diff --check`通过；边界复核见上条记录。
- API文档同步；无数据库迁移或配置变化。仅离线模型/桩数据库验证，未连接真实数据库、NAS或来源网站，未部署。
- 下一步：真实获准样本及人工标签到位后执行九字段评估；V0.1备份到位后完成隔离迁移保真验收。

## 2026-11-11 P0-03按来源校验人工纠正的挂牌ID
- 本轮目标与状态：完成。此前人工纠正ID只限制7–220字符，非数字值可进入候选；7位ID也可能写入贝壳候选。
- `CandidateCorrection`现只接受数字ID；`correct_candidate`按候选来源校验贝壳8–220位、安居客7–220位。新增非数字拒绝、贝壳7位拒绝、安居客7位接受回归。
- 全量pytest **430 passed、14 skipped**（需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告；`compileall`、GOAL_STATE JSON及变更文件尾随空白扫描通过。API文档已同步。
- 无数据库迁移或配置变化；仅离线模型/桩数据库验证，未连接NAS、来源网站或真实数据库，未部署。
- 下一步：获准页面与人工标签到位后运行九字段分来源评估；V0.1备份到位后做隔离迁移保真验证。

## 2026-11-11 P0-03规范人工纠正的文本输入
- 本轮目标与状态：完成。修复`CandidateCorrection`接受空格小区名/区域/楼层/装修、来源ID和审核备注的问题；其中空格小区名可能被必填检查当作有效值。
- 来源ID、标题、小区、区域、楼层、装修和审核备注现在先去除首尾空白，再执行长度/类型校验；纯空白字符串拒绝，可空字段仍可用`null`显式清除。新增7种空白字段拒绝及规范化后长度边界回归；定向9 passed。
- 全量pytest **427 passed、14 skipped**（需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告；`compileall`、GOAL_STATE JSON及`git diff --check`通过。API文档已同步。
- 无数据库迁移或配置变化；未连接数据库、NAS或来源网站，未部署。
- 材料盘点仍只有`data/raw-pages/.gitkeep`，无真实HTML清单或V0.1备份。后续优先完成离线工具与审核链路，材料到位后再验收P0-01/02/03。

## 2026-11-11 P0-03拒绝空白人工标题纠正
- 本轮目标与状态：完成。`CandidateCorrection`此前只限制标题长度，纯空白字符串可通过并覆盖候选标题。现拒绝纯空白标题，并去除有效标题首尾空格。
- 新增回归先复现再通过；全量pytest **419 passed、14 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。`compileall`、GOAL_STATE JSON解析和`git diff --check`通过。
- API模型行为文档已同步。无数据库迁移或配置变化；仅离线验证，未连接数据库、NAS或房源网站，未部署。
- 本机材料盘点仍只有`data/raw-pages/.gitkeep`，未找到样本清单或V0.1数据库备份。后续优先等待获准样本/备份并继续离线任务。

## 2026-11-11 P0-03核验人工纠正标题的证据标记
- 本轮目标与状态：完成回归补强。人工改写候选标题后，保存值应变为人工审核值，证据来源应标记`manual_review`，避免继续显示旧的自动识别来源。
- 扩展服务层人工纠正回归，同时纠正标题和小区。定向1 passed；全量pytest **418 passed、14 skipped**（需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。`compileall`及`git diff --check`通过。
- 仅桩化数据库验证，无真实数据库、NAS或来源网站操作；未部署，无迁移/配置变化。
- 下一步：真实获准样本到位后运行九字段分来源评估；V0.1备份到位后进行隔离迁移保真验证。

## 2026-11-11 P0-03核验标题证据进入待审候选
- 本轮目标与状态：完成服务边界回归。`stage_html`生成的`extracted_fields`会连同`field_evidence.title`的标题值、来源和引用文本一起写入候选，供人工审核读取。
- 更新服务层桩数据库回归，使用真实解析函数并检查传入JSON字段；定向1 passed。全量pytest **418 passed、14 skipped**（需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告；`compileall`和`git diff --check`通过。
- 未连接实际数据库、来源网站或NAS，未部署；数据库集成仍跳过。标题样本准确率还需获准真实HTML及人工标注验证。无迁移或配置变化。
- 下一步：待获准真实样本后完成P0-02/P0-03指标验收；待V0.1备份后完成P0-01迁移保真。离线期间继续维护解析器与审核链路回归。

## 2026-11-11 P0-03将标题纳入准确率评估
- 本轮目标与状态：完成评估工具扩展。此前解析器已输出标题证据，但人工样本清单和分字段准确率只覆盖8个字段，导致标题提取无正式度量。
- CSV模板和校验器新增必需`title`人工标签；最大500字符，空值必须由`missing_fields`解释。评估器现按来源报告包含标题在内的9项字段准确率、覆盖率和精确率；`docs/ACCEPTANCE.md`同步将标题纳入每项95%目标。
- 新增标题准确率、缺标题、超长标题回归。解析器/评估器/样本清单专项 **233 passed**；全量pytest **418 passed、14 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。`compileall`及`git diff --check`通过。
- 仅虚构样本验证工具逻辑，不代表真实页面准确率；未连接数据库、来源网站或NAS，未部署。无数据库迁移或运行配置变化。清单schema已更新，尚无用户真实样本清单需迁移。
- 下一步：继续P0-03离线验证；获准真实HTML和逐字段人工标注到位后运行分来源评估；拿到V0.1备份后在隔离库验证P0-01。

## 2026-11-11 P0-03记录解析标题的来源证据
- 本轮目标与状态：完成。标题现在按`og:title`→`h1`→`head title`择取，并在`field_evidence.title`记录实际来源和引用文本，供人工审核追溯。
- 新增三种来源的参数化回归，确认元数据优先顺序与证据字段一致。解析器版本升至`generic-labelled-v0.2.49`。
- 专项测试：**230 passed**；全量`pytest -q -rs`：**415 passed、14 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。`compileall`、GOAL_STATE JSON解析及`git diff --check`通过。
- 无数据库迁移或配置变化；仅合成HTML离线验证，未连接数据库、来源网站或NAS，未部署。真实页面字段准确率仍未验证。
- 下一步：继续P0-03离线解析回归；取得每站20份获准HTML后报告分字段准确率/覆盖率；取得V0.1备份后在隔离库验证P0-01迁移保真。真实材料当前均缺。

## 2026-11-11 P0-03忽略空白标题并继续回退
- 成功标准：`og:title`或`h1`只有空白时，继续取下一个非空来源；顺序为`og:title`→`h1`→`head title`。
- 新增空白`og:title`失败回归、空白`h1`回退回归；前者修复前失败，修复后均通过。解析器版本升至`generic-labelled-v0.2.48`。
- 解析器/评估器/样本清单专项 **227 passed**；全量pytest **412 passed、14 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。`compileall`及`git diff --check`通过。
- 仅合成HTML离线验证，未连接数据库、来源网站或NAS，未部署；无迁移或配置变化。真实解析质量仍待每站20份获准样本。

- 下一步：继续用合成回归推进P0-03（验收为专项及全量回归通过）；取得每站20份获准HTML后报告分字段准确率/覆盖率；取得V0.1备份后在隔离库验证P0-01迁移保真。当前两类材料均缺，不虚报验收。

## 2026-11-11 P0-03补齐head title备用标题来源
- 成功标准：缺少`og:title`与`h1`时，从`head title`填充标题；优先级固定为`og:title`→`h1`→`head title`。
- 新增失败回归后实现备用来源，解析器版本升至`generic-labelled-v0.2.47`。解析器/评估器/样本清单专项 **225 passed**；全量pytest **410 passed、14 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- `git diff --check`通过。仅合成HTML离线验证，未连接数据库、来源网站或NAS，未部署；真实页面准确率仍待每站20份获准样本。

## 2026-11-11 P0-03排除详情区域的交互表单字段
- 失败回归复现：`main`内筛选/询价表单包含小区、建筑面积和总价输入提示，被解析为与挂牌详情冲突的字段。
- 解析预处理现移除`form`及独立`button`、`select`、`textarea`，避免交互控件稀释页面挂牌证据。解析器版本升至`generic-labelled-v0.2.46`。
- 解析器/评估器/样本清单专项 **224 passed**；全量pytest **409 passed、14 skipped**（需`TEST_DATABASE_URL`），`compileall`、GOAL_STATE JSON解析及`git diff --check`通过；保留1条Starlette/httpx弃用警告。
- 仅合成HTML离线验证；未连接数据库、来源网站或NAS，未部署。无数据库迁移或配置变化。
- 刷新`MANIFEST.sha256`并生成同级开发包`../ningbo-re-ai-v0.2-dev-2026-11-11-form-controls.zip`，构建器校验ZIP完整性和包内哈希。

## 2026-11-11 P0-03限制页面身份元数据在head内
- 失败回归复现：body里的非标准canonical/og:url造成来源ID误冲突，body里的og:title覆盖了页面标题。
- canonical link和Open Graph URL/title现只从`head`读取；标准canonical link不允许放在body，OG基本元数据也约定放在head。解析器版本升至`generic-labelled-v0.2.45`。
- 解析器/评估器/样本清单专项 **223 passed**；全量pytest **408 passed、14 skipped**（需`TEST_DATABASE_URL`），`compileall`、GOAL_STATE JSON解析及`git diff --check`通过；保留1条Starlette/httpx弃用警告。
- 仅合成HTML离线验证；未连接数据库、来源网站或NAS，未部署。无数据库迁移或配置变化。
- 刷新`MANIFEST.sha256`并生成同级开发包`../ningbo-re-ai-v0.2-dev-2026-11-11-head-metadata.zip`，构建器校验ZIP完整性和包内哈希。

## 2026-11-11 P0-03按标准匹配canonical rel关键字
- 失败回归复现：`rel="alternate CANONICAL"`未被大小写敏感的匹配识别，canonical URL 的房源 ID 冲突未触发保护。
- `rel`按ASCII空白分词，并按ASCII大小写不敏感精确匹配`canonical`；不会将其他 token 的子串误当canonical。解析器版本升至`generic-labelled-v0.2.44`。
- 解析器/评估器/样本清单专项 **222 passed**；全量pytest **407 passed、14 skipped**（需`TEST_DATABASE_URL`），`compileall`、GOAL_STATE JSON解析及`git diff --check`通过；保留1条Starlette/httpx弃用警告。
- 仅合成HTML离线验证；未连接数据库、来源网站或NAS，未部署。无数据库迁移或配置变化。
- 刷新`MANIFEST.sha256`并生成同级开发包`../ningbo-re-ai-v0.2-dev-2026-11-11-canonical-rel-case.zip`，构建器校验ZIP完整性和包内哈希。

## 2026-11-11 P0-03排除template惰性元数据
- 失败回归复现：模板子树中的canonical/og:url把来源ID误判为冲突，og:title覆盖可见页面标题；模板内容虽不进入`stripped_strings`，仍被元数据查询扫描。
- 解析前移除`template`节点，避免其中的惰性正文、链接及Open Graph元数据参与字段提取。解析器版本升至`generic-labelled-v0.2.43`。
- 解析器/评估器/样本清单专项 **221 passed**；全量pytest **406 passed、14 skipped**（需`TEST_DATABASE_URL`），`compileall`、GOAL_STATE JSON解析及`git diff --check`通过；保留1条Starlette/httpx弃用警告。
- 仅合成HTML离线验证；未连接数据库、来源网站或NAS，未部署。无数据库迁移或配置变化。
- 刷新`MANIFEST.sha256`并生成同级开发包`../ningbo-re-ai-v0.2-dev-2026-11-11-template-metadata.zip`，构建器校验ZIP完整性和包内哈希。

## 2026-11-11 P0-03过滤折叠details摘要中的隐藏文本
- 失败回归复现：折叠`details`把`summary`提前压平成纯文本，隐藏样式清理之前就将摘要里的隐藏报价纳入挂牌字段。
- 现先移除隐藏文本，再保留首个直接`summary`的可见内容；嵌套`details`按内层到外层处理。解析器版本升至`generic-labelled-v0.2.42`。
- 折叠详情专项 **8 passed**；解析器/评估器/样本清单 **220 passed**；全量pytest **405 passed、14 skipped**（需`TEST_DATABASE_URL`）。`compileall`、GOAL_STATE JSON解析及`git diff --check`通过；保留1条Starlette/httpx弃用警告。
- 仅合成HTML离线验证；未连接数据库、来源网站或NAS，未部署。无数据库迁移或配置变化。
- 刷新`MANIFEST.sha256`并生成同级开发包`../ningbo-re-ai-v0.2-dev-2026-11-11-details-summary-visibility.zip`，构建器校验ZIP完整性和包内哈希。

## 2026-11-11 P0-03排除content-visibility隐藏文本
- 失败回归复现：`content-visibility:hidden`广告挂牌价及其后代进入解析，导致与可见挂牌价冲突。HTML标准定义该值会跳过元素内容渲染。
- 显式栈遍历现在传播祖先`content-visibility:hidden`状态；隐藏祖先下的后代即使设置`content-visibility:visible`也不会被解析。解析器版本升至`generic-labelled-v0.2.41`。
- 解析器/评估器/样本清单专项 **215 passed**；全量pytest **400 passed、14 skipped**（需`TEST_DATABASE_URL`），`compileall`、GOAL_STATE JSON解析及`git diff --check`通过；保留1条Starlette/httpx弃用警告。
- 仅合成HTML离线验证；未连接数据库、来源网站或NAS，未部署。无数据库迁移或配置变化。
- 刷新`MANIFEST.sha256`并生成同级开发包`../ningbo-re-ai-v0.2-dev-2026-11-11-content-visibility.zip`，构建器校验ZIP完整性和包内哈希。

## 2026-11-11 P0-03尊重hidden属性的内联display覆盖
- 失败回归复现：`hidden`节点有`display:block`时浏览器会显示内容，但解析器无条件移除该节点，漏掉可见字段和冲突报价。
- 解析器现保留带常见有效非`none`内联`display`值的普通`hidden`节点；`display:none`和`hidden="until-found"`仍按隐藏处理。解析器版本升至`generic-labelled-v0.2.40`。
- 解析器/评估器/样本清单专项 **213 passed**；全量pytest **398 passed、14 skipped**（需`TEST_DATABASE_URL`），`compileall`、GOAL_STATE JSON解析及`git diff --check`通过；保留1条Starlette/httpx弃用警告。
- 仅合成HTML离线验证；未连接数据库、来源网站或NAS，未部署。无数据库迁移或配置变化。
- 刷新`MANIFEST.sha256`并生成同级开发包`../ningbo-re-ai-v0.2-dev-2026-11-11-hidden-display.zip`，构建器校验ZIP完整性和包内哈希。

## 2026-11-11 P0-08留存策略文档一致性
- 用户已确认数据库备份保留90天，原始页面证据随关联数据库记录保留；修正`docs/ACCEPTANCE.md`仍将期限标为待决定的旧文字。
- 当前规则：`storage_report.py`仅列出严格早于90天的备份候选，不自动删除；清理备份前核对可恢复性，清理原始证据前核对数据库引用。
- 本轮仅文档修改；全量pytest **393 passed、14 skipped**（均需`TEST_DATABASE_URL`），`compileall`、GOAL_STATE JSON解析和`git diff --check`通过；保留1条Starlette/httpx弃用警告。未连接数据库、来源网站或NAS，未部署。
- 刷新`MANIFEST.sha256`并生成同级开发包`../ningbo-re-ai-v0.2-dev-2026-11-11-retention-docs.zip`，构建器将校验ZIP完整性和包内文件哈希。

## 2026-11-11 P0-03固定template惰性内容不参与解析
- 检查`<template>`中的广告挂牌价是否会污染可见正文；当前BeautifulSoup `stripped_strings`会跳过template惰性内容，回归在未改解析器实现时通过。
- 新增测试锁定模板内容不会进入挂牌字段/多价冲突；未添加冗余过滤代码，解析器版本不变。
- 定向：**1 passed**；全量：**393 passed、14 skipped**（数据库集成需`TEST_DATABASE_URL`）；`compileall`和GOAL_STATE JSON校验通过；保留1条Starlette/httpx弃用警告。
- 仅合成HTML离线验证，未连接数据库、网站或NAS，未部署。
- 刷新`MANIFEST.sha256`并生成同级开发包`../ningbo-re-ai-v0.2-dev-2026-11-11-template-content.zip`；构建器核验ZIP完整性及包内SHA清单。

## 2026-11-11 P0-03跳过已脱离文档树的隐藏节点
- 失败回归复现：处理外层`display:none`容器后，循环仍读取已被`decompose()`的内层标签属性，触发`AttributeError`。
- 在各批量移除DOM节点的循环中跳过已脱离节点，避免嵌套的`display:none`、`hidden`、关闭`dialog/details`及导航/侧栏元素导致解析中断。
- 嵌套隐藏节点专项：**5 passed**；全量：**392 passed、14 skipped**（数据库集成需`TEST_DATABASE_URL`）；`compileall`和GOAL_STATE JSON校验通过；保留1条Starlette/httpx弃用警告。
- 仅合成HTML离线验证；未连接数据库、网站或NAS，未部署；解析器版本与字段规则不变。
- 刷新`MANIFEST.sha256`并生成同级开发包`../ningbo-re-ai-v0.2-dev-2026-11-11-parser-nested-removal.zip`；构建器核验ZIP完整性及包内SHA清单。

## 2026-11-11 P0-03避免深层HTML触发递归溢出
- 失败回归复现：1,200层嵌套`div`会使可见性递归遍历触发`RecursionError`，即使HTML远低于1 MB上限。
- 将可见性/透明度遍历改为显式栈，不依赖Python递归深度；CSS处理语义保持不变，解析器版本不变。
- 深层HTML/可见性/透明度定向：**17 passed**；全量：**387 passed、14 skipped**（数据库集成需`TEST_DATABASE_URL`）；`compileall`和GOAL_STATE JSON校验通过；保留1条Starlette/httpx弃用警告。
- 仅合成HTML离线验证；未连接数据库、网站或NAS，未部署。
- 刷新`MANIFEST.sha256`并生成同级开发包`../ningbo-re-ai-v0.2-dev-2026-11-11-parser-depth.zip`；构建器核验ZIP完整性及包内SHA清单。

## 2026-11-11 P0-03识别opacity为零的内联隐藏文本
- 失败回归确认：`opacity:0`广告报价会参与挂牌冲突；父元素透明度为零时，子元素设为`opacity:1`也无法恢复可见性。
- 解析器现在将内联`opacity:0`/`0%`作为不可见状态，按CSS透明度合成继承至后代；同样遵循声明顺序与`!important`。解析器升至`generic-labelled-v0.2.39`。
- 透明度/可见性专项：**10 passed**；全量：**386 passed、14 skipped**（数据库集成需`TEST_DATABASE_URL`）；`compileall`和GOAL_STATE JSON校验通过；保留1条Starlette/httpx弃用警告。
- 仅合成HTML离线验证，真实站点CSS/布局未校准；未连接数据库、网站或NAS，未部署。
- 刷新`MANIFEST.sha256`并生成同级开发包`../ningbo-re-ai-v0.2-dev-2026-11-11-parser-opacity.zip`；构建器验证ZIP完整性和包内SHA清单。

## 2026-11-11 P0-03识别内联visibility隐藏文本
- 失败回归复现：内联`visibility:hidden`的广告报价会被当成可见内容，与挂牌价冲突并清空字段；另覆盖隐藏父级下显式`visibility:visible`子节点仍应参与解析。
- 解析器现在按内联`visibility`继承关系移除隐藏文本，允许后代`visible`覆盖隐藏祖先；解析器版本升至`generic-labelled-v0.2.38`。
- 解析器/可见性级联定向测试：**11 passed**；全量：**380 passed、14 skipped**（数据库集成需`TEST_DATABASE_URL`）；`compileall`和GOAL_STATE JSON校验通过；保留1条Starlette/httpx弃用警告。
- 仅合成HTML离线验证，真实站点CSS/布局准确率未验证；未连接数据库、网站或NAS，未部署。
- 刷新`MANIFEST.sha256`并生成同级开发包`../ningbo-re-ai-v0.2-dev-2026-11-11-parser-visibility-cascade.zip`；构建器核验ZIP完整性和包内SHA清单。

## 2026-11-11 P0-03精确比较95%评估门槛
- 失败回归确认：1,899/1,999的实际精确率为94.997...%，展示值四舍五入为95.00%，旧逻辑错误标记达标。
- `precision_target_met`现在直接比较正确数与抽取数（整数交叉相乘），报告中的百分比仍按两位小数展示；样本量门槛保持独立。
- 精确率门槛专项：**4 passed**；全量：**375 passed、14 skipped**（数据库集成需`TEST_DATABASE_URL`）；`compileall`和GOAL_STATE JSON校验通过；保留1条Starlette/httpx弃用警告。
- 仅合成清单/HTML离线验证，未连接数据库、网站或NAS，未部署。真实获准样本准确率仍待验证。
- 刷新`MANIFEST.sha256`并生成同级开发包`../ningbo-re-ai-v0.2-dev-2026-11-11-precision-threshold.zip`；构建器已核验ZIP完整性和包内SHA清单。

## 2026-11-11 P0-04有界读取HTTP来源响应
- 失败回归确认，`client.get()`在超限检查前已缓冲完整响应；8 MB模拟页面与robots响应均被全部读取，才返回超限错误。
- HTTP客户端改用流式读取：页面上限1,000,000字节、robots上限256,000字节，按64 KB分块并在超限时停止；添加响应Content-Length预检，并保留状态码、挑战页和robots fail-closed行为。
- `tests/test_collection_http.py`：**17 passed**；全量pytest：**374 passed、14 skipped**（数据库集成需`TEST_DATABASE_URL`），`compileall`通过；保留1条Starlette/httpx弃用警告。
- 仅MockTransport本地测试；未实际联网、连接NAS或部署。P0-04来源许可仍未确认，在线来源保持关闭。

## 2026-11-11 P0-08拒绝软链接raw-pages证据目录
- 失败回归复现`RAW_HTML_DIR`指向目录软链接时会跟随链接，在备份/库存工具不遍历的目标目录写入证据；现在写入前后均拒绝软链接存储目录。
- 保持前轮损坏gzip、错误内容gzip与SHA目标文件软链接重建逻辑；`tests/test_collection_service.py -k save_html`：**4 passed**；全量：**371 passed、14 skipped**，数据库集成需`TEST_DATABASE_URL`；保留1条Starlette/httpx弃用警告。`compileall`通过。
- 仅本机临时文件系统和假数据库验证；未连接或更改NAS，未部署。

## 2026-11-11 P0-08修复重复提交复用损坏证据
- 回归先复现：内容寻址的HTML证据文件已存在时，仅凭路径存在就复用；gzip损坏、内容不匹配或路径被软链接占用时，候选仍可能引用无效/外部证据。
- `_save_html`现在对既有非软链接gzip作有界解压，并逐字节核对本次HTML；校验失败或目标为软链接时走原子替换，保持正确的内容寻址文件。
- 新增损坏gzip、合法但内容不符gzip、软链接三项回归；定向3 passed，全量**370 passed、14 skipped**，14项需`TEST_DATABASE_URL`；保留1条Starlette/httpx弃用警告。`compileall`通过。
- 仅本地文件系统/假数据库逻辑验证；未检查或修改NAS库存，也未部署，真实PostgreSQL集成仍未运行。

## 2026-11-11 数值精度尾随零的正向契约回归
- 增加候选纠错正向回归：`120.2300`/`365.1200`归一为两位小数；与挂牌模型的长尾零精度回归共同固定只拒绝数值会改变的输入。
- 定向2 passed；全量：**367 passed、14 skipped**，数据库集成需`TEST_DATABASE_URL`；保留1条Starlette/httpx弃用警告。`compileall`通过。
- 仅模型验证，无数据库/NAS连接或部署。

## 2026-11-11 P0-03审批精度错误的HTTP契约回归
- 增加FastAPI `TestClient`回归，使用API Key调用候选审批路由；数据库模型校验发现面积/报价超精度时，响应为409且明确指出待纠正字段。
- 解析器/服务/API专项：**109 passed**；全量：**365 passed、14 skipped**，14项需`TEST_DATABASE_URL`；保留1条Starlette/httpx弃用警告。`compileall`通过。
- 路由由真实本地FastAPI应用执行，数据库为假连接；未运行真实PostgreSQL/NAS或部署。

## 2026-11-11 P0-03超精度警告贯穿候选暂存
- 新增服务层回归验证解析器的面积/挂牌价超精度警告与字段证据一起写入待审核候选，返回`ready_for_review=false`，不在暂存时丢失。
- 解析器/服务专项：**107 passed**；全量：**364 passed、14 skipped**，14项需`TEST_DATABASE_URL`；保留1条Starlette/httpx弃用警告。`compileall`通过。
- 仅本机合成页面与假数据库验证；未运行真实PostgreSQL/NAS或部署。

## 2026-11-11 P0-03检查页面原始数字文本的两位小数边界
- 新回归复现长小数先转`float`后精度丢失：页面`160.00000000000000001㎡`会变成160.0，旧检查未发现不可无损写入的原始值。
- 精度检查现直接读取解析命中的原始数字字符串；按Decimal系数/指数识别分币位非零，额外尾随零仍可接受，避免依赖当前Decimal上下文的`quantize`精度限制。解析器版本升至`generic-labelled-v0.2.37`。
- 解析器/服务专项：**106 passed**；全量：**363 passed、14 skipped**，14项需`TEST_DATABASE_URL`；保留1条Starlette/httpx弃用警告。`compileall`通过。
- 仅合成HTML和假数据库验证；真实页面数字格式、PostgreSQL集成及NAS部署未验证。

## 2026-11-11 P0-03解析精度与数据库入库边界
- 回归确认解析出的`160.005㎡`/`365.005万`原先会显示`ready_for_review=true`，但正式挂牌模型与PostgreSQL两位小数列拒绝该精度，审批可能返回未处理的模型错误。
- 解析器升至`generic-labelled-v0.2.36`；保留原抽取数值并记录字段级`numeric_precision_requires_correction:*`警告、阻止候选ready。审批先返回409要求纠正；历史候选即使无警告也把模型校验错误映射成409。人工纠正只清除对应字段警告。
- 定向解析器/服务测试：**104 passed**；全量：**361 passed、14 skipped**，14项需`TEST_DATABASE_URL`；保留1条Starlette/httpx弃用警告。`compileall`通过。
- 仅本机合成页面/假数据库验证，未连接PostgreSQL/NAS或部署；真实页面精度分布未知。

## 2026-11-11 P0-03缺字段场景拒绝被截断样本误通过
- 回归先复现：人工标注某字段缺失，但该字段实际值位于35,000字符解析上限之后时，评估器仍将`missing_fields`场景计为通过。
- 评估器现要求缺字段场景样本没有`visible_text_truncated`警告才通过；其它字段指标与解析器行为不变。
- 定向`tests/test_parser_evaluation.py tests/test_sample_set.py`：**96 passed**；全量：**357 passed、14 skipped**，14项需`TEST_DATABASE_URL`；保留1条Starlette/httpx弃用警告。`compileall`通过。
- 仅合成HTML/清单离线验证；真实获准样本、准确率、PostgreSQL集成与NAS部署未验证。

## 2026-11-11 API数值输入对齐PostgreSQL两位精度
- PostgreSQL挂牌/条件单数值列使用`NUMERIC(...,2)`，但API模型之前接受超过两位且不可等价归一的Decimal，写库时会静默舍入。现挂牌录入、条件单创建、候选纠错均拒绝数值会改变的第三位小数；尾随零等价输入接受并规范成两位。
- 专项`tests/test_models.py tests/test_collection_models.py`：**7 passed**；全量：**356 passed、14 skipped**，14项需`TEST_DATABASE_URL`；保留1条Starlette/httpx弃用警告。`compileall`、GOAL_STATE JSON解析、`git diff --check`通过。
- 仅本机模型/API离线验证；数据库集成未运行，未连接NAS或部署。

## 2026-11-11 P0-01迁移脚本静态安全复核
- 静态检查002–005：002为新增采集表/字段及来源默认记录；003使用`CREATE INDEX IF NOT EXISTS`；004在事务内锁定来源表、由现存业务表回填健康汇总并重建触发器；005为条件单增列及幂等约束。未发现删除业务表/行的SQL。
- 当前`TEST_DATABASE_URL`未配置，本机127.0.0.1:5432无PostgreSQL响应；本轮没有执行SQL、连接数据库/NAS或运行迁移集成测试。静态阅读不证明SQL运行正确，也不替代V0.1真实备份升级和逐字段保真核对；P0-01保持blocked。

## 2026-11-11 P2-01可比面积阈值精确边界
- 回归先复现：目标100㎡、可比110㎡时，float舍入让`abs(1.1-1)>0.10`成立，错误排除恰好+10%；恰好−10%原本可纳入。
- 相对面积差改用Decimal，按目标挂牌面积为分母；±10%均纳入，±10.01%排除，保持原有10%阈值。
- 定向`tests/test_opportunities.py`：**16 passed**；全量：**349 passed、14 skipped**，14项需`TEST_DATABASE_URL`；保留1条Starlette/httpx弃用警告。`compileall`、GOAL_STATE JSON解析、`git diff --check`通过。
- 仅合成数据本机验证；未运行PostgreSQL集成、未访问NAS或部署。

## 2026-11-10 P2-01修复可比面积阈值浮点边界
- 先复现同小区/户型可比面积恰好比目标大10%时，float舍入使`abs(1.1-1)>0.10`意外成立、可比房源被排除；低10%边界原本能通过。
- 面积相对差现使用Decimal并以目标挂牌面积为分母，保留既有10%阈值且正负边界一致；新增±10%回归。
- `tests/test_opportunities.py`：**14 passed**；全量：**347 passed、14 skipped**，14项需`TEST_DATABASE_URL`；保留1条Starlette/httpx弃用警告。`compileall`、GOAL_STATE JSON解析、`git diff --check`通过。
- 仅合成挂牌离线验证；未运行PostgreSQL集成、未访问NAS或部署。

## 2026-11-10 P2-01排除户型未知房源的可比价误报
- 回归复现：目标房源和5套可比挂牌的`bedrooms`均为空时，Python将`None == None`当作相同户型，系统错误生成低于可比中位数的机会信号。
- 可比池现要求目标户型已知；未知户型的挂牌不用于同户型单价中位数。`tests/test_opportunities.py`新增用例，先失败后通过。
- 定向`tests/test_opportunities.py`：**12 passed**；全量：**345 passed、14 skipped**，14项需`TEST_DATABASE_URL`；保留1条Starlette/httpx弃用警告。`compileall`、GOAL_STATE JSON解析、`git diff --check`通过。
- 仅合成挂牌与本机代码验证；未运行PostgreSQL集成、未访问NAS或部署。

## 2026-11-10 P0-03证据展示上限之后的报价/面积冲突回归
- 新增两条解析器回归：第21条同字段命中与前20条不同，确认解析值仍清空、对应`multiple_*_mentions`告警存在、命中总数为21且候选不能ready。既有解析逻辑会扫描全文后判定冲突；本轮以测试固定该行为，没有改解析器实现。
- 定向：`tests/test_collection_parser.py -k conflict_after_evidence_cap_still_blocks_review_ready` → **2 passed**；全量：**344 passed、14 skipped**，14项需`TEST_DATABASE_URL`；保留1条Starlette/httpx弃用警告。`compileall`、GOAL_STATE JSON解析、`git diff --check`通过。
- 仅合成HTML离线验证；不代表真实页面准确率或数据库/NAS验收。

## 2026-11-10 P0-03评估器离线复核与全量回归
- 审阅样本清单校验器和评估器对字段分母、冲突候选集合、截断证据、样本哈希及来源覆盖的处理；本次未发现可复现的误通过缺陷，未改解析器/评估器代码。
- 全量离线验证：`/private/tmp/ningbo-re-ai-verify-venv/bin/python -m pytest -q -rs` → **342 passed、14 skipped**；14项均需`TEST_DATABASE_URL`，另有1条Starlette/httpx弃用警告。
- 仅虚构HTML/清单及本地代码；未连接数据库、NAS或来源网站。真实页面准确率、PostgreSQL集成与NAS部署仍未由本次验证。

## 2026-11-10 P0-07健康指标验收口径缺口复核
- 对照`docs/ACCEPTANCE.md`第43行与当前`GET /api/collection/health`实现：API已提供采集运行、候选审核和挂牌计数，但尚未提供采集成功、解析成功、字段完整、人工审核通过四种比率。
- 采集运行和审核状态可由现有计数派生；审核通过率是否排除待审项尚待确认。解析成功与字段完整没有已确认的状态/字段判定口径，不自行定义。
- 将P0-07从已验证调整为进行中，避免把计数接口误报为完整满足比率验收。当前不改API或数据库；已向用户征询口径，收到答复后再实现并验证。

## 2026-11-10 P0-03评估器识别截断点后的冲突报价
- 本轮目标：确认挂牌价冲突位于35,000字符抽取上限之后时，样本评估不能将`multiple_prices`场景记为通过。
- 已完成：新增评估器回归，将第二个人工标注报价放在截断点之后，核对场景计数仍记录该样本但通过数为0。
- 验证：样本清单/解析评估专项95 passed；全量离线pytest 342 passed、14 skipped（数据库用例需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 边界：仅虚构HTML和合成清单；真实样本准确率仍未验证，未运行数据库集成、未访问网站/NAS或部署。
- 下一步：获准样本到位后运行每站20份正式解析评估；取得V0.1备份后完成旧库升级验收。

## 2026-11-10 P0-03样本上传HTTP路由截断状态回归
- 本轮目标：验证HTML样本上传端点将截断警告与不可复核状态返回给API调用者。
- 已完成：新增FastAPI `TestClient`回归，经过`POST /api/collection/pages`和API Key鉴权，断言返回候选保持pending、warnings含`visible_text_truncated`且`ready_for_review=false`，同时核对传给存储层的警告。
- 验证：解析器/评估器/服务层/API专项136 passed；全量离线pytest 341 passed、14 skipped（数据库用例需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 边界：HTTP请求与应用服务是真实本地代码，数据库使用假连接；未运行真实PostgreSQL、NAS或来源网站，未部署。无迁移或配置变化。
- 下一步：取得V0.1备份后完成真实旧库升级；获准网页样本到位后运行20+20解析评估。

## 2026-11-10 P0-03截断警告经候选存储返回
- 本轮目标：确认正文截断状态经过`stage_html`持久化后仍会阻止候选显示为可复核。
- 已完成：新增服务层回归，使用截断点后的第二个报价，核对写入候选的`visible_text_truncated`警告，并验证从数据库返回的pending候选`ready_for_review=false`。
- 验证：解析器/评估器/服务层专项135 passed；全量离线pytest 340 passed、14 skipped（数据库用例需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 边界：服务层使用假数据库连接和虚构HTML；未运行真实PostgreSQL、NAS或来源网站，未部署。无迁移或配置变化。
- 下一步：取得V0.1备份后完成真实旧库升级；获准网页样本到位后运行20+20解析评估。

## 2026-11-10 P0-03正文截断导致的未检查报价保护
- 本轮目标：正文超过35,000字符解析上限时，明确标记不完整解析，并防止未扫描区域里的冲突报价被误报为无冲突候选。
- 已完成：解析器版本升至`generic-labelled-v0.2.35`；超过上限时添加`visible_text_truncated`警告，并使`ready_for_review=false`。新增回归将第二个报价放在截断点后，先复现缺警告/仍ready再修复；`docs/API.md`已同步35,000字符上限和pending复核语义。
- 验证：解析器/评估器专项125 passed；全量离线pytest 339 passed、14 skipped（数据库用例需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 边界：仅虚构HTML离线验证；未访问网站/NAS/数据库，未部署。真实解析准确率和数据库集成未验证，无迁移或配置变化。
- 下一步：获准样本到位后运行20+20评估；取得V0.1备份后完成旧库升级验收。

## 2026-11-10 P0-03内联CSS注释下的隐藏状态解析
- 本轮目标：正确识别`display:none`声明中的CSS注释，不让隐藏广告报价污染挂牌字段。
- 已完成：`_inline_display_none`先移除CSS注释再按声明顺序计算display值；解析器升至`generic-labelled-v0.2.34`。新增注释含分号、注释后覆盖声明及端到端伪报价回归；先复现隐藏报价使365万字段置空，再修复。
- 验证：解析器/评估器专项124 passed；全量离线pytest 338 passed、14 skipped（数据库用例需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 边界：仅虚构HTML离线验证；未访问网站/NAS/数据库，未部署。真实字段准确率和数据库集成未验证，无迁移或配置变化。
- 下一步：获准样本到位后运行20+20评估；取得V0.1备份后完成旧库升级验收。

## 2026-11-10 P0-03排除嵌入内容备用文本
- 本轮目标：避免把iframe/object/canvas的备用内容误认为页面可见挂牌信息，导致冲突候选被置空。
- 已完成：解析前移除iframe、object、embed、canvas节点；解析器版本升至`generic-labelled-v0.2.33`。新增三种有内容模型标签的回归，均验证嵌入备用“900万”不影响正文挂牌价365万；先复现3例失败，再修复。
- 验证：解析器/评估器专项121 passed；全量离线pytest 335 passed、14 skipped（数据库用例需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。真实样本准确率和数据库集成未验证。
- 边界：仅使用虚构HTML；未访问来源网站、NAS或数据库，未部署。无数据库迁移或配置变化。
- 下一步：获准样本到位后运行每站20份评估；取得V0.1备份后完成旧库升级验收。

## 2026-11-10 P0-06抖音账户链接移除跟踪参数
- 成功标准：通过白名单的Douyin主页URL在存库和转交DTK前，不保留query/fragment跟踪参数；原有主机/协议校验不放宽。
- `AccountIn`现在在验证URL后规范化去除query和fragment，同时保留scheme/host/path；新增含`share_token`的失败优先回归。模型/DTK专项：**75 passed**；全量离线pytest：**332 passed、14 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。编译、目标JSON、模板/validator列一致性、`git diff --check`及开发包校验通过。
- 仅本地合成字符串验证；未连接DTK或真实账号。P0-06真实接口版本/权限和获准账号联调仍待完成。

## 2026-11-10 P0-06抖音主页URL大小写绕过修复
- 成功标准：抖音账户配置为URL时，无论协议大小写都必须校验HTTPS、允许域名、userinfo和端口；异常URL不得以`url`参数发送给DTK。
- 回归先复现`HTTPS://other.example/...`绕过大小写敏感`startswith('http')`，并发现正常大小写下的userinfo/非标准端口也未拒绝。现对URL形式统一解析，接受大小写HTTPS的douyin.com子域名，拒绝其他主机、凭据、非443端口及控制字符。
- 模型/DTK专项：**74 passed**；全量离线pytest：**331 passed、14 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。compileall、GOAL_STATE JSON、模板/validator列一致性、`git diff --check`及开发包校验通过。
- 仅本机离线验证；未连接DTK或真实账号。接口版本/权限与获准账号联调仍待完成。

## 2026-11-10 P0-04权限撤销竞态与PostgreSQL锁回归
- 执行端改为抓取前读取来源当前策略，并持有`FOR SHARE`至抓取/样本暂存完成；目标领取时的旧策略快照不再用于授权。离线服务回归复现撤销后的旧任务阻断，并验证批准策略正向流程。
- 新增真实PostgreSQL双连接锁集成用例：共享锁期间策略撤销需等待/超时，释放后更新成功。当前无`TEST_DATABASE_URL`，该集成测试明确跳过，未据此声称PG锁验收通过。
- 服务/模型/策略专项：**19 passed**；全量离线pytest：**328 passed、14 skipped**（均需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。编译、目标JSON、模板/validator列一致性、`git diff --check`及开发包校验通过。
- 在线来源仍OFF；未访问网站/NAS/数据库，也未部署。下一步在隔离PG环境执行锁并发用例，再等待平台许可、获准样本和V0.1备份完成其余P0验收。

## 2026-11-10 P0-04任务执行时复核并锁定最新来源权限
- 成功标准：目标领取后若来源许可被撤销/关闭，执行端必须读取最新来源策略并在HTTP前阻断；有效策略行需在抓取及候选暂存期间保持锁定，避免撤销与请求并发竞态。
- `claim_due_target`不再把易过期的策略字段作为授权依据。`run_collection_target`在全局开关开启后读取当前`source_registry`行并`FOR SHARE`锁定，使用最新来源开关/状态/引用判断；锁保持到抓取和样本暂存结束。新增回归先复现“领取后撤销仍尝试fetch”，再覆盖拒绝及有效策略正向执行/锁区间。
- 服务/模型/策略专项：**19 passed**；全量离线pytest：**328 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。编译、目标JSON、模板/validator列一致性、`git diff --check`及开发包校验通过。
- PostgreSQL `FOR SHARE`路径由假数据库服务测试验证逻辑，未在本机真实PostgreSQL/NAS运行；在线来源仍OFF，未访问网站/NAS/数据库或部署。
- 下一步：在隔离PostgreSQL环境验证权限撤销与抓取锁并发行为；平台书面许可/适用规则、获准HTML及V0.1备份材料到位后再做对应P0验收。

## 2026-11-10 P0-04服务层权限门拒绝网络请求回归
- 成功标准：在线采集任一审批条件不满足时，后台任务必须在调用HTTP抓取器前返回`blocked_policy`，不能产生请求。
- 为`run_collection_target`新增服务层回归，分别覆盖全局开关关闭、来源开关关闭、策略未批准及空白许可引用；四种场景均断言抓取器调用数为0、运行记录状态为`blocked_policy`。此前纯函数权限组合测试继续保留。
- 服务/模型/策略专项：**17 passed**；全量离线pytest：**326 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。编译、目标JSON、模板/validator列一致性、`git diff --check`及开发包校验通过。
- 仅离线假数据库回归；没有打开任何来源开关，没有访问网站/NAS/数据库或部署。非空引用不证明许可真实有效。
- 下一步：取得平台书面许可后重新核对适用协议/Robots；P0-02/P0-03仍需获准真实样本，P0-01仍需V0.1备份。

## 2026-11-10 P0-04拒绝空白许可引用
- 成功标准：来源策略不得显示`approved`却没有可引用的非空白许可依据；保持在线采集权限判断的既有双开关与批准状态要求。
- `PolicyReviewIn`此前接受`online_policy_status=approved`且`policy_reference`仅为空格；虽然执行门仍会拒绝抓取，但策略状态会误导审阅。现批准状态一律要求非空白引用，新增回归先失败后通过。
- `tests/test_collection_models.py tests/test_collection_policy.py`：**10 passed**；全量离线pytest：**322 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。编译、目标JSON、模板一致性、`git diff --check`及开发包校验通过。
- 该检查只验证引用文本非空，不判断文件真实性/授权效力；未打开在线来源开关，未访问网站/NAS/数据库或部署。
- 下一步：取得平台书面回复后更新来源协议审查；同时等待真实页面样本与V0.1备份，分别完成P0-02/P0-03和P0-01验收。

## 2026-11-10 P0-03报告公开样本状态与场景构成
- 成功标准：评估报告除总数外，按来源可见各挂牌状态与必需/歧义场景样本数，便于复核训练/评估集是否偏斜；现有样本覆盖校验规则保持不变。
- 新增`sample_composition`，按来源统计active/withdrawn/sold/unknown及各场景标签计数；主评估回归核对虚构5样本中状态和场景的准确数量。`docs/SAMPLE_DATASET.md`及验收标准同步说明。
- parser/样本/评估专项：**175 passed**；全量离线pytest：**322 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。compileall、GOAL_STATE JSON、模板/validator列一致性、`git diff --check`及开发包校验通过。
- 仅离线合成输入验证；真实准确率仍待每站20份获准HTML和人工标注。未访问网站/NAS、未连接数据库或部署。
- 下一步：取得获准样本后运行正式20+20评估；取得V0.1备份后做隔离升级保真验证；在许可及备份门槛满足后再评估NAS发布。

## 2026-11-10 P0-03解析评估快照与零覆盖门槛回归
- 成功标准：清单校验与指标计算使用同一不可变字节快照；字段零抽取时覆盖率为0、精确率为null，95%精确率门槛不得标记达标。
- 补齐替换清单后恢复原文件的竞态回归，以及零抽取精确率门槛回归；后者确认人工标签仍进入分母，零覆盖不能虚报高精度。
- parser/样本/评估专项：**175 passed**；全量离线pytest：**322 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。compileall、GOAL_STATE JSON、模板/validator列一致性、`git diff --check`及开发包校验通过。
- 仅离线合成输入验证；真实准确率仍待每站20份获准HTML和人工标注。未访问网站/NAS、未连接数据库或部署。
- 下一步：取得获准样本后运行正式20+20评估；取得V0.1备份后做隔离升级保真验证；在许可及备份门槛满足后再评估NAS发布。

## 2026-11-10 P0-03解析评估使用同一清单快照
- 成功标准：清单校验与字段/场景指标计算必须基于完全相同的清单字节，即使路径文件在中途被替换后恢复，报告也不能混用两个版本。
- evaluator启动时读取清单快照并计算SHA-256；样本校验和CSV指标计算均消费该快照，评估结束仍复核路径文件。新增竞态回归：校验后替换为错误标注清单、结束前恢复原文件，报告仍按原快照计算。
- parser/样本/评估专项：**174 passed**；全量离线pytest：**321 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。compileall、GOAL_STATE JSON、模板/validator列一致性、`git diff --check`及开发包校验通过。
- 仅离线合成输入验证；真实准确率仍待每站20份获准HTML和人工标注。未访问网站/NAS、未连接数据库或部署。
- 下一步：取得获准样本后运行正式20+20评估；取得V0.1备份后做隔离升级保真验证；在许可及备份门槛满足后再评估NAS发布。

## 2026-11-10 P0-03解析评估输入指纹与竞态保护
- 成功标准：每份评估报告可追溯其清单版本；清单或HTML样本在校验后发生变化时，评估必须中止，不能输出混合版本结果。
- evaluator报告新增`manifest_sha256`；评估前后复核清单SHA-256，且解析样本时复核磁盘字节哈希与清单一致。新增验证后修改清单/样本的竞态回归。
- 解析器/样本/评估专项：**173 passed**；全量离线pytest：**320 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。compileall、GOAL_STATE JSON、模板/validator列一致性、`git diff --check`及开发包校验通过。
- 仅离线合成输入验证；真实解析准确率仍待每站20份获准样本。未访问网站/NAS、未连接数据库或部署。

## 2026-11-10 P0-03千分位数值跨格式等值回归
- 成功标准：页面原文和人工候选采用不同但等值的千分位写法时应按数值匹配；例如页面`1,234`、人工`1234`；等值重复候选如`1,234|1234.0`必须拒绝。
- 扩展 parser 回归确认合法分组与未分组的面积/报价提及不触发冲突；validator/evaluator端到端覆盖异格式候选核对和等值候选重复拒绝。严格千分位正则仍由parser模块统一提供。
- Parser/样本/评估专项：**171 passed**；全量离线pytest：**318 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。compileall、GOAL_STATE JSON、模板一致性、`git diff --check`和开发包校验通过。
- 仅合成/虚构页面验证，未访问网站/NAS、未运行数据库集成或部署；真实页面数字格式仍待样本确认。

## 2026-11-10 P0-03共享严格数值文本格式
- 成功标准：HTML parser、样本validator与解析evaluator使用同一份严格数字/千分位语法，避免有效值被解析、校验或评估层差异化处理。
- 将`NUMERIC_TEXT_PATTERN`集中定义于parser模块；三个入口共享该常量。原有合法千分位解析、面积/报价候选精确对账和畸形分组拒绝回归均继续通过。
- Parser/样本/评估专项：**169 passed**；全量离线pytest：**316 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。compileall、GOAL_STATE JSON、模板一致性及`git diff --check`通过。
- 仅离线实现；真实挂牌格式未验证，未访问网站/NAS、未运行数据库集成或部署。

## 2026-11-10 P0-03数值候选千分位归一化一致
- 成功标准：页面可识别的合法千分位面积/报价候选能通过清单校验并按数值与人工候选对账；错误千分位分组继续拒绝。
- validator和evaluator现在共同接受`1,234`、`1,234.5`等严格三位分组形式，并在Decimal比较前去除分组逗号；`12,34`等格式不合法。清单文档已说明规则。
- Parser/样本/评估专项：**169 passed**；全量离线pytest：**316 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。覆盖分组面积/报价候选端到端对账和畸形格式拒绝；compileall、GOAL_STATE JSON、模板一致性及`git diff --check`通过。
- 仅离线合成页面验证；真实挂牌数字格式与准确率未验证，未访问网站/NAS、未运行数据库集成或部署。

## 2026-11-10 P0-03单个越界户型异常场景
- 成功标准：单个无法接受的户型值（21–99室）可作为`invalid_bedrooms`明确标注并评估；不与多值冲突混淆，最终有效户型标签仍限0–20。
- 新增`invalid_bedrooms`和`invalid_bedroom_candidates`。validator要求恰好一个21–99整数候选，且拒绝与`multiple_bedrooms`并用；evaluator要求字段留空、出现`invalid_bedrooms_mentions`并与解析证据一致。样本指南和模板同步，当前模板/validator均为29列。
- Parser/样本/评估专项：**83 passed**；全量离线pytest：**311 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。compileall、GOAL_STATE JSON、模板一致性和`git diff --check`通过。
- 仅离线合成页面验证；未访问网站/NAS、未运行数据库集成或部署。真实户型数据和解析准确率仍待获准样本。

## 2026-11-10 P0-03保留越界户型冲突证据
- 成功标准：`multiple_bedrooms`候选必须能记录解析器实际识别的原始户型值（包括越界值），并与页面证据一致；最终人工`bedrooms`标签仍限制为0–20整数。
- 修复validator将候选复用最终业务范围导致`3室/21室`冲突无法标注的问题：`bedroom_candidates`现接受0–99整数原始提及；最终`bedrooms`校验不变。新增validator及evaluator回归，确认21室证据可以被完整对账。
- Parser/样本/评估专项：**75 passed**；全量离线pytest：**303 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。compileall、GOAL_STATE JSON及`git diff --check`通过。
- 仅离线合成HTML验证；真实户型页面分布和准确率未验证，未访问网站/NAS、未运行数据库集成或部署。

## 2026-11-10 P0-03来源房源ID冲突纳入人工对账
- 成功标准：详情URL与canonical/og:url ID冲突时，样本清单允许保留双方候选并将正式ID留空；评估器核对全部未截断解析证据，unknown ID仍与可验证ID冲突分开。
- 新增`source_id_conflict`与`source_listing_id_candidates`；validator要求候选符合来源ID格式、候选互异且包含可识别详情URL ID，并禁止同时标记`unknown_id`。evaluator按来源ID证据精确对账；样本指南已同步。模板与validator均为28列。
- Parser/样本/评估专项：**154 passed**；全量离线pytest：**301 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。覆盖正确候选、不匹配、证据截断、重复值及URL ID遗漏；compileall、GOAL_STATE JSON、模板一致性和`git diff --check`通过。
- 仅本地离线实现；无获准真实样本，未访问网站/NAS、未运行数据库集成或部署。真实ID冲突分布仍未知。

## 2026-11-10 P0-03建筑面积歧义纳入候选对账
- 成功标准：解析器产生`multiple_area_mentions`时，人工清单可标记`multiple_areas`并列出面积候选；评估器核对解析器未截断候选集合与人工集合，清单校验限制数值在(0, 20000]㎡。
- 新增`area_candidates_sqm`模板/validator列，将面积场景加入歧义标签、冲突字段空值校验及Decimal集合对账；文档同步记录标注格式和范围。模板与validator当前均为27列。
- Parser/样本/评估专项：**148 passed**；全量离线pytest：**295 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。覆盖场景通过、不匹配、证据截断、重复候选和非有限/越界数值拒绝。compileall、GOAL_STATE JSON及变更文件尾随空白扫描通过。
- 仅本地离线代码/文档/测试变更；未取得真实样本、未访问网站/NAS、未运行数据库集成或部署，真实解析准确率仍未知。

## 2026-11-10 P0-03显式报告抽取精确率95%门槛
- 成功标准：解析评估报告逐字段明确显示抽取精确率目标95%及是否达标；该判断与每站20份正式样本门槛、字段覆盖率分别呈现。
- `evaluate_parser.py`为每个字段新增`precision_target_pct`与`precision_target_met`，只在存在实际抽取值且精确率≥95%时标记达标；`sample_requirements`仍独立判断每站20份。验收文档补充报告字段说明。
- 定向`tests/test_parser_evaluation.py tests/test_sample_set.py`：**59 passed**；全量离线pytest：**287 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。回归覆盖95%边界和90%未达标；compileall、GOAL_STATE JSON与`git diff --check`通过。
- 仅本地离线代码/文档变更；指标仍需真实获准样本验证。未访问网站/NAS、未运行数据库集成或部署。

## 2026-11-10 P0-02/P0-03小区歧义清单校验补强
- 成功标准：小区多值候选在清单层面必须至少两项且互异；未标记`multiple_communities`时不得填写候选列；人工标注指南完整列出该场景。
- 将样本validator回归扩展到`community_candidates`重复值和缺少匹配标签两种情况，并修正文档遗漏的小区多值场景。清单模板仍与validator列集合一致，当前均为26列。
- parser/样本/评估专项：**138 passed**；全量离线pytest：**285 passed、13 skipped**（数据库集成需要`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。compileall、GOAL_STATE JSON及`git diff --check`通过。
- 仅本机离线测试/文档变更；未访问网站/NAS、未运行数据库集成或部署。真实获准样本与解析准确率仍待用户材料。

## 2026-11-10 P0-03小区冲突候选纳入人工对账
- 成功标准：多小区页面必须同时满足字段留空、发出歧义告警、候选证据完整，且解析候选集合与人工清单完全一致；清单模板、校验器和评估器字段保持同步。
- 为样本清单新增`community_candidates`列并纳入`multiple_communities`校验/评估；评估器回归覆盖小区候选集合不匹配和证据截断。`docs/SAMPLE_DATASET.md`同步说明所有歧义候选列。
- Parser/样本/评估专项：**136 passed**；全量离线pytest：**283 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。compileall、JSON解析、`git diff --check`及开发包完整性/SHA验证通过。
- 仅本地离线开发；没有获准真实页面、未访问网站/NAS、未运行数据库集成或部署。P0-02仍缺两站各20份获准样本，P0-03真实准确率未验证。

## 2026-11-10 P0-06兼容空游标终止哨兵
- 成功标准：metadata中`next=""`表示没有下一游标时应保留为无游标；由空格或Tab构成的空白令牌仍须拒绝。
- 回归先复现`result_meta.cursor.next=""`被空白令牌保护误判为异常；现回退metadata后将空字符串归一为空游标，再拒绝非空的纯空白字符串。显式`has_more=false`仍按原值停止。
- DTK/Worker/模型专项 **72 passed**；全量离线pytest **267 passed、13 skipped**（均需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。
- 仅本机离线代码/测试/文档变更；未连接DTK/NAS、未运行DB集成。真实DTK游标规范仍需联调确认。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-10-p0-06-cursor-metadata-compat.zip`；由项目构建器验证ZIP与包内SHA。

## 2026-11-10 P0-06拒绝空白DTK分页游标
- 成功标准：DTK返回空白字符串游标时不得将其当作可用令牌继续请求；合法数字游标`0`仍须保留。
- 回归先复现空格/Tab游标被接受；`parse_page`现在对此抛出明确`DtkError`。数字`0`仍转换为字符串`"0"`，游标存在且无`has_more`时仍推断有后续页。
- DTK/Worker/模型专项 **71 passed**；全量离线pytest **266 passed、13 skipped**（需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。
- 仅本机离线代码/测试/文档变更；未连接DTK/NAS，未运行数据库集成。真实DTK字段规范与账号联调仍未验证。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-10-p0-06-cursor-validation.zip`；由项目构建器验证ZIP与包内SHA。

## 2026-11-10 P0-06 DTK游标缺少has_more时防止漏页
- 成功标准：DTK页含后续游标但未返回`has_more`时，不得被解释为分页结束；若上游明确返回`has_more=false`，仍尊重该终止标记。
- 回归先复现含`cursor`但无`has_more`被解析为false；解析器现在在payload与cursor metadata均未给出标记时以游标存在性推断分页继续，同时保留明确false优先级。
- DTK/Worker/模型专项 **68 passed**；全量离线pytest **263 passed、13 skipped**（需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。Python 3.12 compileall、GOAL_STATE JSON与`git diff --check`通过。
- 本轮仅本机离线代码/测试/文档变更；未连接DTK/NAS或运行数据库集成。真实DTK协议、权限和3个获准账号24小时联调仍待验收。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-10-p0-06-cursor-inference.zip`；由项目构建器验证ZIP与包内SHA。

## 2026-11-10 P0-06大小写合法HTTPS主页链接识别
- 成功标准：Pydantic模型已接受的大小写HTTPS抖音主页链接必须传给DTK的`url`参数，不能误作`sec_user_id`。
- 回归先复现`AccountIn`接受`HTTPS://...`但`DtkClient`请求缺少`url`的缺陷；现按URL解析后的scheme不区分大小写判断主页链接，并保留原始合法URL传递。
- DTK/Worker/模型专项 **66 passed**；全量离线pytest **261 passed、13 skipped**（均需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。
- 仅本机离线代码/测试/文档变更；未连接DTK/NAS、未部署或改数据库。真实DTK接口版本、权限和3个获准账号24小时联调仍待验收。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-10-p0-06-https-scheme.zip`；由项目构建器验证ZIP与包内SHA。

## 2026-11-10 P0-03正式样本数达标边界回归
- 成功标准：按正式默认门槛评估时，贝壳和安居客各恰好20条有效清单记录均显示`sample_requirements.met=true`；低于20条仍显示false。
- 扩展评估器测试清单构造器以生成20条不同HTML/详情URL；新回归通过默认参数完整校验并确认两站恰好20条均达标。既有5条场景测试继续确认诊断模式不会弱化正式门槛。
- `tests/test_parser_evaluation.py tests/test_sample_set.py tests/test_storage_report.py` **57 passed**；全量离线pytest **259 passed、13 skipped**（均需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。Python 3.12 compileall、GOAL_STATE JSON与`git diff --check`通过。
- 本轮仅修改本地测试/文档；未连接或写入NAS、未访问网站、未运行数据库集成。真实获准样本/准确率、V0.1备份及NAS隔离PG17部署评估仍待完成。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-10-p0-03-sample-threshold-boundary.zip`；由构建器验证ZIP与包内SHA。

## 2026-11-10 P0-08 NAS留存库存只读复核
- 经授权`notedock-nas`只读扫描确认90天外备份候选为**0个/0字节**，未删除文件。`raw-pages`在API服务UID下仅有`.gitkeep`和AppleDouble占位文件，共2个/249字节；数据库候选数为0。
- NAS上的`storage_report.py` SHA-256为`54b39480b8b2a2f6b3f45b19ede649c5ba1f8e29c033bd4253c1db4727f648ac`，工作区逐路径列报版本为`7f491af1e55532040b31f67438057ee1ad6a4ba0db4079c3f50649b162245f74`；NAS版本没有`expired_backup_files`逐路径列报。直接以`sheng`运行报告因raw-pages目录权限不足而显式失败，没有把不可读目录误报为空。
- `tests/test_storage_report.py` **12 passed**。本轮未改应用代码、未修改NAS权限或容器、未删除/创建备份；新版报告待后续获授权同步。

## 2026-11-10 P0-01/P0-03 NAS只读复核与API-only部署差异审计
- 经授权OpenSSH别名确认目标为`DXP4800`/`sheng`，`ningbo-re-ai`仍由登记的`/volume3/docker/ningbo-re-ai/docker-compose.yml`管理。API、Worker运行，PostgreSQL 17 healthy，API本机`/healthz`=200。
- 生产只读查询确认`beike`/`anjuke`均`online_enabled=false`，`collection_candidates`、`source_listings`、`saved_searches`均为0行。现有备份`backups/ningbo-re-ai-20261110T063944Z-1816930`的`SHA256SUMS`核验通过；已盘点备份仅见当前V0.2项目备份，无V0.1数据库备份。
- 镜像SHA对比确认工作区解析器/候选代码未部署：NAS API仍为旧`collection_service.py`及`parser.py`，且缺少工作区的`beike.py`、`anjuke.py`、`url_policy.py`。部署若获授权需整体构建工作区API镜像，保持Compose登记路径、DB、Worker、卷和在线采集开关不变；不可只替换解析器单文件。
- 本轮仅只读核验；未创建备份或隔离资源、未传输文件、未更改NAS/容器/数据库。实际V0.1升级仍缺旧库备份；API-only写入部署须在新鲜生产备份与隔离PostgreSQL 17验证后另行授权。

## 2026-11-10 P0-03评估报告显式标注正式样本门槛
- 成功标准：即使诊断时通过`--minimum-per-source`降低清单校验门槛，评估报告仍并列给出项目正式门槛每站20份、实际样本数和达标状态。
- 新增报告`sample_requirements`字段；不足20份仍可在测试中输出诊断指标，但明确`met=false`，不误示已满足正式样本量。样本 intake 文档同步说明。
- 回归先复现报告缺少正式门槛字段；`tests/test_parser_evaluation.py tests/test_sample_set.py` **44 passed**；全量离线pytest **258 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。
- 仅本机离线代码/文档变更；未连接NAS、网站或数据库，无部署、迁移、配置变化。无获准真实样本，实际站点准确率未验证；P0-01仍缺V0.1备份，P0-02/P0-03仍需每站20份获准页面及人工标签。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-10-p0-03-sample-threshold.zip`；由项目打包器刷新manifest并验证ZIP完整性与包内SHA。

## 2026-11-10 P0-03来源房源ID出处与canonical路径隐私
- `source_listing_id`现记录ID来自提交`source_url`还是页面canonical/og:url；ID冲突仍留空并保留两边命中。canonical证据仅保存标准挂牌路径后缀及ID，剥除query/fragment和路径前缀，避免将页面附带令牌写进候选。解析器版本升至`generic-labelled-v0.2.27`。
- 相关解析器/候选/评估器/清单专项 **122 passed**；全量离线pytest **258 passed、13 skipped**，13项均需`TEST_DATABASE_URL`。本机uv缓存依赖运行，未联网安装；保留Starlette/httpx弃用警告。compileall、GOAL_STATE JSON及`git diff --check`通过。
- 数据库集成未运行（测试URL缺失且本地PG socket受沙箱限制）；真实20+20获准样本和准确率未验证；未连接或部署NAS，无迁移/配置变化。
- 本轮开发包：`../ningbo-re-ai-v0.2-dev-2026-11-10-p0-03-id-evidence.zip`；已由构建器校验ZIP完整性及包内SHA。

## 2026-11-10 P0-03冲突字段保留有界证据
- 对面积、总价、户型、小区、区域、楼层、装修等识别字段，`field_evidence`现保留最多20个原文命中片段及候选值、归一化文本偏移、总命中数和截断标记。冲突/越界字段值仍为空，不自动挑选；总体置信度仍标记未校准。解析器版本升至`generic-labelled-v0.2.26`。
- 人工更正字段写入`manual_review`来源并清空旧解析mentions；未更正字段维持原证据。
- 解析器/候选修正/评估器/样本清单专项 **121 passed**；全量离线pytest **257 passed、13 skipped**，跳过项均需`TEST_DATABASE_URL`。使用本机uv缓存依赖，未联网安装；保留Starlette/httpx弃用警告。compileall、GOAL_STATE JSON及变更文件尾随空白扫描通过。
- 未运行数据库集成（`TEST_DATABASE_URL`缺失，临时PG16 socket预检被沙箱拒绝）、未使用真实获准页面、未连接或部署NAS；没有迁移/配置变化。P0-03仍等每站20份人工标注样本和准确率验收。
- 本轮开发包：`../ningbo-re-ai-v0.2-dev-2026-11-10-p0-03-conflict-evidence.zip`；构建器已验证ZIP完整性和包内SHA。

## 2026-11-10 P0-03网页候选字段出处与人工更正来源
- 解析器为明确识别的可见挂牌属性保存字段值、可见文本来源、原文片段和归一化文本内偏移，并标记置信度未校准；解析器版本升至`generic-labelled-v0.2.25`。多值歧义字段仍留空。
- 人工修正字段的出处改标为`manual_review`，未更正字段保留解析证据。新增解析与修正回归。
- 解析器/候选修正/评估器/样本清单专项：**120 passed**；全量离线pytest：**256 passed、13 skipped**，13项均需`TEST_DATABASE_URL`。通过本机uv缓存里的pytest/依赖运行，未联网安装；保留Starlette/httpx弃用警告。`compileall`、GOAL_STATE JSON及变更文件尾随空白扫描通过。
- DB集成未运行：`TEST_DATABASE_URL`未设置；临时PG16测试环境预检时沙箱拒绝本地socket绑定（`Operation not permitted`），未启动数据库集群。仅本机离线验证，无真实20+20样本准确率或NAS部署结论；无数据库迁移/配置变化。P0-03仍需每站20份获准真实页面和人工标签。
- 本轮开发包将按项目脚本生成到工作区同级，并刷新`MANIFEST.sha256`；ZIP完整性和包内哈希由构建器验证。

## 2026-11-10 P1视频规则提示增加字段证据定位
- 目标：让现有未验证规则提示能回指OCR/转写/标题/描述中的匹配片段与字符区间，并明确置信度尚未校准。
- `extract_hints`现为唯一值提示附带字段、值、来源、原文匹配片段及来源内字符偏移；`enrich_video`提供固定来源名。跨来源拼接不能作为小区名证据。规则输出仍为未验证提示，不成为正式挂牌。
- 新增2项提取器pytest回归，但当前Python环境无pytest，定向pytest未启动。对应3条直接断言和compileall通过。无真实视频样本、数据库/API集成或置信度指标。
- 仅本机离线变更；未连接NAS、未部署，无迁移/配置变化。下一步：在项目依赖可用环境运行pytest；获得授权视频样本后评估规则召回/准确率，再决定是否扩展到小区分期/楼栋识别。

## 2026-11-10 P0-08过期备份路径只读列报
- `storage_report.py`现按稳定顺序逐项列出严格早于留存期限的备份文件相对路径，同时保留数量/字节汇总；仍仅供人工复核，不删除文件，也不跟随符号链接。
- `tests/test_storage_report.py`：**12 passed**，覆盖91/90/89天边界、候选路径可定位和文件未删除。全量离线pytest：**252 passed、13 skipped**（PostgreSQL需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告；compileall通过。
- 本轮无配置、数据库或NAS变更。NAS部署版尚未包含本轮路径列报更新；本地PG16 DB全套264 passed结果属于此前P0-03修复验证。

## 2026-11-10 P0-03本地修复后的NAS只读基线核验
- 经授权SSH别名只读确认目标为`DXP4800`/`sheng`。NAS项目`/volume3/docker/ningbo-re-ai`的Compose标签和路径均指向已登记项目；API/Worker运行、PostgreSQL 17 healthy，`/healthz`=200。
- 当前业务表候选/挂牌/价格历史/条件单均为0，两来源`online_enabled=false`，启用目标0。NAS `app/collection_service.py` SHA-256为`479c191f67d413ad388aaa75993fc07c94115dacf19e58cd4478c33e41f36ffd`，工作区修复版本为`d9d040a372f23cfa6bd05919e012f8adea7ada3565f3a07c174abef736856a39`，故修复尚未部署。
- 本轮未在NAS创建备份或修改文件/容器/数据库。此前离线PG16完整套件264 passed、0 skipped不代表NAS部署验收；本地改动需另行完成新备份、评估API-only更新和部署后核验。

## 2026-11-10 P0-03候选重提SQL占位符回归修复与PG16全量验收
- PG16数据库执行暴露`stage_html`重复候选SQL中`LIKE 'operator_note:%'`与psycopg参数占位语法冲突，导致采集页接口500；SQL现将字面百分号写为`%%`，假连接回归同步断言转义形式。
- 在临时PostgreSQL 16 `rehouse_test`库（仅Unix socket）运行完整测试：**264 passed、0 skipped**，含全部13项DB集成测试；保留1条Starlette/httpx弃用警告。验证后停止临时实例，删除测试库/集群目录并确认清理。
- Python 3.12 compileall与GOAL_STATE JSON解析通过。无迁移或配置变化；未连接NAS/网站、未触碰生产数据。此合成V0.1迁移覆盖不替代真实V0.1备份升级；P0-02/P0-03真实获准页面与准确率仍缺。
- 下一步：①取得真实V0.1数据库备份后进行隔离升级对账；②取得每站获准HTML和人工标注后报告解析准确率；③保持在线采集关闭，直至许可与robots复核完成。

## 2026-11-10 P0-03解析器调用点审计与来源ID拆分
- 修复测试对旧`parse_source_listing_html`函数名的3处引用，统一使用`app.collectors.parse_listing_html`；HTTP客户端改从`url_policy`导入共享URL校验，避免重构后导入失败。
- 来源ID提取分别在贝壳/安居客入口执行，并由统一分发器按source提供；保留通用HTML解析基线。
- Python 3.12 `compileall`/目标`py_compile`通过；桩化路由/ID/URL smoke 8项通过。pytest、BeautifulSoup等项目依赖未安装，因此pytest及真实HTML解析未运行；无真实样本准确率结论。未连接NAS/网站。
- 配置/数据库无变化；本轮不部署。下一步：①恢复本机依赖后运行解析器与全量pytest；②取得合规页面后做每站样本校准；③收到V0.1备份后在隔离库执行升级字段保真测试。

## 2026-11-10 P0-03解析架构文档同步
- `docs/ARCHITECTURE.md`与README现在说明API/评估按来源路由到`beike.py`/`anjuke.py`，适配器仍委托通用保守基线；合成fixture不代表真实站点准确率。
- 本轮仅改文档；现有状态仍为完整解析器pytest未运行、真实样本缺失。

## 2026-11-10 P0-03下架/缺字段失败fixture
- 新增`beike_unavailable_synthetic.html`与`anjuke_missing_fields_synthetic.html`，文件内显式标记为合成、非采集页面；经站点分发入口验证不从“已下架/信息不完整”标题臆造小区、面积、挂牌价或未知URL房源ID，候选不满足审核条件。
- 测试文件语法编译通过；定向pytest因当前环境缺少pytest未能启动。fixture不代表真实页面或授权样本。

## 2026-11-10 P0-03站点解析入口拆分
- 新增`app/collectors/beike.py`、`anjuke.py`和统一分发器；API候选采集、解析评估器和负载测试均改用按source路由的入口。
- 两个站点模块目前仍委托`generic-labelled-v0.2.24`通用保守基线，保证不凭虚构fixture添加站点专用选择器；真实布局校准和20+20样本指标仍待获准样本。
- 语法编译通过；通过注入测试桩验证两适配器向通用解析器传递正确source/url/html（2 passed）。依赖缺失，真实fixture解析pytest未运行。

## 2026-11-10 P0-03解析器版本回归不再硬编码
- 解析器升至`generic-labelled-v0.2.24`后，canonical冲突测试仍断言旧版`.2.23`，会使完整测试失败。现改为与`PARSER_VERSION`常量比较，避免下次版本递增再次产生陈旧断言。
- `py_compile app/collectors/parser.py tests/test_collection_parser.py`通过，`app/`与`tests/`中未发现`.2.23`硬编码。pytest未能启动（当前无pytest依赖）。

## 2026-11-10 P0-06分享URL拒绝首尾C0/C1控制字符
- 成功标准：分享URL原始输入含C0/C1控制字符时，无论在链接首、尾或中间都回退canonical；普通首尾空格继续裁剪兼容。
- `strip()`会移除首尾Tab/换行等C0后再校验。现在先扫描原始输入中的C0/C1，再裁剪普通空白；增加首Tab、尾换行和DEL前的C0回归。
- 直接调用`normalize_post`的6个smoke场景通过，`py_compile`通过。完整pytest无法运行（pytest/httpx依赖未安装）；未连接DTK/NAS。

## 2026-11-10 P0-03语义主内容区优先级
- 成功标准：页面中较早出现的通用`.content`导航容器不能遮蔽语义`<main>`/`<article>`中的挂牌字段；空`<main>`不能遮蔽后续非空`<article>`。
- 解析器现在优先取非空`main`、再取非空`article`，最后回退至既有房源内容类与body；新增两个结构回归，解析器版本升为`generic-labelled-v0.2.24`。
- 当前仅通过`compileall`与语法编译；解析器pytest未运行，因为本机缺少pytest/BeautifulSoup项目依赖。未使用真实页面，不产生准确率结论。

## 2026-11-10 P0-01迁移命令增加原子回滚
- V0.1升级指南现对`002`、`003`、`005`使用`psql --single-transaction`，并保留`ON_ERROR_STOP`，让语句错误回滚整份迁移；`004`已有内建`BEGIN/COMMIT`，明确不再额外套单事务。
- 本轮只修改部署步骤；迁移/数据库集成未运行（当前无测试依赖和`TEST_DATABASE_URL`），未连接NAS。
- 标准库静态核对确认002/003/005没有内建事务或`CREATE INDEX CONCURRENTLY`，对应psql命令均含`--single-transaction`和`ON_ERROR_STOP`；004恰有一个BEGIN/COMMIT且未外包单事务。

## 2026-11-10 P0-01扩大V0.1迁移数据保真断言
- 成功标准：在隔离升级用例中，运行V0.2迁移两次后，除确认新增默认列外，V0.1各业务表的代表性字段值均保持一致，且新来源在线功能仍关闭。
- 扩充`test_v01_schema_migration_preserves_existing_data`：覆盖账号同步状态/历史策略、seen-post基线标记、视频元数据/文本/JSONB、社区地址/坐标与别名、房源详情、挂牌与权限说明、历史报价类型/证据、同套关系、条件单和通知投递状态；挂牌新增列仍断言采用安全默认值。
- 本机已通过`py_compile tests/test_db_integration.py`；PostgreSQL集成未运行（当前无`TEST_DATABASE_URL`，且测试依赖未安装）。该改动增强的是合成旧库字段保真覆盖，不替代缺失的真实V0.1备份升级验收。

## 2026-11-10 P0-06拒绝首尾C1控制字符
- 成功标准：分享URL即使将C1控制字符放在首尾，也必须回退到canonical作品URL；普通首尾空格裁剪继续兼容。
- 复核发现`str.strip()`会先裁掉U+0085，使原有尾部C1回退断言与实现不符。现先检查原始字符串的C1范围，再执行普通空白裁剪；新增前置U+0085回归。
- 5个直接函数smoke场景通过（首尾C1、内部空格/Tab及普通首尾空格）；`compileall`、GOAL_STATE JSON和Compose配置检查通过。系统Python缺少pytest/httpx，`uv --offline`也受缓存目录权限限制，完整pytest未能运行；前序240 passed记录不能作为本轮独立验收证据。
- 仅本机离线验证；未连接DTK、NAS或来源网站。真实DTK联调仍未完成。

## 2026-11-10 P0-03重复候选随解析器版本刷新
- 成功标准：相同来源URL与HTML重提时，旧解析器生成的待审候选可刷新；人工更正或已审核候选必须保持不变，仍复用原候选ID。
- `stage_html`现仅在候选仍pending、parser_version不同且未人工更正时更新来源ID、解析版本、字段和解析告警；保留已有operator_note。若冲突候选为人工更正/已审核或版本未变，转为读取现有记录，避免覆盖人工决定。
- 新增SQL构造单测 **2 passed**，parser/sample/HTTP/evaluator/models相关专项合计 **123 passed**；全量离线pytest **225 passed、13 skipped**，其中13项均需`TEST_DATABASE_URL`，保留1条Starlette/httpx弃用警告。compileall、目标JSON及Compose校验通过。
- 本机PostgreSQL集成未能运行：`initdb`因环境拒绝`shmget`失败；本机Docker API也不可访问。已增加待审核升级、人工更正保护和已审核保护的数据库集成回归，需在隔离PostgreSQL环境执行确认SQL运行时行为。未连接NAS/生产库。
- `ready_for_review`现在根据最终返回的数据库候选字段和warnings计算，避免人工更正/已审核候选的状态与当前解析结果混淆。

## 2026-11-10 P0-02来源URL空白与控制字符拒绝
- 成功标准：URL共享校验不得在`urlsplit`规范化后接受原字符串中的空白/控制字符；在线请求前及离线清单校验都应拒绝，避免等价URL以不同原文存储。
- 复现前共享校验接受前导/尾随空格、换行、制表符、NUL与DEL；样本清单又会先去除空白。现URL校验拒绝Unicode空白和C0/C1控制字符，清单保留原始URL字符串并给出错误，不会发请求。
- parser/HTTP/sample-validator/evaluator专项 **117 passed**；全量离线pytest **223 passed、11 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。编译、目标JSON和Compose配置检查通过。解析器版本`generic-labelled-v0.2.23`。
- 仅本机离线验证；未访问网站/NAS，来源仍OFF。

## 2026-11-10 P0-02清单复用共享来源URL校验
- 成功标准：清单校验与API/解析器的来源URL主机、协议、凭据、端口、查询/片段及ID识别规则一致，避免重复白名单再次漂移。
- 样本校验器删除本地宁波主机白名单和重复URL解析，改为复用`extract_source_id`及共享URL校验；保留清单易读的错误分类和220位ID行为。
- parser/样本校验/评估器专项 **96 passed**；全量离线pytest **211 passed、11 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。CLI、编译、GOAL_STATE JSON及Compose检查通过。
- 仅本机离线验证，来源仍OFF，未访问网站/NAS。

## 2026-11-10 P0-02/P0-03来源URL限定宁波主机
- 成功标准：API手工样本、在线采集目标和离线样本清单都只接受项目配置的宁波站点，不能将其他城市同平台挂牌混入宁波房源库。
- 新增上海/杭州及平台根域拒绝回归，旧共享URL校验会放行上海、杭州子域；现仅允许贝壳`nb.ke.com`与安居客`ningbo.anjuke.com`，最多规范化一个DNS根尾点。样本清单主机规则同步，解析器版本升至`generic-labelled-v0.2.22`。
- parser/HTTP/模型/清单/评估器专项 **109 passed**；全量离线pytest **211 passed、11 skipped**（DB集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。compileall、目标JSON及Compose校验通过。
- 仅本机验证；在线采集仍受许可/robots门控且OFF，本轮未连接网站或NAS。

## 2026-11-10 P0-03统一样本与解析器的房源ID识别
- 成功标准：样本清单URL ID核验和页面解析共用同一房源ID提取规则，防止两处正则再次漂移；校验器CLI应在项目依赖环境可直接运行。
- 清单校验器改为复用`extract_source_id`，移除重复维护的来源URL ID正则，并显式加载项目根路径；此前新增的两来源221位ID回归和CLI子进程用例均通过。
- 解析器/样本校验/评估器专项 **87 passed**；全量离线pytest **202 passed、11 skipped**（数据库测试需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。`validate_sample_set.py --help`、compileall、GOAL_STATE JSON及Compose校验通过。
- 仅本机项目依赖环境验证；系统Python缺少项目依赖，未用其执行脚本；未连接网站/NAS。

## 2026-11-10 P0-03从无ID提交URL使用唯一规范房源ID
- 成功标准：若提交URL未包含可识别ID，页面中唯一且通过同源/格式校验的canonical或og:url详情ID可作为稳定ID；多个规范ID冲突时不猜测，继续留空并告警。
- 新增贝壳canonical、安居客og:url补足ID及互相冲突规范链接回归，修复前均失败；解析器版本升至`generic-labelled-v0.2.21`。
- 专项`tests/test_collection_parser.py tests/test_parser_evaluation.py tests/test_sample_set.py`：**87 passed**；全量离线pytest **202 passed、11 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。编译、目标JSON和Compose配置校验通过。
- 只验证离线解析逻辑及合成评估清单；无真实样本准确率、站点布局或授权结论，未连接网站/NAS。

## 2026-11-10 P0-03数值准确率精确比较
- 成功标准：解析器评估报告中的数值准确率必须遵守“严格匹配”，不能把有实际差异的面积或挂牌价四舍五入成正确。
- 新增面积`120`对标签`120.004`及挂牌价`400`对标签`400.004`回归；修复前均被算作正确，现以有限Decimal精确比较，等值数值格式仍自然相等。
- 解析器/样本校验/评估器专项 **83 passed**；全量离线pytest **198 passed、11 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。编译、目标JSON和Compose配置校验通过。
- 仅离线逻辑验证；无获准真实样本，不产生真实站点准确率结论。

## 2026-11-10 P0-03样本URL房源ID上限对齐
- 成功标准：样本清单与解析器使用相同的来源详情URL ID范围，避免样本评估因超过模型长度的数字串被误认成真实可解析ID。
- 新增两来源221位URL ID且标记`unknown_id`的回归；修复前清单错误报告ID冲突，现两站均按解析器的220字符上限视为不可识别ID。
- `tests/test_sample_set.py tests/test_collection_parser.py tests/test_parser_evaluation.py`：**81 passed**；全量离线pytest **196 passed、11 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。编译、目标JSON和Compose配置校验通过。
- 仅本机离线逻辑验证；真实样本、许可和V0.1备份仍缺，未连接网站/NAS。

## 2026-11-10 P0-02样本文件扩展名边界
- 成功标准：样本清单仅接受校验器及解析评估器支持的普通HTML或gzip HTML文件；其他扩展名即使内容可解码也必须拒绝。
- 新增`.txt`回归，修复前清单会将其作为HTML样本接受；现在仅允许`.html`和`.html.gz`，并在解析前明确报错。
- 样本校验/解析评估专项 **30 passed**；全量离线`pytest -q -rs`：**195 passed、11 skipped**（11项需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 仅本机离线验证；无真实样本、许可或V0.1备份，不代表页面准确率、来源授权或NAS部署验收。
- `scripts/package_dev.py`生成源码开发包（97个文件，含SHA256清单）；ZIP完整性及包内哈希核验通过。

## 2026-11-10 PostgreSQL 16隔离全量回归（含样本编码校验）
- 当前工作区全量pytest在本机临时PostgreSQL 16 `rehouse_test`执行：**182 passed、0 skipped**；保留1条Starlette/httpx弃用警告。
- 数据库只监听Unix socket；测试后停止，`pg_isready`确认no response，临时集群目录已删除。
- 验证覆盖当前样本UTF-8前置校验和数据库集成用例；不替代NAS PostgreSQL 17/生产运行、真实V0.1数据库升级，也不证明样本授权或解析准确率。

## 2026-11-10 P0-02样本HTML编码前置校验
- 成功标准：清单校验通过的普通/gzip HTML必须能以评估器使用的UTF-8严格解码，避免校验通过后才在解析阶段报错。
- 回归先复现：哈希正确的非UTF-8普通与gzip文件均被清单校验接受；现于样本完整性校验时拒绝并给出`HTML sample must be valid UTF-8`。
- 样本校验/解析评估专项 **27 passed**；全量默认`pytest -q -rs`为**171 passed、11 skipped**（跳过项需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。`compileall`和目标JSON解析通过。
- 仅本机离线验证，不判断来源授权、不代表真实页面质量；本轮未运行数据库集成或NAS部署。V0.2样本工具不自动猜编码/转码。

## 2026-11-10 PostgreSQL 16隔离全量回归
- 在本机临时PostgreSQL 16 `rehouse_test`库执行全量pytest：**179 passed、0 skipped**；保留1条Starlette/httpx弃用警告。
- 测试期间集群只监听Unix socket，实例/schema使用专用隔离库；测试后停止集群，`pg_isready`返回no response，`/private/tmp`临时集群目录已删除。
- 该结果验证当前工作区全套DB与离线用例，不替代NAS PostgreSQL 17/生产运行验收，也不替代真实V0.1数据库备份升级或DTK联调。

## 2026-11-10 P0-06 DTK分页上限路径覆盖
- 补齐页大小上限的两处遗漏验证：异步任务嵌套`data.items`超限和实际请求参数`count`。
- 现在普通页/任务结果都拒绝21条，20条正常；请求参数断言与`PAGE_SIZE`同源。
- 全量本机`pytest -q -rs`：**168 passed、11 skipped**；跳过项需`TEST_DATABASE_URL`，另有1条Starlette/httpx弃用警告。`compileall`和目标JSON解析通过。
- 只验证本地模拟响应，不证明真实DTK遵循请求页大小；未连接DTK/NAS。

## 2026-11-10 P0-06 DTK响应分页大小上限
- 成功标准：请求页大小与解析器上限使用同一常量；超过请求数的响应显式失败，不让异常大页被Worker整批落库。
- 新增20条边界接受与21条超限拒绝回归；`PAGE_SIZE=20`同时用于请求参数和响应校验，超限抛`DtkError`。
- 全量本机`pytest -q -rs`：**166 passed、11 skipped**；跳过项需`TEST_DATABASE_URL`，另有1条Starlette/httpx弃用警告。`compileall`及GOAL_STATE JSON解析通过。
- 仅离线逻辑验证，不代表真实DTK响应规格；未连接DTK/NAS或获准账号，不涉及数据库迁移。

## 2026-11-10 P0-03 aria-hidden与视觉隐藏区分
- 成功标准：`aria-hidden="true"`本身不得使仍可见的详情文本从解析输入中消失；真正隐藏的元素仍由`hidden`属性或可识别的内联`display:none`规则排除。
- 回归先复现可见`aria-hidden`价格被误忽略，导致解析器错误保留另一个价格；现解析器仅把`hidden`视为HTML隐藏标记，不再把ARIA可访问性标记等同于视觉隐藏。版本升至`generic-labelled-v0.2.9`。
- 全量本机`pytest -q -rs`：**164 passed、11 skipped**；跳过项需`TEST_DATABASE_URL`，另有1条Starlette/httpx弃用警告。`compileall`、GOAL_STATE JSON解析通过。
- 仅离线回归验证，不代表真实页面字段准确率；无DB迁移/配置变化，未部署NAS。

## 2026-11-10 全量离线回归复核
- 对当前工作区执行全量`pytest -q -rs`：**163 passed、11 skipped**；11项均为需`TEST_DATABASE_URL`的PostgreSQL集成用例。另有1条Starlette/httpx弃用警告。
- 覆盖近期DTK时间戳、字段类型和分享URL保护，以及解析器、API、worker、脚本等离线测试；编译、ZIP构建和GOAL_STATE JSON结构另行校验。
- 本轮仅验证工作区，不连接真实DTK/NAS、未访问来源网站、未运行数据库集成；生产部署状态未变化。

## 2026-11-10 P0-06 DTK分享链接主机校验
- 成功标准：保存为Douyin作品来源的HTTPS链接必须属于`douyin.com`或`iesdouyin.com`根域/子域；其他主机回退canonical链接。
- 回归先复现任意HTTPS域（含`douyin.com.example`伪后缀）会被原样接受；现使用边界明确的域后缀匹配，保留两类平台域名及短链`v.douyin.com`。
- `tests/test_dtk.py tests/test_worker.py`：**46 passed**；`compileall`通过。未运行全量测试。
- 仅本机离线验证；允许域名基于已知分享链接形式，未在线核实其当前完整清单，亦未连接DTK/NAS。未知但合法的外部分享域会回退canonical地址。

## 2026-11-10 P0-06 DTK分享链接校验
- 成功标准：视频来源链接仅接受有效HTTPS URL，拒绝脚本/数据/明文HTTP、用户密码、非法端口或控制字符；无效值回退至作品ID对应的HTTPS抖音链接。
- 回归先复现`javascript:`、`data:`、HTTP与含凭据HTTPS链接被原样保存；现按URL结构校验并裁剪空白，fallback将作品ID编码为单一路径段。
- `tests/test_dtk.py tests/test_worker.py`：**43 passed**；`compileall`通过。未运行全量测试。
- 仅本机离线验证；未连接DTK服务或测试获准账号。HTTPS外部域名仍可作为上游分享链接保留；本轮不做平台域名鉴真。

## 2026-11-10 P0-06毫秒时间戳单位边界
- 成功标准：时间戳恰好等于`10^12`时按毫秒解释；整数和数字字符串行为一致。
- 回归先复现阈值边界被按秒解释并返回未知时间；毫秒判定由`>`改为`>=`。
- `tests/test_dtk.py tests/test_worker.py`：**37 passed**；`compileall`通过。未运行全量测试。
- 仅本机离线验证；真实DTK服务/账号联调未做，P0-06仍需接口版本/权限核验及3个获准账号24小时运行。

## 2026-11-10 P0-06 DTK文本字段类型校验
- 成功标准：上游文本字段类型异常时不把列表/对象的Python表示写入视频元数据；优先回退到同字段的有效字符串。
- 回归先复现：列表型作者名被写为`['unexpected']`；新增`_first_text`仅接纳非空字符串，标题、作者名、描述采用有效候选回退，非字符串`poi_name`置空。
- `tests/test_dtk.py tests/test_worker.py`：**35 passed**；`compileall`通过。未运行全量测试。
- 仅本机离线验证；未连接DTK实例或测试获准账号。未更改DB字段/配置；真实DTK版本、权限和24小时账号联调仍未验证。

## 2026-11-10 P0-06 DTK异常时间戳防护
- 成功标准：不可表示或无法转换的数字时间戳不应使整轮账号同步崩溃，而应作为未知发布时间处理。
- 回归先复现超大整数在`float()`转换处抛出`OverflowError`；`normalize_datetime`现捕获数值转换的`OverflowError`/`ValueError`并返回`None`。覆盖超大整数、Unicode上标数字和超长数字字符串。
- `tests/test_dtk.py tests/test_worker.py`：**34 passed**；`compileall`通过。未运行全量测试。
- 仅本机离线验证；未连接DTK实例或测试获准账号。P0-06仍需核对DTK版本/权限并完成3个账号24小时联调。

## 2026-11-10 P0-03折叠详情区内容隔离
- 成功标准：默认折叠的`details`只保留可见首个摘要；内部隐藏内容不污染挂牌字段；显式`open`内容继续解析。
- 回归先复现折叠推荐价令挂牌价变为`None`；解析器现保留首个直接子级`summary`文本并移除其余折叠内容，无摘要则移除整个区块。版本升至`generic-labelled-v0.2.8`。
- `tests/test_collection_parser.py tests/test_parser_evaluation.py tests/test_sample_set.py`：**54 passed**；`compileall`与GOAL_STATE JSON解析通过。未运行全量测试。
- 仅本机离线逻辑验证；真实页面、浏览器脚本/CSS状态、NAS部署及真实准确率未验证。无数据库迁移或配置变化。

## 2026-11-10 P0-03关闭弹层内容隔离
- 成功标准：默认关闭的`dialog`中推荐挂牌价不影响详情挂牌解析；`open`弹层仍保留可见内容解析。
- 回归先复现关闭弹层中的第二个总价会令详情价格变为`None`；解析器现仅移除没有`open`属性的`dialog`，版本升至`generic-labelled-v0.2.7`。另覆盖`template`惰性内容和显式打开弹层。
- `tests/test_collection_parser.py tests/test_parser_evaluation.py tests/test_sample_set.py`：**52 passed**；`compileall`与GOAL_STATE JSON解析通过。未运行全量测试。
- 仅本机离线逻辑验证；真实页面、CSS/JS浏览器渲染、NAS部署及真实准确率未验证。无数据库迁移或配置变化。下一步仍需获准真实样本与旧库备份材料。

## 2026-11-10 NAS连接路径复核
- 按 `nas-ssh-connect` 对 `nas-lan` 做沙箱外只读身份核验仍超时；Tailscale CLI无法加载偏好，`/Applications/Tailscale.app`启动报`kLSNoExecutableErr`。
- 未使用Netcatty或公网SSH。技能要求自动化切换至现有`notedock-nas`公网别名前先取得授权，已向用户提出该项具体授权；回复前不连接公网别名。

## 2026-11-10 P0-05隔离PostgreSQL 16完整回归
- 在 `/private/tmp` 新建PostgreSQL 16临时集群和 `rehouse_test` 专用数据库，只监听Unix socket；运行完整套件 **144 passed、0 skipped**，覆盖本轮API正文边界与现有数据库迁移/API集成。
- `pg_isready`确认测试后socket无响应，临时集群目录已删除；未连接NAS或写入现有数据库。保留1条Starlette/httpx弃用警告。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-10-p0-05-pg16-full.zip`，包含本轮API字节上限实现及验证文档。

## 2026-11-10 P0-02/API样本提交字节上限
- 成功标准：API请求在完整缓冲/解析前有固定体积上限；提交HTML按UTF-8字节数限制为1,000,000，与本地清单和CLI一致。
- 新增Content-Length超限、分块无长度超限、正常体积正文重放、模型多字节UTF-8上限及解析器字节上限回归；`tests/test_collection_models.py tests/test_collection_parser.py tests/test_collection_body_limit.py` **31 passed**。
- 全量默认pytest **133 passed、11 skipped**（数据库集成需`TEST_DATABASE_URL`）；`app/collectors/parser.py`版本更新为`generic-labelled-v0.2.5`。超限API请求返回413；未进行真实网页采集。NAS技能复核时LAN SSH超时，Tailscale CLI无法读取偏好；`/Applications/Tailscale.app`因可执行文件缺失无法启动。未切换Netcatty、未同步或部署。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-10-p0-02-api-body-limit.zip`，构建器校验97个源码/文档文件及包内清单。

## 2026-11-10 P0-02样本时间顺序校验
- 成功标准：真实样本清单中的人工复核时间不得早于页面采集时间；时区不同也按实际时间比较。
- 新增回归先复现校验器接受倒序时间，再修复为解析带时区ISO-8601并检查 `reviewed_at >= captured_at`。样本专项 **11 passed**；全量默认 pytest **128 passed、11 skipped**（数据库集成需 `TEST_DATABASE_URL`）。
- 只验证清单时间一致性，不证明许可真实有效或页面是真实获准样本。按NAS技能复核时，LAN SSH连接超时，Tailscale CLI无法读取偏好且系统未找到Tailscale App；未切换Netcatty、未同步或部署。

## 2026-11-10 P0-03内联 display 声明级联修正
- 成功标准：内联样式按声明顺序和 `!important` 优先级判断最终 `display`；被后续声明恢复可见的详情内容仍可解析。
- 新增 CSS 级联优先级回归及可见详情容器解析回归；解析器专项 **23 passed**。全量默认 pytest **127 passed、11 skipped**（数据库用例需 `TEST_DATABASE_URL`）。
- `PARSER_VERSION` 更新为 `generic-labelled-v0.2.4`。没有真实获准页面，未报告站点准确率；外部样式表仍不在本轮范围内。
- NAS LAN SSH 超时；Tailscale CLI 无法读取偏好。本轮未同步或部署，也未使用 Netcatty。下一步待 LAN 恢复后再按技能核验并执行适用的隔离验收；P0-02仍缺真实获准样本。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-10-p0-03-css-cascade.zip`；95个源文件及清单由构建器校验。

## 2026-11-10 P0-02样本提交端尺寸预检
- 成功标准：提交本地HTML前只读取最大限制加1字节检查，超限时在HTTP调用之前退出。
- 新增`tests/test_submit_html_snapshot.py`子进程回归；修复前会读完整超大文件并尝试请求API，现`submit_html_snapshot.py`对超过1,000,000字节或非UTF-8样本直接给CLI错误。
- 专项 **1 passed**；全量默认pytest **122 passed、11 skipped**（数据库用例需`TEST_DATABASE_URL`）；编译、Compose配置、GOAL_STATE JSON解析通过。
- 只验证本地CLI边界；服务器模型上限仍为1,000,000字符，真实授权样本、NAS服务行为及网络部署未在本轮验证。
- 下一步：取得每站20份获准人工标注页面后进行清单校验与评估；NAS通道恢复后先核实身份和备份，再执行适用的隔离验收。

## 2026-11-10 P0-03内联隐藏报价及解析版本
- 成功标准：详情价格解析忽略明确使用内联`display:none`隐藏的广告/推荐内容，解析逻辑变更后候选带有可追溯版本。
- 两项样式回归先复现隐藏报价导致价格字段冲突、挂牌价被置空；解析器现在识别`display:none`及`display: none !important`并移除对应元素。`PARSER_VERSION`递增为`generic-labelled-v0.2.3`。
- 解析器专项 **18 passed**；全量默认pytest **121 passed、11 skipped**（数据库用例需`TEST_DATABASE_URL`）；`compileall`、Compose配置、GOAL_STATE JSON解析通过。
- 只覆盖明确内联隐藏样式，不含CSS外部样式表/类选择器的完整浏览器计算；真实贝壳/安居客样本和准确率仍缺。
- 下一步：取得获准真实样本后执行20+20解析评估；NAS通道恢复后先备份，再按需隔离验证并同步可部署增量。

## 2026-11-10 P0-02拒绝样本路径符号链接
- 成功标准：样本清单解析只能读取真实位于项目`data/raw-pages`内的普通路径；根目录或文件路径中的链接不得扩大样本边界。
- 新增样本文件链接与`data/raw-pages`根目录链接回归，均先复现错误接受。校验器现在沿样本路径检查符号链接组件，再验证解析后路径仍处于真实样本目录。
- 样本校验/评估专项 `tests/test_sample_set.py tests/test_parser_evaluation.py` **15 passed**；全量默认pytest **119 passed、11 skipped**（需`TEST_DATABASE_URL`）；编译、Compose配置、目标JSON解析通过。
- P0-02仍缺每站20份获准真实页面；这一改变只验证文件系统路径，不判断样本授权。未访问网站。
- 下一步：取得许可来源及人工标签后校验样本并评估解析器；NAS恢复后先核实身份/备份，再做适用的隔离验证与只读报告同步。

## 2026-11-10 P0-02/P0-03样本读取尺寸上限
- 成功标准：清单校验与解析评估在读取本地样本时限制磁盘输入和解压HTML大小，拒绝超限内容后再交给解析器。
- 新增普通HTML超1,000,000字节与gzip解压后超限用例，先复现校验器接受超限样本；`validate_sample_set.py`现在最多读取2,000,000字节压缩文件，gzip使用有界解压，HTML最多1,000,000字节。解析评估器复用同一读取函数，不能绕过清单限制。
- `tests/test_sample_set.py tests/test_parser_evaluation.py`：**13 passed**；全量默认pytest **117 passed、11 skipped**（数据库集成需`TEST_DATABASE_URL`）；`compileall`、Compose配置和GOAL_STATE JSON解析通过。
- 样本路径不访问网络。超限用例为本地合成文件；没有真实页面，P0-02仍待每站20份获准人工标注样本，P0-03仍无真实性能/准确率结论。
- 下一步：NAS恢复后先核实主机与备份，再同步并只读验证P0-08报告脚本；P0-02真实样本仍待许可来源与人工标注。

## 2026-11-10 P0-08留存报告符号链接边界
- 成功标准：`storage_report.py`统计仅限传入的真实raw-pages/备份目录及其普通文件，不跟随指向范围外的符号链接。
- 新增文件符号链接、目录符号链接和根目录符号链接回归；修复前2项失败，报告原先分别把外部文件计入并进入链接根目录。现在统一使用不跟随链接的普通文件遍历。
- 专项 `tests/test_storage_report.py` **7 passed**；默认全量pytest **114 passed、11 skipped**（数据库集成需`TEST_DATABASE_URL`）；编译、Compose配置、GOAL_STATE JSON解析通过。
- 备份90天/原始页面证据随关联记录保留策略不变；报告不删除文件。本轮NAS LAN仍超时、Tailscale CLI无法读取偏好，报告脚本未同步，NAS当前超期数量未读取。
- 下一步：NAS通道恢复后先按技能核验主机与目录，再运行新版只读报告；任何备份清理仍需人工核对可恢复性和回滚引用。

## 2026-11-10 P0-03隔离侧栏及隐藏报价
- 成功标准：详情页字段解析不受语义侧栏推荐房源和HTML显式隐藏内容中的相似价格污染。
- 新增`aside`推荐报价和`aria-hidden=true`广告报价回归；隐藏内容用例先失败并把挂牌价置空，随后`app/collectors/parser.py`统一移除`aside`及`[hidden]`/`[aria-hidden="true"]`元素后通过。
- 解析器专项 **16 passed**；全量默认pytest **112 passed、11 skipped**（11项需`TEST_DATABASE_URL`）；`compileall`、Compose配置和GOAL_STATE JSON解析通过。
- 此改进只针对语义标记可识别的侧栏/隐藏元素，不代表能识别所有广告布局。没有真实获准网页，未报告字段准确率；来源在线采集仍OFF，未访问房源页或生产数据库。
- 下一步：取得获准的每站20份页面后按清单和评估器报告实际指标；NAS通道恢复后先备份，再隔离验收本轮API/Worker适用增量。

## 2026-11-10 P0-06 DTK任务状态响应校验
- 成功标准：异步任务状态字段缺失或类型异常时可及时、明确失败；失败响应格式异常不能引发未处理的Python异常或回显上游详情。
- 新增用例先复现：缺失/null/数组/数字/空白`state`均会轮询到52秒截止；格式错误的`error`数组会触发`AttributeError`。`app/dtk.py`现在校验状态为非空字符串，失败状态只抛固定`DtkError('DTK task failed')`。
- 未限定或猜测未知非空状态字符串的语义，仍由现有绝对截止时间兜底。DTK专项 **30 passed**；默认全量pytest **110 passed、11 skipped**（11项需`TEST_DATABASE_URL`）；`compileall`、Compose配置和GOAL_STATE JSON解析通过。
- 未连接真实DTK、未使用账号数据、未同步NAS。LAN SSH本轮超时、Tailscale CLI无法读取偏好；P0-06仍待NAS核验接口版本/权限及3个获准账号24小时联调。
- 下一步：NAS通道恢复后按技能先核实主机并只读盘点，再隔离验证代码增量；真实账号联调需用户提供获准账号。

## 2026-11-10 开发包构建器凭据排除加固
- 成功标准：开发包不包含符号链接目标、常见凭据目录、私钥或凭据文件；正常源码、`.env.example`与运行所需占位文件仍可打包。
- `scripts/package_dev.py`现跳过符号链接，并排除`.aws`/`.ssh`/凭据目录、常见私钥扩展名及凭据文件名。新增回归先复现归档包含4项而预期1项，再验证仅普通源码入包；`tests/test_package_dev.py` **3 passed**。
- 默认全量pytest **105 passed、11 skipped**（11项需`TEST_DATABASE_URL`）；`compileall`、`docker compose config -q`及`docs/GOAL_STATE.json`解析通过。历史115 passed的隔离PostgreSQL 16测试未覆盖本轮新增打包器用例。
- NAS LAN连接仍未恢复，Tailscale状态不可读取；本轮未同步或部署。采集来源保持OFF，未连接生产数据库或访问房源页面。
- 下一步：保留P0优先级，待NAS通道恢复先只读确认主机与备份，再隔离验收跨平台机会API增量并评估API-only部署；P0-02仍需许可明确的真实样本，P0-01仍缺V0.1备份。

## 2026-11-10 P0-08 NAS备份库存复核
- 通过现存 `nas-lan` SSH 复用连接只读盘点：`backups/`约1.1MiB、29个文件、6个一级子目录；数据库/raw-pages备份目录分别约64–200KiB，源码快照目录约272KiB。
- `/volume3`可用约405GiB、使用率56%；API/Worker运行，PostgreSQL healthy，`/healthz`=200。未删除或修改备份、证据或容器。
- 新盘点只提供当前容量证据，不能决定留存期限或代替压力测试；自动清理仍未配置，P0-08继续进行中。

## 2026-11-10 P0-01/P0-08 UGREEN项目页视觉核验
- 通过桌面状态只读检查，Mac仍锁定，自动解锁失败；未能打开UGREEN Docker项目页，因此不将CLI/Compose运行态当作UI视觉验收。
- 已请求用户解锁Mac；容器服务和项目登记未触碰。

## 2026-11-10 P0-02/P0-03 样本证据审计
- 工作区`data/raw-pages/`仅有`.gitkeep`；`fixtures/`只有两份虚构演示HTML。没有可证明获准使用的贝壳/安居客真实页面，故不计入每站20份样本验收，也不报告解析准确率。
- P0-02与依赖它的P0-03继续未完成；需要获准页面、来源/许可范围和人工字段标签。

## 2026-11-10 P0-04 状态一致性审查
- 发现`GOAL_STATE.json`曾将P0-04标为`verified_on_NAS`，与备注、来源矩阵和路线图中“无项目书面许可、目标未完成”的证据矛盾。未收到新许可信息，现已按证据修正为`in_progress`。
- Robots规则核验不构成来源使用授权；两来源在线采集继续关闭。

## 2026-11-10 P1-08 条件单匹配执行 API 部署 NAS
- 新增只读 `GET /api/saved-searches/{id}/matches?limit=100`：按条件单硬条件筛选正式挂牌，偏好小区优先排序并标记，返回总匹配数和受 `limit` 控制的结果；API 文档与 PostgreSQL 集成用例同步。
- 本机全量测试 **54 passed、8 skipped**（数据库用例需 `TEST_DATABASE_URL`）；NAS 隔离 PostgreSQL 17 在内部 bridge 网络、无生产卷/环境密钥的临时运行器中执行 `tests/test_db_integration.py`：**9 passed**。新用例验证硬筛选、偏好排序/标记、`total`/`limit` 和未知条件单 404。测试容器和源码包已定向清理。
- 部署前数据库/raw-pages备份：`backups/ningbo-re-ai-20261109T232953Z-1351503`，`SHA256SUMS`、`pg_restore --list`及归档结构由备份脚本检查通过；数据库备份权限700/600。旧API源码/Compose/状态文件快照 `backups/source-snapshots/api-before-matches-20261109T232952Z.tar.gz`，SHA-256 `74ee4dce82a31460e53b7a0761c53ba9ca24accee0dc63279b03bf31745d99ac`，文件600。
- 复用已部署依赖层构建API镜像 `sha256:b2e24f878bbd24b0b62130c4bc02e29fed8ac9336e30f8b22afba9ef19f9a794`；只重建API，Worker、PostgreSQL、数据库卷、Docker引擎和005迁移均未触碰。Compose项目名 `ningbo-re-ai`、登记文件路径及本机端口8788保持不变。
- NAS验收：`/healthz`=200；OpenAPI显示匹配路径为GET；无API Key请求返回401；容器内 `main.py/services.py` 哈希与工作区一致。PostgreSQL healthy，两来源 `online_enabled=false`，条件单和正式挂牌均0条；没有写生产测试数据。
- SSH数据库隧道、NAS测试容器及临时源码/归档均已清理。后续仍按 P0 优先处理合法来源许可与真实样本；UGREEN项目页视觉核对、正式备份留存周期仍未完成。

## 2026-11-10 P1-07条件单筛选扩展部署生产NAS
- 部署前确认生产`saved_searches`为0行、005新增字段0个、两来源OFF、启用采集目标0；`/volume3`可用约406GiB，API/Worker运行、DB healthy、`/healthz`=200。
- 使用项目备份脚本生成生产数据库与raw-pages备份`backups/ningbo-re-ai-20261109T224647Z-1242652`，SHA256校验通过；变更前代码/Compose快照保存在`backups/source-snapshots/workspace-before-p1-07-20261110.tar.gz`（600，SHA-256 `9785ef9a5a47ba19187ebfb9fdda56f64ffebc8099129cb36e44cac974eb4441`）。
- 只加列的005迁移已执行：四个新字段存在、约束1个、saved_searches仍0行。构建新API/Worker镜像后仅更新这两个应用容器，未重启DB或Docker引擎。
- 容器内`main.py/services.py/models.py/http_client.py`哈希与工作区一致；认证GET `/api/saved-searches`返回200且0条，`/healthz`=200，DB healthy。两来源仍OFF、启用目标0。Compose登记路径和数据库卷不变。
- 本机全量54 passed、7 skipped（DB集成需`TEST_DATABASE_URL`）；数据库功能此前已在NAS隔离PostgreSQL 17跑8项通过。本轮未向生产条件单写入测试记录，UGREEN页面视觉核对及正式备份留存周期仍未完成。
- 同轮复核备份权限时发现旧`worker.py.pre-log-fields-20261110`快照为777，已收紧为600；现`source-snapshots`目录700、5个快照文件均600。数据库备份目录700、文件600；本轮临时传输文件已清理。

## 2026-11-10 P0-04挑战页阻断修复部署NAS Worker
- 部署前复核NAS `/volume3/docker/ningbo-re-ai`：sources `anjuke/beike` 均`online_enabled=false`，策略分别`not_reviewed/not_authorized`，启用目标0；API和DB运行、DB healthy、`/healthz`=200。
- 将旧`app/collectors/http_client.py`备份至`backups/source-snapshots/http_client.py.pre-challenge-guard-20261110`（权限600，旧SHA-256 `ca4f9cddc03d61c9e68058e12249d0d2e0a6baf4a64ecd582bb3d8ecfd8b7fe2`），上传新文件SHA-256校验后替换为644。
- NAS构建Worker镜像`sha256:72dbb681920a74590bd543a7d317714fb5cf307fb0af606f02ca25dad8db345d`，仅执行Worker重建；容器内源码哈希与工作区`f82033dc6242a0dba48e94cf0795dd1c54e450a438c303143fb3d7befdea723a`一致，Worker启动日志存在，容器内挑战识别检查通过。
- 部署后API仍运行、DB healthy、`/healthz`=200；两来源保持OFF、启用目标0。API镜像、数据库、数据卷和Compose登记未动；未请求任何房源页。

## 2026-11-10 P0-04验证码挑战页阻断修复
- 复现发现：上游返回HTTP 200的58 antibot验证页时，采集器原先会把响应当普通HTML返回，存在误生成候选风险。
- `app/collectors/http_client.py`现识别58 `antibot/verifycode`、CAPTCHA/验证码、滑动/人机/访问验证等高信号标记，统一抛出`blocked_upstream`并保留HTTP状态；挑战正文不进入候选或错误文本，也不重试。在线开关及来源策略未改变。
- 新增模拟HTTP 200 challenge与验证码用例；回归`54 passed, 7 skipped`（7项需`TEST_DATABASE_URL`），`compileall`及占位环境变量下Compose配置解析通过。本次未访问外站；NAS部署结果见上方Worker-only记录。
- P0-04仍因协议许可未确认保持`in_progress`；本轮修复已Worker-only部署验证。P0-08仍需正式留存期限和UGREEN项目页视觉核对。

## 2026-11-10 NAS LAN直连与来源政策复核续接
- 按`nas-ssh-connect`先核对Tailscale状态，再用`nas-lan`直连；SSH身份确认为`DXP4800/sheng`（`admin users docker`）。直连成功，无需Netcatty。
- 只读复核NAS容器：宁波项目API、Worker运行，DB healthy；`http://127.0.0.1:8788/healthz`返回200。未改生产容器、数据、Compose或Docker服务。
- 通过NAS对安居客官方协议中心的只读请求返回58反爬验证页，未取得协议正文；未绕过验证或请求房源详情页。P0-04仍`in_progress`，在线采集保持OFF。
- 本轮仅更新政策证据和项目状态，未改应用代码。项目回归`52 passed, 7 skipped`（跳过项需`TEST_DATABASE_URL`），`compileall`通过，使用占位环境变量执行`docker compose config -q`通过；保留Starlette/httpx弃用警告。下一步等待平台明确书面用途许可；P0-08仍需正式备份留存期限和UGREEN项目页视觉核验。

## 2026-11-10 P0-08 NAS源码与配置权限收紧
- ACL只读核查确认部署目录的`app/`、代码/迁移/脚本/测试/文档及根配置存在真实`other::rwx`，不是显示映射；`.env`为600，`data/`与`backups/`为700。
- 修改前将96条路径的模式/属主清单保存在NAS `backups/source-snapshots/permissions-before-20261110.txt`（SHA-256 `c24a855275c2ffcdafa26b1ca7ce0c7650e02a9b9e0b00bf88f1837872e9b8a9`，权限600）。将项目源码/配置目录调整为755、普通文件644，保留属主；未触碰`.env`内容、数据、备份或Compose登记。
- 复核时保护路径权限仍为`.env 600 / data 700 / backups 700`；保护区外无全员可写文件/目录。`docker compose config -q`通过；API/Worker运行、DB healthy、`/healthz`=200。未重启容器，文件内容未变。

## 2026-11-10 P0-04按项目真实主机核验robots
- 通过NAS技能`nas-lan`直连后，只读请求项目实际采集目标的robots文件：`https://nb.ke.com/robots.txt`和`https://ningbo.anjuke.com/robots.txt`，均HTTP 200；未请求房源详情页。
- 使用项目实际UA `NingboHousingResearchBot/0.2 (operator-controlled; respect robots)`及Python `RobotFileParser`核验：贝壳详情页`can_fetch=False`（通配组`Disallow: /`）；安居客详情页`can_fetch=True`（通配组`Allow: /`，若干其他UA全禁）。SHA-256与长度见来源审查记录。
- 贝壳当前官方协议要求书面许可；安居客有效协议版本/用途范围及本项目书面许可仍未确认。robots允许不代表授权；两站全局与来源在线开关继续OFF，P0-04保持`in_progress`。

## 2026-11-10 P0-08日志修复部署至NAS Worker
- NAS已启用账号和采集目标计数均为0；用`nas-lan`备份原源码至`backups/source-snapshots/worker.py.pre-log-fields-20261110`，原文件哈希`f227bd…534d907`。
- 上传源码哈希与工作区一致（`150a09…9a040d`）；Compose配置解析及`docker compose build worker`成功，镜像ID `sha256:e89b2d…581073a`。只执行`docker compose up -d --no-deps worker`，API、DB、数据卷及项目登记未动。
- 部署后API/Worker运行、DB healthy；容器内Worker源码哈希匹配，启动日志标记存在，最近3分钟日志1行，六类敏感模式0命中；API `/healthz` 返回200、schema=v0.2。

## 2026-11-10 P0-08外部字段名日志泄漏修复
- 抖音上游条目缺少稳定作品ID时，worker原先把外部对象的完整字段名列表写入warning；字段名本身不可信，可能包含敏感文本。现改为仅记录对象类型和字段数量。
- 新增回归用例注入含API key/手机号标记的字段名，确认warning只含固定元数据、不含外部字段名。
- 全量本机回归`52 passed, 7 skipped`（7项需`TEST_DATABASE_URL`），`compileall`通过。该代码随后已按Worker-only方式部署NAS，详见下方记录。
## 2026-11-10 P0-08生产日志只读抽查
- 使用`nas-lan`直连NAS，确认生产API/DB/Worker均运行、DB healthy；只读读取API与Worker日志尾部，实际共13行。
- 在本机内存中扫描手机号、邮箱、Bearer凭据、URL用户信息、凭据赋值和JWT六类模式，均0命中；日志正文未输出或落盘。该结论仅覆盖本次可读日志样本和这些模式，不代表所有日志字段绝无敏感信息。
- 未改NAS配置、服务、数据或日志。本机应用回归不重跑（本轮仅做只读核查及文档更新）；P0-08继续等待留存期限决策和UGREEN页面视觉核对。

## 2026-11-10 P0-08交付打包与NAS直连复核
- 按NAS SSH连接技能使用`nas-lan`确认主机`DXP4800`、用户`sheng`及SSH复用连接正常；本轮未使用Netcatty。
- 已生成工作区同级开发包`ningbo-re-ai-v0.2-dev-2026-11-10-p0-08-30m.zip`，包含30分钟合成负载脚本、报告/资源采样及项目源码、迁移、测试和文档。
- 更新`MANIFEST.sha256`；归档中83个清单文件哈希匹配，未包含环境密钥、备份、缓存、运行数据或旧ZIP。P0-08仍待正式证据/备份留存期限与UGREEN项目页视觉核对；本轮未改NAS生产服务或数据。

## 2026-11-10 Dockerfile命名数据卷权限修复
- `Dockerfile` 现在在降权到UID 10001前创建`/data`，设置owner为10001、权限700；Docker创建全新命名卷时可继承可写目录，避免API首次写raw-pages时报PermissionError。
- 本机pytest **43 passed, 6 skipped**；compileall与Compose配置解析通过。NAS隔离测试以现有API镜像派生临时镜像，仅叠加相同目录权限层；全新`/data`命名卷显示`10001:0 700`，人工样本POST返回200，候选pending=1、原始gzip文件1份、线上OFF。
- 完整工作区Dockerfile离线构建因已有`pip install`层在禁网状态退出，故不声称完整镜像已构建；仅镜像权限层通过NAS实测。隔离容器、卷、网络和临时镜像已清理；生产镜像、服务和数据卷未改。

## 2026-11-10 P0-08 NAS备份库存与留存决策依据
- 通过`nas-lan`只读盘点：`/volume3/docker/ningbo-re-ai/backups`共532KiB、3个子目录、15个文件；`/volume3`约406GiB可用、55%已用。
- 该目录占用当前较低，但不能据此替代运营留存要求或推断未来增长。正式保留期限仍待确定；没有配置自动删除，现有备份和证据保持原样。
- 本轮顺手核对发现部署指南旧“NAS恢复演练尚未完成”文字与2026-11-10隔离恢复记录矛盾，已修正文档，明确NAS隔离恢复已通过、遗留V0.1升级仍因无旧库而无法验证。

## 2026-11-10 P0-04官方robots直连读取未成功
- 从本机对`https://www.ke.com/robots.txt`和`https://www.anjuke.com/robots.txt`各发起一次只读GET；两次TLS握手均以`SSL_ERROR_SYSCALL`失败，没有取得正文。
- 结合网页工具也无法读取的结果，当前仍没有可引用的robots规则内容；不推断为允许或禁止。未访问详情页、未采集，来源开关继续OFF，P0-04保持`in_progress`。

## 2026-11-10 本机全量回归验证
- `/private/tmp/ningbo-re-ai-venv312/bin/python -m pytest -q -rs`：43 passed、6 skipped。6项均因未设置`TEST_DATABASE_URL`而跳过；NAS隔离PostgreSQL 17集成文件另有7 passed验证记录。
- `python -m compileall -q app scripts tests`通过；占位值执行`docker compose config -q`通过。
- 测试输出1条Starlette/httpx弃用警告；本轮没有应用代码或依赖变更。

## 2026-11-10 P0-04贝壳协议与robots入口复核
- 只读打开贝壳官方《平台服务使用协议》，当前页面标注2026-09-24更新、2026-09-25生效。第七条第2项限制未获书面许可读取/使用内容及机器人、蜘蛛擅自获取；第3项限制超出书面许可范围的商业使用，并要求遵守Robots协议。
- 通过网页工具打开贝壳与安居客 `robots.txt` 均不可访问；工具错误不能判断robots内容允许或禁止。安居客协议中心正文仍未能由工具显示，已有官方PDF版本日期缺失。没有本项目书面许可。
- 没有访问房源详情页、没有在线采集或尝试绕过访问限制。P0-04继续 `in_progress`，在线采集保持关闭；后续仍需平台书面确认用途范围及可读取的robots规则。

## 2026-11-10 P0-08 NAS隔离业务负载延长至15分钟
- `nas-lan` 直连DXP4800，运行唯一临时Compose项目 `ningbo-re-ai-load15m-20261110`；API/DB各限1 CPU/512MiB，网络为internal且无宿主机端口，独立数据库/证据卷，在线采集总开关和来源开关均OFF。负载只向隔离API提交固定虚构HTML，source URL仅作候选字段存储，没有访问来源网站。
- 先做20秒烟雾检查：158个导入→审核→挂牌→健康读取完整工作流、791请求、0错误；候选/审批/挂牌/价格历史各158，待审0。
- 延长负载运行15分钟：脚本报告5,981个完整工作流；退出后隔离DB核对候选5,981、approved 5,981、pending 0、挂牌5,981、价格历史5,981、汇总指标2条、在线开关false。终端对较长JSON摘要作了截断，因此本记录不报告15分钟运行的端点P95/完整错误字段；有效证据采用已完成工作流数、DB对账与退出码。资源采样142次，DB峰值约96.3%单核/74.6MiB；API峰值摘要未保留。该结果仅适用于受限合成负载，不是生产SLO或容量承诺。
- 初次烟雾尝试发现临时空数据卷默认root属主、API UID 10001不能创建raw-pages目录；只修正该隔离卷属主后烟雾通过，无应用代码或生产目录改动。
- 临时容器、卷、网络及脚本定向清理。清理后生产API/Worker仍running、DB healthy；生产 `collection_runs`、候选、挂牌、价格历史均0，来源开关false。
- P0-08继续 `in_progress`：补充15分钟隔离业务链路证据；正式备份留存期限和UGREEN页面视觉核对未完成。测试不触及真实网站/房源，不能替代经许可样本验收。

## 2026-11-10 P0-08迁移后备份隔离恢复验收
- 使用 `nas-lan` 直连DXP4800/sheng，恢复部署后备份 `backups/ningbo-re-ai-20261109T194304Z-884213`。`database.dump`、`raw-pages.tar.gz` 的SHA256、PostgreSQL恢复目录与归档结构均通过；目录权限700、文件600。
- 将数据库恢复到独立PostgreSQL 17隔离栈，核对来源策略和健康汇总各2行；运行、候选、挂牌及价格历史业务表均为0行，在线采集开关保持关闭。隔离API实际连接恢复库后，`/api/collection/health` 返回两个来源且计数为0、状态OFF。
- NAS生产 `raw-pages` 与恢复归档树摘要一致：2个文件、249字节，哈希摘要匹配。隔离容器、卷、网络及临时恢复文件已定向删除；生产API/Worker运行、DB healthy、`/healthz`=200，生产业务表仍为空。
- P0-08继续 `in_progress`：本轮补齐迁移后备份的隔离恢复证据；正式备份留存期限、UGREEN项目页视觉核对和更长时段/递增负载验收仍待完成。

# 项目事实状态（跨会话接力优先读取）

更新：2026-11-10。版本：V0.2。**请不要把“代码存在”“单元测试通过”“NAS已验证”“线上可稳定采集”视为同一件事。**

## 2026-11-10 条件单筛选扩展（NAS隔离验收后已部署生产）
- 为条件单新增多区域硬筛选、偏好小区标记、排除小区硬筛选和挂牌最近观察天数；旧版`district`、`community_name`及价格/面积/户型字段保持可用。
- 新增幂等迁移`sql/005_saved_search_filters.sql`，Compose空库初始化顺序扩为001–005，并在NAS部署指南记录既有库迁移步骤。迁移只加列及约束，不改写或删除既有条件。
- 新建`tests/test_saved_search.py`覆盖区域/社区排除、硬筛选、软偏好和挂牌时效；PostgreSQL集成fixture重复执行005，并验证API持久化及提醒偏好字段。
- 通过NAS `nas-lan` 在隔离PostgreSQL 17中运行`tests/test_db_integration.py`：8 passed，包含重复运行005迁移、创建新条件单并核对数据库数组字段，以及新房提醒中的偏好标记。隔离容器、网络和临时源码已清理。
- 本机全量测试47 passed、7 skipped（需`TEST_DATABASE_URL`）；`compileall`及Compose配置解析通过。NAS隔离数据库集成8项通过后，已于2026-11-10完成生产备份、005迁移及API/Worker更新；生产部署细节见本文件顶部记录。
- 在线采集策略未改变。

## 2026-11-10 P0-08五分钟NAS隔离业务负载
- 使用当前NAS API镜像和PostgreSQL 17建立独立Compose栈：内部网络、无宿主机端口、独立512MiB数据卷；API与DB各限1 CPU/512MiB。在线采集总开关和两个来源开关均OFF，没有访问贝壳/安居客。
- 4并发运行300.4秒，循环执行虚构HTML候选导入、待审核列表读取、人工审批、挂牌查询和健康指标查询；2,175个完整工作流、10,876个API请求，0错误。
- 主端点P95：候选导入173.90ms（2,175次）、待审核列表107.76ms（2,175次）、挂牌读取177.87ms（2,175次）、健康指标106.40ms（2,176次）。审批端点逐UUID统计，采样脚本未聚合其P95，故不报告该指标。
- 每约3秒采样资源95次：API平均/峰值CPU约78.0%/94.9%，峰值内存71.3MiB；DB平均/峰值CPU约101.4%/108.0%，峰值内存45.3MiB。DB受单核上限约束并接近饱和；这些结果只适用于隔离合成负载，不是生产SLO或容量承诺。
- 结束后候选2,176条全部approved、pending=0，挂牌与价格历史各2,175条；同一虚构来源ID复用使挂牌数比候选数少1。2,176份gzip证据逐一解压验哈希，0差异；汇总与原表按来源对账一致，在线开关仍关闭。
- 临时容器、网络、数据库卷、证据卷和采样脚本均已定向清理；生产API/Worker/DB继续运行，/healthz=200，生产业务表仍为0行。没有生产数据或生产raw-pages进入测试。
- P0-08保持in_progress：还需明确正式备份保留期限、完成UGREEN页面视觉核对，并继续更长时段/递增负载验收。

## 2026-11-10 P0-08 NAS当前版本部署与生产迁移验收
- 通过nas-lan同步当前工作区版本至原Compose目录 /volume3/docker/ningbo-re-ai；先对数据库和raw-pages生成新备份，随后另存旧源码归档。备份目录权限700、文件600，SHA256、pg_restore目录、raw-pages tar结构均通过；不含.env。
- rsync明确排除.env、data和backups；保留原Compose项目名ningbo-re-ai、登记文件路径 /volume3/docker/ningbo-re-ai/docker-compose.yml 与PostgreSQL卷ningbo-re-ai_pgdata。NAS本地API端口仍为127.0.0.1:8788。
- NAS原生产库在迁移前有0条collection_runs、0条collection_candidates和0条source_listings。工作区代码和Compose配置经SHA256/配置解析检查后，在生产DB执行003及004；004回填后两个来源指标均为0、在线采集均关闭。
- 当前API/Worker镜像由NAS成功构建；DB重建后healthy，API/Worker均running。/healthz返回200/schema=v0.2；使用容器环境中的API Key直接调用/api/collection/health，两个来源计数均为0且online_enabled=false。Compose标签仍指向原登记路径，持久卷名保持不变。
- 近24小时脱敏日志扫描API 2,840行、Worker 1行，凭据字段/手机号/错误堆栈计数均为0；部署后10分钟API 6行、Worker 1行，错误计数0。已尝试通过Chrome视觉复核UGREEN UI，但Mac处于锁定状态且自动解锁失败；项目页运行计数仍未视觉确认。Compose CLI显示ningbo-re-ai running(3)，容器标签保持原登记路径。
- 本轮未运行本机pytest：系统Python无pytest，uv离线缓存访问受限；没有安装依赖或联网。NAS生产数据库目前仍为0条业务记录；没有外部网站访问。
- P0-08保持in_progress：新备份已校验、003/004已部署；仍需完成UGREEN项目页视觉核对、正式备份留存期限确认及更长业务负载验收。

## 2026-11-10 P0-08候选字段纠错触发器写入成本检查
- 使用nas-lan OpenSSH直连DXP4800（用户sheng，docker组可用），在独立PostgreSQL 17容器和临时数据库卷中加载001–004；生产数据库、容器和卷未参与。测试库有10,000条虚构候选（URL域名均为.invalid），其中5,000条pending、5,000条approved。
- 针对1,000条pending候选运行与人工字段纠错相同的字段更新SQL，对比关闭/开启健康汇总触发器。EXPLAIN ANALYZE总执行时间分别32.9ms/48.6ms；开启时触发器自身报告4.818ms/1,000次调用（约4.8μs/行）。单次批量计时存在环境噪声，不能外推生产延迟。
- 触发器开启时pending计数保持5,000，collection_health_metrics.updated_at未变化，确认字段纠错路径未写健康汇总行；现有集成用例也覆盖review_note纠错不改变汇总更新时间。
- 临时容器、合成数据库卷和internal网络已定向删除；NAS生产API、Worker运行，DB healthy。未修改生产数据库或项目容器。
- 本机pytest本轮未运行：系统Python没有pytest模块，uv离线执行因用户缓存目录权限不足未能启动；未安装依赖或访问网络。数据库断言由NAS隔离库内SQL执行。
- P0-08保持in_progress。下一步需完成NAS运行日志抽查/备份恢复留存验收，并在备份后评估生产004迁移时机；本轮不申请或执行生产迁移。

## 2026-11-10 P0-08迁移004并发写锁演练
- NAS `nas-lan` 隔离PostgreSQL 17复用001–003基线，载入250,000条run、250,000条candidate、10,000条listing；DB限1核/512MiB，仅internal网络，无端口/数据卷。
- 一个已有写事务插入合成run后持有事务3秒；迁移在其开始后约0.4秒启动。004的`LOCK TABLE`语句等待2.608秒后获得锁，回填0.597秒；按psql逐语句计时累加，`BEGIN`至`COMMIT`约3.239秒，其中取得锁后到提交约0.631秒。
- 迁移完成后run数为250,001（包含等待期间已提交的写入）；全部来源的汇总计数、时间戳、最新状态/原因与原表聚合逐字段对比0差异。该演练直接证明已有写事务可延迟迁移取得锁；没有单独启动“锁已取得后新到达的写事务”计时，因此不把0.631秒推为生产写请求延迟承诺。
- 临时数据库容器、internal网络和SQL均已清理；NAS生产API/Worker仍运行、DB healthy，`/healthz` 200/schema=v0.2，生产镜像未变；生产数据库未迁移。
- P0-08仍`in_progress`：本轮补充一个有界锁等待证据；生产写入模式、长事务分布、长期写入成本和正式升级仍待验证。

## 2026-11-10 P0-08挂牌观察时间触发器写放大优化
- 实际`upsert_listing_conn`在已有挂牌收到新观察时间时会更新`source_listings.last_observed_at`。在NAS隔离PostgreSQL 17、101,000条合成挂牌、1核/512MiB上，对1,000条同来源挂牌逐行推进观察时间：关闭触发器基线61.923毫秒，旧触发器13,035.919毫秒（约210倍）；`EXPLAIN ANALYZE`显示每次全表`max(last_observed_at)`扫描约16.273毫秒。
- 修改004挂牌触发器：同来源时间前进直接`GREATEST`维护汇总最大值，不再对挂牌数做减一/加一；只有当前最大时间回退或来源变化才重算。优化后同负载触发器开启146.421毫秒，对照基线80.371毫秒，约1.82倍；汇总最大观察时间与原表仍一致。
- NAS隔离PostgreSQL 17完整数据库集成文件**7 passed**，包含观察时间前进、回退、来源迁移及删除后重算。临时数据库、网络、运行器镜像和源码包已清理；生产API/Worker运行、DB healthy，健康接口200，生产镜像未变，生产库没有应用004。
- P0-08保持`in_progress`：本轮降低常见挂牌更新的同步汇总开销；回退/来源变化的重算成本、长时负载及生产部署仍需验收。

## 2026-11-10 P0-08迁移004已有数据回填演练
- NAS `nas-lan` 直连建立 PostgreSQL 17 临时 internal 网络/容器，限1核CPU/512MiB；按001–003初始化后写入250,000条`collection_runs`、250,000条`collection_candidates`及10,000条`source_listings`合成数据（URL均为`.invalid`），再执行正式`sql/004_collection_health_metrics.sql`。
- 首次迁移墙钟0.739秒，回填INSERT语句0.550秒，LOCK TABLE语句约1.036毫秒；再次执行墙钟0.737秒、回填0.589秒、LOCK TABLE约0.695毫秒。使用PostgreSQL `DO`断言将全部来源计数、时间戳、最新状态/原因与原表聚合逐项对比，0差异；二次执行无重复计数。
- 本测没有并发写事务，不能据此断言生产迁移的锁等待或实际停写时长；仍应备份并选低写入时段操作。临时容器/网络已定向清理，未创建数据卷或对外端口；生产API/Worker仍运行、DB healthy，`/healthz` 200/schema=v0.2，生产API镜像未变，未迁移生产数据库。
- P0-08仍`in_progress`：获得当前合成基数下的回填时间证据，但生产升级、并发写入锁等待、长期写入成本、获准真实样本及正式留存期限仍待验收。

## 2026-11-10 P0-08高基数健康汇总优化
- 250k run + 250k candidate基线下，逐请求扫描两张大表使隔离DB单核达110.54% CPU，60秒并发8仅149次、P95 5,303.34ms。新增`collection_health_metrics`小型汇总表，由同事务触发器增量维护运行状态、审核状态、挂牌数及最新时间；`GET /api/collection/health`改为读此表，响应字段保持不变。
- NAS PostgreSQL 17隔离集成测试**7 passed**：迁移重复执行与现存数据回填准确；重复候选写入、候选审核状态变化、运行记录状态更新/删除、挂牌插入/删除均验证汇总正确。
- 补强挂牌触发器集成断言：挂牌`last_observed_at`回退后汇总重算，来源从贝壳迁移至安居客再迁回时两来源计数/时间均正确，删除最后挂牌后观察时间清空；完整NAS数据库集成文件仍为7 passed。
- 相同250k/表数据、API/DB各限1核/512MiB、60秒并发8复测：**2,702次、0错误、计数全匹配**；平均177.80ms、P50 187.65ms、P95 264.76ms、最大501.49ms（约45次/秒），吞吐约18.1倍，P95下降约95%。DB CPU峰值96.36%/226.4MiB；API峰值104.96%/74.69MiB，瓶颈转至受限API容器。
- 隔离PostgreSQL批量写入/变更测试：插入10,000条run与10,000条candidate、将5,000条candidate改为approved，并分别删除1,000条run和candidate。每阶段汇总与原表聚合均无计数或时间戳差异；写入合计13.93秒，三轮核对合计0.22秒。分项耗时：run插入1.97秒、candidate插入3.07秒、状态转换4.76秒、删除run 2.37秒、删除candidate 1.76秒；测试库1核/512MiB，采样峰值约102.75% CPU/53.89MiB。
- 本机全量测试43 passed、6 skipped；`compileall`及占位环境变量下的Compose配置解析通过。隔离环境已清理，NAS生产API/Worker仍运行、DB healthy，健康接口200/schema=v0.2，生产API镜像未变。未在生产库执行004迁移。
- P0-08仍`in_progress`：隔离库已验证批量触发器正确性及本轮写入成本，但长期/真实业务写入成本、生产升级迁移尚未验收；真实授权数据与正式证据留存期限仍待验证/确定。
- 下一步验收：在隔离环境继续评估挂牌`last_observed_at`与来源变更触发器的更新时间/回填边界，并完善生产迁移前的隔离升级演练；生产数据库仍不执行004，真实页面解析仍等待获准样本。

## 2026-11-10 P0-08 25万行/表隔离容量验证
- 在NAS通过`nas-lan`部署当前工作区源码到独立Compose栈；PostgreSQL与API各限1核/512MiB，使用仅内部网络，在线采集关闭。数据库写入250,000条合成`collection_runs`和250,000条合成`collection_candidates`，URL均为`.invalid`。
- 真实`GET /api/collection/health`持续60秒、并发8：149次、0错误、所有来源的run/candidate计数每次匹配；平均3,309.82ms、P50 2,999.29ms、P95 5,303.34ms、最大6,789.72ms（约2.40次/秒）。
- 每2秒容器采样约22组：API峰值86.52% CPU/74.25MiB；DB峰值110.54% CPU/216.6MiB。DB接近/达到单核限额，延迟随数据规模增加；本结果限于合成健康聚合查询，不外推为生产容量，也不代表真实房源数据质量。
- 测试后移除隔离Compose容器、内部网络、数据库卷、构建镜像、测试目录和临时密钥；生产API/Worker仍运行、DB healthy，`/healthz`返回200/schema=v0.2，API镜像ID未变。未访问外站、未使用生产数据或生产卷。
- 本轮交付完成，P0-08保持`in_progress`。下一步可在隔离环境优化/验证高基数汇总查询，另需获准真实样本和运营者确定正式证据留存期限。

## 2026-11-10 P0-05 NAS隔离PostgreSQL集成验证
- 通过 `nas-lan` 直连，在独立 PostgreSQL 17 Compose 数据库运行 `tests/test_db_integration.py`：6 passed，覆盖连接错误脱敏、003索引/004汇总迁移幂等与回填、候选重复提交/审批幂等、审批异常回滚、汇总触发器插入/更新/删除、历史价格保护及通知去重。
- 测试用随机 schema，结束后清理临时 Compose 容器、数据库卷、测试运行器镜像、临时项目目录和本机临时凭据；SSH 转发端口15555/15556未监听。
- NAS生产API/Worker仍运行，生产PostgreSQL healthy；从API容器实际访问`127.0.0.1:8000/healthz`返回200、schema=v0.2，API镜像ID保持`sha256:165a79ee88fc2d590bbef7ae86f9612807865f10c56b9cbdbad4f2366e287d70`。没有迁移或写入生产数据库。P0-05现为`verified_on_NAS`，证据范围仅限隔离PostgreSQL 17测试库。
- 本机全量测试43 passed、5 skipped；跳过项需要额外测试数据库。`compileall`与用临时占位值执行的`docker compose config -q`通过；清单和新开发包内75项SHA-256均通过。
- 下一步：继续P0-08隔离环境递增规模/持续性验证并明确证据留存要求；P0-02/03待每站获准样本，P0-04待协议、robots及许可范围明确，P0-06待获准账号。

## 2026-11-10 P0-08空库Compose自动初始化验证
- 在NAS以独立PostgreSQL 17 Compose项目挂载当前 `sql/001_init.sql`、`002_collection_pipeline.sql`、`003_collection_health_indexes.sql`，用空的临时volume启动；未运行API/Worker、未使用生产库。
- DB健康检查通过；`source_registry`为2条且`online_enabled=false`，`collection_runs`与`collection_candidates`均为0；两项新索引均存在，证明新库初始化顺序生效。
- 测后删除临时容器、网络、卷和目录。NAS生产API/DB/Worker仍运行，生产API镜像ID不变。

## 2026-11-10 P0-08数据规模扩展与查询索引
- 在NAS隔离栈将 `collection_runs`、`collection_candidates` 各增至100,000行；API和PostgreSQL分别限制1核CPU/512MiB内存，回环端口8799，在线采集OFF。
- 未加索引时，30秒并发8访问 `GET /api/collection/health`：86次、0错误、2.77次/秒，平均2,851.40ms、P95 3,697.44ms、最大4,397.96ms；每来源计数一致，DB峰值106.51% CPU/141.4MiB。
- 在隔离库试验覆盖索引后，同样负载152次、0错误、4.88次/秒，平均1,619.82ms、P95 2,099.43ms、最大2,409.33ms；DB峰值106.68% CPU/141.5MiB。吞吐约提升76%，P95约下降43%；两索引共约9.1MiB。候选计数切换到index-only scan，最新运行状态使用索引，运行计数仍由顺序扫描计算。
- 根据实测新增幂等迁移 `sql/003_collection_health_indexes.sql`，将两个索引加入新库初始化Compose，并在NAS部署指南加入现有库升级步骤；集成测试夹具执行迁移两次并检查索引存在。
- 在仅含合成数据的隔离库对正式迁移文件执行两次：第一次建索引，第二次安全跳过；迁移后API计数仍正确。测试库、索引、数据卷、随机密钥、镜像及目录已清理，生产容器/数据库未改，生产API镜像ID未变。
- 本机全量套件43 passed、4 skipped；编译和Compose配置解析通过。P0-08仍`in_progress`：数据规模只测至每表10万行；更高规模、更长周期、真实授权样本和正式留存期限仍待验证。

## 2026-11-10 P0-08 60秒受限资源持续压测
- NAS `nas-lan` 直连，隔离API与PostgreSQL各设置1核CPU、512MiB内存上限，端口只绑定127.0.0.1:8799；合成库为50,000条`collection_runs`和50,000条`collection_candidates`。
- 对真实`GET /api/collection/health`执行60秒、并发8；357次请求、0错误、5.86次/秒，平均1,360.64ms、P50 1,304.37ms、P95 1,900.81ms、最大2,392.88ms；每个响应的两来源运行/候选计数均核对一致。
- 通过每2秒Docker stats采样30次：API峰值约17.46% CPU/71.37MiB；DB峰值约108.36% CPU/87.92MiB（各自限制512MiB）。负载结束后NAS可用内存约8.0GiB，PostgreSQL活动/总会话各1。DB CPU受1核限额约束时为主要瓶颈，响应比无额外CPU限额的20秒压测慢；这反映受限测试容器，不是生产容器的容量结论。
- 测后清除唯一测试栈、合成数据库卷、采样日志、随机凭据、容器、镜像和目录，8799关闭。生产API/DB/Worker仍运行，生产API镜像ID未变化。
- P0-08保持`in_progress`：有界持续测试已完成；更长时段、递增数据规模、实际数据质量和正式证据留存期限仍需验证，不把隔离1核测试结果外推为生产容量。

## 2026-11-10 P0-08人工样本写入闭环 NAS 验收
- 通过 `nas-lan` 在独立临时Compose项目和空PostgreSQL库运行当前应用代码；使用项目虚构 HTML 夹具内容和虚构来源ID，启用键为全新随机临时密钥，`ENABLE_ONLINE_COLLECTION=false`，没有向来源站点发请求。
- `POST /api/collection/pages` 首次及相同内容重提均返回200，得到同一候选ID；`GET /api/collection/candidates?status=pending`读回唯一待审核候选。API写出的gzip证据成功解压，内容与输入一致，SHA256与候选记录完全匹配。
- 隔离库内调用候选人工批准API：首轮和重复批准均返回200，重复操作标记`idempotent=true`；挂牌API可读回该条虚构挂牌，价格历史可读回365万快照。数据库核对为candidate=1/approved=1/listing=1/price_history=1，写入均在隔离库。导入阶段挂牌/历史价为0。
- 所有来源 `online_enabled=false`；测试后删除临时Compose容器、网络、数据库卷、随机凭据、证据文件、镜像和目录，8799端口关闭。生产API/DB/Worker仍运行，API生产镜像ID未变。
- 本次验证证明虚构样本下的API写证据、候选审核、批准、挂牌/价格快照读取链路；不代表实际房源数据质量、平台许可、写入压力或持续资源压力验收。

## 2026-11-10 P0-08业务聚合负载与查询优化
- 通过 `nas-lan` 直连，在 NAS 新建隔离 Compose 项目 `ningbo-re-ai-bench-20261110`，只启动临时 API 和 PostgreSQL；端口仅绑定 `127.0.0.1:8799`，未登记 UGREEN，不复用生产卷或凭据。
- 隔离数据库加载当前 SQL schema，并写入 50,000 条 `collection_runs` 与 50,000 条 `collection_candidates` 合成记录（URL 使用 `.invalid`）。访问真实 API `GET /api/collection/health`，20 秒、并发 8，输出计数逐请求核验。
- 初始实现 90 次、0错误，平均1,849.99ms、P95 2,460.60ms、最大2,774.18ms（4.50次/秒）。执行计划显示聚合成本触发 PostgreSQL JIT，重复编译占用明显；改为来源分组聚合并在当前事务局部 `SET LOCAL jit = off` 后，596次、0错误，平均270.41ms、P95 411.90ms、最大650.18ms（29.80次/秒），约6.6倍吞吐，输出计数一致。
- 最终采样容器内存：API 47.61MiB、DB 142.6MiB；NAS可用内存约7.8GiB。采样发生在负载结束后，不作为峰值或饱和度数据。
- 已通过 `docker compose down -v` 删除隔离容器、网络、合成数据卷、临时密钥和目录，并移除测试镜像；端口8799已关闭。复核生产 `ningbo-re-ai` API、DB、Worker仍运行，DB healthy，API镜像ID未变；未重启任何生产容器或Docker服务。
- 本机全量测试43 passed、3 skipped；`compileall -q app scripts tests`通过。P0-08仍为 `in_progress`：本项只覆盖合成数据下的健康聚合查询，实际房源写入路径、递增/持续/饱和压力与正式留存周期仍待验收。

## 2026-11-10 P0-08只读容量盘点工具
- 新增 `scripts/storage_report.py`：只读统计原始页面、备份的文件数/字节数/最早与最新修改时间，以及当前文件系统容量；不创建、修改或删除文件。
- 过渡留存规则明确为不自动删除原始证据和备份；原始证据在数据库记录保留期间必须可用。正式清理周期仍须结合实际数据量、恢复要求和运营者要求决定。
- 本轮全量测试 **43 passed, 3 skipped**；`compileall -q app scripts tests` 通过。3项跳过为需要独立PostgreSQL环境的集成用例。
- 使用 `nas-lan` SSH直连将脚本经标准输入只读运行于NAS：API容器内 `/data/raw-pages` 共2个文件、249字节（`.gitkeep` 0字节、`._.gitkeep` 249字节），没有HTML归档；NAS主机 `backups/` 共3个文件、50,301字节，`/volume3`剩余约437GB。因权限/挂载边界，原始页和备份需在容器、主机两个上下文分别盘点。
- 通过NAS API容器对数据库健康探针发出20次请求（并发4），全部返回200及schema=v0.2，平均34.77ms、最大67.35ms、总耗时0.193秒。容器采样前/后内存：API 47.57/48.36MiB、DB 38.22/38.47MiB、Worker 39.63/39.63MiB。该轻量探测不是资源压力测试。
- 追加有界只读检查：20秒、并发8访问`/healthz`，共2,801次，0错误；平均57.16ms、P95 79.39ms、最大113.89ms、约139.7请求/秒。容器采样前/后内存：API 47.80/48.35MiB、DB 38.72/38.77MiB、Worker 39.63/39.63MiB；NAS可用内存约8.2GiB，检查后PostgreSQL会话数6。仅覆盖健康探针，不代表真实业务链路或主机资源饱和测试。
- NAS API/Worker运行、DB healthy。未读取页面内容、未改动NAS项目文件或容器。
- P0-08仍为 `in_progress`：容量工具和有界健康探针负载检查已通过NAS实跑；真实业务读写链路、递增/持续资源压力测试、依据实际房源证据数据确定正式保留周期仍待完成。

## 2026-11-10 P0-04来源权限与 robots 复核
- 复核贝壳官网当前服务协议，页面标示2026-09-25生效；条文要求平台内容使用取得书面许可，并要求遵守平台Robots规则。
- 安居客官网登录页当前协议链接转到官方协议中心；其正文未能由浏览工具展示。另核对安居客官方域名托管的用户协议PDF，协议未标版本日期，包含明确书面许可、商业使用及Robots限制；无法确认该PDF是否为协议中心最新版本。
- 两站robots.txt正文仍无法读取，没有访问房源详情页或实际采集；两站均没有本项目书面许可，在线采集继续关闭。P0-04保持 `in_progress`。


## 2026-11-09 P0-08日志错误脱敏（进行中）
- `worker` 的账号同步、主循环和网页采集异常不再记录原始异常文本/堆栈；日志和 `last_error` 只保留异常类型、固定操作名和记录ID，避免上游回显的URL参数或令牌进入日志/数据库。
- 采集策略阻断仍使用已定义的 `blocked_policy`、`blocked_robots`、`blocked_upstream` 状态和固定原因，操作员仍可区分阻断原因。
- 新增敏感错误文本脱敏用例；一次性本机PostgreSQL 16隔离库运行完整测试 **43项通过**，临时集群已停止并清理；`compileall -q app scripts tests` 通过。
- 新增 `scripts/backup.sh`：导出PostgreSQL custom格式、归档原始HTML、校验恢复目录和SHA256；本机一次性PostgreSQL 16演练成功恢复合成记录并核对HTML归档，临时库/文件已清理。`backups/` 已加入 Git 和 Docker 构建排除项。
- P0-08保持 `in_progress`：NAS备份恢复、UGREEN项目页和容器运行态已核实；原始页面留存/容量策略及负载资源测试仍待完成。NAS源码同步归档SHA256匹配，清单71项中70项由SSH用户验证通过；`data/raw-pages/.gitkeep` 的空文件SHA256按本地清单保留，但该目录权限阻止SSH用户读取。2026-11-10只读资源基线：/volume3可用408G（55%使用），NAS内存可用8.3GiB，备份目录68K/1个备份；API、Worker、DB当前分别约47.39MiB、39.62MiB、38.07MiB。未重启容器。

## 2026-11-09 NAS备份验收续接
- 局域网 SSH 只读确认目标为 `DXP4800`、用户为 `sheng`（docker组可用），`/volume3` 可用空间为408 GB。
- Netcatty显示 `ningbo-re-ai` 项目3/3运行，详情页列出API、PostgreSQL和Worker；配置路径为 `共享文件夹/docker/ningbo-re-ai/docker-compose.yml`。
- 首次执行备份脚本时因SSH用户无法遍历属主为UID 10001、权限700的主机 `data` 目录，原先的主机侧目录预检查误报缺失。容器内 `/data/raw-pages` 可读且当前只含 `.gitkeep`；三个Compose服务仍运行。
- 已从脚本移除不适用的主机侧目录预检查，保留容器内归档和tar结构校验；Netcatty同步后远端脚本SHA256与本机一致。
- 备份位于 `backups/ningbo-re-ai-20261109T133821Z-273669`；数据库dump及raw-pages归档的SHA256校验均通过，`pg_restore --list`通过。备份目录权限700，dump、归档及清单权限600。
- 将dump恢复到临时隔离数据库；`source_registry`恢复出贝壳和安居客两条默认策略且在线开关均为false，`source_listings`、`collection_candidates`、`collection_runs`计数均为0。原始页面归档可列出，仅有占位文件。临时隔离数据库已删除。
- UGREEN Docker项目页显示 `ningbo-re-ai` 3/3运行，详情列出API、PostgreSQL 17和Worker，路径为 `共享文件夹/docker/ningbo-re-ai/docker-compose.yml`。本轮未重启容器或Docker服务，未改动数据卷。
- P0-08仍为 `in_progress`：NAS备份恢复及项目页核验已完成；本轮状态文档和备份脚本已同步，归档SHA256匹配，清单中70个可读文件校验通过，受保护的raw-pages占位文件哈希沿用本地清单。2026-11-10只读资源基线记录：/volume3可用408G、NAS内存可用8.3GiB、备份68K/1份，API/Worker/DB用量约47.39/39.62/38.07MiB；未做负载测试。原始页面留存/容量策略和资源压力验收仍待完成。没有重启容器或Docker服务。

## 2026-11-09 P0-05数据库API集成用例
- 新增 `tests/test_db_integration.py`，仅允许连接数据库名严格为 `rehouse_test` 的隔离库；每条用例在随机 schema 内运行 V0.1/V0.2 SQL 并在结束时删除该 schema。
- 覆盖未审批候选不可见、重复导入/审批幂等、审批中途数据库异常的事务回滚、历史价格回填不覆盖最新挂牌价，以及降价提醒事件去重。
- 在一次性本机 PostgreSQL 16 集群和专用 `rehouse_test` 数据库中运行完整测试：**42项通过**；集群仅用Unix socket，无TCP监听，结束后已停止并删除。
- P0-05验收条件全部通过，状态更新为 `verified_local_postgres`。先前NAS专用库连接曾在schema创建前报角色不存在，临时库已清理；它不代表已完成NAS端数据库API复测。
- 增加测试保护，数据库连接异常不会回显连接串或密码。
- 安全处置：详细错误输出包含数据库密码，视为凭据暴露；本轮停止使用该凭据。轮换须同步NAS `.env` 与本项目API/Worker连接配置，并重新验证服务。

## 2026-11-09 NAS登记目录源码同步复核
- 用已部署镜像内的 `sha256sum` 对 `/volume3/docker/ningbo-re-ai/MANIFEST.sha256` 全量复核，通过；此前5份状态/目标/路线/测试/部署文档的哈希不匹配已用工作区文件纠正。
- UGREEN项目登记数据库记录已在前序工作中完成；Docker项目页视觉3/3复核仍因Mac锁屏未完成。没有重启 `docker_serv` 或Docker引擎。

## 2026-11-09 本轮迭代
- 目标：在无法进行NAS迁移的环境下，推进可本地交付的P0来源健康指标。
- 完成：新增受API Key保护的 `GET /api/collection/health`，按来源汇总成功/失败/阻断次数、候选审核计数、挂牌数、最近尝试/成功/挂牌观察时间、最近运行状态和原因，以及来源/全局在线开关；新增接口文档与单元测试。
- 状态：新增健康接口及单测；P0-07继续标记`in_progress`，因为SQL聚合尚未在PostgreSQL执行。
- 环境验证：临时Python 3.12虚拟环境执行 `python -m pytest -q`：38项通过；`python -m compileall -q app scripts`通过；`POSTGRES_PASSWORD=local-check-only APP_API_KEY=local-check-only docker compose config -q`通过（仅配置解析，未启动容器）；`sha256sum -c MANIFEST.sha256`通过。宿主Docker CLI可用但守护进程不可连接。
- 未做：未连接或修改NAS；未迁移/改动数据库；未访问贝壳、安居客或其他真实网站。
- 下一步：①启动Docker并配置本地测试密钥，执行Compose新库启动和该接口DB验证；②在NAS先备份V0.1数据库，再按部署指南做V0.2迁移；③在获准使用的真实HTML样本到位后推进P0-02/P0-03。

## 2026-11-09 持续目标续接
- 目标：复查P0-01的真实NAS前提，并推进P0-04来源规则核验。
- NAS只读事实：SSH确认目标为DXP4800；Compose列表、容器及卷未发现 `ningbo-re-ai` 现有部署/同名卷；UGREEN登记表中未发现同名项目；NAS端口8787由 `nas-image-manager` 占用。因此当前不能执行V0.1→V0.2升级验收，P0-01改为`blocked`；任何新装应另用端口并先完成UGREEN项目登记。
- 来源核查：已阅读贝壳当前服务协议与安居客官方协议PDF，证据和条款范围记录在 `docs/SOURCE_POLICY_REVIEW_2026-11-09.md`。两者均未提供本项目的书面许可；robots文本无法读取，未访问房源详情页；在线采集继续双重关闭，P0-04保持`in_progress`。
- 本轮未改变NAS运行状态、未执行SQL写入/备份、未启动或创建容器，也未访问真实房源页。
- 下一步：①取得可用的NAS项目登记权限/登录后，在隔离空库上完成Compose新装API+Worker及 `/api/collection/health` 集成验收；②若找到V0.1项目和数据库备份，再做升级测试；③取得正式数据使用许可并能读取robots后，补齐P0-04；否则继续离线样本和替代来源工作。
- 单测环境位于 `/private/tmp/ningbo-re-ai-venv312`，没有把依赖或环境文件写入项目目录。

## 2026-11-09 NAS 空库新装与指标验收
- 部署：源码位于 `/volume3/docker/ningbo-re-ai`，UGREEN Compose 登记 `ningbo-re-ai`（记录ID 53，状态运行，3个容器）；UGREEN登记库修改前备份为 `ugreen-docker-info-log-pre-change.db`，`PRAGMA integrity_check=ok`，仅新增一条精确路径记录。容器标签指向该目录和 `docker-compose.yml`。
- 运行态：`db` healthy，`api`、`worker`运行；`/healthz`返回V0.2；PostgreSQL新卷为 `ningbo-re-ai_pgdata`。只重启项目自己的`db`容器后，schema及`anjuke:not_reviewed:false,beike:not_authorized:false`仍在，证明本次新库初始化数据随卷保留。
- 网络/密钥：API仅绑定NAS本机 `127.0.0.1:8788`（8787由 `nas-image-manager` 占用）；`.env`在NAS且权限600，随机密钥未写入仓库或日志；在线采集总开关及两个来源开关均为false。证据目录由UID 10001拥有，权限700。
- P0-07：`GET /api/collection/health`通过NAS实际PostgreSQL验收；初始空状态返回两个来源且在线OFF。另临时插入3条采集运行及3条审核候选，接口正确返回成功/失败/阻断、pending/approved/rejected计数及最新状态；临时记录已删除，之后确认`collection_runs`、`collection_candidates`、`source_listings`均为0。P0-07更新为`verified_on_NAS`。
- P0-01仍`blocked`：当前NAS上没有旧V0.1项目或数据库卷，故无法进行V0.1备份升级；空库新装成功不替代迁移验收。**没有重启Docker引擎或其他项目，也没有导入真实房源。**
- 登记界面：数据库记录已准确登记，但Mac在操作期间锁定，UGREEN Docker项目页的3/3视觉状态尚未复核；不声称管理页验收完成。
- 测试：本机Python 3.12全量38项通过；远端Compose配置、构建、初始化SQL、API、指标SQL及项目DB重启验证通过。真实房源网站、robots正文、DTK及视频号仍未联调。
- 下一步：①解锁Mac后刷新UGREEN Docker项目页，核实 `ningbo-re-ai` 显示3/3；②若用户提供真实旧V0.1项目/数据库备份，再完成迁移验收；③继续等待获准使用的真实HTML样本与robots/权限结论，推进P0-02/P0-04。

## 已确认的用户目标与资源
- 宁波二手房为第一市场；房源、短视频、官方公开数据融合；日后做客户条件单、智能识别洼地、主动推送和中介撮合。
- 绿联DXP4800（Intel N100）、16GB RAM、已部署Docker；希望尽量自采和积累新数据，外部授权数据接口仅是后期选项。
- 指定抖音号/视频号监控；新品优先，历史补采可按需开启。
- **贝壳/安居客目前是采集技术路线，当前没有授权API；线上采集的合规性需要逐站审核。**

## V0.2本轮真正完成的代码/文档
- 在V0.1基础上新增 `sql/002_collection_pipeline.sql`：来源状态、采集目标、原始证据候选、采集执行日志、挂牌来源追溯字段。
- 新增 `app/collectors/parser.py`、`http_client.py`：离线HTML保守解析、URL白名单、robots/403/429阻断。
- 新增 `app/collection_service.py`、`collection_models.py` 和 `/api/collection/*`：样本导入、候选查询/纠错/审批、来源审查、目标调度与状态。
- 修改 `app/services.py`，让人工审批与来源挂牌和价格历史写入同一事务。
- Compose增加原始HTML证据目录挂载、来源采集总开关（默认关闭）、SQL迁移初始化挂载。
- 添加两份**完全虚构的HTML测试样本**与离线提交脚本。
- 添加项目长期开发提示词 `AGENTS.md`、主提示词、短续接提示词、PRD、架构、数据源矩阵、测试/迁移文件。

## 已验证
- Python应用代码静态编译（`python -m compileall -q app`）通过。
- 初始V0.2本地无数据库测试：37项通过；本轮增加1个健康接口用例后共38项通过。

## 未验证 / 禁止当作完成
- 当前执行环境无Docker服务及PostgreSQL数据库服务；**没有V0.2容器端到端验证或数据库实际迁移测试**。
- `app/collectors/parser.py`只是通用规则解析器，**没有通过贝壳和安居客真实页面样本集的字段准确率验收**。
- 线上抓取默认不运行；两个网站并未确认具有商业自动抓取许可，未验证实际稳定抓取。
- 抖音DTK作者作品接口与实际NAS环境未完成联调；视频号没有无人值守监控。
- 未实现ASR/OCR自动视频处理、正式通知发送、用户登录、多租户、手机端界面、可靠成交价和完整估值模型。

## 当前最高优先级任务
1. P0-01旧V0.1数据库升级（当前NAS无旧项目/卷，等待旧实例或备份证据）。
2. P0-02/P0-04：经允许使用的真实HTML样本、当前robots与使用范围核验；在许可未明确前在线采集保持关闭。
3. P0-06：DTK v5指定作者小规模联调，先确认获准账号及接口权限。

## 本轮交付边界
V0.2是**可部署源码原型+完整研发协作文档**，不是已上线网站爬虫、不是已拥有贝壳/安居客授权API，也不是已具备商业化SaaS能力。

## 2026-11-10 P0-08 NAS隔离业务负载30分钟
- 本轮推进目标：在不能访问真实房源站点的前提下补齐更长时段业务写入/读取验收。新增 `scripts/collection_load.py`，API目标只允许`api`/loopback，错误即停；完成导入→候选待审查询→审批→挂牌→价格历史→健康指标闭环。
- NAS `DXP4800` 经`nas-lan`运行独立PostgreSQL 17/API Compose栈，当前工作区`app/`只读挂载；internal网络、无宿主端口、独立数据库/证据卷，API/DB各限1 CPU/512MiB。所有HTML和房源编号为虚构；链接仅写入测试数据，不发外站请求；线上开关均OFF。
- 正式负载1,800.61秒、4并发：10,199完整工作流/61,194请求/0错误。候选10,199（approved 10,199、pending 0）、挂牌10,199、价格历史10,199；健康API汇总与源表一致、两来源和全局开关OFF。各端点P95：导入186.54ms、待审列表165.52ms、审批272.59ms、挂牌222.71ms、价格历史165.83ms、健康指标123.76ms。
- 每容器284组资源采样：API/DB峰值CPU 106.37%/108.60%，峰值内存65.69/65.15MiB；DB受单核限额约束，结果不外推生产容量。10,199个合成gzip证据占3,262,751字节。
- 报告及原始采样见`docs/LOAD_TEST_2026-11-10.md`和`docs/reports/`。NAS传输SHA-256一致。测试容器、卷、网络、临时源码和随机密钥已定向清理；生产API/Worker运行、DB healthy，生产数据库/镜像/数据卷未变。
- 本机全量pytest **51 passed, 7 skipped**（跳过项需`TEST_DATABASE_URL`）；compileall、Compose配置解析通过。Starlette/httpx弃用警告仍存在。
- P0-08已按NAS验收证据标记`verified_on_NAS`：备份90天、原始页面证据随关联数据库记录保留；UGREEN Docker项目页视觉核对已完成。下一步继续最高优先级未完成目标；在线采集继续关闭。


## 2026-11-10 UGREEN Docker 项目页复核
- 用户解锁Mac后，在UGREEN Docker原生应用打开`ningbo-re-ai`项目详情页；页面显示运行中，登记路径为`共享文件夹/docker/ningbo-re-ai/docker-compose.yml`，API、PostgreSQL 17、Worker均显示运行。
- 经`nas-lan`直连确认目标为`DXP4800/sheng`；Compose状态复核API、Worker运行，PostgreSQL healthy，API端口仍绑定`127.0.0.1:8788`。
- UGREEN项目页待核验项已关闭。P0-01仍blocked，仅因NAS没有旧V0.1项目/数据库备份，无法完成旧库升级；P0-08留存策略现已确认：备份90天，原始页面证据随关联记录保留。未改NAS配置、数据卷或容器。


## 2026-11-10 P0-08留存策略与NAS只读盘点
- 用户确认：数据库/raw-pages备份保留90天；原始页面证据在关联数据库记录保留期间持续保留。
- `scripts/storage_report.py`新增`--backup-retention-days`（默认90）和过期候选统计；只读列出超期文件数量/字节数，绝不删除。新增测试覆盖90天边界、递归目录与无效期限。
- 本机pytest：56 passed、8 skipped（PostgreSQL集成需`TEST_DATABASE_URL`）；`compileall`通过。Starlette/httpx弃用警告仍存在。
- 本轮通过`nas-lan`执行只读核验时SSH连接超时，未读取NAS当前90天超期候选数，也未同步新脚本。此前NAS库存为532KiB/15文件（2026-11-10既有只读证据）；待LAN连接恢复后再运行报告。未执行清理。正式清理前须逐个确认备份集完整性、可恢复性及无回滚引用；raw-pages文件不按备份周期删除。
- P0-08其余验收（备份恢复、有限日志扫描、内网边界、隔离负载及资源边界）已有NAS证据。综合既有NAS验收及本次留存策略，P0-08为`verified_on_NAS`；新报告脚本尚未同步到NAS，且本轮未取得当前超期候选数。合成压测不代表生产容量SLO。


## 2026-11-10 P2-01 价格机会报价类型与时间窗
- `/api/opportunities` 的 `days` 限定为7/30/90，与F6产品定义一致；窗口右边界固定在请求时间，未来快照不参与。降幅使用同一挂牌窗口内首末 `platform_listed` 快照，`agent_claim`不混入；`source=agent`挂牌不进入平台挂牌机会及可比中位数。
- 新增`tests/test_opportunities.py`覆盖时间窗口、agent_claim隔离、上涨不报降幅、至少两条有效快照及7/30/90参数。单测以假连接检查SQL过滤；未连接NAS生产库，也没有生产房源数据。
- 本机完整pytest 61 passed、8 skipped（均为未设置`TEST_DATABASE_URL`的PostgreSQL集成用例）；compileall、`docker compose config -q`和OpenAPI窗口枚举检查通过。NAS `nas-lan`连接再次超时，本次代码尚未同步/部署。
- 剩余：异常检测、可比池更细分层和NAS部署。返回的金额、价格、时间与末次证据链接均限于同挂牌平台快照；此改动不代表成交价或估值。


## 2026-11-10 P2-01 价格降幅解释字段
- 机会接口在存在同挂牌降幅信号时新增降价金额、窗口首末价格、观察时间和末次证据链接；原有降幅比例字段保留。无有效下降时这些字段为`null`，不制造降价信号。
- `tests/test_opportunities.py`覆盖金额/比例、快照时间、证据链接、经纪人报价隔离、未来与窗口外记录、价格回升及API周期约束。NAS直连已连续超时，本项未同步或部署。


## 2026-11-10 P0-02/P0-03获准样本清单与校验
- 新增`docs/SAMPLE_MANIFEST_TEMPLATE.csv`、`docs/SAMPLE_DATASET.md`及`scripts/validate_sample_set.py`。默认清单位置`data/sample-manifest.csv`已加入`.gitignore`，避免提交真实来源元数据。
- 校验器不访问网络；检查HTML文件位于`data/raw-pages/`且SHA-256匹配、HTTPS来源域名及无query/fragment、URL可识别ID与人工ID一致、权限引用/范围与带时区时间、字段标签和在售/下架/多价/缺字段/未知ID覆盖，以及每站最低样本数。它不判断许可是否合法或充分。
- 两项新测试只使用临时虚构HTML验证校验逻辑，不能计入P0-02样本集。当前工作区仍无真实获准页面，P0-02保持`todo`，P0-03继续依赖真实人工标注集。
- 本机完整pytest **63 passed, 8 skipped**（需`TEST_DATABASE_URL`）；`compileall`和`docker compose config -q`通过。NAS `nas-lan`直连超时，脚本/文档未同步或部署；本轮没有外站请求或生产数据操作。

## 2026-11-10 P0-02样本清单工具收尾
- 成功标准：校验器及文档/模板纳入当前交付包；全量测试、编译、Compose静态配置检查通过；保留真实样本验收为未完成。
- 校验器已覆盖本地页面哈希/路径、来源主机与URL房源ID一致性、权限依据字段、带时区时间、人工标签、每来源最低样本数，以及与项目数据模型一致的面积/户型/报价范围。多报价至少包含两个不同数值。3项逻辑测试只用临时虚构文件，不计入真实页面样本；另有CLI启动测试。
- 本机全量pytest **65 passed、8 skipped**；8项因未设置`TEST_DATABASE_URL`跳过。`compileall`、`docker compose config -q`及目标状态JSON解析通过；有1条Starlette/httpx弃用警告。
- 更新`MANIFEST.sha256`，当前88个项目文件校验通过；交付包`ningbo-re-ai-v0.2-dev-2026-11-10-sample-intake-v2.zip`含89项（含清单），ZIP完整性及包内清单哈希全部通过。
- NAS `nas-lan`连接超时；Tailscale CLI未能读取本机偏好，故未切换连接路径。本轮未同步NAS、未访问网站、未改生产数据或容器。
- P0-02保持`todo`、P0-03继续依赖真实标注样本；P0-08留存策略按用户决定为备份90天、原始证据随关联记录保留。下一步：取得获准真实页面并人工标注；NAS连接恢复后只读核验过期备份候选并同步报告脚本，清理仍须逐个核实完整性、可恢复性及回滚引用。

## 2026-11-10 P0-01 V0.1 schema迁移回归补强
- 成功标准：在真实PostgreSQL中构造已存在V0.1 schema和合成旧数据，单独执行V0.2 002迁移并重复执行；确认旧数据保留、默认回填与来源安全策略正确。
- 新增`test_v01_schema_migration_preserves_existing_data`：V0.1初始化后在11张业务表写入合成账号同步/作品、视频、社区别名、房源挂牌/历史价、同套候选、条件单及提醒记录，再运行002两次；验证各表原行及价格不变、旧挂牌`acquisition_method=manual_import`、新来源`online_enabled=false`。
- PostgreSQL 16隔离集群（仅Unix socket、`/private/tmp`）数据库集成 **10 passed**；以该库运行完整pytest **74 passed、0 skipped**，有1条Starlette/httpx弃用警告。临时数据库服务已停止，数据目录与日志已删除。
- V0.1 schema来自项目内`sql/001_init.sql`，旧数据均为合成数据；这证明代码迁移路径可在PostgreSQL执行，不证明真实NAS旧库兼容性或其备份可恢复。
- NAS `nas-lan`仍连接超时，Tailscale CLI/桌面状态读取失败；本轮未连接、同步或修改NAS。P0-01继续blocked，直到找到旧项目/数据库备份并完成NAS恢复/升级验收。

## 2026-11-10 P0-08 90天留存边界核验
- 成功标准：确认过期候选严格按“早于90天”计算；恰好90天文件不得报为超期，且不删除任何文件。
- 扩展`tests/test_storage_report.py`，同一测试数据包含91天、恰好90天和89天文件；只有91天文件计入人工复核候选。业务函数原有只读/不删除行为保持不变。
- 专项测试：5 passed；本轮默认全量pytest **65 passed、9 skipped**（PostgreSQL集成用例需`TEST_DATABASE_URL`），1条Starlette/httpx弃用警告。此前完整PG16运行74 passed；本轮仅增加一个纯单元边界样本。
- `nas-lan`连接仍超时，无法读取NAS的真实超期候选数或同步报告脚本；未删除/修改NAS备份、raw-pages、容器或配置。
- 路线图历史记录已标注留存期限在当时待定、后续用户确认90天；当前策略仍是备份90天、页面证据随关联记录保留。

## 2026-11-10 P1-08条件单命中理由
- 成功标准：只为SQL硬条件实际筛出的挂牌返回可核对理由；准确区分硬筛选和偏好标记，不根据未存储的购房动机生成解释。
- `GET /api/saved-searches/{id}/matches`新增`match_reasons`：列出匹配区域/指定小区、总价上限、面积下限、户型下限、挂牌最近更新时间及命中的偏好小区；无条件时返回“符合当前条件单筛选项”。金额/面积文本去除数据库NUMERIC尾随零，理由字段只描述服务端实际应用的条件。
- 更新`docs/API.md`及测试。PostgreSQL 16隔离数据库完整pytest **76 passed、0 skipped**，有1条Starlette/httpx弃用警告；`compileall`、Compose配置解析通过。临时数据库仅Unix socket运行，测试后已停止清理。
- NAS `nas-lan`超时，Tailscale CLI无法读取本机偏好；新增字段尚未同步NAS。P1-08既有NAS验收仅覆盖原匹配API，本次增量只完成本机验证，不声称已部署。
- 更新`MANIFEST.sha256`并生成独立开发包；当前88个项目文件及包内清单哈希通过。下一步：NAS直连恢复后备份并API-only同步/验收此增量；P0-02仍待每站获准真实样本，P0-01仍待V0.1旧库/备份。

## 2026-11-10 P2-01 可比样本按房屋去重
- 成功标准：多渠道挂牌归属于同一`property_id`时只计一套；可比样本不足5套时不产生挂牌中位数折价信号。
- 机会池现在按不同`property_id`聚合；同一房屋多条符合条件的挂牌先取套内单价中位数，再计算不同房屋的可比中位数。样本数也按独立房屋计数。
- 新增两个回归用例：5条相似挂牌实际只有3套房屋时不产出折价信号；14条可比挂牌中同一房屋有10条记录时只计一套，并验证单套价格先取中位数。
- `/private/tmp/ningbo-re-ai-venv312/bin/python -m pytest -q tests/test_opportunities.py`：7 passed。全量`pytest -q -rs`：69 passed、9 skipped（均需`TEST_DATABASE_URL`），1条Starlette/httpx弃用警告。新增逻辑运行于假连接，不是PostgreSQL集成验证。曾尝试在`/private/tmp`启动PostgreSQL 16 Unix-socket临时集群，系统两次拒绝`shmget`（Operation not permitted），实例未启动且临时目录已清理。
- `compileall`、占位变量`docker compose config -q`及目标状态JSON解析通过。NAS `nas-lan`连接超时、Tailscale CLI无法读取偏好；本轮未同步/部署，未访问外站及生产数据库。
- 已生成89文件开发包，包内88项源文件SHA-256、ZIP完整性及工作区清单核对通过。下一步：恢复NAS通道后备份并同步API源码、使用隔离库验收；楼层/装修/楼龄分层仍未完成，接口仍是挂牌线索而非估值。


## 2026-11-10 P0-04安居客官方协议PDF核读
- 官方帮助中心`https://www.anjuke.com/helpcenter/policy?id=44`显示消费者与经营者的协议规则及历史版本目录；本次网页提取只返回导航，未显示协议正文。
- 通过网页搜索索引打开安居客官方静态域名托管的《安居客用户服务协议》PDF。条款称数据商业性利用需事先书面同意、搜索引擎应遵循Robots，并规定抓取/其他使用需明确特别书面许可；文件无发布日期/生效日，不能确认是否为协议中心当前版本。
- 本项目没有安居客书面许可；此前NAS只读核验的宁波origin robots允许项目UA，也不替代授权。来源继续OFF。P0-04保持`in_progress`，直到确认适用协议版本及用途范围；没有访问房源详情页或启动采集。


## 2026-11-10 P0-01用户附件旧库线索复核
- 只读检查用户提供的`ningbo-re-ai-v0.2.zip`与`ningbo-re-ai-goal-mode-dev-kit-v0.2.zip`目录：项目ZIP包含`sql/001_init.sql`与`sql/002_collection_pipeline.sql`，未包含`.dump`、`.backup`或SQL数据备份；dev-kit ZIP也未包含数据库备份文件。
- 因附件没有V0.1实际库或备份，P0-01仍`blocked`；本机合成V0.1数据迁移测试不能代替真实NAS旧库升级验收。没有读取/修改NAS或生产数据库。


## 2026-11-10 P0-04平台书面许可申请模板
- 新增`docs/SOURCE_PERMISSION_REQUEST_TEMPLATE.md`，依据PRD准确区分当前局域网单操作者原型、未来免费消费者功能与经用户授权的中介撮合；分别询问平台官方接口/导出或明确授权网页方式、字段、域名/路径/频率、robots、留存/删除、展示/提醒、商业用途、撮合和个人信息范围。
- 模板明确项目的数据库记录/原始证据留存政策及90天备份策略，并允许平台给出更严格期限或替代证据方式；没有把Robots允许当作使用授权，也明确403/429/验证码等阻断不绕过。
- 模板只作待审草稿，未填入主体信息、未发送；没有平台回复或项目许可，P0-04保持`in_progress`，在线来源继续OFF。模板更新后的全量pytest **69 passed、9 skipped**（数据库集成需`TEST_DATABASE_URL`），`compileall`、Compose配置与GOAL_STATE JSON解析通过；仅1条Starlette/httpx弃用警告。本轮复核`nas-lan` SSH仍超时、Tailscale CLI仍无法读取偏好，未同步或部署。

## 2026-11-10 P2-01 机会折价解释字段
- 成功标准：可比折价机会能解释目标挂牌单价、独立房屋可比中位数/数量、目标挂牌最近观察时间和触发理由；不足5套仍不显示可比中位数折价。
- 回归测试先因响应缺少`unit_price_wan_per_sqm`失败，再在`app/services.py`补上`unit_price_wan_per_sqm`、`comparable_median_wan_per_sqm`、`comparable_sample_count`、`last_observed_at`及`signal_reasons`。可比池仍按不同`property_id`计数；理由只解释当前触发的同挂牌降价或挂牌折价信号。
- 更新`docs/API.md`、`docs/ROADMAP.md`、`docs/GOAL_STATE.json`及`CHANGELOG.md`。机会模块测试8 passed；全量pytest **70 passed、9 skipped**（需`TEST_DATABASE_URL`），compileall、`docker compose config -q`和目标状态JSON解析通过；1条Starlette/httpx弃用警告。
- NAS `nas-lan`近期SSH直连超时，Tailscale状态不可读取；本次未经Netcatty兜底，未同步或部署，也未访问房源页面/生产库。目标阈值未改变，NAS部署仍待连接恢复与隔离集成验收。
- 下一步：NAS通道恢复后先备份，再在隔离PostgreSQL上验收机会API增量并仅更新API；若暂不可连接，继续处理不依赖真实平台样本/生产库的离线任务。P0-02仍需每站获准真实样本，P0-01仍需V0.1旧库或备份。
- 已刷新`MANIFEST.sha256`并生成工作区同级开发包；包完整性与包内清单哈希均通过，交付包不含环境密钥、备份、缓存或运行数据。

## 2026-11-10 P0-03 页面挂牌 ID 错配保护
- 成功标准：保存页面明确声明的canonical URL或`og:url`与提交URL包含不同可识别挂牌ID时，不将提交URL的ID送入候选；记录告警并使候选保持待核实。
- 新增canonical link与`og:url`冲突回归用例，含相对canonical路径和多个互相冲突声明；均验证来源ID为空、告警`canonical_source_id_mismatch`且`ready_for_review=false`。测试先复现首个canonical匹配但后续声明冲突时漏报，再补解析器防护；解析器版本升级为`generic-labelled-v0.2.2`以便追溯。
- 更新`docs/COLLECTION_SPEC.md`、`docs/API.md`、`docs/ROADMAP.md`、`docs/GOAL_STATE.json`、`CHANGELOG.md`及下一轮目标。P0-03改为`in_progress`，只代表离线安全逻辑已有进展；贝壳/安居客20+20真实获准样本及准确率仍未验证。
- 本机`tests/test_collection_parser.py`：14 passed；全量pytest **73 passed、9 skipped**（均需`TEST_DATABASE_URL`），1条Starlette/httpx弃用警告；`compileall`、占位变量`docker compose config -q`、GOAL_STATE JSON解析均通过。NAS直连再次超时；Tailscale CLI无法加载偏好，且本机未找到Tailscale App，故不切换到交互通道，也未同步/部署。
- 下一步：在隔离环境继续覆盖页面ID/字段矛盾，不对虚构fixture报告真实准确率；NAS LAN/Tailscale路径恢复后先备份，再验证部署增量。P0-02仍需平台允许的样本，P0-01仍需实际V0.1库或备份。
- 已刷新`MANIFEST.sha256`并打包`ningbo-re-ai-v0.2-dev-2026-11-10-p0-03-canonical-id-guard.zip`；89项源文件加清单的哈希、ZIP完整性均通过，未包含密钥、备份、缓存或运行数据。

## 2026-11-10 P0-03 离线解析准确率与覆盖率评估器
- 成功标准：对通过来源/标签/哈希校验的本地样本，分别报告贝壳和安居客各字段准确率、覆盖率、非空输出精确率，以及缺字段、多价、未知ID场景通过率；全程不访问平台。
- 新增`scripts/evaluate_parser.py`和`tests/test_parser_evaluation.py`。评估器支持`.html`与`.html.gz`，要求默认每站至少20份并覆盖活跃/下架及异常场景；字段指标以人工非空标注和有明确缺失含义的场景作为分母，冲突多价用独立安全场景计分。输出不包含房源URL或页面正文，也不代表许可审查。
- 单测以临时虚构数据检查数值指标、异常场景、gzip解析、无效哈希拒绝和CLI启动；这不是实际页面准确率数据。工作区没有真实授权样本清单，因此未生成或报告实际站点指标，P0-03保持`in_progress`。
- 本机全量pytest **77 passed、9 skipped**（数据库集成需`TEST_DATABASE_URL`），1条Starlette/httpx弃用警告；`compileall`、占位变量`docker compose config -q`、GOAL_STATE JSON解析和评估器`--help`通过。评估器测试覆盖正确率/覆盖率、gzip、坏压缩、无效哈希及CLI；NAS SSH仍不可达，本轮不涉及NAS部署。
- 实际执行默认评估命令时，`data/raw-pages/`只有`.gitkeep`且无`data/sample-manifest.csv`；评估器按设计拒绝产出任何准确率数字。没有联网或使用虚构fixture代替。
- 下一步：用户取得每站20份获准、人工标注页面后运行`python scripts/evaluate_parser.py`；在此之前继续改进离线解析失败检测。NAS通道恢复后先备份，再做隔离集成和API-only同步。
- 已更新`MANIFEST.sha256`并生成`ningbo-re-ai-v0.2-dev-2026-11-10-p0-03-parser-evaluator.zip`；91项源文件加清单的工作区/包内SHA-256与ZIP完整性校验通过，包内不含环境密钥、备份、缓存或原始运行数据。

## 2026-11-10 P0-02 gzip页面去重与完整性
- 成功标准：同一HTML无论普通文件还是使用不同gzip头压缩，都只计作一个来源样本；损坏gzip不得进入解析器评估；清单SHA仍校验原始落盘字节。
- 复现并修复`validate_sample_set.py`只按原始文件SHA去重的问题。现在另对解压后的HTML内容做来源内去重，保留原始字节SHA完整性检查；坏gzip产生明确清单错误。评估器复用此校验，因此不再解析损坏压缩样本。
- `tests/test_sample_set.py`新增两项回归：相同HTML以不同gzip头重复提交、损坏gzip被拒绝；`tests/test_parser_evaluation.py`验证坏压缩清单不能生成评估结果。专项校验器6 passed、评估器4 passed；本机全量pytest **79 passed、9 skipped**（需`TEST_DATABASE_URL`），1条Starlette/httpx弃用警告；`compileall`、Compose配置、目标JSON和评估器CLI帮助通过。
- 当前工作区仍无`data/sample-manifest.csv`，`data/raw-pages/`只有`.gitkeep`；没有真实样本或准确率结果。NAS `nas-lan`本轮SSH至`10.10.10.7:22222`超时，未部署或改动NAS。
- 已生成`ningbo-re-ai-v0.2-dev-2026-11-10-p0-02-gzip-dedupe.zip`；91项源文件及清单SHA、ZIP完整性与包内哈希校验通过，不含密钥、备份、缓存或真实原始数据。
- 下一步：收到许可范围明确的每站20份样本后先跑清单校验，再生成准确率报告；NAS通道恢复后备份，再进行隔离集成/API-only同步。
# 2026-11-10 跨平台挂牌价差机会信号
- 目标：让贝壳/安居客疑似同套但挂牌单价差异明显的记录进入机会列表，并保留“待核实”边界。
- 用户确认：同小区、同户型、面积差≤5%；挂牌单价差≥10%，计算公式为`(高单价−低单价)÷低单价`，恰好10%计入。
- `/api/opportunities` 对贝壳和安居客不同来源的挂牌执行候选比较，返回对端挂牌ID/来源/链接/报价/面积/单价/更新时间、面积差及价差；两端均可分别展示机会，不自动合并、不认定同套。其他来源、同来源、户型未知/不一致、面积超差及价差不足均排除。
- 更新`docs/API.md`、`docs/DECISIONS.md`、`docs/ROADMAP.md`、`docs/GOAL_STATE.json`及`CHANGELOG.md`。机会专项回归覆盖10%边界、以低价为分母及排除条件。
- 本机全量pytest **95 passed、9 skipped**（需`TEST_DATABASE_URL`），`compileall`、Compose配置和目标JSON解析通过；存在1条Starlette/httpx弃用警告。当前尚未执行数据库集成或NAS验收。
- NAS `nas-lan`本轮连接`10.10.10.7:22222`超时；随后Tailscale CLI返回无法读取本机偏好，未切换到Netcatty，未同步或部署。两来源采集仍OFF，未访问房源网站或写入生产数据库。下一步：LAN直连恢复后先备份，以隔离PostgreSQL验收API增量，再仅部署API并检查UGREEN项目与生产来源开关。

## 2026-11-10 P0-08 NAS备份库存复核
# 2026-11-10 P0-06 DTK缺失分页游标的部分成功状态
- 成功标准：若DTK声明仍有后续内容（`has_more=true`）但未返回可用游标，Worker不能将不完整轮询记为`success`，须在运行记录中标记可见的`partial`原因。
- 新增`tests/test_worker.py`回归。修复前测试复现为`success`，修复后`app/worker.py`标记`partial`并写入“DTK indicated more posts without a pagination cursor”。已写入页面的数据仍保留，Worker不会猜游标或自动重试。
- 专项测试1 passed；全量pytest **96 passed、9 skipped**（需`TEST_DATABASE_URL`），编译、Compose配置、GOAL_STATE JSON解析通过。没有改数据库结构/API，也没有NAS同步。
- `nas-lan`连接`10.10.10.7:22222`超时；Tailscale CLI无法读取本机偏好。未切换Netcatty，未部署；DTK版本/接口权限及3个获准账号24小时联调仍待NAS和账号条件。

# 2026-11-10 跨平台挂牌价差机会信号
# 2026-11-10 P2-02跨平台机会数据库/API集成用例
- 新增`test_opportunities_returns_cross_platform_price_gap_candidates`：使用API写入两条合成挂牌（同小区/户型、面积100/105㎡、单价差恰好10%），要求机会API两边均返回待核实候选、面积差为5%、保留对端链接，并确认两挂牌仍属于不同property。
- 本机全量pytest **96 passed、10 skipped**；新集成用例因未配置`TEST_DATABASE_URL`跳过。尝试在`/private/tmp`启动PostgreSQL 16 Unix socket测试集群，`initdb`临时服务器遭系统`shmget`权限拒绝；Docker socket也返回permission denied，因此未能运行数据库用例。临时数据目录已清理。
- NAS `nas-lan`仍连接超时；Tailscale CLI偏好读取失败，尝试按技能打开本机`/Applications/Tailscale.app`时系统报告包内可执行文件缺失，未能恢复连接。未切换Netcatty、未同步或部署。后续在隔离PostgreSQL环境运行该集成用例，再按流程备份并API-only部署。

# 2026-11-10 P0-06 DTK缺失分页游标的部分成功状态
# 2026-11-10 P2-02排除未来时间戳挂牌
- 成功标准：`/api/opportunities` 不将未来`last_observed_at`挂牌与有效挂牌比较生成跨平台价差候选。
- 回归用例先复现SQL缺少上界，再在房源机会查询增加`last_observed_at <= now()`，保留过去90天窗口。单测断言SQL上界；新增隔离数据库/API用例以合成当前与未来挂牌验证机会列表为空。
- `tests/test_opportunities.py`机会单测11 passed；本机全量pytest **97 passed、11 skipped**（均需`TEST_DATABASE_URL`）。数据库API用例尚未执行：本机PostgreSQL启动被`shmget`权限拒绝，NAS不可达。
- 更新`docs/API.md`、`docs/GOAL_STATE.json`、`CHANGELOG.md`、`docs/TEST_REPORT.md`与下一轮目标。无迁移；未部署。

# 2026-11-10 P2-02跨平台机会数据库/API集成用例
# 2026-11-10 PostgreSQL 16隔离完整套件验收
- 为运行新增P2-02机会API集成用例，在`/private/tmp`启动一次性PostgreSQL 16集群，仅开放Unix socket，数据库名`rehouse_test`；完整`pytest -q -rs`结果 **108 passed、0 skipped**，覆盖价差恰好10%、面积边界、两条挂牌未合并及未来时间戳挂牌不参与机会信号。
- 测试后停止PostgreSQL并清理临时集群；没有访问或写入NAS/生产数据库。`compileall`、占位环境变量下`docker compose config -q`、GOAL_STATE JSON解析通过。保留1条Starlette/httpx弃用警告。
- NAS `nas-lan`连接仍超时，Tailscale App/CLI状态未恢复；这次本机PG16结果不替代NAS PG17集成验收，也未同步/部署。下一步NAS路径恢复后先备份，再隔离验收机会API并API-only部署。

## 2026-11-10 P0-08 NAS备份库存复核
# 2026-11-10 P0-06 DTK任务轮询绝对超时
- 成功标准：DTK返回任务ID后，轮询总时长受约52.5秒绝对截止时间约束，HTTP任务状态请求超时不得突破剩余窗口，慢响应不能将单Worker拖延数分钟。
- 新增可控时钟回归：修复前模拟慢任务状态请求会轮询35次；改为单调时钟截止后最多轮询3次，并为每次HTTP请求设置`min(30秒, 剩余时间)`。未增加自动重试或猜测DTK状态语义。
- 全量测试在一次性隔离PostgreSQL 16中 **109 passed、0 skipped**；临时库仅Unix socket可访问，测试后停止并清理。`compileall`、Compose配置、目标JSON解析通过；1条Starlette/httpx弃用警告。
- NAS `nas-lan`仍超时，Tailscale CLI无法读取偏好；没有真实DTK服务/账号联调，本轮未部署。P0-06仍待NAS确认DTK接口版本/权限及3个获准账号连续24小时运行。

# 2026-11-10 PostgreSQL 16隔离完整套件验收
# 2026-11-10 P0-06 DTK任务 ID 输入边界
- DTK返回的`task_id`现仅接受非空字符串或整数；布尔值/对象/空白值明确记为`DtkError`。合法ID经过URL路径段编码，斜线、问号等字符不会改变请求路径结构。
- 新增3种无效ID和1种特殊字符回归；修复前4项均失败，修复后`tests/test_dtk.py` **25 passed**。
- 本机完整PostgreSQL 16隔离测试 **113 passed、0 skipped**；`compileall`、Compose配置与GOAL_STATE JSON解析通过，保留1条Starlette/httpx弃用警告。临时库仅Unix socket，测试后清理。
- NAS `nas-lan`超时，Tailscale CLI无法读取偏好；没有访问真实DTK接口或部署。P0-06仍待NAS核对版本/权限及至少3个获准账号连续24小时联调。

# 2026-11-10 P0-06 DTK任务轮询绝对超时
# 2026-11-10 可复用开发包构建器
- 新增`scripts/package_dev.py`，用于每轮刷新`MANIFEST.sha256`、生成ZIP、校验ZIP完整性及包内哈希，并确保输出在项目目录之外；排除`.env`、备份、运行数据、缓存、旧ZIP和数据库/日志文件，保留`.env.example`与`data/**/.gitkeep`。
- 新增2个临时目录测试，覆盖秘密/备份/缓存/真实运行数据/旧包排除、示例环境文件保留、包内哈希检查及拒绝在项目目录内生成ZIP；专项 **2 passed**。
- 本机完整隔离PostgreSQL 16测试 **115 passed、0 skipped**；`compileall`、Compose配置和目标状态JSON解析通过。1条既有Starlette/httpx弃用警告。
- NAS仍不可达，本轮未同步或部署。后续开发包可使用`python scripts/package_dev.py --output ../<name>.zip`重复生成。

# 2026-11-10 P0-06 DTK任务 ID 输入边界


## 2026-11-10 P0-02 API上传体积保护 API-only NAS部署
- 目标：将HTML上传请求6,100,000字节上限及HTML UTF-8正文1,000,000字节限制部署到现有NAS服务；不执行数据库迁移，不重启Worker/DB/Docker引擎。
- 部署前在NAS创建并核验新鲜数据库/raw-pages备份`backups/ningbo-re-ai-20261110T063944Z-1816930`（含`SHA256SUMS`；用`postgres:17-alpine`镜像只读执行`pg_restore --list`通过）；保存回滚源码快照`backups/source-snapshots/api-before-body-limit-20261110T063944Z.tar.gz`，SHA-256 `c42280a44e0a115d8f4b3d0048df02a2209cfc6774b7c23be2642c27ed0b56cb`。
- 已校验开发ZIP SHA-256 `088f67c41f3e9e5a260c26cba21e557ecc95cf6f0674723a851ada16f08428d3`，在NAS隔离PostgreSQL 17完整测试 **144 passed、0 skipped**。开发源码包SHA一致；源码清单文件同步后96项通过SHA-256，排除运行数据、备份与`.env`。
- 使用保留登记路径`/volume3/docker/ningbo-re-ai/docker-compose.yml`只构建并重建API。新API镜像`sha256:c7d12ea6f745583224b2fa937b30bb58203036dc93b85109e44c491c3083daaf`，容器ID `e240004e52ad`；容器内`app/*.py`树哈希与NAS项目源码均为`9b9435ff09e0d646d037270e21d837a27b7046b9d6ba216c918bb0f8ca577a7e`。
- 验收：`/healthz`=200；未认证业务API=401；超过6,100,000字节的HTML提交=413。全局在线采集false，安居客`not_reviewed`/关闭、贝壳`not_authorized`/关闭。监控账号、视频、小区、房源、挂牌、历史价、同套候选、条件单、通知、采集目标/候选/运行均为0行。
- Worker容器`e13a59d935fd`、PostgreSQL容器`869f62ca7cab`及`ningbo-re-ai_pgdata`卷保持原ID/挂载；项目名与UGREEN Compose登记路径不变。`.env`权限600，`data/`与`backups/`权限700。临时PG17容器、测试源码/ZIP及本轮传输包已清理，备份和回滚快照保留。
- 未验证：UGREEN UI本轮未再次视觉检查；没有真实获准页面，P0-02样本验收和P0-03真实字段准确率仍未完成；P0-01仍缺V0.1实际库/备份。
- 下一步：继续优先取得贝壳/安居客明确书面用途许可及每站20份获准标注样本；在线采集保持关闭。


## 2026-11-10 P0-08 NAS 90天备份只读盘点与权限误报保护
- 按NAS目录真实属主分别以只读挂载运行`storage_report.py`：`data/raw-pages`为2个文件/249字节（最早/最新均为2026-11-09 00:45:38 UTC）；`backups`为33个文件/1,053,956字节（最早2026-11-09 13:38:21 UTC，最新2026-11-10 07:10:33 UTC）。90天超期候选0个/0字节，无文件删除。`/volume3`可用436,787,408,896字节（约406.9GiB）。
- 首次容器以不匹配的身份运行时，受保护目录被脚本静默当作空目录；未据此作结论。修复`storage_report.py`为直接扫描目录并向上传播权限错误，避免把不可读误报为0；新增不可读目录回归，旧实现先失败，新实现后`tests/test_storage_report.py` **8 passed**。
- 本次盘点通过分别使用raw-pages UID 10001和backups属主UID 1006:10的禁网、只读临时容器完成；不读取`.env`、不变更权限、不触碰数据库。新版脚本已同步NAS并复核：匹配目录属主时统计成功，无权容器返回PermissionError。


## 2026-11-10 P0-02 CSV样本清单结构校验
- 用户确认暂时没有获准真实HTML样本或V0.1数据库备份；没有用虚构数据填充验收。工作区`data/raw-pages/`仍仅有`.gitkeep`，P0-02保持`todo`、P0-01保持`blocked`。
- 离线检查发现`validate_sample_set.py`将CSV列名转为集合，会隐藏重复表头；行字段多于/少于表头也没有明确拒绝，可能让来源/人工标签映射错位。新增3个回归用例，旧实现3项失败。
- 现拒绝重复/空表头，跳过并报错字段数与表头不匹配的行，不让畸形行计入来源样本数。`tests/test_sample_set.py tests/test_parser_evaluation.py` **19 passed**；`compileall`与GOAL_STATE JSON解析通过。未访问网站、NAS或生产数据库。
- 更新样本集说明、测试报告与开发包；获准样本、许可范围及人工标注仍需用户提供。


## 2026-11-10 P0-03 可选挂牌字段冲突告警
- 成功标准：户型、行政区域、楼层或装修在可见详情中出现多个不同标注时不选择其一，并通过稳定告警让审核者看见冲突。
- 回归测试先复现“字段留空但没有任何冲突警告”；解析器现为四类可选字段分别输出`multiple_*_mentions`，仍保持字段为null，不改写为猜测值。解析器版本升至`generic-labelled-v0.2.6`。
- `tests/test_collection_parser.py tests/test_parser_evaluation.py tests/test_sample_set.py` **44 passed**；`compileall`和GOAL_STATE JSON解析通过。没有真实样本，不能据此报告站点准确率；本轮未访问网站、NAS或生产库。


## 2026-11-10 P0-02/P0-03 标注完整性与字段冲突评估
- 复核发现清单允许未标记的空人工字段，评估器会将其从准确率/覆盖率分母省略；同时解析器虽能警告户型/区域/楼层/装修冲突，样本模板和评估器未覆盖楼层/装修或冲突通过率。新增两个回归，旧行为均失败。
- 扩充清单人工标签为source ID、小区、区域、面积、户型、楼层、装修、挂牌价；要求每个空标签由`missing_fields`、`unknown_id`、`multiple_prices`或匹配的多值冲突场景解释。楼层/装修进入字段准确率/覆盖率。对`multiple_bedrooms`、`multiple_districts`、`multiple_floors`、`multiple_decorations`逐项统计场景通过率，要求对应字段留空且警告存在；未强制每站采集此类场景。
- `tests/test_sample_set.py tests/test_collection_parser.py tests/test_parser_evaluation.py` **49 passed**；编译、GOAL_STATE JSON解析通过。改动仅本地，未部署。用户暂时没有样本或V0.1备份；未访问网站/NAS/生产库。
## 2026-11-10 P0-03 UTF-8 BOM解析回归
- 目标：确保合法UTF-8 BOM不会使页面首个挂牌字段漏解析，同时不改变原始HTML哈希和字节长度证据。
- `tests/test_collection_parser.py -k utf8_bom`：**1 passed**；小区、面积、挂牌价均成功识别，解析器版本保持`generic-labelled-v0.2.9`。
- 全量离线`pytest -q -rs`：**172 passed、11 skipped**；跳过项均要求`TEST_DATABASE_URL`，保留1条Starlette/httpx弃用警告。未启动数据库集群。
- 仅本地验证；未访问网站、NAS、生产数据库或DTK。P0-02获准样本、P0-03真实字段准确率及P0-01 V0.1备份升级仍未验收。

## 2026-11-10 P0-03户型字段范围保护
- 成功标准：解析器输出必须满足当前 API/数据库对卧室数0至20的约束；超范围页面值不应进入候选字段。
- 回归先复现：`户型：21室`被解析成21。现将超范围值置空并输出`invalid_bedrooms_mentions`，解析器版本升至`generic-labelled-v0.2.10`。
- 解析器/评估器/样本校验专项 **60 passed**；全量离线pytest **173 passed、11 skipped**（跳过项需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 未改API、数据库、迁移或配置；仅本地离线验证，未访问网站/NAS/DTK，真实页面准确率未验证。

## 2026-11-10 P0-03来源ID长度边界
- 成功标准：URL提取的来源ID以及样本人工标签不得超出`ListingIn`的220字符上限；超长URL ID不能令候选看似可审批。
- 新增221位URL ID和样本标签回归，旧逻辑均未拒绝。现解析器仅提取最多220位ID，超长时字段留空且候选不ready；样本清单拒绝超过220字符的人工ID。解析器版本升至`generic-labelled-v0.2.11`。
- `tests/test_collection_parser.py tests/test_parser_evaluation.py tests/test_sample_set.py`：**62 passed**；全量离线pytest **175 passed、11 skipped**，11项为PostgreSQL集成用例，另有1条Starlette/httpx弃用警告。
- 未改数据库/API/配置；仅本地验证，真实样本与字段准确率未验收。

## 2026-11-10 P0-02来源URL隐私边界
- 成功标准：query参数/fragment不进入候选记录，也不被在线采集器请求；拒绝发生在任何网络访问前。
- 新增 query token、fragment及“不得发出HTTP请求”回归。共享`check_source_url`现在拒绝两类后缀；canonical URL只在来源ID比较时剥除后缀，冲突检查仍有效。
- 解析器版本升至`generic-labelled-v0.2.13`。`tests/test_collection_parser.py tests/test_collection_http.py`：**46 passed**；全量离线pytest **180 passed、11 skipped**，保留1条Starlette/httpx弃用警告。
- 未访问网站或NAS；不改变来源权限/在线开关，不代表取得采集授权。

## 2026-11-10 P0-02来源URL长度边界统一
- 成功标准：离线解析、API上传、在线目标及样本清单使用一致的12–2000字符来源URL范围。
- 新增超长URL回归，旧解析入口和样本清单均接受超过2000字符；现`check_source_url`与清单校验器拒绝越界URL，文档与API模型范围一致。解析器版本为`generic-labelled-v0.2.14`。
- `tests/test_collection_parser.py tests/test_collection_http.py tests/test_sample_set.py tests/test_parser_evaluation.py`：**76 passed**。
- 仅本地验证；未访问网站/NAS，没有许可或真实页面解析准确率结论。

## 2026-11-10 P0-02畸形URL输入错误处理
- 成功标准：无效用户URL返回项目输入异常而不导致未处理`ValueError`；页面自身的畸形canonical字段不应阻断其余解析。
- 回归复现不完整IPv6主机导致原生`ValueError`；共享校验器现转换为`CollectionError`，畸形canonical链接忽略，合法提交URL ID继续解析。解析器版本`generic-labelled-v0.2.15`。
- `tests/test_collection_parser.py tests/test_collection_http.py tests/test_sample_set.py tests/test_parser_evaluation.py`：**78 passed**；全量离线pytest **184 passed、11 skipped**，保留1条Starlette/httpx弃用警告。
- 仅本地验证；未访问网站、NAS或DTK，不代表真实样本质量或在线授权。

## 2026-11-10 P0-03数值标注规范化
- 成功标准：数值等价但格式不同的重复面积/价格/户型不触发虚假冲突；数值不同仍需留空并警告。
- 新增`160`/`160.0`面积、`365`/`365.00`挂牌价、`02室`/`2室`户型回归；旧逻辑将字段留空。现用Decimal等值归一，解析器版本升至`generic-labelled-v0.2.16`。
- parser/HTTP/sample-validator/evaluator专项 **79 passed**；全量离线pytest **185 passed、11 skipped**，保留1条Starlette/httpx弃用警告。
- 仅本地逻辑验证；没有获准真实样本，未产生真实页面准确率。

## 2026-11-10 P0-03损坏数值标注容错
- 成功标准：格式损坏的数字片段不应让解析流程抛异常或使有效候选整体失败；有效值与损坏值共存时不静默挑选有效值。
- 新增逗号-only面积/价格及有效报价+损坏报价回归；旧逻辑因`Decimal.InvalidOperation`崩溃。现损坏值保持不可用，混合标注作为多值冲突，解析器版本`generic-labelled-v0.2.17`。
- parser/HTTP/sample-validator/evaluator专项 **81 passed**；全量离线pytest **187 passed、11 skipped**，保留1条Starlette/httpx弃用警告。
- 仅本地合成HTML验证；无数据库/API配置变化，未报告真实站点准确率。

## 2026-11-10 P0-03数值千分位格式校验
- 成功标准：逗号只能用于标准三位千分位分组；`12,34`不得被解释为1234，合法`1,234.5`保持可解析。
- 新增非法/合法分组回归。解析器先捕获候选数值片段，再校验分组；非法值按缺失处理，存在另一个不同值时仍触发冲突告警。版本`generic-labelled-v0.2.18`。
- parser/HTTP/sample-validator/evaluator专项 **83 passed**；全量离线pytest **189 passed、11 skipped**，保留1条Starlette/httpx弃用警告。
- 仅本地合成输入验证；无真实样本准确率结论。

## 2026-11-10 P0-02空userinfo URL拒绝
- 成功标准：来源URL只要包含userinfo分隔段即拒绝，不能因用户名/密码为空而通过共享校验。
- 新增`https://@host`及`https://:@host`回归，旧校验均接受；现检查userinfo字段是否存在，与样本清单规则一致。解析器版本`generic-labelled-v0.2.19`。
- parser/HTTP/sample-validator/evaluator专项 **85 passed**；全量离线pytest **191 passed、11 skipped**，保留1条Starlette/httpx弃用警告。
- 仅本地验证；未连接网站/NAS或改变在线策略。

## 2026-11-10 P0-02来源主机尾点校验
- 成功标准：来源主机最多规范化一个DNS根尾点；多余的点不能通过域名白名单。
- 新增双/三尾点拒绝及单尾点接受回归，旧逻辑将两类多尾点主机均规范化成合法域名。现只去除一个末尾点，版本升至`generic-labelled-v0.2.20`。
- parser/HTTP/sample-validator/evaluator专项 **88 passed**；全量离线pytest **194 passed、11 skipped**，保留1条Starlette/httpx弃用警告。
- 本地验证；未访问网站/NAS，没有变更在线来源状态。


## 2026-11-10 P0-08原始证据引用只读审计
- 成功标准：能在只读模式下识别磁盘上无候选记录引用的内容寻址证据，以及候选记录引用但磁盘缺失的证据；任何情况下均不自动删除文件。
- `scripts/storage_report.py`新增`--check-evidence-references`，按证据文件名对比`collection_candidates.raw_storage_path`，分别汇总孤儿和缺失文件并列出哈希文件名。数据库连接错误会直接失败，不把不可读状态误报为0；常规盘点不需要数据库，行为保持只读。
- 回归覆盖正常引用、孤儿、缺失引用、非内容寻址文件、符号链接和数据库不可用时显式失败。`tests/test_storage_report.py` **11 passed**；全量pytest **228 passed、13 skipped**（PostgreSQL集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 本轮仅本机离线验证；没有数据库/NAS连接，因此未盘点生产孤儿，也未同步脚本。NAS运行时需有raw-pages目录读取权限和数据库只读查询权限；不自动清理，不改变已确认留存策略。
- `compileall`、`GOAL_STATE.json`解析及使用占位变量的`docker compose config -q`通过。生成开发包并刷新`MANIFEST.sha256`。
- 下一步：①恢复NAS连接后以匹配UID和只读数据库账号执行该报告并核对输出；②继续P0-02/P0-03，等待每站20份获准样本与人工标签；③P0-01仍等待真实V0.1备份以完成升级验收。

## 2026-11-10 P0-02拒绝模板外CSV字段
- 成功标准：样本清单只接受`SAMPLE_MANIFEST_TEMPLATE.csv`定义的列；未知列必须在读取样本行前明确拒绝，不能静默丢弃个人联系信息或误拼字段。
- 新增包含`contact_phone`列的回归，修复前被完整接受；现在校验器同时列出缺失/未知表头并在处理数据行前返回错误。更新样本集说明与P0路线图。
- `tests/test_sample_set.py -k unsupported_manifest_columns`：1 passed；样本清单+解析评估专项39 passed；全量pytest **229 passed、13 skipped**（PostgreSQL集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 仅离线验证，不涉及数据库迁移、API配置、真实页面、许可、NAS或生产数据；虚构样本仅用于回归。P0-02继续等待每站20份获准页面及人工标注。
- 下一步：①用户提供获准样本后执行清单与解析评估并报告每站每字段准确率/覆盖率；②P0-01仍等待真实V0.1备份；③P0-04在许可确认前保持两来源在线关闭。


## 2026-11-10 P0-02损坏清单编码错误处理
- 成功标准：非UTF-8清单必须作为验证错误返回，不能让UnicodeDecodeError逃逸；异常清单的来源计数应为零。
- 新增损坏CSV字节回归，修复前在读取表头时抛UnicodeDecodeError；现转换为`manifest must be valid UTF-8`并返回零计数。更新样本集说明。
- `tests/test_sample_set.py -k non_utf8_manifest`：1 passed；样本清单与解析评估专项40 passed；全量pytest **230 passed、13 skipped**（PostgreSQL集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 本机Python 3.12离线验证；未连接数据库、网站或NAS，无迁移/配置变化；P0-02真实获准样本仍缺。
- 下一步：①获准样本到位后执行20+20清单与准确率评估；②P0-01等待真实V0.1备份；③P0-04在书面许可和协议范围核验完成前保持在线来源OFF。


## 2026-11-10 P0-02严格CSV引号语法
- 成功标准：格式错误的CSV引号必须被拒绝，不能被宽松解析为看似有效的标注；失败时所有来源计数归零并返回明确错误。
- 新增引号闭合后仍有尾随字符的CSV回归，修复前`DictReader`静默接收；现启用`strict=True`并将`csv.Error`转换为`manifest CSV is malformed`。
- `tests/test_sample_set.py -k malformed_csv_quoting`：1 passed；样本清单与解析评估专项41 passed；全量pytest **231 passed、13 skipped**（PostgreSQL集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 本机Python 3.12离线验证；未连接数据库、网站或NAS，无迁移/配置变化；P0-02仍需获准真实样本及人工标注。
- 下一步：①获准样本到位后运行20+20清单和解析准确率/覆盖率评估；②P0-01等待真实V0.1备份；③许可未确认前保持来源在线关闭。


## 2026-11-10 P0-06抖音分享链接尾点边界
- 成功标准：分享URL只允许douyin.com/iesdouyin.com根域或子域；最多一个DNS根尾点可接受，多个尾点不得规范化为允许主机，非法链接须回退canonical作品URL。
- 新增douyin.com双尾点、iesdouyin.com三尾点拒绝回归及单根尾点接受回归。修复前前两者被`rstrip('.')`误接受；现最多剥除一个尾点后匹配允许域。
- `tests/test_dtk.py tests/test_worker.py`：**53 passed**；全量pytest **234 passed、13 skipped**（PostgreSQL集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 本机Python 3.12离线验证，无数据库迁移/配置变化；未连接DTK、NAS或获准账号。不能据此认定DTK实际分享域名全量或平台权限已验证。
- 下一步：①P0-06仍需在NAS核对DTK版本/权限并取得至少3个获准账号完成24小时联调；②P0-02待每站20份获准样本与人工标注；③P0-01待真实V0.1备份完成升级验收。


## 2026-11-10 P0-02样本路径控制字符拒绝
- 成功标准：HTML路径字段中的C0/C1控制字符在路径解析前明确拒绝；不能通过strip静默改变路径，也不能令NUL导致未处理异常。
- 新增换行、NUL和C1控制字符回归；修复前换行会被strip后通过、NUL在`Path.resolve()`触发`ValueError`，C1未有明确拒绝规则。现于构造`Path`前统一拒绝。
- `tests/test_sample_set.py -k control_characters_in_html_path`：3 passed；样本清单与解析评估专项44 passed；全量pytest **237 passed、13 skipped**（PostgreSQL集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 本机Python 3.12离线验证；无迁移/配置变化，未连接数据库、网站或NAS；P0-02真实样本仍待许可及人工标注。
- 下一步：①获准样本到位后运行每站20份校验与字段评估；②P0-01等待真实V0.1备份；③P0-04许可确认前维持在线采集OFF。
## 2026-11-10 P0-06分享URL拒绝内嵌空白与C1控制字符
- 成功标准：分享链接结构检查拒绝原字符串中的任意空白/C1控制字符，避免把带隐藏分隔符的URL保存为作品来源。
- `_safe_post_url`在`urlsplit`前拒绝内部空格、Tab及C1控制字符，同时维持首尾普通空白裁剪，并回退到由作品ID构造的规范抖音URL。DTK/Worker专项 **56 passed**；全量pytest **240 passed、13 skipped**（跳过均需`TEST_DATABASE_URL`），存在既有Starlette/httpx弃用警告。
- 仅本机离线验证；未连接DTK、NAS或来源网站。P0-06仍需真实接口版本/权限核验及3个获准账号24小时联调。
- 本轮复跑时系统Python未安装pytest/httpx，项目虚拟环境不存在；`uv --offline`因缓存目录权限受限也无法启动，因此本轮无法独立重现前序项目环境的240 passed结果。该运行限制不改变代码，但下次需在具备项目依赖的环境复跑。
- `scripts/package_dev.py`重建源码包`ningbo-re-ai-v0.2-dev-2026-11-10-dtk-url.zip`（98个源码/文档文件）；ZIP完整性、包内SHA256清单及外部ZIP SHA256复核通过。



## 2026-11-10 P0-04官方协议入口在线复核
- 本轮重新打开贝壳官方服务协议；更新/生效日期仍为2026-09-24/2026-09-25，关于自动化获取、书面许可和Robots的条款记录见`docs/SOURCE_POLICY_REVIEW_2026-11-10.md`。
- 安居客官方协议中心显示当前协议分类及历史版本入口，但网页正文未暴露具体协议；官方静态域名PDF没有版本日期，不能证明它是当前协议。项目目标主机robots页面本轮仍不能经网页工具读取；不推断权限变化。
- 两来源均无项目书面许可，在线来源继续OFF；没有访问房源页或启动采集，P0-04保持`in_progress`。解析器/样本工具专项`pytest`：120 passed；不构成真实样本准确率或来源许可验证。


## 2026-11-10 P0-03建筑面积与套内面积区分
- 成功标准：同页出现建筑面积和套内/使用面积时，只将建筑面积用于房源`area_sqm`，不错误触发多值冲突；不同建筑面积仍保守留空。
- 新回归先复现面积字段被清空；解析正则现在排除使用、套内、室内、公摊、占地、赠送面积标签。版本`generic-labelled-v0.2.28`。
- 解析器/样本/评估专项121 passed；全量pytest **268 passed、13 skipped**（均为需要`TEST_DATABASE_URL`的数据库集成用例），保留1条Starlette/httpx弃用警告。
- 仅离线合成HTML验证，不代表真实平台字段准确率或样本授权；未连接网站/NAS、未做数据库迁移。P0-03仍需每站20份获准样本校准。


## 2026-11-10 P0-01隔离数据库验证环境受限
- 尝试本机一次性PostgreSQL 16隔离测试；`initdb`完成，但服务启动因sandbox内`shmget`共享内存限制失败，切换mmap共享内存类型仍失败。
- 本机Docker API socket返回`permission denied`，无法以容器另建隔离测试实例。临时数据目录由退出清理钩子删除，检查确认55441端口无PostgreSQL响应。
- 本轮未设置`TEST_DATABASE_URL`、未运行数据库集成文件，未连接NAS/业务库；不得将此前或离线测试结果当作本轮PG集成通过。真实V0.1备份迁移仍待该材料与可用隔离数据库环境。


## 2026-11-10 P0-01提升权限重试PostgreSQL仍受限
- 在提升权限下以全新PG16实例重试（仅Unix socket、临时数据库和端口），仍因`shmget`失败；切换mmap共享内存配置也未改变结果。
- `ipcs`显示当前System V IPC对象列表为空，但系统拒绝读取内核IPC参数；临时目录清理成功，测试端口55442无响应。
- 这次确认普通sandbox提权无法消除此运行环境限制；数据库集成仍未运行，不能代替NAS隔离验收。


## 2026-11-10 P0-03挂牌语义根节点选择
- 成功标准：非空加载壳层`<main>`不得遮蔽后续有明确挂牌字段的`<article>`；并列或无挂牌信号时维持既有语义根顺序。
- 回归先复现`<main>页面信息正在加载</main>`导致小区/面积/价格全空；现按小区、面积、总价显式标签匹配数选择语义根，未命中时按`main`、`article`、既有内容类顺序回退。解析器版本`generic-labelled-v0.2.29`。
- Parser/样本/评估专项**122 passed**；全量pytest **269 passed、13 skipped**（需`TEST_DATABASE_URL`的DB集成），保留1条Starlette/httpx弃用警告。
- 仅离线合成结构回归；真实页面布局与准确率仍待每站20份获准HTML。未连接来源网站/NAS。


## 2026-11-10 P0-03多报价场景校验人工候选
- 成功标准：多报价歧义场景只有在解析器不选定单一价格、发出冲突警告且解析出的全部报价数值与人工`price_candidates_wan`一致时才算通过；候选证据截断必须显式失败。
- 新增标注候选故意与页面实际报价不同、以及21条报价证据超过20条上限的失败回归；两者修复前均误报通过。现按Decimal数值集合对账并拒绝缺证据/截断。
- 评估器专项`tests/test_parser_evaluation.py`：**16 passed**；全量pytest：**271 passed、13 skipped**（需TEST_DATABASE_URL），保留1条Starlette/httpx弃用警告。
- 更新`docs/SAMPLE_DATASET.md`说明。仅离线合成数据验证，不能证明真实样本准确率或授权；未连接网站/NAS。


## 2026-11-10 P0-03歧义字段候选证据对账
- 成功标准：户型/区域/楼层/装修歧义场景必须校验解析证据与人工看到的候选值集合一致；不能只凭字段为空和告警存在就算通过。
- 样本模板新增四个`*_candidates`字段；validator要求对应歧义tag下至少两个有效不同值，且tag外列必须为空。评估器逐字段按Decimal/规范化文本集合比较，并拒绝缺证据、集合不符或证据被截断的场景。
- 新增区域候选不匹配、候选重复、未标场景标签填写候选、候选证据截断回归；parser-evaluation/sample-set专项 **51 passed**，全量pytest **275 passed、13 skipped**（DB集成需`TEST_DATABASE_URL`），1条既有Starlette/httpx弃用警告。
- 更新`docs/SAMPLE_DATASET.md`和`docs/SAMPLE_MANIFEST_TEMPLATE.csv`。仅合成清单验证，真实站点样本及准确率仍未验证；未连接网站/NAS。


## 2026-11-10 P0-03紧凑分隔下的小区标签识别
- 成功标准：小区字段在标签前为常见标点且无空格时仍正确解析；仍只接受明确小区标签，不从无标签叙述猜测。
- 回归先复现`挂牌信息|小区：东湖花园；...`漏掉小区名；现允许常见中文/ASCII标点作为标签边界，解析器版本`generic-labelled-v0.2.30`。
- Parser/样本/评估专项 **129 passed**；全量pytest **276 passed、13 skipped**（DB集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 仅合成离线页面验证；真实页面准确率和授权仍未验证，未连接网站/NAS。


## 2026-11-10 P0-03小区值紧凑分隔符终止
- 成功标准：小区值后紧邻竖线、斜线或冒号时，应在该分隔符停止捕获，不把后续挂牌字段并入小区名。
- 回归先复现`小区：东湖花园|建筑面积.../总价...`被整个吞入小区名；现常见标点同时用作小区标签前置边界和值终止符。解析器版本`generic-labelled-v0.2.31`。
- Parser/样本/评估专项 **130 passed**；全量pytest **277 passed、13 skipped**（DB集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 仅合成离线页面验证，真实解析准确率仍需每站20份获准样本；未连接网站/NAS。


## 2026-11-10 P0-03楼层装修值紧凑分隔处理
- 成功标准：楼层/装修值后紧邻常见字段分隔符时，不得把后续标签和值并入当前文本；小区名中的括号仍保留。
- 回归先复现楼层捕获`高楼层|装修：精装/总价：365万`整段；现对小区、楼层、装修采用受控标点终止规则。解析器版本`generic-labelled-v0.2.32`。
- Parser/样本/评估专项 **131 passed**；全量pytest **278 passed、13 skipped**（需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 仅合成离线页面验证；真实布局/准确率待获准样本，未连接网站/NAS。


## 2026-11-10 P0-02模板列与validator schema锁定
- 为新增歧义候选列后的清单入口增加自动一致性检查：模板列无重复且与validator `REQUIRED_COLUMNS`集合完全相等。当前模板25列、必需列25列。
- 专项`tests/test_sample_set.py -k template_matches_validator`：**1 passed**；全量pytest **279 passed、13 skipped**（需`TEST_DATABASE_URL`），保留1条既有Starlette/httpx弃用警告。
- 只验证模板/schema一致，不判断授权；工作区仍无获准真实样本，P0-02仍待完成。


## 2026-11-11 P0-01统一初始化与手动迁移事务边界
- 成功标准：镜像首次初始化和手动升级执行同一批SQL时，每个001–005文件均自行`BEGIN`/`COMMIT`；手册命令不再叠加`psql --single-transaction`；静态回归锁定该契约。
- `001_init.sql`、`002_collection_pipeline.sql`、`003_collection_health_indexes.sql`、`005_saved_search_filters.sql`补上文件内事务；`004`原有事务保留。更新`docs/NAS_DEPLOYMENT.md`并新增`tests/test_migration_transactions.py`两条回归。
- Python 3.12标准库直接执行新增断言：2项通过；`compileall`、占位变量下`docker compose config -q`及`git diff --check`通过。pytest当前未安装，新增测试未由pytest运行；PostgreSQL运行时迁移与回滚未验证。
- 仅离线修改，未连接NAS、PostgreSQL或网站，未部署；真实V0.1备份仍缺，P0-01保持blocked。
- 下一步：①获得真实V0.1备份后在隔离PG17按迁移脚本逐份执行并验证失败回滚和记录保真；②继续等待P0-02每站20份获准页面与人工标注；③来源许可确认前维持在线采集关闭。


## 2026-11-11 P0-09限制离线已发现ID文件读取
- 成功标准：`--seen-ids`输入最多读取2,000,000字节；有效UTF-8按行构成去重集合；超限或非法UTF-8输入明确拒绝。
- 修复此前`Path.read_text()`无界读取的问题；新增标准库回归覆盖有效ID、2,000,001字节拒绝和非法UTF-8拒绝。更新`docs/DISCOVERY.md`。
- `python3.12 -m unittest discover -s tests -p 'test_discovery_state_stdlib.py' -v`：**12 passed**；另`compileall`、GOAL_STATE JSON、占位变量下Compose配置和`git diff --check`通过。pytest未安装，完整pytest及BeautifulSoup HTML解析测试未运行。
- 仅离线工具边界修改，未访问房源网站、NAS或数据库，未部署。P0-09仍缺来源许可、真实列表样本及数据库端分页游标/失效状态。
- 下一步：①取得授权页面样本后按站点校准详情及分页链接；②按许可范围设计数据库分页游标和错误状态；③P0-01等待V0.1备份以执行隔离迁移验收。


## 2026-11-11 P0-01锁定事务包装和初始化顺序
- 扩展静态迁移回归：每个SQL文件必须恰有一条独立事务`BEGIN;`和`COMMIT;`；Compose必须按001–005顺序挂载，且部署命令不得再次包装事务。
- 3项迁移契约检查通过；P0-09发现状态/CLI标准库测试12 passed。`compileall`、占位变量下Compose配置、GOAL_STATE JSON及差异检查通过。pytest未安装，未执行PostgreSQL运行时迁移。
- 仅本地静态/标准库验证；未连接NAS或业务数据库。P0-01仍需V0.1真实备份和隔离PG17验收。


## 2026-11-11 P0-09拒绝管道型已发现ID输入
- `--seen-ids`现在只接受普通文件；避免路径指向FIFO等特殊文件时阻塞读取。保留2,000,000字节有界读取和严格UTF-8解码。
- 新增命名管道拒绝测试；发现器状态/CLI标准库测试 **13 passed**。`compileall`、GOAL_STATE JSON、Compose配置和`git diff --check`通过。pytest仍未安装。
- 本机Docker API socket返回`permission denied`，无法启动隔离PostgreSQL；未连接NAS或业务数据库、未部署。迁移实际执行/回滚仍未验证。
- P0-09仍待许可与真实列表页；P0-01仍待真实V0.1备份及可用PG17隔离环境。


## 2026-11-11 P0-09校验seen-ids来源挂牌ID
- `--seen-ids`现根据所选来源校验ID仅为ASCII数字，贝壳8–220位、安居客7–220位；裁剪首尾空白、忽略空行并去重，拒绝来源不支持、格式错误、超长、非UTF-8及超限文件。
- 新增来源边界回归（含安居客7位最短、贝壳7位拒绝、221位拒绝）；标准库发现状态/CLI测试 **14 passed**。`compileall`、GOAL_STATE JSON、Compose配置和`git diff --check`通过。pytest未安装。
- 仅离线输入校验变更，未连接网站、数据库或NAS，未部署。P0-09仍待许可范围、真实列表样本和数据库端分页状态。


## 2026-11-11 P0-08备份前拒绝raw-pages符号链接
- 发现`backup.sh`对`/data/raw-pages`直接执行tar；若目录被替换为指向其他位置的符号链接，tar可能只保存链接本身但仍通过归档结构检查。
- 备份命令现于容器内要求该路径为真实目录且非符号链接后才运行tar。新增标准库测试从脚本提取同一shell命令，在临时目录验证真实目录归档成功、符号链接在tar前失败且不输出归档内容。
- `python3.12 -m unittest discover -s tests -p '*_stdlib.py' -q`：**16 passed**；`bash -n scripts/backup.sh`、`compileall`、占位变量Compose配置、GOAL_STATE JSON及变更文件尾随空白扫描通过。完整pytest未运行。
- NAS此前的备份/恢复验收对应旧版脚本；本轮补丁仅本机验证，未连接NAS或数据库，未部署。P0-08暂调为`in_progress`，等待新版本同步后重新核验；P0-01真实V0.1备份迁移仍blocked。


## 2026-11-11 P0-08完整备份流程临时隔离回归
- 扩展标准库测试，用临时假Docker CLI运行`backup.sh`完整流程：成功路径验证custom dump占位数据、真实tar内容、SHA256清单、700目录/600文件权限及临时目录发布后清理；`raw-pages`符号链接失败路径验证无归档发布且临时目录清理。归档使用系统真实tar，数据库dump/pg_restore由假Docker命令模拟。
- 与发现器状态测试合计18项标准库测试通过；`bash -n`、`compileall`、Compose配置、GOAL_STATE JSON及`git diff --check`通过。pytest未安装。
- 更新`docs/NAS_DEPLOYMENT.md`说明容器内目录检查。此测试不是PostgreSQL备份恢复验收；未访问NAS/业务库，未部署。P0-08仍`in_progress`，待新脚本NAS复验；P0-01仍缺V0.1真实备份。


## 2026-11-11 P0-01扩展旧库全链路迁移回归
- 合成V0.1保真集成用例现按顺序执行001建库、插入旧业务记录，再对002–005逐份执行两次；除了原有11张业务表字段对账，还核对004健康汇总将旧挂牌回填为1、其他状态计数为0，以及005条件单新字段为空数组/NULL默认值。
- `tests/test_db_integration.py`通过`py_compile`与全项目`compileall`语法检查；可运行的迁移静态契约3项和发现/备份标准库测试18项通过。pytest/PostgreSQL集成未运行；Docker API仍无本地数据库访问权限。
- 该用例现在为隔离PG环境准备了更完整的重复迁移/数据保真检查，但它不是运行结果，也不替代真实V0.1备份升级。未连接NAS或业务数据库，P0-01继续blocked。


## 2026-11-11 P0-08拒绝证据目录树内的符号链接
- 备份前置检查现使用容器内`find`检查`raw-pages`整棵目录树；若根路径是链接、任意后代文件/目录是链接、目录不可完整遍历或检查命令失败，都会在tar前中止。
- 新增完整`backup.sh`假Docker回归：嵌套证据链接导致脚本失败、无最终备份目录且临时目录清理。备份脚本专项5 passed，全部标准库测试 **19 passed**；`bash -n`、`compileall`、Compose、JSON、迁移静态契约和`git diff --check`通过。
- 仅本地临时目录验证，未连接NAS或数据库、未部署。P0-08仍`in_progress`，需NAS重新执行新鲜备份与隔离恢复后确认。


## 2026-11-11 P0-01迁移契约改为标准库测试并重试本机SQL执行
- 将001–005事务边界、升级命令不嵌套包装及Compose挂载顺序3项检查改为标准库`unittest`，可与当前无pytest环境下的其他stdlib测试统一运行。
- `python3.12 -m unittest discover -s tests -p '*_stdlib.py' -v`：**22 passed**。`test_db_integration.py`和迁移测试编译通过，`compileall`、占位变量Compose配置与`git diff --check`通过。
- 尝试Homebrew PostgreSQL 16单用户执行路径，但全新`initdb`本身再次因系统`shmget`共享内存限制失败，临时数据目录自动清理；Docker API仍权限拒绝。PostgreSQL集成/迁移未执行。
- 真实V0.1备份仍缺，P0-01保持blocked；本轮未连接NAS、业务库或网站。


## 2026-11-11 机会查询连接生命周期与全量回归
- 修复`/api/opportunities`价格历史查询在数据库session结束后继续使用连接的问题：查询现保持在session上下文中。另将候选更正集成测试断言对齐PATCH路由直接返回候选行的实际契约，没有改变API响应结构。
- 临时隔离PostgreSQL 16全量测试：**574 passed、12 subtests passed**，另有1条既有Starlette/httpx弃用警告；无数据库URL离线测试：**560 passed、14 skipped、12 subtests passed**。临时测试容器和虚拟环境已清理。
- 仅验证隔离PG16和离线套件；这不是NAS PG17部署验收，也不包含真实业务数据。未访问来源网站、未改NAS或生产数据库。P0-01继续等待真实V0.1备份，P0-02继续等待每站20份获准页面及人工标注，在线来源保持关闭。
- 下一步：继续处理不依赖真实样本、旧库备份或来源授权的最高优先级离线任务；这些外部材料到位后再完成对应验收。


## 2026-11-11 P0-08只读连接复核与P0-07口径待确认
- 按`nas-ssh-connect`连接规则核查Tailscale；CLI无法加载偏好，且`open -a Tailscale`确认本机没有该App。`nas-lan`连接`10.10.10.7:22222`超时后，使用用户已授权的`notedock-nas`只读核验也在`300858.xyz:5005`超时。连接均未成功，没有读取或修改NAS；新版`backup.sh`尚未同步/实机复验。
- 查看`ugreen-nas-docker-deploy`要求：NAS变更前必须先盘点并验证主机、Docker权限、Compose路径及数据挂载。因SSH未连通，本轮没有部署或启动Docker操作。
- P0-07四种健康率的分母/阻断口径仍未确定；已向用户询问采集成功、解析成功、字段完整、人工审核通过率的分母定义，本轮不按猜测实现。P0-01真实V0.1备份和P0-02每站20份获准样本及标注仍缺。
- 这次核验只更新交接状态，不改应用代码。下一步在口径确认前继续其他无外部材料依赖的离线开发；NAS当前版本重新验收须待连接恢复。

## 2026-11-11 P0-04 官方协议版本复核
- 贝壳官网协议页确认当前标示2026-09-24更新、2026-09-25生效；第七条继续要求书面许可、遵守Robots并限制自动化获取。
- 安居客官网协议中心有消费者/经营者协议与历史版本入口；官方静态PDF标示2021年5月更新，但无法证明其与现行协议中心条目对应。条文限制未获明确特别书面许可的抓取/使用，并要求搜索引擎遵循Robots。
- 本轮网页工具未能取得两宁波目标主机Robots新正文；2026-11-10 NAS只读结果仍是最近可核对证据。未请求房源页、未采集、未改变许可状态；两来源在线保持OFF。P0-04仍需平台书面确认适用协议及具体授权范围。
- 来源依据及边界见`docs/SOURCE_POLICY_REVIEW_2026-11-10.md`补充；本轮是官方公开条款核对，不构成法律意见。

## 2026-11-11 P0-08 NAS只读复核续
- 经用户授权的`notedock-nas`首次SSH只读命令成功，身份为`DXP4800/sheng`，组含`docker`；确认Compose服务为db/api/worker，PostgreSQL数据使用独立`ningbo-re-ai_pgdata`命名卷，数据库版本镜像仍需另行核对。`backups/`根目录700，顶层可见7个归档文件；该命令未统计子目录内容，不能据此断言没有数据库备份。宿主机用户无法直接列出`data/raw-pages`。
- 随后再次连接时SSH复用控制套接字被本机权限拒绝，公网别名主机名解析失败；没有继续远端命令，也没有NAS写入、备份、传输或容器操作。新版`backup.sh`及`storage_report.py`仍未在NAS复验。
- 当前执行环境未安装`bs4`，未运行解析器回归；因此没有在未验证环境下修改解析器。下一步继续处理可离线验证的任务，或在依赖可用后推进P0-03合成回归。

## 2026-11-11 P0-08内容寻址证据完整性只读核验
- `scripts/storage_report.py`新增`--check-evidence-integrity`，流式解压`<sha256>.html.gz`并核对HTML内容SHA-256；损坏gzip与哈希/文件名不符均报告异常，不修改证据。
- 新增标准库临时文件回归覆盖有效归档、内容哈希不符、坏gzip、符号链接及非证据文件；`python3.12 -m unittest tests.test_storage_report_stdlib -v`：**3 passed**。`py_compile`、`compileall`、`bash -n scripts/backup.sh`及GOAL_STATE JSON校验通过。完整pytest未运行（本机无pytest/bs4）。
- 仅使用临时虚构文件，未读取NAS证据、未访问网站、未执行清理/部署。P0-08仍`in_progress`，需有连接后在NAS实机执行；P0-01/P0-02仍等待真实备份/获准样本。

## 2026-11-11 P0-08保护备份根目录目标
- 代码审查发现`BACKUP_ROOT=/`、`.`、`..`或项目目录时，旧脚本会尝试对目标执行`chmod 700`。现在拒绝文件系统根、当前目录/父目录及任何包含项目工作目录的已存在目录；拒绝点在`mkdir`、`chmod`及Docker命令之前。
- 证据校验现只将gzip格式/CRC错误或意外EOF归为损坏；文件读取权限/系统IO错误向上传播，由CLI明确失败，不冒充坏证据。权限拒绝回归先重现误报后通过。
- 标准库隔离测试通过根目录、当前项目目录、父目录及相对`.`/`..`，用假命令日志断言无外部命令运行；另覆盖权限错误传播。`python3.12 -m unittest discover -s tests -p '*_stdlib.py' -q`：**34 passed**。`bash -n`、`compileall`、JSON检查通过。
- 结合本轮新增的原始证据gzip内容哈希检查，均仅离线/临时合成输入验证；pytest/解析器套件未运行（本机无pytest/bs4），未执行NAS备份、部署或清理。P0-08仍需NAS实机复验。

## 2026-11-11 P0-08/P0-03离线完整套件复核
- 复用本机已有的Python 3.12测试环境（未联网安装依赖）运行当前工作区完整pytest：**651 passed、15 skipped、13 subtests passed**；15项数据库集成因未配置`TEST_DATABASE_URL`而跳过，保留1条既有Starlette/httpx弃用警告。此前标准库全套34 passed。
- 另用合成深层HTML检查可见及隐藏节点处理：2,000–8,000层嵌套的普通、`hidden`、`display:none`、`script`场景均未触发递归异常。此仅作为压力探针，不代表真实站点准确率。
- 没有测试数据库、真实获准页面或人工标签；NAS LAN SSH当前仍超时。P0-08不因此视为NAS已复验，P0-03仍需真实样本校准。

## 2026-11-11 P0-09报告本地重试状态保存失败
- `record_failure`此前吞掉本地state原子写入错误，CLI仍只报告页面读取/解析失败，容易让操作员误以为失败页已排入重试。现返回保存结果；若state写入失败，CLI在不暴露路径内容的前提下追加“discovery retry state could not be saved”。
- 状态层和CLI回归覆盖权限拒绝写入，定向标准库状态测试**21 passed**；完整pytest **653 passed、15 skipped、13 subtests passed**，15项数据库集成未配置`TEST_DATABASE_URL`而跳过，保留1条Starlette/httpx弃用警告。
- NAS复核：`nas-lan`连接超时；Tailscale CLI无法加载偏好且系统找不到App；已授权的`notedock-nas`连接超时。没有建立远程会话、执行远端命令或进行写入。P0-09仍等待来源许可、真实分页样本和自动Worker分页流程；P0-08仍待NAS新版脚本复验。

## 2026-11-11 P0-09缺少状态路径时安全返回未保存
- `record_failure`签名允许`path=None`；传入有效state但没有保存路径时，旧行为会对`None`调用文件保存并抛出类型异常。现先在内存记录失败attempt/error，再返回`False`表示持久化未发生，CLI可沿用未保存诊断契约。
- 新增状态层回归，修复前失败后通过；状态/CLI定向**22 passed**，完整pytest **654 passed、15 skipped、13 subtests passed**。15项数据库集成因未配置`TEST_DATABASE_URL`跳过，1条既有Starlette/httpx弃用警告。
- 离线状态层修复，不涉及数据库迁移、网络、来源或NAS部署；P0-09仍依赖获准列表页和自动Worker分页。

## 2026-11-11 P0-03/P0-09先按字符数拒绝超大HTML
- 解析器与离线发现器此前先调用`html.encode('utf-8')`再检查1 MB限制；直接传入超大字符串时，会先分配额外编码缓冲区。两处现先按字符数做必然超限的快速拒绝，再保留UTF-8字节数核验，保证多字节输入仍按字节限额处理。
- 新增不会被调用的encode探针回归，证明超限字符数在编码前被拒绝；解析器/发现器定向**206 passed**，完整pytest **656 passed、15 skipped、13 subtests passed**。15项数据库集成因未配置`TEST_DATABASE_URL`跳过，1条既有弃用警告。
- 仅本地合成HTML验证；未访问网站/NAS，P0-03真实准确率和P0-09获准分页样本仍未验证。

## 2026-11-11 P0-08拒绝规范化后指向文件系统根的备份路径
- 复查发现`BACKUP_ROOT=/tmp/..`的原始字符串不等于`/`，但物理路径会规范化到文件系统根，绕过字面路径检查。脚本现检查`cd -P`得到的规范化路径，若为`/`即在任何mkdir/chmod/Docker调用前拒绝。
- 假命令日志回归覆盖`/tmp/..`、项目父目录别名、`.`/`..`和直接根目录；专项通过，完整stdlib测试**37 passed**，完整pytest **656 passed、15 skipped、13 subtests passed**。数据库集成15项因未设置`TEST_DATABASE_URL`跳过。
- 仅临时目录/假命令验证；没有在NAS执行新版脚本。P0-08仍需NAS新鲜备份和隔离恢复复验。

## 2026-11-11 P0-08拒绝规范化后根目录备份别名
- `backup.sh`之前按原始字符串拒绝`/`，但像`/tmp/..`的路径会在`cd -P`后规范化为`/`。现对物理规范化路径增加根目录拒绝，发生在目录创建、chmod和Docker命令前。
- 假命令回归覆盖直接根、`/tmp/..`、当前/父目录及其`..`别名；stdlib组合37 passed，全量pytest656 passed、15 skipped、13 subtests passed。未配置隔离数据库，15项数据库集成跳过。
- 未在NAS执行新版脚本；P0-08仍需新鲜备份和隔离恢复实机验收。

## 2026-11-11 P0-08拒绝备份根路径的符号链接祖先
- `backup.sh`在创建目录前查找最近已存在祖先，以`pwd -L`/`pwd -P`比较逻辑/物理路径；若任一已有目录组件是符号链接则拒绝，覆盖最终备份目录存在与下级路径尚未创建两种情况。
- 假命令日志测试确认拒绝前无mkdir/chmod/Docker；备份脚本8 passed、stdlib37 passed，完整pytest656 passed/15 skipped/13 subtests passed。临时备份路径测试使用物理规范路径，避免macOS`/var`系统别名成为伪阳性。
- 仅本地测试，未在NAS执行新版脚本，P0-08仍需实机备份与隔离恢复复验。

## 2026-11-11 P0-09排除菜单导航中的详情链接
- 离线发现器此前会把 `<menu>` 中指向详情页的导航链接当作挂牌候选；现过滤菜单子树，保留主列表链接。回归先失败后通过，`tests/test_discover_listing_urls.py` **13 passed**。
- 当前完整离线pytest **657 passed、15 skipped、13 subtests passed**；15项数据库集成因未设置`TEST_DATABASE_URL`跳过。标准库测试**37 passed**，`bash -n scripts/backup.sh`及`GOAL_STATE.json` JSON校验通过。
- 用户暂无V0.1备份、获准真实HTML、许可范围或人工标签，已明确要求继续离线开发。本轮未访问网站、未连接/写入NAS、未部署。P0-09仍待真实获准分页样本与自动Worker流程；P0-08仍待NAS新鲜备份及隔离恢复复验。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-09-menu-filter.zip`；打包器已校验ZIP完整性和包内SHA-256清单。

## 2026-11-11 P0-03排除菜单导航内容污染挂牌字段
- 失败回归复现：`<main>`内的`<menu>`包含另一套小区/面积/总价时，解析器把不同来源的字段合并并将社区字段置空。解析前现移除`menu`子树；解析器版本升至`generic-labelled-v0.2.64`。
- 回归先失败后通过，原正文中的挂牌字段保留，菜单字段不再参与候选和冲突判断。完整离线pytest **658 passed、15 skipped、13 subtests passed**；标准库测试**37 passed**。15项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- 仅合成HTML验证，未访问网站/NAS或部署；未进行当前版本的PG16集成回归。P0-03仍依赖每站20份获准真实页面和人工标签，当前准确率未验证。
- 下一步：继续离线核对解析器的语义/可见内容边界；获准样本到位后运行评估器并报告逐来源逐字段精确率/覆盖率；NAS连接可用后复核新版本部署。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-03-menu-parser.zip`；由打包器生成并校验ZIP与包内SHA-256清单。

## 2026-11-11 P0-09拒绝seen-ids符号链接
- 失败回归复现：`read_seen_ids`用`Path.is_file()`检查输入时会跟随符号链接，仍读取链接目标文件。现在打开前明确拒绝符号链接；普通文件限额、UTF-8和来源ID校验保持不变。
- 新增回归先失败后通过；完整离线pytest **659 passed、15 skipped、13 subtests passed**，标准库测试**38 passed**。15项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- 仅临时文件和离线输入验证，未读取NAS/房源网站或部署。P0-09仍需来源许可、真实分页样本和自动Worker流程；P0-03真实页面准确率仍未验证。
- 下一步：继续按P0顺序推进离线分页状态/重试边界；获准页面到位后验证真实分页和解析字段，NAS可连接后复验备份恢复。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-09-seen-id-symlink.zip`；打包器已校验ZIP完整性及包内SHA-256清单。

## 2026-11-11 P0-09拒绝seen-ids符号链接
- 失败回归复现：`read_seen_ids`用`Path.is_file()`检查输入时会跟随符号链接，仍读取链接目标文件。现在打开前明确拒绝符号链接；普通文件限额、UTF-8和来源ID校验保持不变。
- 新增回归先失败后通过；完整离线pytest **659 passed、15 skipped、13 subtests passed**，标准库测试**38 passed**。15项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- 仅临时文件和离线输入验证，未读取NAS/房源网站或部署。P0-09仍需来源许可、真实分页样本和自动Worker流程；P0-03真实页面准确率仍未验证。
- 下一步：继续按P0顺序推进离线分页状态/重试边界；获准页面到位后验证真实分页和解析字段，NAS可连接后复验备份恢复。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-09-seen-id-symlink.zip`；打包器已校验ZIP完整性及包内SHA-256清单。

## 2026-11-11 P0-09 Worker分页发现与候选入队
- `run_collection_target`现区分详情目标与列表目标：列表目标在全局及来源许可门通过后读取已持久化游标，最多抓取5个列表页、20个详情页；只把详情页HTML送入候选解析，保存已见ID/访问页/下页URL。429/来源阻断会记录状态和安全错误类别、禁用目标以停止自动重试；详情失败时回退到失败列表页，超限则保留继续游标。直达详情目标保持原路径。
- mock服务回归覆盖两页推进、详情页入候选、20详情上限、5列表页上限、已访问页详情429重试游标回退，以及全局策略关闭时列表目标零请求。定向`tests/test_collection_service.py` **26 passed**；完整离线pytest **664 passed、16 skipped、13 subtests passed**；标准库测试**38 passed**。
- 本地Docker socket返回permission denied，没有`TEST_DATABASE_URL`；16项数据库集成跳过。mock没有访问网站、PostgreSQL或NAS，也未部署；Worker分页状态写入及迁移006仍待隔离PG验证，真实列表/详情HTML和来源许可仍缺，P0-09调整为in_progress，待隔离数据库和获准样本验收。 已新增`tests/test_db_integration.py::test_worker_paginates_list_targets_and_persists_detail_candidates`覆盖该端到端路径，但本轮因缺TEST_DATABASE_URL跳过，尚无数据库运行证据。
- 下一步：在隔离PostgreSQL `rehouse_test`运行Worker分页状态端到端用例；获准样本和许可到位后核对真实站点分页/详情链接；恢复NAS通道后再验证PG17部署和备份。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-09-worker-pagination.zip`；打包器已校验ZIP完整性及包内SHA-256清单。


## 2026-11-11 P0-08拒绝备份路径父目录遍历
- 失败回归复现：`BACKUP_ROOT=<项目目录>/not-created/..`中间目录缺失时，旧检查未将目标解析为项目根目录，会继续执行Docker归档命令。
- `backup.sh`现于任何目录/权限/容器副作用前拒绝路径中的`..`组件。临时项目目录回归确认明确失败、项目权限不变且中间目录未创建。备份脚本专项**9 passed**，全部标准库测试**39 passed**，完整离线pytest **670 passed、16 skipped、13 subtests passed**；16项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过。`bash -n`及`compileall`通过。
- 仅本机临时目录与假Docker命令验证；未连接NAS、数据库或房源网站，未执行备份/恢复、清理或部署。P0-08仍需NAS当前版新鲜备份和隔离恢复复验。


## 2026-11-11同步目标模式下一轮交接提示
- `prompts/NEXT_ITERATION.md`曾保留过时解析器版本、旧测试结果及与当前GOAL_STATE冲突的目标状态，容易让后续轮次误判完成度。现按GOAL_STATE、项目状态和代码现况重写，列明P0-01至P0-09边界、用户已确认的P2-02规则及不得自行猜测的P0-07/P0-09口径。
- 文档交叉检查确认当前P0状态、`generic-labelled-v0.2.64`、离线pytest **670 passed/16 skipped/13 subtests passed**、真实样本/许可/V0.1备份缺口一致。未改应用代码或业务数据，未连接/写入NAS。


## 2026-11-11 P0-09 Worker分页状态 PostgreSQL 17 隔离集成
- PG17集成首次运行发现新增用例默认允许每轮最多5页，但断言假定首次只处理1页。实现符合批次上限，问题在测试未设边界；现将`MAX_DISCOVERY_PAGES_PER_RUN`在该用例中设为1，明确验证游标跨两轮持久化。
- NAS临时PG17执行`tests/test_db_integration.py`：**17 passed、0 skipped**，其中Worker用例验证两页/两轮、seen IDs、详情候选pending隔离及`collection_runs`成功状态。本机完整pytest：**670 passed、16 skipped、13 subtests passed**；16项数据库用例因未配置`TEST_DATABASE_URL`跳过。
- 测试数据库位于Docker internal网络、tmpfs、无宿主端口和持久卷；应用源码只读挂载，页请求由Mock替代。测试在线许可状态只写入随机临时schema；临时容器/网络/暂存文件清理并复核。没有触碰生产数据库/卷、API/Worker容器或Compose登记，也未访问房源网站。
- P0-09仍依赖获准真实列表/详情页和用户确认的失效阈值；未因此标记完成或部署。


## 2026-11-11 DXP4800只读运行态与代码差异复核
- 经授权`notedock-nas`连接确认主机`DXP4800/sheng`；Compose的API、Worker、PostgreSQL容器均运行，PG17 health状态为`healthy`，API `/healthz`返回200/schema v0.2。
- 只读查询确认Beike为`online_enabled=false/not_authorized`，Anjuke为`online_enabled=false/not_reviewed`；采集运行、候选、挂牌、采集目标行数均为0。`backups/`共有34个文件、占用约1.2MiB。该盘点未校验备份哈希或90天候选，不能视为备份/恢复验收。
- 工作区与生产API容器中的`collection_service.py`、`parser.py`哈希不同；生产容器没有`collectors/discovery.py`和`url_policy.py`。因此此前NAS隔离PG17集成17 passed只验证了只读挂载的当前工作区代码与测试，不代表生产API/Worker已更新。
- 本轮只读，无生产DB/卷/源码/备份变更，未部署或访问房源网站。P0-08新版备份脚本仍待NAS实机备份/恢复；P0-09仍需评估部署差异，但来源许可、真实样本与失效阈值缺口不变。

## 2026-11-11 P0-08当前版NAS备份与隔离PG17恢复
- 按用户确认的90天备份保留、原始页面证据随关联记录保留策略，运行当前工作区`scripts/backup.sh`；NAS新备份：`/volume3/docker/ningbo-re-ai/backups/ningbo-re-ai-20261111T030737Z-3584908`。脚本SHA-256为`5353fc94ce3ae356e1f67c9aba78be46487a24f3542b826061219440a3ddcc43`；`bash -n`通过，备份脚本专项**9 passed**。
- 备份目录权限700、文件权限600；`database.dump` SHA-256=`4555836d9f002dafb1d516f411bf9fea5ca62281dde334983ad332e9f729e46a`，`raw-pages.tar.gz` SHA-256=`edf08bd9e0cdce5c638164daf3e08a376d3089e3c19654c5ec116b6a09daaf8a`。两项校验通过。
- 在Docker `--network none`、tmpfs数据库目录、无宿主端口/挂载的临时PG17容器执行完整`pg_restore`成功；恢复库`source_registry=2`，`collection_runs`、`candidates`、`source_listings`、`collection_targets`均为0；raw-pages归档解压成功。临时恢复容器和脚本已清理。
- P0-08的备份恢复、日志脱敏、内网控制及隔离负载/容量验收均有NAS证据，状态更新为`verified_on_NAS`。该合成容量测试不构成生产SLO；工作区逐路径留存盘点版尚未同步，本轮未盘点90天超期候选、未删除任何文件。
- 未改生产数据库、持久卷、API/Worker容器或Compose登记；未部署工作区代码、未访问房源网站。生产API仍与工作区存在`collection_service.py`/`parser.py`差异并缺`collectors/discovery.py`、`url_policy.py`，因此恢复验证不代表当前工作区代码已部署。新备份为V0.2数据，不能替代P0-01所需真实V0.1备份升级验收。
- 验收文件：`docs/NAS_DEPLOYMENT.md`、`docs/TEST_REPORT.md`、`docs/GOAL_STATE.json`。开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-08-nas-backup-restore.zip`；构建器已校验ZIP完整性及包内SHA-256。

## 2026-11-11 P0-09路线图与隔离PG17证据对齐
- 审阅发现路线图主条目仍称Worker数据库分页集成未运行、持久游标未实现；这与`GOAL_STATE.json`和本文件已有的NAS隔离PG17结果冲突。
- 已更正路线图主条目：`tests/test_db_integration.py`在断网internal网络、tmpfs、无宿主端口/持久卷、只读源码挂载环境为**17 passed、0 skipped**，含两轮Worker游标、seen IDs、详情候选pending和collection_runs持久化。HTTP以Mock替代。
- P0-09仍为`in_progress`：真实来源许可、真实分页HTML/准确性及生产当前工作区代码部署均未完成；失效判定阈值仍待用户确认。仅同步文档，不改代码、数据库、NAS或生产服务。

## 2026-11-11 P0-03限制解析评估CSV清单大小
- 失败边界：`evaluate_parser.py`为保证清单快照一致性直接对manifest执行无界`read_bytes()`，同时评估后还会无界读取路径复核哈希。CSV清单现在限2,000,000字节；初次最多读上限+1，评估后哈希复核也按同一上限流式拒绝增长文件。
- 新增初次超限、恰好2,000,000字节以及评估过程中清单增长三项pytest回归。当前宿主Python 3.9/3.12均没有pytest及项目依赖；`python3 -m pytest -q tests/test_parser_evaluation.py`因`No module named pytest`未运行。尝试uv离线环境时，测试缓存目录访问被系统拒绝。
- 使用标准库隔离模块替身直接验证初始超限拒绝、恰好边界哈希通过及评估后文件增长拒绝：**3 passed**；Python 3.12 `compileall`通过。此验证仅覆盖manifest上限逻辑，不代替完整评估器测试或真实HTML准确率验收。
- P0-03仍等待每站20份获准页面及人工标签；本轮未访问来源、数据库或NAS，未部署。

## 2026-11-11 P0-03锁定评估报告解析器版本
- 评估报告已输出`parser_version`，但端到端评估回归未检查其与解析器当前版本一致。新增断言锁定报告契约，防止解析器升级后评估结果仍携带旧版本。
- `tests/test_parser_evaluation.py` **54 passed**；`tests/test_collection_parser.py tests/test_sample_set.py` **260 passed**；标准库回归 **42 passed**；`python3.12 -m compileall -q app scripts tests`通过。测试通过现有临时Python 3.12环境执行。未运行全量pytest或数据库集成。
- 仅离线测试与状态文档变更；未访问来源网站、NAS或数据库，未部署。真实页面准确率仍未验证；P0-03继续等待获准页面和人工标签。开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-03-parser-version-contract.zip`。


## 2026-11-11 当前工作区全量离线回归
- 使用现有临时Python 3.12环境运行`pytest -q`：**688 passed、16 skipped、13 subtests passed**，保留1条Starlette/httpx弃用警告。16项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- 本次全量运行包含评估报告`parser_version`契约断言，并实际执行合成HTML解析路径；此前的“当前全量pytest未运行/使用BeautifulSoup占位”描述已过时。此结果不包含真实网站页面，真实解析准确率仍未验证。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-03-full-offline-suite.zip`；由项目打包器校验ZIP完整性及包内哈希。未访问来源网站、NAS或数据库，未部署。


## 2026-11-11 P0-07健康率口径与数据来源核查
- 对照`docs/ACCEPTANCE.md`、`collection_runs`表和写入路径后确认：运行状态仅有`success`、`failed`及`blocked_*`；网络请求失败与解析失败共用`failed`，运行记录没有“取得HTML/开始解析/解析成功”阶段标记。
- 因此解析成功率无法由当前运行计数准确计算；需要用户先确认口径，并决定是否增加显式解析阶段计数/状态及数据库迁移。采集成功率中策略阻断是否纳入分母、字段完整必需项和审核通过分母也待确认。本轮未改接口或数据库。
- 已向用户提出建议口径及是否设计离线迁移的问题；答案到达前不以候选行数冒充解析尝试数。其它离线目标可继续推进。


## 2026-11-11 P0-08按完整备份集列报90天留存候选
- 复核发现，原留存报告按文件列候选；数据库转储和raw-pages归档实际同处一个`ningbo-re-ai-...`备份目录，逐文件处理可能留下不完整备份。
- `storage_report.py`现将该脚本生成的命名目录作为一个候选路径，要求目录及其全部普通文件均严格早于保留期限；目录中有任一较新文件时整套不列为候选。旧式散落文件仍逐文件报告。报告只读、不删除。
- 新增混合新旧成员的边界回归，storage-report专项**22 passed**；全量离线pytest **689 passed、16 skipped、13 subtests passed**，16项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。Python 3.12 compileall及GOAL_STATE JSON校验通过。
- 仅本地临时目录验证；新版留存工具未同步/运行于NAS，本轮未盘点或删除备份，也未访问网站、NAS或数据库。P0-08既有NAS备份/恢复证据不代表本工具已部署。


## 2026-11-11 P0-03畸形HTML结构回归
- 以未闭合和错配闭合标签构造3种本地合成页面；解析器仍从明确标签中提取来源ID、小区、面积与挂牌价，并保留`human_review_required`。新增pytest参数化回归。
- `tests/test_collection_parser.py` **200 passed**；全量离线pytest **692 passed、16 skipped、13 subtests passed**。16项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。Python 3.12 compileall通过。
- 仅合成HTML结构验证，不代表真实页面准确率；未访问网站、NAS或数据库，未部署。


## 2026-11-11 P0-03按Decimal精确检查解析数值范围
- 失败回归复现：`20000.000000000000000001㎡`与`200000.000000000000001万`先转float会舍入回合法上限，候选字段错误显示为`20000`/`200000`，虽然已有精度警告会阻止审核就绪。
- `_number_str`现先用Decimal与范围边界精确比较，仅范围内值才转为API所需float；超界值保持null并带缺失/精度告警。解析器版本升至`generic-labelled-v0.2.66`。
- 新回归先失败后通过；解析器/评估器/样本清单专项**318 passed**，全量离线pytest **693 passed、16 skipped、13 subtests passed**。16项数据库集成缺少`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告；Python 3.12 compileall通过。
- 仅合成HTML验证；真实页面准确率未验证，未访问网站、NAS或数据库，未部署。


## 2026-11-11 P0-03补齐精确范围检查下界回归
- 补充下界边界：面积`9.999999999999999999`与总价`0.999999999999999999`经float会分别舍入成合法下限10和1；Decimal范围判断后两字段保持null并保留缺失/精度修正告警。上下界专项**2 passed**。
- 全量离线pytest **694 passed、16 skipped、13 subtests passed**；16项数据库集成缺少`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。Python 3.12 compileall通过。解析器版本保持`generic-labelled-v0.2.66`，因为本次补充测试覆盖同一修复。
- 仅合成HTML验证；真实页面准确率未验证，未访问网站、NAS或数据库，未部署。


## 2026-11-11 P0-03锁定数值范围端点为包含边界
- 新增面积10/20,000㎡及总价1/200,000万元四个精确边界回归（使用两位小数写法）；均被接受、未产生精度警告并保持`ready_for_review=true`。上下界数值专项**6 passed**。
- 全量离线pytest **698 passed、16 skipped、13 subtests passed**；16项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。Python 3.12 compileall通过，解析器版本保持`generic-labelled-v0.2.66`。
- 仅合成HTML验证；真实页面准确率未验证，未访问网站、NAS或数据库，未部署。


## 2026-11-11 P0-09许可撤销后保存已完成详情进度
- 失败回归复现：列表页内第一条详情已成功暂存、第二条请求前策略被撤销时，`blocked_policy`分支原先跳过所有发现状态保存，已完成详情ID未记入持久`seen_ids`。
- 现策略阻断分支在已有详情成功暂存时，仅保存成功ID、当前列表页重试游标及尝试页；不增加失败次数、不记网络错误。下轮从当前列表页重试时会过滤已完成ID。
- 失败回归先失败后通过；策略/分页相关定向**3 passed**，全量离线pytest **699 passed、16 skipped、13 subtests passed**。16项数据库集成缺少`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告；Python 3.12 compileall通过。
- 本轮使用Mock请求/连接离线验证，无SQL迁移、未运行PostgreSQL或NAS测试，未访问来源网站、未部署。


## 2026-11-11 P0-09验证策略恢复后跳过已完成详情请求
- 扩展中途撤销策略回归为两轮流程：第一轮暂存首条详情后返回`blocked_policy`并持久化；第二轮策略恢复后重读相同列表页，过滤已保存seen ID，只请求并暂存未完成详情。
- `tests/test_collection_service.py` **28 passed**；全量离线pytest **699 passed、16 skipped、13 subtests passed**。16项数据库集成因未设置`TEST_DATABASE_URL`跳过；保留1条Starlette/httpx弃用警告。仅Mock，不代表PG/NAS集成。


## 2026-11-11 P0-09策略撤销后的PostgreSQL分页断点回归
- 新增隔离数据库集成用例：一页首个详情成功暂存后，模拟来源策略被撤销；核对已完成ID、当前页重试游标、失败计数和pending候选均真实落库。恢复策略后再次运行，确认跳过已完成详情并继续暂存未完成详情。HTTP仍由mock替代。
- `tests/test_collection_service.py`：**28 passed**。全量pytest：**699 passed、17 skipped、13 subtests passed**；17项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，其中新增断点用例未能运行。标准库测试**42 passed**，Python 3.12 compileall和GOAL_STATE JSON校验通过；保留1条Starlette/httpx弃用警告。
- 用户确认目前没有真实V0.1数据库备份、获准页面样本、许可范围或人工标签，要求继续离线开发。本轮未访问NAS/来源网站/数据库、未部署或迁移；新增数据库集成用例仅编译通过，需以后在专用隔离PostgreSQL `rehouse_test` 中执行。


## 2026-11-11 P0-09许可撤销断点 PostgreSQL 16 及完整套件验证
- 在本机Docker创建临时PostgreSQL 16：数据目录为tmpfs，无持久卷；宿主访问只绑定`127.0.0.1`，工作区此前集成测试中的HTTP由Mock替代。`tests/test_db_integration.py`完整文件 **18 passed**，新增策略撤销断点场景通过：部分详情候选、seen ID、当前页游标和零失败次数落库；许可恢复后跳过已完成详情并继续暂存。
- 配置该临时`rehouse_test`后，全量pytest **716 passed、0 skipped、13 subtests passed**，保留1条Starlette/httpx弃用警告；标准库套件此前**42 passed**，Python 3.12 compileall、JSON与脚本语法检查通过。
- 检查随机集成schema残留数为0。临时PostgreSQL容器、网络和依赖目录均已删除；未连接NAS、来源网站或生产数据库，未部署。该结果验证本机PostgreSQL 16，不替代NAS PostgreSQL 17或生产运行态验收。真实来源页面、许可和失效阈值仍待确认。


## 2026-11-11 P0-02清单诊断过滤样本ID控制字符
- 失败回归确认：`sample_id`中的ESC、CR/LF和C1控制字符会原样进入validator错误消息，可能注入终端控制序列或伪造多行诊断。现在错误标签先转义C0/C1，样本ID含这些字符时拒绝清单；普通可读ID保持原样。不会以此判断授权或改变样本标签含义。
- 三项回归先失败后通过；样本清单/评估专项 **120 passed**。本机临时PostgreSQL 16运行全量pytest **719 passed、0 skipped、13 subtests passed**，保留1条Starlette/httpx弃用警告。
- 随机集成schema残留数0；tmpfs数据库容器已删除。通过Python 3.12 compileall、GOAL_STATE JSON和差异检查。仅离线合成清单验证，真实获准页面和人工标签仍缺；未访问NAS、网站或生产数据库，未部署。


## 2026-11-11 P0-02补齐样本ID与列名诊断边界
- 复查发现首尾换行/Tab会在控制字符检测前被`strip()`吞掉，另外重复/未支持列名也会直接进入validator错误。现在对原始sample_id（裁剪前）检测C0/C1；诊断中的sample_id与列名都先转义控制字符，非控制字符显示习惯保持不变。
- 新增首尾/内部C0/C1及重复/未支持列名回归，共13项控制字符诊断用例通过；样本清单/评估专项 **127 passed**。本机临时PostgreSQL 16全量pytest **726 passed、0 skipped、13 subtests passed**，保留1条Starlette/httpx弃用警告；标准库测试**42 passed**。
- 随机集成schema残留0，PostgreSQL容器及临时依赖已删除。仅离线合成清单验证；真实页面/人工标签/许可仍缺，未访问NAS、来源网站或生产数据库，未部署。


## 2026-11-11 P0-03隔离口播价与挂牌价
- 失败回归确认：页面仅含“口播总价”时，解析器会错误写入`asking_price_wan`；同时出现挂牌价与口播价时，会误报挂牌报价冲突并清空字段。现将口播报价标签从挂牌价候选中排除，兼容“口播总价”“口播挂牌价”及分隔符形式；解析器版本升至`generic-labelled-v0.2.67`。
- 新增两来源回归后，解析器专项 **216 passed**。本机临时PostgreSQL 16上全量pytest **736 passed、0 skipped、13 subtests passed**；标准库测试**42 passed**，保留1条Starlette/httpx弃用警告。
- 随机集成schema残留0，临时数据库/容器/依赖均已清理。仅用合成HTML验证；真实网页结构与准确率仍未验证，未访问NAS、来源网站或生产数据库，未部署。

## 2026-11-11 README与健康率状态同步
- 更新README，加入跨平台挂牌价差候选的已实现边界、面积分母尚待确认说明，迁移范围更新至010；健康率口径逐项按用户确认内容说明。
- README验证摘要同步为当前代码全量离线pytest **734 passed、21 skipped、17 subtests passed**。本轮重跑同样得到734 passed、21 skipped、17 subtests passed；21项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。另有健康率迁移010较早快照的PG16全量结果741 passed、0 skipped（含数据库集成），明确不代表之后代码快照已重跑数据库集成。
- `GOAL_STATE.json`的P0-07口径等待描述以新增确认记录澄清：用户已确认并已实现；仍待NAS PG17及生产代码差异验收。JSON解析、Python 3.12 compileall、`git diff --check`通过。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-readme-health-cross-platform.zip`，由项目打包器校验ZIP完整性及包内SHA-256清单。仅本地文档/状态同步，未访问NAS、来源网站或生产数据库，未部署；在线采集仍关闭。

## 2026-11-11 NAS只读状态复核及解析率历史边界
- 使用用户已授权的`notedock-nas`只读连接；成功会话确认主机`DXP4800/sheng`、账户属于`docker`组，UGREEN登记目录及Compose路径为`/volume3/docker/ningbo-re-ai/docker-compose.yml`。`docker compose ps`显示API与Worker运行、PostgreSQL 17 healthy，API仅绑定`127.0.0.1:8788`。
- SSH复用套接字受本机权限限制；关闭复用后公网DNS曾成功、后续多次间歇性无法解析`300858.xyz`。因此未完成PG查询、`/healthz`或生产代码差异核对；不能证明生产库已应用迁移010。未在NAS写入、传输、备份、启动/停止容器或访问业务数据。
- P0-07数据语义复核：010之前没有逐页面的解析阶段记录，旧`collection_runs`将网络失败与解析失败混在一起，无法可靠反推出历史解析尝试；健康API的解析成功率和字段完整率从迁移010启用后累计。README已明确这一边界，不能把该两项率解释为覆盖迁移前全部历史；采集与审核累计率仍来自现有历史汇总。
- 最新离线全量pytest重跑 **734 passed、21 skipped、17 subtests passed**；21项数据库集成因未配置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`和开发包校验通过。未做DB迁移或部署。开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-health-metric-window-nas-audit.zip`，安全打包器验证包内SHA-256与ZIP完整性。下一步：NAS通道稳定后只读确认生产010和API版本；部署或生产迁移仍须先备份并独立验收。

## 2026-11-11 P0-07 NAS PG17隔离迁移烟雾及生产代码差异
- 通过用户已授权的`notedock-nas`进行运行态只读核验；发现生产PostgreSQL 17.11中`collection_parse_attempts`不存在，生产API `collection_service.py`、`models.py`、`main.py`哈希均与当前工作区不同。生产`/healthz`=200；未认证`/api/collection/health`=401。仅检查元数据和响应码，未读取业务行。
- 当前开发包传输SHA-256核对一致。独立PG17.11测试容器使用`--network none`、512MiB tmpfs、无端口、无持久卷、1 CPU/512MiB；迁移001–010全部成功，重复010成功。插入合成成功/失败解析尝试各1条后汇总为2/1/1（attempt/success/complete）；重跑010后仍为2/1/1。
- 首轮测试脚本在结束时普通NAS用户无法删除Docker属主源码目录，导致脚本退出码1；解析和SQL迁移/计数命令均已成功。随后用一次性`--network none`容器以文件属主清理，确认测试DB容器、临时归档和解压树均不存在。没有生产库、数据卷、容器或Compose变更。开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-pg17-isolation-evidence.zip`，打包器校验包内SHA-256和ZIP完整性。
- 这项烟雾结果验证迁移SQL与触发器可在PG17.11执行；当时完整集成套件尚未运行。后续已在隔离PG17对当前工作区运行完整`tests/test_db_integration.py`，22 passed，详见下节；这不代表工作区API已部署。P0-07继续`in_progress`，生产变更仍需新鲜备份及单独授权评估。


## 2026-11-11 P0-07隔离NAS PostgreSQL 17数据库集成
- 用户授权的`notedock-nas`会话确认主机`DXP4800/sheng`。当前工作区测试包SHA-256与NAS收到文件一致；在NAS运行镜像中以只读挂载源码，在internal Docker网络及tmpfs PostgreSQL 17测试库执行`tests/test_db_integration.py`：**22 passed**，覆盖当前代码的数据库集成，包括P0-07健康率迁移/计数路径。
- 测试库无宿主端口和持久卷；随机集成schema残留为0。自动清理后复核目标容器、网络、临时归档及解压目录均不存在。
- 此次仅写入/清理由本轮创建的临时测试资源；未连接生产数据库作测试、未读取业务行，未修改生产容器、代码、Compose、卷、UGREEN登记或备份，未部署。已知生产库仍缺迁移010且运行代码与工作区不同；P0-07保持`in_progress`，后续需先做新鲜备份并单独评估获授权的API-only部署/生产迁移。


## 2026-11-11 P0-07逐字段完整率回归
- 补齐`source_listing_id`、`community_name`、`asking_price_wan`、`area_sqm`逐项缺失/None时必须判为不完整的回归；文本字段空白也必须判为不完整。应用逻辑未需修改。
- `tests/test_collection_health.py`：**3 passed**；全量离线pytest：**735 passed、21 skipped、17 subtests passed**，21项数据库集成因未配置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。当前数据库集成上一轮在NAS隔离PG17为22 passed。
- 本轮仅测试和文档变更；无迁移、生产数据库/NAS/Compose或来源网站变更，未部署。P0-07仍因生产未迁移/版本未同步而`in_progress`。


## 2026-11-11 P0-07生产schema迁移范围只读确认
- `nas-lan`连接超时、Tailscale CLI偏好读取失败后，使用用户已授权的`notedock-nas`只读确认DXP4800/sheng；API、Worker运行，PostgreSQL 17 healthy，`/volume3`剩余406GB。Compose配置路径为`/volume3/docker/ningbo-re-ai/docker-compose.yml`。
- 仅查询生产`information_schema`：`collection_health_metrics`、`collection_runs`、`collection_targets`、`source_registry`存在；`collection_discovery_states`、`collection_listing_observations`、`collection_listing_reviews`、`collection_parse_attempts`及健康汇总中的3个解析计数列缺失。该表结构说明当前服务处在迁移006之前/不完整状态，部署现工作区API前须核对并准备顺序迁移006–010，不能只应用010。
- 本轮不读业务行或凭据，不创建备份、不运行迁移、不改容器/Compose/数据卷或生产服务。生产升级仍待新鲜备份与单独变更批准；P0-07保持`in_progress`。


## 2026-11-11 P0-07隔离PG17模拟生产基线升级
- 经用户授权的`notedock-nas`在NAS内部Docker网络及tmpfs PostgreSQL 17运行纯合成演练：应用001–005，插入代表性source listing、collection target/run/candidate和saved search，再按顺序运行006–010并重复一次。
- 迁移后旧挂牌/候选/运行/条件单关键值保留，迁移默认字段正确；discovery state、sweep columns、observation/review及parse attempt均可用。解析触发器汇总为2次尝试、1次成功、1次四字段完整，重复迁移后仍为2/1/1。
- 测试容器无宿主端口、无持久卷，网络为internal；所有数据均为本轮合成数据。自动清理并复核容器、网络、归档、解压目录均不存在。未读取生产业务行、未创建备份或修改生产schema/容器/Compose/数据卷，未部署。该演练不代替V0.1真实备份或生产恢复验收。

## 2026-11-11 P2-02面积差分母确认
- 用户确认面积差公式后核对`app/services.py`确以`abs(a-b)/min(a,b)`判定，机会定向测试 **21 passed**；无需改业务逻辑。
- 用户确认面积差≤5%使用较小挂牌面积作分母，即`abs(a-b)/min(a,b)≤0.05`；现有实现与用户口径一致，无应用代码变更。

## 2026-11-11 P0-03嵌套折叠details单次文本提取
- 失败回归复现：80层嵌套关闭`details`让摘要文本重复提取81次、累计重建13,541字符。现将关闭details折叠并入隐藏文本后序遍历；外层关闭块统一提取摘要，已折叠内层不再重复处理。开放details内的关闭子块仍保留摘要并排除折叠正文。
- 新增深层嵌套、开放details中的关闭子块和遍历计数回归；同一合成场景降至1次摘要提取、重建237字符。解析器版本`generic-labelled-v0.2.112`。collection parser/service **341 passed**；全量离线pytest **820 passed、22 skipped、23 subtests passed**。22项数据库集成因未配置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包构建/manifest/ZIP完整性验证通过。仅合成HTML离线验证，未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标签；P0-01真实V0.1备份与P0-02样本/许可/标签仍缺。
- 下一轮继续P0-03在1 MB HTML上限内审计DOM/文本处理的重复遍历，以可重复的节点/字符计数回归验收；数据材料到位后再做真实页面评估。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-details-summary-performance.zip`（122个源码文件，打包器与独立manifest校验通过）。

## 2026-11-11 P0-03消除样式表检查的重复祖先遍历
- 复杂度回归复现：样式表可见性检查对每个`style`/`link`调用`find_parent`排除`template`/`noscript`；80层递增嵌套的80个`link rel="preload"`标签都不会触发告警，却会逐个搜索祖先直到扫描结束。现沿已有DOM顺序扫描并记录惰性子树节点，单次确定当前节点是否位于`template`/`noscript`，不再逐个向上遍历；活动样式表和模板/`noscript`语义保持不变。解析器版本保持`generic-labelled-v0.2.112`。
- 新增80层/80个`link rel="preload"`回归，禁止样式审查调用`find_parent`；解析器测试 **312 passed**，全量离线pytest **821 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未配置`TEST_DATABASE_URL`跳过。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包manifest/ZIP校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面解析准确率仍待获准样本与人工标签。
- 下一轮继续检查1 MB HTML上限内可明确计数的DOM/文本重复遍历；先添加回归，再实施最小优化并跑定向与全量离线测试。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-stylesheet-depth-scan.zip`（源码打包器与包内SHA-256清单校验通过）。

## 2026-11-11 P0-03合并房源身份与Open Graph标题头部扫描
- 复杂度回归复现：同一`<head>`为canonical链接、`og:url`和`og:title`分别遍历3次。现合并为一次DOM顺序扫描，实时校验canonical/`og:url`房源ID并统计全部提及，分别保留最多20条来源证据以维持原证据顺序；`og:title`只保存最多两个不同非空值供歧义判断，标题来源优先级不变。解析器版本保持`generic-labelled-v0.2.112`。
- 100个无关meta标签及canonical、`og:url`、`og:title`合成回归确认head后代仅遍历1次、标题与来源ID正确、ID提及数为3；解析器测试 **313 passed**，全量离线pytest **822 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未配置`TEST_DATABASE_URL`跳过。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包manifest/ZIP校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面解析准确率仍待获准样本与人工标签。
- 下一轮审计1 MB HTML上限内重复H1候选文本展开，使用重复等值的深层H1回归确定工作上限，再按最小改动优化；保留标题歧义及回退语义。

## 2026-11-11 P0-03避免等值嵌套H1重复展开子树
- 复杂度回归复现：80层嵌套H1只在最内层含标题文本，所有标题候选归一化后相同；旧逻辑仍对80个H1各自完整展开后代。现跳过仅含空白文本/注释和一个直接嵌套H1的冗余包装层，最内层标题仍参与候选；含自有文本或多个子标题的H1继续按原逻辑提取，歧义与回退契约不变。解析器版本保持`generic-labelled-v0.2.112`。
- 新回归确认80层等值结构的H1文本提取由80次降至1次，标题值不变且不产生伪歧义；不同标题冲突回归继续通过。解析器测试 **314 passed**，全量离线pytest **823 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包manifest/ZIP校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面解析准确率仍待获准样本与人工标签。
- 下一轮检查等值H1之间存在无文本透明格式节点时是否还有重复子树提取；先用节点访问计数验证具体复杂度，再保持歧义处理契约做有证据支持的最小改动。

## 2026-11-11 P0-03沿透明格式节点消除嵌套H1重复提取
- 复杂度回归复现：等值嵌套H1之间增加`span`后，上一轮仅识别直接H1包装的优化不生效，80层仍提取80次。现沿唯一非空子节点链识别连续H1包装，只跳过到下一个H1为止未包含其他文字/分支的冗余标题；拥有自身文字或多分支内容的候选继续提取，标题歧义和document-title回退保持。
- 80层`h1 > span > h1`等值标题回归确认文本提取由80次降至1次；不同标题冲突并回退到document title的测试通过。解析器测试 **314 passed**，全量离线pytest **823 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包manifest/ZIP校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。解析器版本保持`generic-labelled-v0.2.112`，真实页面准确率仍待获准样本与人工标签。
- 下一轮继续审计1 MB输入上限内DOM文本复杂度，优先覆盖分支标题、隐藏子树和证据节点组合；只有节点计数回归证明重复工作时才调整。

## 2026-11-11 P0-03忽略空图标节点以保持H1标题链线性
- 回归边界补充：`h1 > i.icon(empty) > span > h1`中的空图标节点会让单链判断误判为分支；80层输入再次触发80次标题子树提取。现在在沿标题链扫描时忽略无内容或仅含空白/注释的直接子节点，不递归展开这些节点；含可见文字或多个有内容分支的标题不跳过。
- 80层嵌套、每层含空图标和span的等值H1仍只提取1次；标题内容和冲突回退保持。解析器测试 **314 passed**，全量离线pytest **823 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包manifest/ZIP校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。解析器版本保持`generic-labelled-v0.2.112`。
- 下一轮继续审计1 MB页面中分支H1标题的重复文本展开，以节点计数确认任何优化不会吞掉标题冲突或回退证据。

## 2026-11-11 P0-03复用可见文本节点集识别H1空分支
- 复杂度回归复现：每层H1旁有`i.icon > span(empty)`装饰子树，标题链浅层检查会把空装饰误判为分支，80层等值标题再次提取80次。现复用内联可见性后序扫描已计算的textful节点ID，空/隐藏分支不再阻断唯一标题链；该扫描也继续完整判定未解析可见性。H1文本提取恢复为1次，含可见文字的分支仍保留。
- 合成回归覆盖80层`h1 > i.icon > span(empty)`与标题span链，确认标题值不变、提取1次；解析器测试 **314 passed**，全量离线pytest **823 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包manifest/ZIP校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。解析器版本保持`generic-labelled-v0.2.112`。
- 下一轮针对有可见文本的分支标题检查提取短路上限；必须保留歧义告警与document-title回退，只有确定性计数回归证实重复展开才改动。

## 2026-11-11 P0-03锁定分支H1冲突后的提取短路
- 80层H1各含不同的可见标题文本，形成有内容分支；现有唯一值判定在出现第二个不同标题后停止继续展开。新增明确的H1文本提取计数断言，确认只提取2次，并同时锁定`ambiguous_title_source:h1`及document-title回退。未发现需修改的生产逻辑。
- 解析器测试 **314 passed**，全量离线pytest **823 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未配置`TEST_DATABASE_URL`跳过。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包manifest/ZIP校验通过。本轮为回归测试与文档变更；未访问来源网站、NAS或生产数据库，无迁移/部署。解析器版本保持`generic-labelled-v0.2.112`。
- 下一轮测量`_remove_inline_invisible_text`中同一内联style字符串被多次解析的规模，先用重复声明计数回归确认是否存在可避免的工作。

## 2026-11-11 P0-03合并节点内联CSS多属性读取
- 重复工作回归复现：同一span的`style`串（display、visibility、opacity、content-visibility及普通声明）在节点过滤、文本可见性处理、未解析可见性判定和文本布局阶段触发 **16次单属性解析调用**。新增`_inline_css_values`单遍解析请求属性集合；节点过滤一次读取display，文本清理一次读取visibility/opacity/content-visibility，可见性审查一次读取全部检查属性。重复/无效声明、级联与`!important`规则沿用原单属性解析器语义。
- 同一页面的CSS声明扫描回归由 **16次**降至 **5次**，挂牌价与审核结果保持；解析器测试 **315 passed**，全量离线pytest **824 passed、22 skipped、23 subtests passed**，保留1条Starlette/httpx弃用警告。22项数据库集成因未配置`TEST_DATABASE_URL`跳过。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包manifest/ZIP校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。解析器版本保持`generic-labelled-v0.2.112`。
- 下一轮判断同一style跨阶段剩余5次解析是否值得用parse-scope缓存合并；以相同计数回归验证收益，并避免全局/跨请求缓存。

## 2026-11-11 P0-09当前工作区 PostgreSQL 17 集成续验
- NAS `DXP4800/sheng` 上的隔离测试库再次执行完整 `tests/test_db_integration.py`：**23 passed**，含分页上限、策略撤销后的跨轮续跑、已发现 ID 去重、扫轮状态和迁移/API回归。测试前后的临时数据库仅有 `public` schema，测试通过后无残留 schema。
- NAS SSHD 对端配置 `AllowTcpForwarding no`，SSH隧道请求被明确拒绝；未修改SSH配置。改为在现有 `ningbo-re-ai-api` 镜像中启动一次性测试运行器，将当前工作区源码只读挂载，并与临时 PostgreSQL 17 接入本轮 Docker internal 网络。数据库目录使用512 MiB tmpfs，无持久卷、无宿主端口，测试请求均由 Mock 替代。
- 测试容器、internal 网络、临时运行器和NAS暂存文件均已清理。复查生产 `ningbo-re-ai-db-1` 为healthy，API/Worker仍运行，生产卷 `ningbo-re-ai_pgdata` 未改变。未写生产数据库、未改生产服务/Compose、未部署，未访问房源网站。
- 这验证的是只读挂载的当前工作区与 NAS PostgreSQL 17 的集成兼容性，不代表工作区代码已部署。P0-09保持 `in_progress`；真实来源许可、获准列表/详情页面和生产版本差异验收仍未完成。

## 2026-11-12 P0-03合并同一样式跨阶段的属性解析
- 现有回归将`_inline_css_values`调用次数误当作声明扫描次数。用`_scan_inline_css_values`重新计数后，同一带`display`、`visibility`、`opacity`和`content-visibility`的span样式在一次页面解析中实际扫描3次。新增断言先失败（3次），再把单次解析缓存改为按原始style缓存全部受审属性的结果；同一样式按不同属性请求时复用同一解析结果。缓存仍仅限单次解析、保留1024项上限及FIFO淘汰。
- 解析器专项 **319 passed**；全量离线pytest **832 passed、22 skipped、23 subtests passed**，22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。编译、GOAL_STATE JSON、差异与开发包校验通过。
- 合成微基准30次取中位数：300种唯一style页面，旧行为13.25ms/约901次声明扫描，新行为9.41ms/约301次；300个重复style页面6.13ms对6.16ms，整体近似持平。结果仅用于合成输入的实现比较，不代表真实页面或生产性能。
- 仅处理本地合成HTML；未访问网站、NAS或数据库，无迁移/部署。P0-03仍待每站20份获准页面及人工标签进行真实性能和准确率评估。
- 下一轮继续P0-03有计数证据的离线DOM/文本遍历审查；先用回归复现真实重复工作，再决定是否需要最小优化。真实页面材料到位后转入标注集评估。

## 2026-11-12 P0-03惰性选择最高证据内容根
- `_parse_generic_listing_html`此前先运行`find(main)`、`find(article)`和内容类`select_one`，再把所有重叠候选根分别完整文本化后评分。计数回归确认嵌套main/article/.content且字段齐全时执行3次根查询和3次文本化。现在按原顺序惰性查找候选；一旦当前候选命中小区、面积、总价全部3项最高分即停止。分数未满时继续搜索；同分仍保留先出现的外层根。
- 回归先失败后通过：满分main路径现在只查询/文本化main；外层信号不足时仍检查article并选择更强证据。解析器专项 **320 passed**，全量离线pytest **833 passed、22 skipped、23 subtests passed**；22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`和开发包校验通过。仅合成HTML/Mock验证；未访问来源网站、NAS或生产数据库，无迁移/部署。P0-03仍待每站20份获准页面与人工标签验证真实页面准确率。
- 下一轮继续P0-03以节点/文本计数定位重复DOM工作；发现具体可复现问题后再做小幅优化，真实样本到位后转入标注集评估。

## 2026-11-12 P0-03优化候选根搜索与折叠摘要空白裁剪
- 候选内容根现按证据分数惰性搜索：外层`main`若具备小区、面积、总价全部信号则不再查询/文本化重叠的`article`和`.content`；未满分时继续搜索，维持同分先选外层根。计数回归覆盖停止与继续两条路径。
- `_text_with_inline_boundaries`对折叠`details`摘要曾逐项`pop(0)`移除前置空白片段，合成测量显示节点数翻倍时耗时明显超比例增长。现以索引定位前置空白段，再一次切片删除；4,000/8,000/16,000/32,000节点中位数由旧版约5.46/12.03/29.52/94.16ms降为4.80/9.83/19.77/40.20ms。计数单测确认0次头部pop和1次批量删除，摘要结果保持。
- 解析器专项 **321 passed**；全量离线pytest **834 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`和开发包校验通过。
- 仅合成HTML/离线验证，未访问来源网站、NAS或生产数据库，无迁移/部署。计时不代表真实页面性能；P0-03仍需每站20份获准页面与人工标签核验准确率。
- 下一轮继续P0-03计数驱动的DOM/文本遍历审查；真实页面材料到位后按标注集评估。

## 2026-11-12 P0-03避免选中候选文本二次空白归一化
- 计数回归先失败：完整`main`候选正文在评分后被再次执行同一`re.sub(r'\s+', ...)`，唯一候选文本归一化2次。选中候选时复用已归一化文本，仅在回退到body时做归一化；字段结果不变。
- 解析器专项 **322 passed**；全量离线pytest **835 passed、22 skipped、23 subtests passed**，22项数据库集成因未设置`TEST_DATABASE_URL`跳过；保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON及差异空白检查通过，开发包已重建并校验。只使用合成HTML；未访问网站、NAS或生产数据库，无迁移/部署。真实准确率与性能仍需每站20份获准样本和人工标签。
- 用户再次确认P2-02面积差按较小挂牌面积作分母；现有`abs(a-b)/min(a,b)≤5%`实现符合口径，无需业务改动。
- 下一轮继续P0-03计数驱动审查，优先检查有内容分支标题或字段证据上限附近的重复文本工作。

## 2026-11-12 P0-03候选根评分与字段提取使用同一字符窗口
- 失败回归复现：40,000字符前置导航文本位于`main`，房源字段在其后的`article`；旧评分查看完整候选，因后段字段让`main`先得满分，随后字段提取截断前35,000字符，导致三个关键字段均为空。现仅以字段实际可见的前35,000字符给候选根评分，后续`article`凭其窗口内完整字段胜出。
- 回归先失败后通过；候选根专项 **4 passed**；全量离线pytest **836 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 评分与截断共用`MAX_VISIBLE_TEXT_CHARS=35_000`，避免两处边界常量漂移。解析器专项 **323 passed**；全量离线pytest **836 passed、22 skipped、23 subtests passed**。解析器保持`generic-labelled-v0.2.113`。Python 3.12 compileall、GOAL_STATE JSON、空白检查和开发包校验通过。仅用合成HTML；未访问网站、NAS或生产数据库，无迁移/部署。P0-03真实准确率仍待每站20份获准页面和人工标签。
- 下一轮继续审查有界输入下的解析准确性与重复工作，优先复核长前缀截断/候选评分组合；真实样本到位后转入标注评估。

## 2026-11-12 P0-03锁定可见文本上限的包含边界
- 增加35,000字符精确边界回归：恰好达到上限时保留字段且不告警；仅多1字符时保留窗口内字段、增加`visible_text_truncated`并令`ready_for_review=false`。
- 两项边界回归通过；解析器专项 **325 passed**；全量离线pytest **838 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 未改业务逻辑，仅锁定评分/截断/审核边界语义。Python 3.12 compileall、GOAL_STATE JSON、空白检查和源码包校验通过。仅合成HTML验证；未访问网站、NAS或生产数据库，无迁移/部署。真实样本和人工标签仍缺。
- 下一轮继续P0-03审查截断点两侧的字段标签、证据引用和解析器评估场景。

## 2026-11-12 P0-03验证截断后的字段证据范围
- 加强35,000字符截断回归：窗口后的第二个报价不计入`mention_count`、不生成`multiple_price_mentions`；保留窗口内的365万证据，`end_char`不越界，同时`visible_text_truncated`仍阻止审核就绪。精确上限用例也检查社区/面积/总价证据偏移均不超过窗口。
- 定向截断/上限回归 **3 passed**；解析器专项 **325 passed**；全量离线pytest **838 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 本轮只加强合成HTML回归断言，没有业务逻辑变更；未访问网站、NAS或生产数据库，无迁移/部署。真实页面与人工标签仍缺。
- 下一轮继续检查采样评估器如何区分截断导致的不可见冲突和真实缺失字段，避免漏扫样本被误记为通过。

## 2026-11-12 P0-03核对评估器的截断场景判分
- 审查`scripts/evaluate_parser.py`确认：`missing_fields`场景要求无`visible_text_truncated`；`multiple_prices`要求完整候选提及、未截断证据且与人工候选价格集合完全相等；相近的歧义候选与来源ID场景也有截断失败回归。评估器已有防漏扫误通过保护，本轮无需重复改业务逻辑。
- 本轮新增解析器断言锁定窗口外价格不进入证据计数、窗口内offset不越界；解析器325 passed，全量离线pytest838 passed/22 skipped/23 subtests。
- 下一轮检查候选根信号评分面对混合/歧义字段时的选择边界，保持不确定字段留空和人工复核原则。

## 2026-11-12 P0-03锁定混合候选根的冲突留空
- 新增合成回归：外层`main`同时含推荐卡与详情`article`，两处小区/面积/总价值不一致；解析结果将三字段留空并输出对应多值告警，不因缩小到子树而消除同页冲突。
- 该行为符合精确率优先、覆盖率另报的验收口径；未改根选择逻辑。解析器专项 **326 passed**；全量离线pytest **839 passed、22 skipped、23 subtests passed**。22项数据库集成未配置`TEST_DATABASE_URL`，保留1条Starlette/httpx弃用警告。
- 仅增加合成HTML回归，未访问网站、NAS或生产数据库，无迁移/部署。真实页面仍待每站20份授权样本和人工标签。
- 下一轮评估根信号评分与字段歧义在更多有标注合成场景下的精确率/覆盖率取舍；在线采集保持关闭。

## 2026-11-12 P0-03跨语义根字段拼接诊断
- 用合成HTML确认：推荐卡仅提供小区名、详情`article`仅提供面积和总价时，当前解析器会跨兄弟区域组合三个值，并返回`ready_for_review=true`。页面标题/面包屑也可能合法提供小区，因此是否禁止跨根合并需要明确的产品口径；问题已向用户提出，不擅自改变代码。
- 独立性能探针在约800 KB页面上测得`main`与重叠`article`分别完整归一化约800 KB文本，随后选择27字符的`.content`；15次解析中位数约29.92 ms。该合成结果只说明重复归一化工作量，不代表真实页面性能。
- 本轮无应用代码修改、未运行完整测试；未访问网站、NAS或生产数据库。

## 2026-11-12 P0-03复用候选根的有界归一化文本
- 新增`_normalize_text_prefix`：文本按与`re.sub(r'\s+', ' ', ...)`等价的规则归一化，只保留前`MAX_VISIBLE_TEXT_CHARS`字符并返回准确的截断状态。候选根评分和最终字段提取复用同一前缀，避免每个重叠根完整分配归一化后的长字符串；根选择规则及输出字段范围不变。
- 六项边界回归覆盖空串/零上限、空白折叠及截断；另以固定种子对10,000组Unicode空白输入对照完整`re.sub`结果与截断标志，全部一致。解析器专项 **332 passed**；全量离线pytest **845 passed、22 skipped、23 subtests passed**。数据库集成22项因未设置`TEST_DATABASE_URL`跳过。
- 800,144字节重叠main/article合成页，40次交替比较：有界归一化中位数24.80 ms、P90 24.93 ms；完整归一化中位数29.69 ms、P90 29.87 ms，中位数低16.5%。tracemalloc峰值中位数3.86 MiB，对照5.39 MiB。仅为合成实现基准，不代表真实站点。
- Python 3.12 compileall、GOAL_STATE JSON、空白检查和开发包校验通过。未访问网站、NAS或生产数据库，无迁移/部署。跨根是否允许合并社区名的策略仍待用户确认，本优化不改变该行为。

## 2026-11-12 P0-03复核有界归一化的多种DOM输入表现
- 同进程交替基准每类30次：500,098字节/大量短span节点，中位181.88 ms（有界）对182.27 ms（完整归一化，−0.2%）；780,098字节/长空白，中位5.28 ms对5.26 ms（+0.5%）；300,098字节/重复段落，中位112.36 ms对112.46 ms（−0.1%）。P90差异均小，未见有意义的回退；长连续文本的16.5%中位改善和峰值内存下降另见前节。
- 所有输入均为本地合成HTML；页面大小受1 MB输入上限约束，测时包含DOM解析，不能代表真实站点或生产SLO。本轮仅做对照测量，无代码变更、未重跑全量测试。跨根字段合并策略仍待用户确认。
- 下一轮维持简单的有界归一化实现，继续验证语义等价和截断边界；不据合成性能推断真实站点指标。

## 2026-11-12 P0-03检查分段文本下的归一化峰值内存
- 对照完整`re.sub`各5次：450,098字节/30,000个短span token页面，有界方法峰值中位34.79 MiB、完整归一化34.50 MiB（+0.29 MiB）；380,098字节/20,000个短段落页面，24.54 MiB对24.40 MiB（+0.14 MiB）。均在测量噪声/小幅开销范围；说明显著内存节省集中于长连续文本，分段页面收益有限。
- 两种输入均为本地合成页面，tracemalloc包含BeautifulSoup DOM等开销，不能视为真实页面内存SLO。本轮无代码修改、未重跑测试。
- 下一轮保持有界实现的简洁性；若真实获准页面可用，再按真实DOM分布复核耗时与内存。跨根字段合并口径仍待用户确认。

## 2026-11-12 P0-03覆盖body文本回退的有界截断语义
- 增加无`main/article/.content`时body回退用例：窗口内小区/面积/365万正常提取；窗口后的900万不计入提及数或多价告警；`visible_text_truncated`仍存在、证据偏移不越过35,000字符且审核就绪为false。
- 新回归通过；解析器专项 **333 passed**；全量离线pytest **846 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 未改解析器逻辑，只补回退分支验证。Python 3.12 compileall、GOAL_STATE JSON、空白检查和开发包校验通过。本地合成HTML；未访问网站、NAS或生产数据库，无迁移/部署。
- 跨根字段合并口径仍待用户确认；有界归一化继续保持现有输出语义。

## 2026-11-12 P0-03固定Unicode差分回归有界归一化
- 将之前的临时10,000组Unicode空白差分核验固化为pytest固定种子用例（1,000组，覆盖中文、ASCII、TAB/CR/LF、不换行空格、全角空格、行分隔符、BOM及零宽空格），逐项与完整`re.sub(r'\s+', ' ', text)`输出前缀和截断标志比较。
- 解析器专项 **334 passed**；全量离线pytest **847 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 仅测试变更；有界归一化实现和跨根字段策略均未变。Python 3.12 compileall、GOAL_STATE JSON、空白检查和开发包校验通过。
# 2026-11-12 P0-04官方协议时点复核同步
- 贝壳官方协议页标示2026-11-11更新、2026-11-12生效；其第七条第二、三款继续要求书面许可，限制自动化抓取，并要求授权使用遵守许可范围与Robots。安居客官方协议中心可读到消费者/经营者协议目录与历史版本入口，但未取得正文；经营者协议不替代消费者协议，已知官方静态PDF无法确认与当前版本对应。
- 网页工具无法读取项目实际目标主机`nb.ke.com/robots.txt`和`ningbo.anjuke.com/robots.txt`。2026-11-10 NAS只读结果（贝壳项目UA详情路径禁止、安居客示例路径允许）只作历史快照，不推断当前规则。两站无本项目书面许可，来源及全局在线采集保持OFF；未访问房源页、未采集或绕过限制。P0-04继续`in_progress`。
- 更新来源政策复核、路线图、目标状态及变更记录；仅文档同步，无应用代码、数据库、NAS或部署变化。验收仍需正式用途许可、确认安居客适用协议并在获准后读取当前目标Robots。来源和证据边界见`docs/SOURCE_POLICY_REVIEW_2026-11-10.md`。
- `GOAL_STATE.json`解析、5份相关文档尾随空白检查（0项问题）及`git diff --check`通过；`scripts/package_dev.py`生成124文件开发包，ZIP完整性与逐文件SHA-256校验通过。

## 2026-11-12 P0-03字段证据窗口边界一致性
- 候选根文本窗口边界回归现在还断言字段证据偏移切片与独立`quote`完全一致，且候选值可在原文片段中定位；不改变候选根选择或跨语义区域合并行为。
- 精确边界用例2 passed；解析器专项340 passed；全量离线pytest 855 passed、26 skipped、25 subtests passed，26项PostgreSQL集成因未配置`TEST_DATABASE_URL`而跳过；有1条既有Starlette/httpx弃用警告。
- 仅测试断言变更；未访问来源网站、NAS或生产数据库，无迁移/部署。用户已确认同套面积差按较小面积为分母；社区名与详情字段跨语义根合并策略仍待确认，现有行为保持不变。

## 2026-11-12 P2-02公开面积差分母
- API跨平台候选说明补充面积差公式`abs(a-b)/min(a,b)`，明确使用较小挂牌面积作分母，和用户确认的业务口径及`app/services.py`实现一致；未改机会算法。
- `tests/test_opportunities.py` **21 passed**，包含较大/较小面积两种方向和5%边界；未运行数据库集成测试。
- 仅更新契约与状态文档，无应用代码、数据库、NAS或部署变化。

## 2026-11-12 P0-08留存与备份保护当前工作区复验
- 基于当前源码重跑`tests/test_storage_report.py`与`tests/test_backup_script_stdlib.py`，**31 passed**；标准库证据完整性组合`python3.12 -m unittest discover -s tests -p 'test_storage_report_stdlib.py' -v`为**4 passed**。覆盖90天边界、备份集路径与权限/软链接保护、证据gzip大小/哈希校验及错误传播。
- 仅使用本机合成临时目录；未读取NAS实际库存、未上传/运行当前工作区版本、未清理任何文件。P0-08既有NAS备份恢复验收仍是历史部署证据；留存报告逐路径版尚未在NAS复验。

## 2026-11-12 P0-08 NAS只读留存库存复核
- 按NAS技能先试`nas-lan`（超时），Tailscale CLI提示无法读取偏好且本机未安装Tailscale App；随后使用已授权的`notedock-nas`，确认身份`DXP4800/sheng`。
- NAS现有`storage_report.py` SHA-256为`54b39480b8b2a2f6b3f45b19ede649c5ba1f8e29c033bd4253c1db4727f648ac`，工作区版本为`5668942a72c493bc81591afdcadc5a586378001b65ce8a0af9eee897d8b21b1b`，版本不一致。NAS旧版留存函数只读返回90天外备份候选0个/0字节；当前backups库存37文件、1,123,531字节，最早/最新文件修改时间分别为2026-11-09 13:38:21Z、2026-11-11 03:07:37Z。
- 宿主SSH用户直接盘点raw-pages遇到权限拒绝；通过现有API容器的只读挂载统计为2个普通文件/249字节，无符号链接。未读取页面正文或数据库业务行，没有上传/运行工作区脚本、改权限、清理文件、迁移、改Compose/卷/服务或部署。NAS运行的是旧报告版本；本轮结果不能视为工作区逐路径版已部署/验收。

## 2026-11-12 P0-03候选根评分拒绝越界数值信号
- 先添加兄弟`main`/`article`复现：`main`含小区名但面积5㎡、总价0万时，旧评分仅按标签匹配选中它，导致后续有效`article`被忽略。
- 候选根的面积/总价信号现在要求首个匹配值落在解析器支持范围（面积10–20,000㎡、总价1–200,000万）才计分；社区名、面积、总价最终仍全部来自同一个选中根。已有同根多值冲突仍保留并阻止审核。解析器版本更新至`generic-labelled-v0.2.114`。
- 新回归先失败后通过；候选根和外层冲突保护定向3 passed，解析器专项**341 passed**，全量离线pytest **856 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因无`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、文档空白检查、`git diff --check`及开发包校验通过。仅离线合成HTML；未访问来源网站、NAS或生产数据库，无迁移/部署。真实标注页面仍缺，跨语义根字段合并策略仍待用户确认。

## 2026-11-12 P0-03拒绝范围形式的面积和挂牌价
- 补充离线回归覆盖`120㎡-130㎡`、`300万-320万`，以及带两个端点单位的形式；区间的第一个端点原本可能被当成单一挂牌面积/总价。解析字段现在拒绝带范围后缀的值，保持缺失并等待人工核验。
- 解析器升至`generic-labelled-v0.2.115`。使用已存在的`/private/tmp/ningbo-re-ai-test-venv`运行新增回归 **2 passed**、解析器专项 **343 passed**、全量离线pytest **858 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过，另有1条Starlette/httpx弃用警告。Python 3.12编译及标准库正则边界检查通过。
- 未访问房源网站、NAS或生产数据库，无迁移/部署。此边界只验证合成HTML规则，不代表真实页面准确率；获准真实样本仍缺，跨语义根合并策略继续保持待确认。

## 2026-11-12 P0-03核验多值冲突证据偏移
- 审查面积、挂牌价、小区和可选字段冲突处理：字段值与`field_evidence.value`均引用同一最终解析结果；冲突值留空，原始命中、总数及截断标志分开保留。现有边界回归已覆盖20条证据上限后的冲突与千次重复提及。
- 新增长页面冲突证据回归，确认摘录截断后字段值/证据仍为`null`，且每条quote可用完整可见文本偏移还原；该用例及相关冲突回归 **5 passed**，解析器 **344 passed**，全量离线pytest **859 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过，1条Starlette/httpx弃用警告。
- 是否让可选字段冲突也阻止`ready_for_review`尚待用户确认；收到答复前保留现有口径。无生产代码行为变化、迁移或部署；未访问房源网站、NAS或生产数据库。
- 另加待审核候选重提持久化断言，确认写入参数中的小区/面积/总价证据值与字段相同且保留原始quote；collection service专项与解析器合并 **377 passed**，全量离线pytest保持 **859 passed、26 skipped、25 subtests passed**。

## 2026-11-12 P0-03同步区间数值API说明
- `docs/API.md`明确面积/挂牌价区间不提取端点；该字段无其他单值命中时保持为空并给出`missing_*`警告，区间原文留在关联页面证据中。
- 仅对齐公开API说明与解析器v0.2.115及其现有区间回归；无运行代码变化、迁移、来源访问、NAS核验或部署。此前解析器/全量测试基线为344 passed和859 passed/26 skipped/25 subtests。

## 2026-11-12 P0-03覆盖数值范围分隔符边界
- 补充回归覆盖解析器拒绝的10种面积/总价范围分隔符（ASCII/Unicode横线、波浪线及“至/到”），并验证分隔符后接楼层/装修标签时合法单值仍会解析。
- 新增边界定向 **13 passed**；解析器 **355 passed**；全量离线pytest **870 passed、26 skipped、25 subtests passed**。26项数据库集成因未配置`TEST_DATABASE_URL`跳过，1条Starlette/httpx弃用警告。解析器版本保持v0.2.115，无运行逻辑修改。
- 用户尚未确认可选字段冲突对`ready_for_review`的影响；现有口径保持不变。未访问来源网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-03区间与单值同现时保留歧义证据
- 失败回归复现：`120㎡-130㎡`后再出现`125㎡`时解析器旧版会静默采用125；挂牌总价范围与一个挂牌单价亦同样漏掉区间。现将面积/价格区间作为完整证据mention记录，并与同字段单值一起触发`multiple_*_mentions`，字段留空；仅区间时还保留`missing_*`告警。
- 解析器升至`generic-labelled-v0.2.116`。范围及冲突定向 **15 passed**，解析器 **357 passed**，候选保存定向 **1 passed**，全量离线pytest **873 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过，1条Starlette/httpx弃用警告。
- 原始范围quote偏移和字段证据写入均有回归。未访问来源网站、NAS或生产数据库，无迁移/部署；真实获准样本仍缺，可选字段冲突是否阻止`ready_for_review`继续待确认。
- 补充区间证据上限回归：30个重复范围完整计数、只返回20条且截断标志为真；解析器 **358 passed**，全量离线pytest **874 passed、26 skipped、25 subtests passed**。
- 新增API路由回归，确认提交页面的响应返回完整范围/单值冲突证据及`multiple_area_mentions`，且`ready_for_review=false`；该API测试 **1 passed**，全量离线pytest更新为 **875 passed、26 skipped、25 subtests passed**。

## 2026-11-12 P0-03候选根评分忽略歧义信号
- 失败回归复现：兄弟`main`含“小区：导航推荐”、面积范围`120-130㎡`与单值`125㎡`、总价365万时，旧评分将其当作满分并遮蔽清晰的兄弟`article`（东湖花园、120㎡、300万）。
- 候选根评分现在仅把唯一社区、唯一且有效的面积/总价单值作为信号；出现区间、多值或越界值时不因该字段加分。为保持既有语义根边界，外层`main`包含`article`且自身已具备完整字段线索时仍保留外层根；对截断窗口未覆盖线索的情形仍可检查`article`。
- 新增合成回归先失败后通过；候选根/外层冲突定向 **5 passed**。解析器升至`generic-labelled-v0.2.117`。解析器专项 **359 passed**；全量离线pytest **876 passed、26 skipped、25 subtests passed**。26项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本与人工标签；可选字段冲突对审核就绪状态及跨语义根合并策略仍保持待确认口径。
- Python 3.12 compileall、GOAL_STATE JSON解析、`git diff --check`通过；开发包由`package_dev.py`校验器生成并验证包内manifest/ZIP完整性，SHA-256以最终构建结果为准。下一轮优先：①继续P0-03离线解析边界；验收为新增合成回归与全套通过；②获准真实样本到位后评估贝壳/安居客解析准确率；验收为每站20份合规样本及人工标签。

## 2026-11-12 P0-03候选根按规范化值判定歧义
- 新增失败回归：解析器将`1,234㎡`与`1234.0㎡`、`1,234万`与`1234.00万`视为等值，但候选根旧评分按匹配次数误判为多值，导致选中字段不完整的兄弟根。评分现按文本规范化键/Decimal数值键判断不同值，并继续扫描至发现真实冲突；完整等值重复不会降分，等值重复后出现第三个不同值仍能识别冲突。
- 回归先失败后通过；候选根/外层保护/单次扫描约束定向 **8 passed**，解析器专项 **361 passed**，全量离线pytest **878 passed、26 skipped、25 subtests passed**。26项数据库集成因未设置`TEST_DATABASE_URL`跳过，1条Starlette/httpx弃用警告。解析器升至`generic-labelled-v0.2.118`。
- 重复报价场景现由候选评分和证据记录各执行一次有界文本匹配扫描；范围、越界值、不同值冲突仍不作为确定性评分信号。仅合成HTML离线验证，未访问来源网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-03样本校验与评估支持数值范围证据
- 失败回归确认：解析器已把`120㎡-130㎡`、`300万-320万`作为完整歧义mention保存，但样本校验器只接收纯数字候选，评估器也无法将范围mention与人工标注对账。
- 校验器现在允许面积/挂牌价范围作为一个证据候选，要求两端均为合法有限数值、符合字段范围和解析器支持单位/分隔符；`multiple_areas`及`multiple_prices`仍须至少两个不同的证据候选，单个范围不会被拆为两个端点。评估器按Decimal端点元组比对范围候选。范围分隔符常量由解析器和样本校验器共享，避免支持集合漂移；未新增清单列。
- 面积/价格范围校验与评估失败回归先失败后通过；样本校验器+评估器 **139 passed**，解析器 **361 passed**，全量离线pytest **885 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，1条Starlette/httpx弃用警告。
- 仅合成HTML/临时样本验证；无迁移、在线采集、来源网站访问、NAS/生产数据库访问或部署。获准真实样本仍缺；本改动使将来真实范围样本可被清单标注并纳入候选证据评估。

## 2026-11-12 P0-03拒绝窗口末尾未完成范围的首端点
- 失败回归复现：可见文本上限恰好截在`120㎡-`或`300万-`后，第二端点在未扫描尾部；单值正则旧版因此把范围首端点当作挂牌面积/价格。
- 面积和挂牌价单值匹配现也排除“范围分隔符后只有空白并到达当前文本末尾”的情况。完整范围识别/证据、其他有效字段及文本上限行为不变；截断仍有`visible_text_truncated`并阻止审核就绪。
- 10种范围分隔符×面积/价格回归 **20 passed**；解析器专项 **381 passed**，全量离线pytest **905 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过，1条Starlette/httpx弃用警告。解析器升至`generic-labelled-v0.2.119`。
- Python 3.12 compileall、GOAL_STATE JSON解析、`git diff --check`及开发包验证通过。仅合成HTML离线验证；无来源/NAS/生产数据库访问、迁移或部署，真实获准样本仍缺。

## 2026-11-12 P0-03评估单独范围字段证据
- 上轮范围候选评估只覆盖“范围+单值”的多值场景；单独范围时虽应字段留空并保留一条完整range mention，但没有专属样本标签，未来数据无法直接量化这项规则。
- 增加可选场景标签`area_ranges`、`price_ranges`，分别复用`area_candidates_sqm`、`price_candidates_wan`现有列，无CSV列变化。每个场景要求至少一个有效完整范围候选，并核验字段留空、对应告警和完整未截断候选集合；可与`multiple_areas`/`multiple_prices`并用以覆盖范围和单值共存。
- 样本校验器/评估器 **144 passed**，解析器专项 **381 passed**，全量离线pytest **910 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未设`TEST_DATABASE_URL`跳过，1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON解析及`git diff --check`通过。只用合成HTML/临时样本，未访问来源网站、NAS或生产数据库，无迁移/部署；P0-02获准真实样本仍缺。

## 2026-11-12 P0-03范围场景拒绝截断证据
- 补充回归覆盖`area_ranges`/`price_ranges`超过20条重复命中、候选集合仍相同但证据被截断的情况；两种场景都判未通过，避免不完整证据被当成范围验证成功。
- 截断专属用例 **2 passed**；样本校验器/评估器专项 **146 passed**；全量离线pytest **912 passed、26 skipped、25 subtests passed**。26项数据库集成因未配置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 仅增加评估回归，解析器/样本schema、数据库及部署未变；仅合成HTML临时样本验证。

## 2026-11-12 P0-03核验独立价格范围评估路径
- 新增`price_ranges`不依赖`multiple_prices`的端到端评估回归：单个挂牌价范围保持单一候选，字段留空且范围证据匹配时通过。
- 单项回归 **1 passed**；样本校验器/评估器专项 **147 passed**，全量离线pytest **913 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 仅合成HTML临时样本验证，无API、schema、数据库或部署变更。
- 运行时兼容性边界：本机未安装Python 3.11，`uv python list --only-installed`因无法读取受限的`/Users/sven/.cache/uv`而未能列出解释器；本轮只在Python 3.12.13运行测试，Python 3.11兼容性未验证。


## 2026-11-12 P0-03当前离线解析器基线复验
- 本轮以工作区已有Python 3.12虚拟环境运行全量离线pytest：**913 passed、26 skipped、25 subtests passed**；26项PostgreSQL集成测试因未设置`TEST_DATABASE_URL`跳过，保留1条既有Starlette/httpx弃用警告。系统Python未安装pytest，未联网安装依赖。
- Python 3.12 `compileall`、`GOAL_STATE.json`解析和`git diff --check`通过。重建source-only开发包，124个文件；ZIP完整性及包内SHA-256清单校验通过。
- 本轮只复验已有离线基线并刷新开发包，无应用逻辑、数据库、配置变化；未访问来源网站、NAS或生产数据库，无部署。P0-03仍需每站20份获准真实页面与人工标注，合成测试不代表真实准确率。下一轮继续P0-03离线边界审查；待样本到位后运行标注评估。


## 2026-11-12 P0-03拒绝中文数字范围的单端点误报
- 新增回归复现：`建筑面积：120㎡-一百三十㎡`和`总价：300万-三百二十万`的范围端点未被现有阿拉伯数字规则识别，解析器会错误地把首端点写成单值。现在单值规则在范围分隔符后遇到常见中文数字起始符时也拒绝提升首端点；尚不支持中文数字范围解析，因此保留空字段并要求人工复核。解析器版本升至`generic-labelled-v0.2.120`。
- 新增回归先失败后通过；范围/截断/字段边界定向 **35 passed**，解析器专项 **383 passed**，全量离线pytest **915 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。既有“分隔符后接楼层/装修标签”回归仍通过。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包校验通过。仅使用合成HTML，未访问来源网站、NAS或生产数据库；无迁移、配置变化或部署。真实页面准确率仍待获准样本和人工标签。下一轮继续P0-03离线解析边界审查；材料到位后验收每站20份并分别报告字段准确率/覆盖率。


## 2026-11-12 P0-03修正冒号连接的修饰价格误判
- 新增多平台回归复现：`口播:总价：300万`、`成交:总价：300万`及`折后:挂牌价：300万`原会被当作另一个挂牌价，造成字段误报或与明确挂牌价冲突。负向前缀现在覆盖冒号和冒号后空格；保留已有无冒号、空格和中文冒号行为。解析器版本升至`generic-labelled-v0.2.121`。
- 连同上一步中文数字范围保护，解析器专项 **391 passed**，全量离线pytest **924 passed、26 skipped、25 subtests passed**；26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。价格语境专项50 passed；新增评估器回归确认口播冒号价不被计为挂牌价，missing_fields场景通过；相关代码回归先失败再通过。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包校验通过。仅合成HTML验证，无数据库/配置迁移；未访问来源网站、NAS或生产数据库，无部署。P0-03仍待每站20份获准真实页面与人工标注。下一轮继续离线解析准确性边界，样本到位后按来源报告字段准确率与覆盖率。


## 2026-11-12 P0-03阻止修饰复合标签的挂牌价后缀匹配
- 新增失败回归发现：`口播 挂牌总价`、`成交 出售总价`、`折后 挂牌总价`被前缀规则拒绝后，正则仍可退回匹配复合标签里的末尾`总价`，错误地产生第二条挂牌价格证据并将真实挂牌价置空。现`总价`标签要求前面不是`挂牌`或`出售`，完整标签仍按原逻辑处理。解析器版本升至`generic-labelled-v0.2.122`。
- 跨来源解析器相关回归 **54 passed**；评估器合成样本回归 **1 passed**；解析器专项 **397 passed**；全量离线pytest **930 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包校验通过。仅合成HTML验证；无数据库/配置迁移，未访问来源网站、NAS或生产数据库，无部署。P0-03真实准确率仍待获准样本及人工标注。


## 2026-11-12 P0-03挂牌价标签正向回归
- 为复合价格标签后缀保护补充正向回归：贝壳、安居客均验证`总价`、`挂牌总价`、`挂牌价`、`出售总价`可正常提取365万，且字段证据唯一。跨来源标签定向 **58 passed**，解析器专项 **405 passed**，全量离线pytest **938 passed、26 skipped、25 subtests passed**。26项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`和124文件开发包校验通过。仅增加测试，无应用逻辑、数据库或配置变更；未访问来源网站、NAS或生产数据库，无部署。解析器仍为`generic-labelled-v0.2.122`。真实页面准确率仍待每站20份获准页面及人工标注。


## 2026-11-12 P0-03价格修饰语组合矩阵回归
- 将价格修饰语与复合标签的边界核验固化为组合回归：14种非挂牌前缀×6种分隔形式×4种挂牌价格标签×贝壳/安居客两来源，共 **672种输入**；每种都要求真实挂牌价365万保持、排除修饰价且不出现`multiple_price_mentions`。矩阵测试 **2 passed**；解析器专项 **407 passed**。
- 全量离线pytest **940 passed、26 skipped、25 subtests passed**；26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`和开发包校验通过。
- 仅测试变更，解析器版本保持`generic-labelled-v0.2.122`；无数据库、配置、来源网站、NAS或生产数据库操作，无部署。真实获准样本仍缺。


## 2026-11-12 P0-03挂牌价别名评估正向回归
- 样本评估器新增`挂牌总价`、`挂牌价`、`出售总价`三种有效标签的合成清单评估回归，验证每种都将人工标注400万正确计入字段准确率与精确率。评估器专项 **69 passed**。此前新增的14前缀×6分隔×4标签×两来源（672组合）矩阵也通过。
- 解析器专项 **407 passed**，全量离线pytest **943 passed、26 skipped、25 subtests passed**；26项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`与开发包校验通过。仅测试/记录变更，无应用逻辑、数据库、配置变更；未访问来源网站、NAS或生产数据库，无部署。解析器版本保持`generic-labelled-v0.2.122`。


## 2026-11-12 P0-03隔离交易总价
- 失败回归复现`交易总价：300万`原被识别成挂牌价，并可与明确挂牌价构成虚假冲突。现把`交易`加入非挂牌价格语境；单独交易总价保持挂牌价字段为空，与挂牌价并列时只保留真实挂牌价。解析器升至`generic-labelled-v0.2.123`。
- 自动组合矩阵覆盖15种非挂牌前缀×6种分隔形式×4种价格标签×贝壳/安居客两来源，共 **720种输入**；矩阵定向 **2 passed**。评估器单独交易价/口播复合价缺失场景均通过；评估器专项 **67 passed**，解析器专项 **411 passed**，全量离线pytest **948 passed、26 skipped、25 subtests passed**。26项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证，无数据库/配置变化；未访问来源网站、NAS或生产数据库，无部署。真实页面准确率仍待每站20份获准页面及人工标注。


## 2026-11-12 P0-03等待不完整范围尾段口径
- 已向用户询问`120㎡-未知`/`300万-未知`应按不完整范围保守留空，还是将首值视为单值并把短横线后文本视为说明。两种解释会影响覆盖率与误报风险，未擅自改变当前解析行为；等待用户选择。与该决策无关的交易价隔离、价格组合矩阵及别名评估已完成并通过本轮验证。

## 2026-11-12 P0-03排除合同与签约总价
- 新增回归发现`合同总价`、`签约总价`可能被当作挂牌价；现将`合同`、`签约`加入非挂牌价格语境，单独出现不填挂牌价，与挂牌价并列时保留真实挂牌价。解析器升至`generic-labelled-v0.2.124`。
- 价格语境定向 **66 passed**；全量离线pytest **956 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。Python 3.12 compileall、GOAL_STATE JSON解析和`git diff --check`通过。
- 仅合成HTML离线验证，无数据库/配置变更；未访问来源网站、NAS或生产数据库，无部署。真实页面准确率仍待每站20份获准页面及人工标注。

## 2026-11-12 P0-03评估器覆盖合同与签约价格缺失场景
- 扩展评估器`missing_fields`回归，加入“合同总价”“签约总价”页面，验证标注的挂牌价为空时解析器不填值，且缺字段场景仍通过。评估器定向 **69 passed**；全量离线pytest **958 passed、26 skipped、25 subtests passed**。
- 26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，保留1条既有Starlette/httpx弃用警告。仅合成HTML测试与记录更新，无应用逻辑、数据库或配置变更；未访问来源网站、NAS或生产数据库，无部署。

## 2026-11-12 P0-03跨来源评估非挂牌价格缺失场景
- `missing_fields`评估回归扩展到贝壳和安居客两来源，各覆盖口播复合挂牌价、交易总价、合同总价、签约总价四种输入；两来源均确认不填挂牌价且缺字段场景通过。定向 **8 passed**，评估器文件 **73 passed**。
- 全量离线pytest **962 passed、26 skipped、25 subtests passed**；26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，保留1条既有Starlette/httpx弃用警告。仅合成HTML验证，无应用逻辑、数据库或配置变更；未访问网站、NAS或生产数据库，无部署。
- 校正最新价格语境组合矩阵规模：当前测试列出17种前缀×6种分隔×4种标签×2来源，共 **816** 种输入。先前记录的720种对应加入“合同/签约”前的15种前缀组合，作为历史结果保留。

## 2026-11-12 P0-03 API核验合同与签约价证据边界
- 增加API端到端离线回归，覆盖贝壳/安居客的合同总价、签约总价页面。确认挂牌价为空、出现`missing_asking_price_wan`、候选保持pending且`ready_for_review=false`；完整原文按SHA-256内容寻址压缩保留，若落在前1,000字符内也会进入`evidence_excerpt`。首次测试指出排除价格不应伪造挂牌价`field_evidence`命中，测试已按现有证据契约修正。
- API定向 **8 passed**；全量离线pytest **966 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，保留1条既有Starlette/httpx弃用警告。Python 3.12编译、GOAL_STATE JSON及空白检查通过。
- API说明同步字段证据边界；本轮无应用逻辑、数据库迁移或配置变更，仅合成HTML/API mock验证。未访问来源网站、NAS或生产数据库，无部署。

## 2026-11-12 P0-03旧版本待审核候选按新解析器重算
- 扩展重复提交回归：模拟`generic-labelled-v0.2.123`曾把“合同总价300万”存为挂牌价的pending候选；同一页面再次提交后，服务层必须使用当前解析器版本重算，将挂牌价清空并追加`missing_asking_price_wan`，同时保持`ready_for_review=false`。
- 服务层定向 **34 passed**；全量离线pytest **966 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过；本轮使用mock验证应用更新路径，未验证真实PG冲突更新运行时行为。
- 仅测试和状态/变更记录更新；无应用逻辑、数据库迁移或配置变化。未访问来源网站、NAS或生产数据库，无部署。

## 2026-11-12 P0-03添加真实PostgreSQL旧候选修复回归
- 扩展数据库集成用例：先将待审核候选版本设为旧解析器，并人为写入错误挂牌价300万；重复上传只含`合同总价300万`的同一页面后，核验真实冲突更新应采用当前解析器、清空挂牌价、添加`missing_asking_price_wan`并保留pending状态。
- 服务层mock回归 **34 passed**；新增PG集成用例因本机未配置`TEST_DATABASE_URL`而定向 **1 skipped**，故真实PostgreSQL执行尚未验证。全量离线pytest **966 passed、26 skipped、25 subtests passed**；数据库跳过项均未在本机运行。
- Python 3.12 `py_compile`通过；仅测试和状态/变更记录更新，无应用逻辑、数据库迁移或配置变化。未访问来源网站、NAS或生产数据库，无部署。

## 2026-11-12 P0-03保护人工修正不被旧版候选重算覆盖
- 新增服务层mock回归：旧解析器pending候选包含人工修正的挂牌价315万；重新提交只含`合同总价300万`的同一页面时，当前解析结果虽然挂牌价为空，但数据库冲突更新因`manually_corrected`标记被阻止，读取到的人工值315万与旧解析器版本均保持。与旧错价自动重算用例一起定向 **2 passed**。
- `tests/test_collection_service.py` **35 passed**；全量离线pytest **967 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，其中新增的冲突更新/人工修正PG用例尚未运行。
- Python 3.12编译、GOAL_STATE JSON及空白检查通过。仅测试与记录更新，无应用逻辑、数据库迁移或配置变化；未访问来源网站、NAS或生产数据库，无部署。

## 2026-11-12 P0-03按价格类型评估挂牌价隔离
- 样本清单增加可选`oral_prices`和`transaction_prices`标签，不扩展CSV列；空挂牌价可由类型场景解释。评估器按来源报告场景样本数/通过数/通过率：无明确挂牌价时要求预测为空、存在`missing_asking_price_wan`且无价格冲突/文本截断；有挂牌价时要求精确匹配人工真值并无冲突/截断。
- 新增场景回归覆盖贝壳/安居客口播总价、交易总价、合同总价、签约总价。样本校验器 **87 passed**、评估器 **81 passed**；全量离线pytest **977 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON及变更文件空白检查通过。仅合成HTML/临时清单验证；未取得真实许可样本，不代表真实准确率。无数据库/配置迁移，未访问来源网站、NAS或生产数据库，无部署。

## 2026-11-12 P0-03为价格类型场景补充正向挂牌价共存评估
- 扩展`oral_prices`/`transaction_prices`评估回归：除场景只有口播或交易金额、挂牌价应缺失外，也覆盖明确挂牌价与口播/合同金额并存；要求挂牌价按人工真值保留、不因非挂牌金额产生冲突。口播/交易/合同等场景跨来源定向 **12 passed**，评估器 **85 passed**。
- 全量离线pytest **981 passed、26 skipped、25 subtests passed**；26项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过，保留1条既有Starlette/httpx弃用警告。Python 3.12编译、目标JSON和变更文件空白检查通过。
- 仅合成HTML和临时清单验证；未取得真实许可样本，不能据此声明真实准确率。无数据库/配置迁移，未访问来源网站、NAS或生产数据库，无部署。

## 2026-11-12 P0-03固定价格类型场景报告顺序
- `oral_prices`与`transaction_prices`改为固定声明顺序，避免从集合展开导致CLI/API JSON场景键顺序在不同Python进程间漂移；新增顺序契约回归。
- 样本校验器 **87 passed**、评估器 **86 passed**，合计 **173 passed**；全量离线pytest **982 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12编译、目标JSON及变更文件空白检查通过。仅离线测试/文档；无数据库或配置变化、无来源/NAS/生产数据库访问与部署。

## 2026-11-12 P0-03反向验证价格类型指标能检出误归类
- 新增两项评估器变异回归：人为令解析结果把“口播总价”或“合同总价”300万填入挂牌价；`oral_prices`/`transaction_prices`场景通过率必须降为0，证明指标能发现价格类型污染。
- 反向场景定向 **2 passed**；评估器 **88 passed**、样本校验器 **87 passed**，合计 **175 passed**。全量离线pytest **984 passed、26 skipped、25 subtests passed**；26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，保留1条既有Starlette/httpx弃用警告。
- Python 3.12编译、目标JSON及变更文件空白检查通过。仅合成HTML/临时清单验证；无真实许可样本、数据库或配置迁移，未访问来源网站、NAS或生产数据库，无部署。

## 2026-11-12 P0-03锁定零样本价格场景的空通过率
- 为贝壳与安居客的`oral_prices`、`transaction_prices`各增加一项无样本回归，明确报告`samples=0`、`passed=0`且`pass_rate_pct=null`，避免空场景被误读为100%通过或获得虚假准确率。
- 评估器 **92 passed**；全量离线pytest **988 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，保留1条既有Starlette/httpx弃用警告。Python 3.12 compileall、GOAL_STATE JSON解析及`git diff --check`通过。
- `scripts/package_dev.py`生成并校验124个源码/文档文件的开发包：`../ningbo-re-ai-v0.2-dev-2026-11-12-p0-03-zero-scenario-rates.zip`；ZIP完整性及包内SHA-256清单通过。
- 仅合成HTML/临时清单验证；未访问房源网站、NAS或生产数据库，无迁移、配置变化或部署。获准真实页面与人工标签仍缺，真实解析准确率未验收。
- 下一轮优先：①继续P0-03的离线解析评估边界审查，新增可复现失败回归并运行全量套件；②待获准页面与标注到位后，按每站20份验收字段精确率/覆盖率。

## 2026-11-12 P0-03拒绝连接词后的非挂牌价格
- 发现“口播的总价”“合同中的挂牌价”“交易中的总价”“签约里的出售总价”会被解析成挂牌价；若与挂牌价并存还会误报价格冲突。新增两来源、单独出现/与挂牌价并存的回归，修改前16项全部复现失败。
- 非挂牌语境现覆盖限定词后的“的/中/中的/里/里的”连接形式，保留明确挂牌价；解析器升至`generic-labelled-v0.2.125`。评估器同步覆盖新价型。解析器专项 **435 passed**、评估器 **100 passed**；全量离线pytest **1012 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON解析和`git diff --check`通过。仅合成HTML与临时评估清单；未访问来源网站、NAS或生产数据库，无数据库/配置迁移或部署。真实获准样本与人工标注仍缺。
- 已生成并校验124文件开发包：`../ningbo-re-ai-v0.2-dev-2026-11-12-p0-03-linked-price-context.zip`；ZIP及包内SHA-256清单完整。
- 下一轮继续P0-03语义边界检查并以失败回归驱动；获准样本到位后按每站20份验收精确率与覆盖率。

## 2026-11-12 P0-03处理空白分隔的非挂牌价格语境
- 发现“口播 的 总价”“合同 中 的 挂牌价”等可见文本形式仍会误填挂牌价；两来源16项回归失败。HTML相邻节点会在可见文本中插入空白，属于同一价格语义边界。
- 将连接词语境检查改为候选价格前32字符的有界上下文判定，覆盖空格分隔及连接词内部空白；同一检查用于单价与范围证据，确保范围金额不会出现在挂牌价证据中。保留现有直接前缀规则，解析器升至`generic-labelled-v0.2.126`。新价语境解析回归40 passed；解析器文件 **459 passed**、评估器 **108 passed**；全量离线pytest **1044 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON解析和`git diff --check`通过。仅合成HTML/临时清单验证；真实获准样本仍缺，未访问网站、NAS或生产数据库，无数据库/配置迁移或部署。
- 已生成并校验124文件开发包：`../ningbo-re-ai-v0.2-dev-2026-11-12-p0-03-spaced-price-context.zip`；ZIP完整性和包内SHA-256清单通过。
- 下一轮继续P0-03离线语义边界检查；真实精确率/覆盖率验收仍依赖每站20份获准页面与人工标注。

## 2026-11-12 P0-03评估空白连接词后的价格范围
- 评估器新增贝壳/安居客 `oral_prices` 与 `transaction_prices` 范围场景，确认“口播 的 总价：300万-320万”“合同 中 的 挂牌价”等完整范围被排除出挂牌价证据后，场景应通过。
- 新增评估回归 **8 passed**；评估器文件 **116 passed**，解析器文件 **459 passed**；全量离线pytest **1052 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 已生成并校验124文件开发包：`../ningbo-re-ai-v0.2-dev-2026-11-12-p0-03-spaced-price-evaluation.zip`；ZIP及包内SHA-256清单通过。
- 仅合成HTML/临时清单验证；无应用逻辑、数据库或配置变化，无网站/NAS/生产数据库访问或部署。真实获准页面及标注仍缺。
- 下一轮继续P0-03离线边界审查；达到真实准确率验收仍需每站20份获准页面和人工标签。
## 2026-11-12 P0-03候选根评分挂牌价语义回归
- 新增兄弟根回归：`main`只有小区、面积及“合同总价”，`article`含小区、面积及明确“挂牌价”；确认合同价不提供挂牌价根评分信号，解析器选中并保留320万挂牌价。
- 定向测试 **1 passed**；全量离线pytest **1061 passed、26 skipped、27 subtests passed**。26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 仅测试变更，无应用逻辑、数据库或配置变化；未访问来源网站、NAS或生产数据库，无迁移/部署。P0-03真实准确率仍需每站20份获准页面与人工标签。

## 2026-11-12 P0-03评分后续已知类内容根
- 失败回归复现：文档前部`.houseInfo`仅有“推荐阅读”时，旧逻辑没有评分后续含完整小区/面积/挂牌价的`.content`根。现对三个已知类选择器各取首个节点参与既有评分，仍选一个根解析，不跨根合并字段；解析器升至`generic-labelled-v0.2.127`。
- 根选择定向 **5 passed**，解析器专项 **464 passed**；全量离线pytest **1065 passed、26 skipped、27 subtests passed**。26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python编译、GOAL_STATE JSON及`git diff --check`通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无数据库迁移/部署。真实准确率仍待每站20份获准页面与人工标签。

## 2026-11-12 P0-04官方来源协议复核
- 贝壳官方协议页现标示2026-11-11更新、2026-11-12生效；继续限制未经书面许可的数据获取/自动化抓取，并要求许可使用遵守范围及Robots。安居客官方协议中心呈现消费者/经营者协议目录和历史版本入口，但未解析出当前消费者协议正文。
- 网页工具无法读取实际目标及主站Robots正文；NAS只读复核在公网别名DNS解析阶段失败，robots请求未发出。2026-11-10 NAS Robots结果只作为历史快照，不推断当前规则。
- 两站无本项目书面许可，来源/全局在线采集保持OFF；未访问房源页、未采集或绕过限制。政策证据见`docs/SOURCE_POLICY_REVIEW_2026-11-12.md`。

## 2026-11-12 P0-09补充详情队列PG级联回归
- 新增数据库集成回归：插入带`attempt_count=2`和`last_error_type=TimeoutError`的详情队列项，确认失败元数据可读取；删除关联挂牌观察后确认队列因`ON DELETE CASCADE`消失。
- 定向回归因未配置`TEST_DATABASE_URL`而 **1 skipped**，真实PostgreSQL级联仍未验证。全量离线pytest **1065 passed、27 skipped、27 subtests passed**；27项均需数据库，保留1条Starlette/httpx弃用警告。
- 本轮仅增加集成测试；未改应用逻辑、数据库或配置，未访问来源网站/NAS/生产数据库，无迁移/部署。需要获准的隔离PG17环境才能完成实际执行。

## 2026-11-12 P0-09本机PostgreSQL替代路径复核
- 尝试在临时目录初始化本机PostgreSQL 16，以便评估无需后台daemon的单用户数据库验证；`initdb`在bootstrap阶段即因System V `shmget`共享内存限制失败，未建立数据库。initdb清理了数据文件，本轮生成的临时目录也已删除；未执行任何迁移。
- 全量pytest **1065 passed、27 skipped、27 subtests passed**；27项均因未设置`TEST_DATABASE_URL`跳过，包含详情队列级联回归。保留1条Starlette/httpx弃用警告。
- 迁移014真实PostgreSQL执行仍待隔离PG17环境；NAS源码传输/临时容器授权尚未得到答复。本轮未访问来源网站、NAS或生产数据库，无部署。

## 2026-11-12 P0-03候选根排除连接式合同挂牌价
- 失败回归复现：候选 `.houseInfo` 中的“合同中的挂牌价”被根评分当作挂牌价信号，导致评分提前停止，漏掉后续 `.content` 的真实挂牌价；贝壳、安居客两项回归在修复前均失败。
- 候选根评分与字段抽取现在使用相同的连接式非挂牌语境排除规则；解析器升至 `generic-labelled-v0.2.128`。解析器专项 **466 passed**，全量离线pytest **1067 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12离线验证，无数据库/配置/迁移变化；未访问来源网站、NAS或生产数据库，无部署。P0-03真实准确率仍需两站各20份获准页面与人工标签；P0-09迁移014数据库执行仍未验证。
- 下一轮优先：①取得隔离PG17执行授权后验证迁移014、重放幂等及级联回归；②继续P0-03合成边界审查，真实样本到位后按字段报告精确率与覆盖率。

## 2026-11-12 P0-03检查全部同类候选内容根
- 失败回归复现：当第一个 `.content` 只有“推荐阅读”、后续同类 `.content` 才包含完整挂牌信息时，旧逻辑只检查同类选择器首节点并漏掉房源字段；贝壳、安居客两项回归均失败。
- 现按文档顺序评分所有 `.houseInfo`、`.house-info`、`.content` 候选根；仍在首个满分根停止、同分保留先出现者，且不跨根拼接字段。解析器升至 `generic-labelled-v0.2.129`。候选根定向 **15 passed**，解析器专项 **468 passed**，全量离线pytest **1069 passed、27 skipped、27 subtests passed**。
- NAS只读复核确认`notedock-nas`可连接至`DXP4800/sheng`，Docker可用且本地有`postgres:17-alpine`镜像；没有`rehouse-test`容器。本轮未创建容器、上传文件或写入NAS。隔离PG17测试需用户明确批准此前未覆盖的源码传输和远端临时写入。
- Python 3.12编译、目标JSON与差异检查通过；未访问来源网站、未改生产服务/Compose/卷/数据库，无迁移或部署。真实解析准确率仍待每站20份获准页面与人工标注。

## 2026-11-12 P0-03保护嵌套候选根冲突并限制重复遍历
- 同类兄弟根仍需评分，但嵌套已知类根的文本已完整包含于最外层候选中。新增两站回归：外层与内层挂牌价冲突时，解析器必须保留`multiple_price_mentions`并拒绝审核就绪，不能只选内层价格。旧逻辑两项失败。
- 候选类根现惰性扫描；若某个`.houseInfo`、`.house-info`或`.content`根嵌套于另一个此类根中，则不重复独立评分，外层按可见文本保留所有冲突。40层嵌套回归确认仅一次候选文本遍历；10000层/270012字节离线探针耗时约0.072秒（仅为本机合成探针，不代表生产SLO）。解析器升至 `generic-labelled-v0.2.130`。
- nested-root定向 **2 passed**，候选根定向 **17 passed**，解析器专项 **470 passed**，全量离线pytest **1071 passed、27 skipped、27 subtests passed**。27项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、GOAL_STATE JSON及空白检查通过。NAS远端临时测试授权仍未收到；未上传文件或创建容器，未访问来源网站或生产数据库，无迁移/部署。真实准确率仍依赖每站20份获准页面与人工标签。

## 2026-11-12 P0-03复现article与嵌套content的价格冲突口径
- 本地合成页面在外层`article`标注挂牌价300万、嵌套`.content`标注320万时，当前两站解析结果均选择320万，未输出`multiple_price_mentions`。这是因article与class候选根分别评分后选更高分内层根。
- 此行为涉及跨语义根字段/冲突策略的既有待答产品问题；已询问是否保留外层冲突并转人工审核，或优先更具体内层根。答复前不改变解析行为，也不将合成页面结果解释为真实页面准确率。
- 本轮仅复现并记录，无代码/迁移/配置变更；无来源网站、NAS或生产数据库访问/写入，无部署。P0-03仍待各站20份获准页面与人工标签，P0-09隔离PG17远端临时写入授权仍未收到。

## 2026-11-12 P0-04经NAS只读复核两来源Robots
- 按NAS SSH技能核对用户已授权别名 `notedock-nas`，成功确认为 `DXP4800/sheng`，通过NAS直接读取两个实际目标主机的`/robots.txt`，请求带代码中一致的UA，禁止重定向，单响应读取上限65,537字节；未访问房源页、未采集、未写NAS文件。
- 贝壳robots HTTP 200、6,676字节、SHA-256 `9827f8cc4f79a95288af23e411231ebab135230bb1e1d972c6dfaf46cb9d2db9`，示例详情路径`/ershoufang/109900001234.html`被RobotFileParser拒绝。安居客HTTP 200、372字节、SHA-256 `6815680c898027ffb858525efa7c7fe99c6aa8ffdbe66f1c5d5595a46bac9cde`，示例详情路径`/sale/1234567.html`允许；两份文件均未声明对该UA适用的crawl-delay/request-rate。
- robots允许不等于平台许可。贝壳路径拒绝；安居客当前消费者协议正文与本项目书面许可仍缺，两来源和全局在线采集继续OFF。详细证据见 `docs/SOURCE_POLICY_REVIEW_2026-11-12.md`。
- 仅NAS只读HTTP请求和文档记录；无应用、生产数据库、Compose、容器或卷变更，无迁移/部署。


## 2026-11-12 P0-09详情队列与扫轮边界静态复核
- 复核详情队列普通失败持久重试、403/429停止、分页与详情数量上限续跑，以及分页循环不计完整扫轮的状态分支；现有定向回归覆盖这些行为，未发现新的可确认逻辑缺陷。
- 本轮尝试复跑定向pytest未能启动：系统Python未安装pytest；`uv --offline`因沙箱拒绝读取用户缓存目录而失败。此前最近记录的全量离线pytest为 **1071 passed、27 skipped、27 subtests passed**；本轮不能据此声称重新验证，27项PG集成也未运行。
- 用户确认跨平台面积差≤5%以较小面积作分母；当前公式`abs(a-b)/min(a,b)`及双向边界测试已符合，无需改业务逻辑。仅静态审阅和状态记录，无代码、数据库、配置、NAS、来源访问或部署变更。在线采集保持OFF。
- 下一步：在获准隔离PostgreSQL 17环境中运行迁移014及详情队列级联/失败元数据集成回归；继续等待article与嵌套`.content`价格冲突处理口径，答复前维持现有解析行为。


## 2026-11-12 P0-09详情队列全量离线回归复验
- 使用现有临时Python 3.12依赖环境运行全量pytest：**1071 passed、27 skipped、27 subtests passed**，11.98秒；27项均需PostgreSQL，未配置测试数据库因此跳过。保留1条Starlette/httpx弃用警告。队列普通失败重试、403/429中止、分页/详情限额续跑及扫轮完成边界均包含在通过结果中。
- 本机Docker daemon返回permission denied，无法建立本地隔离PostgreSQL；NAS隔离PG17需要源码传输及远端临时写入授权，本轮未执行。迁移014数据库级幂等、索引及级联行为仍未实测。
- Python 3.12 `compileall`、GOAL_STATE JSON解析、`git diff --check`和开发包完整性校验通过。仅离线验证，无应用代码、数据库、配置、NAS、来源网站或生产环境变更；在线采集保持OFF。


## 2026-11-12 P0-09 NAS隔离PG17测试前置条件只读核验
- 按NAS SSH技能的LAN优先顺序：`nas-lan`连接超时；Tailscale CLI无法加载偏好，Mac未安装Tailscale应用。使用此前获准的`notedock-nas`成功连接，核对主机`DXP4800`、用户`sheng`、组`admin/users/docker`。
- 按UGREEN Docker技能只读查看本地镜像：存在`postgres:17-alpine`与`python:3.12-slim`；容器名筛查未发现`rehouse`/`p009`临时测试容器。未传输文件、创建容器、改Compose/卷或查询生产业务数据。
- 本机临时Python 3.12完整离线pytest结果为 **1071 passed、27 skipped、27 subtests passed**；27项PostgreSQL集成因无本机测试数据库而跳过。隔离PG17方案已具备镜像条件，但还需要远端临时Docker写入和源代码传输授权。
- 无部署或生产变更；在线采集保持OFF。


## 2026-11-12 P0-04补充读取安居客官方消费者协议正文
- 官方协议中心确认有消费者“用户服务协议”及历史版本入口，但当前页面提取未给出正文/版本。找到安居客官方静态域名托管的《安居客用户服务协议》PDF；其中有Robots遵守要求，并限制未经书面许可的商业利用、抓取及内容使用。
- 项目此前核读记录该PDF标示2021年5月更新；本次网页文本抽取未显示日期。它与协议中心当前消费者协议/历史版本的映射仍无法确认，故只作为官方风险证据，不宣称适用版本已确认。贝壳当前协议页面标示2026-11-11更新、2026-11-12生效，并要求书面许可。两站缺少本项目许可，在线仍OFF。
- 仅访问官方协议中心及官方PDF；未访问房源页/robots、未采集、未访问NAS或生产数据库，无代码、配置、迁移或部署变化。

## 2026-11-12 P0-03人工改价证据与正数下限复核
- 人工修正挂牌价后，字段证据来源为`manual_review`、不再残留解析器的非精确价mention；`non_exact_asking_price`仍作为解析审计警告保留。该回归也确认未修改的面积证据仍保留原页面来源。
- 用户再次确认面积和挂牌价只需大于0。现有解析器已统一该边界：零值拒绝，正数接受（含小于1万元价格）；本轮未作冗余代码改动。
- 定向回归 **9 passed**；全量pytest **1554 passed、27 skipped、27 subtests passed**。27项需PostgreSQL集成库，本轮未连接。保留1条既有Starlette/httpx弃用警告。
- Python 3.12 `compileall`、GOAL_STATE JSON、更新文档空白检查及开发包完整性/清单哈希均通过。仅合成HTML/mock离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标签，P0-03保持`in_progress`。

## 2026-11-12 P0-03人工改价PATCH API证据回归
- 新增`PATCH /api/collection/candidates/{id}`回归，经真实FastAPI路由和mock数据库写入/返回验证：人工改价后的响应数值与证据一致，证据来源为`manual_review`、旧`is_non_exact`命中清空、`manually_corrected=true`；`non_exact_asking_price`仍作为解析审计警告保留。
- 定向API回归 **1 passed**；全量离线pytest **1555 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未连接，保留1条既有Starlette/httpx弃用警告。
- Python 3.12 `compileall`、目标状态JSON、文档空白检查和开发包完整性/清单校验通过。仅mock数据库与合成候选验证，无真实页面准确率结论；未访问来源网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-03人工改正非精确挂牌价后审批闭环（隔离PG17）
- 新增PostgreSQL集成回归，覆盖近似挂牌价页面提交、候选待审、PATCH人工改价、manual_review证据与解析审计警告落库、审批进入正式挂牌及价格历史。审批后正式挂牌和历史价格均为人工确认值200万元，旧非精确mention清空，`non_exact_asking_price`警告仍在候选审计记录中。 修正后重放同一HTML仍返回同一候选及manual_review数值/证据，不被解析器覆盖。
- NAS隔离PostgreSQL 17完整`tests/test_db_integration.py` **29 passed**，源码SHA-256与本机开发包一致。测试仅用internal网络、PostgreSQL 512 MiB tmpfs，无宿主端口/持久卷；源码只读挂载。临时容器、网络、测试源码/依赖及上传ZIP均已清理。
- 本机全量pytest **1555 passed、28 skipped、27 subtests passed**；28项PostgreSQL集成未设置本机`TEST_DATABASE_URL`而跳过，隔离PG17运行覆盖完整数据库集成文件。保留1条既有Starlette/httpx弃用警告。
- Python 3.12 `compileall`、GOAL_STATE JSON、更新文档空白检查和开发包校验通过。未访问来源网站；生产API、Worker、DB容器保持运行，未修改生产数据库、Compose、卷或部署。真实准确率仍待获准页面及人工标签。
