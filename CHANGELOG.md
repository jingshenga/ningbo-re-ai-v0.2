## 2026-11-13 ZCode双分支集成（GitHub PR #8、#7）
- 修复：网页挂牌价格上下文解析升级`generic-labelled-v0.2.168`；评估总价、租金/年费、原总价不再当作精确挂牌价；正常挂牌价后跟月供、物业费等独立句子仍保留。解析器/评估器/API和新回归测试一起合并。
- 测试与文档：DTK worker的`success`/`partial`/`failed`/`blocked_config`离线行为增加回归；纠正403/429当前仍只记`failed`且没有专门退避机制的说明，列出未来安全改造验收。
- 集成CI：PR #7基于PR #8合并后main重新验收，快速1963项通过、隔离PG17集成31项通过；PR #8/#7均完成审查与Squash Merge，Issue #1关闭，Issue #3保留真实联调。
- 部署边界：未对NAS生产数据或容器部署本轮更改，贝壳/安居客在线采集继续关闭。Mimosa本地Push拦截单列Issue #9跟踪。

## 2026-11-12 P0-02直接采集请求的来源许可门禁
- 核对贝壳官网现行《平台服务使用协议》（页面标示2026-11-11更新、2026-11-12生效）：第七条要求书面许可，并限制未经许可读取、机器人/蜘蛛获取及超出许可范围使用。项目当天NAS读取的贝壳Robots规则还禁止示例二手房详情路径。
- 安居客官方协议入口仍无法确认当前消费者协议正文/版本，且没有本项目书面许可；Robots允许示例路径不等于内容使用授权。
- 用户要求直接采集，但未提供平台书面许可。未请求房源详情页、未采集或绕过限制；两来源继续OFF。P0-02标记为blocked，待取得覆盖域名、路径、字段、频率、用途和留存的书面许可后再采集获准样本。

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
## 2026-11-12 验证限定挂牌价区间证据贯穿提交API
- 两来源页面提交API回归覆盖限定价区间；pending状态、空挂牌价、双告警、完整证据引用、数据库JSONB参数及gzip原始HTML均符合契约。定向4 passed，全量pytest1735 passed、28 skipped、27 subtests passed。本轮为API契约测试加固，无应用逻辑变更。

## 2026-11-12 加固非精确面积/报价证据评估
- `non_exact_areas`与`non_exact_prices`评估要求每条证据`quote`同时包含候选值和近似/上下限限定词；模拟截断限定词的回归由误通过改为失败。定向43 passed，全量pytest1731 passed、28 skipped、27 subtests passed。

## 2026-11-12 补齐挂牌价连接词和限定证据
- 支持“挂牌价为约200万”“挂牌价约为200万”“挂牌价在200万左右”等表达，且保留精确“挂牌价为200万”；近似/上下限单值与区间的证据引用现包含完整限定后缀。解析器升级至`generic-labelled-v0.2.162`；相关定向327 passed，全量pytest1729 passed、28 skipped、27 subtests passed。

## 2026-11-12 处理面积“在”限定和“为”连接词
- `建筑面积在100㎡左右`现留空待审并保留候选证据及告警；精确写法`建筑面积为100㎡`仍可解析。解析器升至`generic-labelled-v0.2.160`。相关回归119 passed，全量pytest1705 passed、28 skipped、27 subtests passed。

## 2026-11-12 补齐估算/参考面积限定
- 建筑面积标签前后的“参考、估算、估计、预估”现留空待审，保留完整数值证据并添加`non_exact_area_sqm`；解析器升级至`generic-labelled-v0.2.159`。相关解析器/API/评估器回归111 passed，全量离线pytest1697 passed、28 skipped、27 subtests passed。

## 2026-11-12 确认近似/上下限面积待审规则
- 用户确认近似或上下限建筑面积应留空待审、保留候选证据并告警。现有解析器、API与评估器已有相应行为；相关定向回归69 passed，全量离线pytest 1649 passed、28 skipped、27 subtests passed。本轮无应用代码变更。

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
- Python 3.12 compileall、目标JSON、`git diff --check`和开发包校验待本轮打包检查后记录。仅合成HTML/模拟API验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率未验证，在线采集保持关闭。

## 2026-11-12 P0-03建筑面积下限“起”留空待审
- 将“建筑面积：100㎡起”纳入非精确面积口径。两来源解析器回归先失败，修复后建筑面积字段留空、保留候选与完整证据、添加`non_exact_area_sqm`并阻止审核就绪；API暂存和评估器也覆盖该表达。
- 解析器版本升至`generic-labelled-v0.2.155`。解析器/API/样本集/评估器相关四个测试文件 **1212 passed**；全量离线pytest **1602 passed、28 skipped、27 subtests passed**。28项本机PostgreSQL集成未连接，既有Starlette/httpx弃用警告1条。
- 本轮无数据库/运行配置变化；未访问来源网站、NAS或生产数据库，无迁移或部署。全部验证使用合成页面/模拟API；真实页面准确率仍未验证，在线采集保持关闭。

## 2026-11-12 P0-03避免“平方”单位证据截短
- 面积解析避免将`平方/平方米/平米`的单位前缀回溯截短为`平`；单值证据保留完整单位，范围只保留完整范围证据。
- 失败回归先复现后通过；解析器版本升至`generic-labelled-v0.2.153`。解析器759 passed，全量pytest1562 passed/28 skipped/27 subtests。

## 2026-11-12 P0-03补齐“平”面积单位
- 建筑面积解析新增`平`单位并复用同一单位规则识别面积范围；范围继续留空待审，不提升端点。
- 两来源新增失败回归先失败后通过；解析器版本升至`generic-labelled-v0.2.152`。
- 全量离线pytest **1559 passed、28 skipped、27 subtests passed**；开发包含129个文件并由项目打包器校验。

## 2026-11-12 P0-07生产schema迁移边界只读核验
- 核实生产schema缺少工作区006–014核心发现、复核、解析账本及详情队列对象；解析健康计数列也未部署。005条件单列/约束可见。
- 状态与路线图已记录生产不具备新版API/Worker schema；本轮只读，未备份、迁移或部署。
- 用户确认解析器面积和挂牌价下限统一为大于0；现有代码已满足，无重复代码改动。
- 全量离线pytest **1555 passed、28 skipped、27 subtests passed**；数据库集成仍由最近一次隔离PG17的29项结果覆盖。编译、GOAL_STATE JSON、diff检查及129文件开发包校验通过。

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

## 2026-11-12 P0-03非精确挂牌价样本评估
- 样本清单新增可选`non_exact_prices`标签：挂牌价留空，候选列须恰有一个正数，不接受范围或与冲突价/范围标签混用。
- 评估器逐样本核验挂牌价为空、`non_exact_asking_price`存在、证据未截断、证据候选与人工标注完全匹配；精确报价或缺少警告时失败。
- 新增证据截断边界回归1 passed；定向样本校验/评估323 passed，全量pytest1553 passed、27 skipped、27 subtests passed。未连接数据库或访问真实页面；真实准确率仍待获准样本与人工标签。

## 2026-11-12 P0-03修复“挂牌售价”限定词后缀绕过
- 扩展限定词组合测试到新标签后，发现`折后挂牌售价`可以从内部`售价`子串绕过`折后`排除规则，与合法挂牌价形成误冲突。
- `售价`仅在不紧接`挂牌`时独立匹配；“挂牌售价”由完整复合标签处理。新增边界后，价签限定词组合 **82 passed**、解析器 **496 passed**、全量pytest **1097 passed、27 skipped、27 subtests passed**。版本升至`generic-labelled-v0.2.137`。
- 仅合成HTML离线验证，无真实页面准确率结论或部署。

## 2026-11-12 P0-03支持“售价/挂牌售价”标签
- 两来源回归复现“售价：365万”和“挂牌售价：365万”不被抽为挂牌价；新测试确认添加标签后均可解析，同时`成交售价`、`合同售价`仍受限价规则排除。
- 解析器升至`generic-labelled-v0.2.136`。价签/限定词专项 **82 passed**，解析器专项 **496 passed**，全量pytest **1097 passed、27 skipped、27 subtests passed**。仅合成HTML离线验证，无真实页面准确率结论或部署。

## 2026-11-12 P0-03支持扩展装修标签
- 失败回归确认“装修情况：精装”和“装修状况：简装”在贝壳/安居客来源解析中均未提取装修值。
- 扩展装修标签识别及字段边界，解析器版本升至`generic-labelled-v0.2.135`；原“装修：精装”规则保留。
- 新回归4项修复后通过；楼层/装修专项 **8 passed**，另验证完整标签quote及字符偏移；解析器专项 **488 passed**，全量pytest **1089 passed、27 skipped、27 subtests passed**。仅合成HTML验证，无真实页面准确率结论或部署。

## 2026-11-12 P0-03排除“总楼层”作为挂牌楼层
- 失败回归复现两来源的共同行为：“总楼层：18层”被当作`floor_text`；与“所在楼层：中楼层”同时出现时，解析器报多值冲突并清空真实楼层。
- 现在拒绝把`总楼层`当挂牌楼层标签，并在总楼层之前终止所在楼层值；保留`楼层：高楼层 14/18层`。解析器版本升至`generic-labelled-v0.2.134`。
- 定向 **4 passed**，解析器专项 **484 passed**，全量pytest **1085 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未连接数据库；compileall、GOAL_STATE JSON与diff空白检查通过。仅合成HTML验证，无真实准确率结论、数据库变化或部署。

## 2026-11-12 P0-03排除“实用面积”作为建筑面积
- 失败回归复现两来源共同行为：只出现“实用面积100㎡”时，解析器会错误写入建筑面积；与“建筑面积120㎡”并列时又产生多值冲突并清空正确值。
- 将“实用”纳入非建筑面积限定词，面积字段保留为建筑面积120㎡；解析器升至`generic-labelled-v0.2.133`。
- 解析器专项 **480 passed**，全量pytest **1081 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未配置`TEST_DATABASE_URL`而跳过；compileall、GOAL_STATE JSON和`git diff --check`通过。仅合成HTML离线验证，无真实页面准确率结论，无数据库/配置/迁移或部署变化。

## 2026-11-12 P0-03同页嵌套挂牌价冲突处理
- 按用户确认，外层`article`和嵌套`.content`给出不同挂牌价时不再只采用内层值：保留article范围内的冲突证据、挂牌价置空并待审核。同价重复不阻止审核，不跨兄弟根拼字段。解析器升至`generic-labelled-v0.2.132`。
- 解析器专项 **476 passed**；全量离线pytest **1077 passed、27 skipped、27 subtests passed**。仅合成HTML验证，真实样本准确率仍未验证。

## 2026-11-12 P0-06 DTK/Worker边界复核
- 定向复核85项通过；没有发现可复现的新缺陷，未修改应用代码。真实DTK接口/权限及至少3个获准账号连续24小时联调仍未完成。

## 2026-11-12 P0-09迁移014隔离PG17验收
- 在NAS隔离PostgreSQL 17.11运行完整数据库集成文件：**28 passed**，覆盖迁移001–014重放、旧数据保留、详情队列/API与外键级联。测试使用合成数据和临时schema。
- 修复数据库集成测试漏导入`json`，并更新Worker恢复顺序断言，使其匹配持久详情队列“先排队详情、后重读列表页完成扫轮”的实现；未修改应用运行代码。
- 本机全量离线pytest **1073 passed、27 skipped、27 subtests passed**。PG17测试使用internal网络和tmpfs，无宿主端口/持久卷；已清理全部临时资源。生产未迁移、未部署。

## 2026-11-12 P0-03将非挂牌价格场景缺失值纳入字段指标
- 失败回归显示，`oral_prices`/`transaction_prices`标注挂牌价为空时，专门场景能检出非挂牌金额被误抽，但该样本未进入挂牌价字段准确率/精确率分母；错误输出因而未降低字段指标。现将这两类显式空挂牌价作为空真值计分，误报会同时反映在字段指标和专门场景指标；未解析的`multiple_prices`继续只在独立场景计分。
- 两来源promotion回归修复前均失败，修复后通过。评估器专项 **116 passed**；全量离线pytest **1073 passed、27 skipped、27 subtests passed**。27项均需PostgreSQL集成库，未运行。Python 3.12 compileall和`git diff --check`通过。
- 更新`docs/SAMPLE_DATASET.md`与`docs/ACCEPTANCE.md`分母说明。仅使用合成HTML/Mock，没有真实样本准确率结论；未访问来源网站、NAS或生产数据库，无迁移或部署。

## 2026-11-12 P0-03评分后续 article 根
- 失败回归证明第一个`article`若是“推荐阅读”壳层，会遮蔽后续含完整挂牌字段的独立`article`；贝壳和安居客旧逻辑均漏解析。现对所有未嵌套于其他`article`的根按原分数规则评分，不跨根拼接。
- 解析器升至`generic-labelled-v0.2.131`。解析器专项 **472 passed**，全量离线pytest **1073 passed、27 skipped、27 subtests passed**；跳过项均为未连接数据库的集成测试。Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。
- 仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移或部署。article与嵌套`.content`的冲突选择仍待用户确认。

## 2026-11-12 P0-03核验多值冲突证据偏移
- 新增长页面冲突回归，确保证据摘录截断后冲突值仍留空，原始quote可按完整文本偏移还原；待审核候选重提断言证据值与字段一致。定向相关5 passed、service/parser组合377 passed、全量离线pytest859 passed/26 skipped/25 subtests passed。
- 仅测试变更；可选字段冲突对`ready_for_review`的影响待用户确认，现有行为不变。未访问来源/NAS/生产库，无迁移/部署。

## 2026-11-12 P0-03覆盖数值范围分隔符边界
- 回归补齐10种范围分隔符，并确认范围横线后接其他标签不影响合法的面积/价格单值；边界13 passed、解析器355 passed、全量离线pytest870 passed/26 skipped/25 subtests passed。
- 仅测试变更；解析器v0.2.115无运行代码变化，未访问来源/NAS/生产库或部署。

## 2026-11-12 P0-03同步区间数值API说明
- `docs/API.md`补充面积/挂牌价区间不提取端点、单独出现时字段为空并有`missing_*`警告，原始区间由页面证据保留。仅文档同步，无应用代码变化。

## 2026-11-12 P0-03拒绝范围形式的面积和挂牌价
- 面积或挂牌价字段若带有范围后缀（如`120㎡-130㎡`、`300万-320万`），现在不把首端点当成唯一挂牌值；解析器版本升至`generic-labelled-v0.2.115`。
- 新增参数化回归覆盖无单位端点及双单位区间；定向2 passed、解析器343 passed、全量离线pytest858 passed/26 skipped/25 subtests passed。26项DB集成因未设置`TEST_DATABASE_URL`跳过；有1条Starlette/httpx弃用警告。未访问来源网站、NAS或生产数据库，无迁移/部署。

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

## 2026-11-12 P0-09长期发现ID规范化存储
- 新增迁移012回填历史去重ID并清空游标JSON中的大数组；Worker查询规范化去重表，扫轮ID从挂牌观察派生。发现状态API继续提供有界ID列表、总数及截断标记；`seen_ids`按挂牌ID字典序输出，利用主键索引且回填后顺序确定。
- 本机全量离线pytest **855 passed、25 skipped、25 subtests passed**；compileall、GOAL_STATE JSON及变更文件尾随空白扫描通过。DB集成回归含100,001条历史ID场景，但本轮25项PG测试未运行：自动审核拒绝将源码包和测试运行时写入NAS，因该远端写入不在当前授权范围；未尝试绕过。
- 未执行数据库迁移或生产部署，未访问房源来源；在线采集关闭。下一步在源码传输/远端临时文件写入获授权后运行隔离PG17数据库集成，另需获准真实来源样本及V0.1备份推进P0验收。

## 2026-11-12 P0-09发现页DOM遍历避免重复复制
- 发现列表页锚点时不再对每个DOM节点复制`children`列表；普通节点读取既有`contents`，闭合`details`只在直接子节点中选摘要，仍忽略折叠正文。
- 新增禁止使用`Tag.children`的回归；发现/URL/状态专项57 passed、7 subtests，全量离线pytest855 passed、23 skipped、24 subtests。23项DB集成因本机无`TEST_DATABASE_URL`跳过；compileall、目标JSON和差异检查通过。
- 仅合成HTML离线验证，无迁移、配置、NAS/生产库或来源网站变更，也未部署。当时发现已处理ID受100,000项/2 MB上限约束；后续已由迁移012规范化存储，详见本文件最新P0-09记录。

## 2026-11-12 P0-07只读复核生产schema与API差异
- 通过已授权 `notedock-nas` 确认DXP4800/sheng；生产API/Worker运行，PostgreSQL 17 healthy。生产schema缺少工作区006–011新增的发现状态、挂牌观测/扫轮/复核、解析尝试和解析计数结构；OpenAPI缺少发现观测、复核历史及发现状态路由。
- 仅读取容器元信息、`information_schema`与OpenAPI路径，不读业务行或秘密；未备份、迁移、修改Compose/卷/服务或部署。P0-07维持进行中。
- 用户确认跨平台同套面积差≤5%按较小面积作分母；现有实现及双向边界测试符合，无需代码变更。目标JSON、文档差异检查通过。

## 2026-11-12 P0-07完整数据库集成在隔离PostgreSQL 17通过
- 当前工作区完整`tests/test_db_integration.py`在NAS隔离PostgreSQL 17.11运行 **24 passed**，覆盖新增011迁移的幂等性及解析尝试明细UPDATE/DELETE/TRUNCATE保护和累计汇总一致性。
- 测试使用internal网络、512 MiB tmpfs、无宿主端口/持久卷及只读源码挂载；数据库容器、网络、依赖/源码暂存目录已清理。生产API/Worker仍运行，PostgreSQL healthy；生产库/卷/Compose未变，未部署。

## 2026-11-12 P0-07在PostgreSQL 17验证追加式解析账本
- 隔离PostgreSQL 17.11按001–011顺序执行成功，011重复执行成功。运行时回归确认解析明细UPDATE/DELETE/TRUNCATE均被拒绝，1条明细与1/1/1解析累计计数保持一致。
- 临时容器使用internal网络、512 MiB tmpfs、无端口/持久卷；测试后容器、网络、源码和脚本暂存目录均已清理。生产API/Worker仍运行、DB healthy，生产数据库和卷未变。未部署。
- 完整离线pytest **854 passed、23 skipped、24 subtests passed**；本地数据库集成因缺少`TEST_DATABASE_URL`跳过。

## 2026-11-12 P0-07防止解析尝试账本被修改
- 新增`011_parse_attempts_append_only.sql`，数据库层拒绝解析明细UPDATE、DELETE和TRUNCATE，确保INSERT触发器维护的累计尝试/成功/完整字段数仍与明细一致；迁移幂等并加入Compose新库和升级顺序。
- 新增静态契约与PostgreSQL集成回归。定向7 passed、1 skipped、11 subtests；全量854 passed、23 skipped、24 subtests。数据库行为测试因缺少`TEST_DATABASE_URL`跳过，尚未执行PG运行时验证。未部署。

## 2026-11-12 P0-03复核长字段文本解析耗时
- 对重复长“装修”标签的合成页面预热后各解析5次，输入从9,933字符/29,613字节增至299,969字符/895,043字节，中位耗时从5.6ms增至22.0ms；未发现明显超线性增长。该探针不构成生产SLO。
- 输入按UTF-8字节计受1 MB上限约束；超限探针被正确拒绝。无代码变更、未联网或部署。

## 2026-11-12 复核跨平台面积边界并等待解析口径
- 用户确认面积差≤5%以较小挂牌面积作分母；`tests/test_opportunities.py` **21 passed**。
- 跨语义区域字段是否可拼接仍待用户明确；未据此改变解析器。未访问网站、NAS或生产数据库，无部署。

## 2026-11-12 P0-03复核剩余文本读取边界
- 复核`get_text()`调用：样式表页面输入上限为1 MB，标题输出最多500字符；未发现值得增加代码复杂度的无界分配或重复遍历问题。
- 用户确认跨平台面积差按较小面积作分母，现有`abs(a-b)/min(a,b)≤5%`实现符合口径。
- 全量离线pytest **853 passed、22 skipped、23 subtests passed**；数据库集成因缺少`TEST_DATABASE_URL`跳过。未连接来源网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-03流式迭代内联CSS声明
- 内联CSS属性扫描和opacity可见性检查改用惰性声明迭代，避免`split(';')`创建整页声明列表。75,000个合成声明的峰值从3.76/3.75 MiB降至0.0067/0.0020 MiB。
- CSS专项70 passed、解析器340 passed、全量pytest853 passed/22 skipped/23 subtests passed。22项数据库集成未配置`TEST_DATABASE_URL`而跳过。
- Python 3.12编译、GOAL_STATE JSON及变更文件尾随空白扫描通过；未联网、未访问NAS/生产库、未部署。

## 2026-11-12 P0-03减少CSS可见文本扫描的逐字符内存分配
- CSS注释/字符串筛除由逐字符列表构建改为按未屏蔽片段写入`StringIO`。300 KB普通CSS回归先失败，旧峰值2,901,577字节；修改后低于1,000,000字节。600 KB探针由5.60 MiB降至1.29 MiB。
- CSS/可见性定向70 passed、解析器338 passed、全量pytest851 passed、22 skipped、23 subtests passed。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12编译、目标JSON、差异检查通过。无网站/NAS/数据库访问或部署；数据为合成输入。

## 2026-11-12 P0-03流式产出CSS规则片段
- `_css_rule_segments`改为按需yield。此前仅600 KB、200,000段合成CSS就分配9.75 MiB峰值片段列表；当前流式消费全部200,001段时峰值0.0008 MiB，不含输入字符串/DOM。上层可在首条样式表风险规则后早停。
- 新增惰性回归：旧版首段产出前切片1,001次；新版只切片1次。CSS专项23 passed、解析器337 passed、全量850 passed/22 skipped/23 subtests passed。
- Python 3.12编译、目标JSON、差异检查通过。合成数据结果不代表生产SLO；未联网、未访问NAS/生产库、未部署。

## 2026-11-12 P0-03复核DOM遍历与样本库存
- 检查解析器后确认仅H1包装链仍直接遍历`Tag.children`，无剩余子节点列表物化。`data/`只有占位文件，`fixtures/`含4份演示HTML，没有真实样本清单；这些fixture不计入P0-02/P0-03验收。
- 使用`python -m pytest`形式定向运行DOM遍历回归1 passed；未改代码。

## 2026-11-12 P0-03复用DOM已有子节点列表
- 可见文本遍历、run-in兄弟布局、隐藏节点/文本裁剪及内联可见性检查改为读取已有`Tag.contents`，需删除时反向遍历，避免重新复制子节点引用列表；新增回归禁止这些DOM遍历调用`Tag.children`，覆盖连续隐藏兄弟节点和多段隐藏文本。
- 解析器专项336 passed；全量离线pytest849 passed、22 skipped、23 subtests passed。22项数据库集成未设置`TEST_DATABASE_URL`而跳过。
- 先后顺序相反的两批各9次完整解析基准，在600,098字节/25,000-span合成页上，旧版中位数1,224.24/1,230.99ms、当前版1,122.29/1,138.92ms；两版tracemalloc峰值均30.02MiB。该对照不代表真实页面SLO。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`通过；未联网、未访问NAS/生产库、未部署。

## 2026-11-12 P0-03穷举Unicode空白归一化边界
- 新增穷举差分回归，覆盖正则表达式识别的全部Unicode空白码点及规范化前缀的每个截断位置，确认与完整`re.sub`的值和截断标志一致；未改解析器逻辑。
- 归一化专项8 passed、解析器专项335 passed；全量离线pytest848 passed、22 skipped、23 subtests passed。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12 compileall、GOAL_STATE JSON及变更文件尾随空白扫描通过。未访问网站/NAS/数据库，无迁移或部署。

## 2026-11-12 P0-03恢复Python 3.12离线全量复验
- 使用`uv`的离线缓存与临时缓存目录运行测试，没有联网或改动项目依赖文件。解析器专项 **334 passed**；全量离线pytest **847 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，另有1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。测试包含固定种子Unicode差分回归；不代表真实来源页面准确率。
- 未访问来源网站、NAS或生产数据库，也未部署。跨语义根字段合并规则仍待用户决定。

## 2026-11-12 P0-03刷新Unicode回归开发包
- 重新生成源代码开发ZIP，脚本核验122个文件及ZIP/manifest内容摘要；ZIP SHA-256为`11c5e2159cac6d33b363e31b30a7c43e474d812f55142346640d3701c12f9e1a`。
- Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。尝试复跑解析器测试时发现Python 3.12和系统Python 3.9均无pytest安装；上一轮记录的334/847通过结果未冒充为本轮重跑。
- 未联网、未访问NAS或数据库、未部署。跨语义根字段合并规则仍待用户决定。

## 2026-11-12 P0-03固定Unicode归一化差分测试
- 加入1,000组固定种子的Unicode空白差分回归，确认有界前缀和截断标志与完整`re.sub`一致。
- 解析器专项334 passed；全量离线pytest847 passed、22 skipped、23 subtests passed。

## 2026-11-12 P0-03覆盖body回退的有界截断
- 新增无语义候选根时的长body回退回归：窗口外冲突不计入证据，但截断仍阻止审核就绪。
- 解析器专项333 passed；全量离线pytest846 passed、22 skipped、23 subtests passed。仅测试变更。

## 2026-11-12 P0-03记录分段页面内存对照
- 有界归一化在短span token和短段落合成页的tracemalloc峰值分别比完整归一化高0.29 MiB、0.14 MiB；收益主要集中于长连续文本，未据此复杂化实现。
- 仅合成HTML内存测量，无代码改动；不代表真实页面SLO。

## 2026-11-12 P0-03复核有界归一化的输入形状
- 同进程交替基准中，大量短节点、长空白和重复段落三种合成页与完整归一化中位耗时相差−0.2%、+0.5%、−0.1%，未见显著回退；长连续文本场景另有改善。
- 仅本地实现对照，无代码变化；该数据不代表真实页面或生产性能。

## 2026-11-12 P0-03对候选根使用有界空白归一化
- 新增`_normalize_text_prefix`并复用同一归一化前缀进行根评分和字段提取，保留原35,000字符窗口及截断状态，减少重叠根完整归一化分配。
- 800,144字节合成页交替基准：中位数29.69 ms降至24.80 ms（16.5%）；tracemalloc峰值5.39 MiB降至3.86 MiB。解析器专项332 passed，全量845 passed/22 skipped/23 subtests。

## 2026-11-12 P0-03跨根字段组合诊断
- 发现推荐卡小区名与详情article面积/总价会被拼为完整候选；标题区小区是否可与article字段合并需用户明确。
- 约800 KB合成页的main/article重叠文本分别归一化约800 KB，解析中位数29.92 ms；仅诊断，未修改代码。

## 2026-11-12 P0-03锁定混合候选根冲突留空
- 外层main含推荐卡和详情article且字段冲突时，确保小区/面积/总价都留空并报告歧义，不因缩小内容根隐藏同页冲突。
- 解析器专项326 passed；全量离线pytest839 passed、22 skipped、23 subtests passed。仅新增合成回归，无业务逻辑改动。

## 2026-11-12 P0-03核验评估器的截断判分保护
- 确认`missing_fields`和`multiple_prices`评估场景均拒绝被35,000字符截断影响的结果；候选/来源ID歧义场景已有截断失败回归，无需重复实现。
- 强化截断字段证据回归：窗口后报价不进入计数，窗口内引用偏移不越界。解析器专项325 passed；全量离线pytest838 passed、22 skipped、23 subtests passed。

## 2026-11-12 P0-03锁定字段证据不越过截断窗口
- 截断点后冲突报价不计入字段提及数或冲突告警；窗口内证据偏移保持在35,000字符内，超限仍阻止审核就绪。
- 解析器专项325 passed；全量离线pytest 838 passed、22 skipped、23 subtests passed。

## 2026-11-12 P0-03锁定可见文本长度边界
- 增加35,000字符含边界回归：恰好到上限不报截断；超出1字符时报截断并阻止审核就绪。
- 解析器专项325 passed；全量离线pytest 838 passed、22 skipped、23 subtests passed。22项数据库集成因未配置`TEST_DATABASE_URL`跳过。

## 2026-11-12 P0-03对齐候选评分与提取文本窗口
- 候选内容根评分现只检查字段提取实际使用的前35,000字符，避免被截断的后段字段抬高外层根分数并导致真实字段丢失。新增长前缀/嵌套article失败回归。
- 评分与截断共享`MAX_VISIBLE_TEXT_CHARS=35_000`，并以该常量构造长前缀边界回归。解析器专项323 passed；全量离线pytest 836 passed、22 skipped、23 subtests passed；22项数据库集成未配置`TEST_DATABASE_URL`。

## 2026-11-12 P0-03复用已归一化的候选文本
- 避免对已选候选根文本重复做空白归一化；只在body回退路径归一化。新增计数回归，锁定候选正文只归一化一次。
- 解析器专项322 passed；全量离线pytest 835 passed、22 skipped、23 subtests passed。数据库集成22项因未配置`TEST_DATABASE_URL`跳过。

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

## 2026-11-11 P0-03覆盖标注缺失字段上的解析器误报
- 增加评估器回归：人工真值为空但解析器产生非空字段时，需作为错误输出纳入准确率与精确率分母，并使缺失字段场景失败。桩化注入一条错误面积后，指标为准确率80%、覆盖率100%、精确率80%。
- 定向1 passed；完整离线pytest **737 passed、22 skipped、17 subtests passed**。不改变评估实现；真实页面指标仍待获准样本与人工标签。

## 2026-11-11 P0-03保留折叠摘要内的连续行内文本
- 失败回归确认折叠`details`将首个`summary`转为字符串时，`get_text(' ')`会拆开跨`span`的字段标签和数值。改用既有行内/块级边界文本遍历后折叠空白；保留隐藏文本过滤与折叠主体排除。解析器升至`generic-labelled-v0.2.72`。
- 回归先失败后通过；定向8 passed。全量pytest **736 passed、22 skipped、17 subtests passed**；22项数据库集成未配置`TEST_DATABASE_URL`而跳过。仅合成HTML验证，真实页面准确率未验证。

## 2026-11-11 P0-07 V0.2基线升级回归
- 增加完整的PG集成用例：从001–005的既有V0.2挂牌、采集运行/目标/候选及条件单起步，升级到006–010；填入发现状态、观察/复核记录和解析阶段计数后重跑迁移，核实数据保留与`2/1/1`计数幂等。
- NAS隔离PostgreSQL 17完整数据库集成：23 passed；测试schema残留0，测试容器、网络及传输目录已清理。只使用合成数据，未操作生产数据库或服务。
- 完整离线pytest：735 passed、22 skipped、17 subtests passed；22项数据库集成未设置`TEST_DATABASE_URL`而跳过。安全开发包已生成并完成ZIP与包内SHA-256清单校验。

## 2026-11-11 P0-09保留首个详情策略阻断时的扫描状态
- 修复列表页已发现挂牌、详情候选尚未暂存即发生`blocked_policy`时漏存扫描号/游标的问题。现在保留活动扫描和列表页重试位置；列表观察不等同于详情抓取成功，且该轮不计为完整遍历。
- 回归先失败后通过。分页/发现/状态专项78 passed、7 subtests；全量pytest734 passed、21 skipped、17 subtests；标准库42 passed。新增数据库集成用例当前因缺少`TEST_DATABASE_URL`跳过。
- 无数据库迁移或API契约变更；未访问NAS、生产数据库或房源网站，未部署。

## 2026-11-11 P2-02精确比较跨平台10%单价门槛
- 对恰好10%边界不再依赖循环Decimal单价的舍入结果；改以原始价格与面积的交叉乘积判断（高单价−低单价）/低单价是否达到10%。数学边界100/7与110/7现在纳入机会列表。
- 先失败后通过；机会专项21 passed，全量pytest734 passed、20 skipped、17 subtests passed。面积差现行较小面积分母未确认，已请求用户澄清，保持现状。
- 无迁移；数据库集成因TEST_DATABASE_URL未设置而跳过，未访问NAS、生产数据库或房源网站。

## 2026-11-11 P0-03按CSS相邻盒规则解析 `display: run-in`
- 上轮将run-in一律视为块级会漏掉应并入后继块的文本。现在仅当run-in序列后紧接普通块级盒时并入；行内后继与`flow-root`等独立格式上下文继续分隔。解析器升至`generic-labelled-v0.2.71`。
- 显示边界专项17 passed；全量离线pytest733 passed、20 skipped、17 subtests passed；标准库42 passed。数据库集成未配置`TEST_DATABASE_URL`而跳过。
- 合成HTML验证。未访问NAS数据库或房源网站，未部署；真实解析准确率未验证。

## 2026-11-11 P0-03将CSS `display: run-in`作为保守文本边界
- 失败回归复现run-in文本与后续行内片段误拼接。通用解析器没有足够布局信息判断run-in排版，故文本提取按块级边界保守分隔，解析器升至`generic-labelled-v0.2.70`；显示可见性级联规则不变。
- 显示专项13 passed；全量离线pytest729 passed、20 skipped、17 subtests passed；标准库42 passed。20项数据库集成未设置`TEST_DATABASE_URL`而跳过。
- 仅合成HTML验证；未访问来源网站、NAS或生产数据库，未部署。真实页面准确率仍待获准样本和人工标签。

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

## 2026-11-11 P0-09挂牌观察记录
- 增加幂等数据库迁移007，记录列表页发现的来源挂牌首次/最近观察时间、观察次数和最后来源页/目标；新增认证只读分页接口。
- 发现器保留已见ID的本页观察事件，同时仍将其从详情重复抓取队列中去除。列表出现仅是一次观察，不用于断言挂牌有效、在售或自动下架。
- 标准库套件42 passed（迁移/Compose专项3 passed），Python compileall通过。pytest及项目依赖缺失；本机PostgreSQL 16 initdb在bootstrap时因shmget共享内存失败，SQL未执行；Docker socket也不可用，未运行PostgreSQL集成。未连接NAS/网站或部署。

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

## 2026-11-11 P0-09规范分页页身份比较

- 新增来源页身份比较，阻止主机大小写、尾点及显式默认443端口变体绕过分页回环保护；发现器、状态API、本地state和CLI共用。
- 定向37 passed、7 subtests passed；全量离线614 passed、15 skipped、13 subtests passed。数据库集成因无隔离测试数据库跳过。

## 2026-11-11 P0-03按CSS ASCII空白解析display值

- 仅折叠CSS ASCII空白，避免NBSP将无效内联display值转换成合法多关键字；解析器升至`generic-labelled-v0.2.59`。
- 新增失败回归；专项282 passed，全量离线609 passed、15 skipped、13 subtests passed。

## 2026-11-11 P0-03规范display CSS空白

- 折叠内联CSS属性值中的连续空白，修复多关键字display值间隔格式变化导致的错误边界；解析器升至`generic-labelled-v0.2.58`。
- 回归先失败后通过；专项281 passed，全量离线608 passed、15 skipped、13 subtests passed。

## 2026-11-11 P0-03解析display继承边界

- 显式`display:inherit`现在按可判定的祖先显示值生成文本边界，避免跨块元素伪造字段标签；解析器升至`generic-labelled-v0.2.57`。
- 新增失败回归；专项280 passed，全量离线607 passed、15 skipped、13 subtests passed。真实网页及NAS未验证。

## 2026-11-11 P0-03识别inline flow list-item

- 补齐行内多关键字`display`值的边界分类，避免跨节点字段漏提；解析器升至`generic-labelled-v0.2.56`。
- 回归先失败后通过；专项279 passed，全量离线606 passed、15 skipped、13 subtests passed。未访问网站或NAS。

## 2026-11-11 P0-03统一内联CSS文本边界与根节点评分

- 按可识别的inline `display`值处理块级分隔；语义根评分与字段解析使用相同的可见文本抽取，修复正文内联字段被误选为推荐内容的问题。解析器升至`generic-labelled-v0.2.55`。
- 三条失败回归修复后通过；补充7种大小写/重要性/单及多关键字display回归。专项278 passed，全量离线605 passed、15 skipped、13 subtests passed。README已同步当前验证数及PG16证据时效。真实网页与NAS未验证。

## 2026-11-11 P0-03补齐CENTER块边界

- 修复块级`<center>`标签未加入文本分隔集合造成的小区标签跨块粘连；解析器升至`generic-labelled-v0.2.54`。
- 新增失败回归；解析器/评估器/样本集270 passed，全量离线597 passed、15 skipped、13 subtests passed。真实页面及NAS仍未验证。

## 2026-11-11 P0-03修复行内节点拆分导致的漏提
- 文本抽取改为跨行内HTML节点保持连续、块级元素加分隔，并排除HTML注释，避免拆分标签/数值漏提及注释中的假报价污染。解析器版本`generic-labelled-v0.2.53`。
- 行内拆分/注释回归先失败后通过；解析器/评估器/样本集268 passed，全量离线595 passed、15项数据库测试跳过。未用真实页面、未访问网站或部署。

## 2026-11-11 P0-03排除折扣及参考总价
- 通用`总价`标签此前会提取`折后总价`或`成交总价`，可能伪造挂牌价或引发错误冲突。现排除带折扣、优惠、参考、成交、预估等限定词的总价；解析器版本为`generic-labelled-v0.2.52`。
- 贝壳、安居客分别覆盖12种限定词及仅有折后价的合成回归，先失败后通过；解析器/评估器/样本集266 passed，全量离线593 passed、15项数据库集成跳过。真实页面准确率未评估；未访问房源网站、NAS或部署。

## 2026-11-11 PostgreSQL 16全量测试通过
- 在断网的ARM64测试容器与临时PostgreSQL 16中运行全量pytest：**582 passed、0 skipped、13 subtests passed**，包括数据库迁移、API和P0-09分页状态集成用例。保留1条既有弃用警告。
- 测试schema已清理，临时容器/网络/依赖目录已定向删除；NAS生产数据、容器和房源网站均未接触，未部署。

## 2026-11-11 P0-09阻断持久游标单页自环
- API输入模型拒绝`next_page_url`等于`last_page_url`，避免访问历史列表缺项时反复读取同一页；失败页重试游标仍可等于`last_attempted_page_url`。
- 新增自环和失败重试契约回归。全量离线pytest 567 passed、15 skipped、13 subtests passed；数据库集成未运行。NAS只读核查确认当前部署未包含006迁移；未部署。

## 2026-11-11 状态核验
- 重试P0-08只读NAS连接：Tailscale客户端不可用，`nas-lan`和此前获准的`notedock-nas`均超时；未连接NAS、未部署或更改远程数据。当前工作区备份脚本待NAS实机复验。
- P0-07健康指标分母口径等待用户确认；本次不按推断修改健康率。

## 2026-11-11
- 修复`/api/opportunities`在session上下文关闭后读取历史价格导致的数据库错误；查询现在在连接生命周期内完成。
- 修正候选更正数据库集成测试断言，以匹配路由当前直接返回候选记录的响应格式。
- 隔离PostgreSQL 16完整测试574 passed、12 subtests passed；无数据库URL离线测试560 passed、14 skipped、12 subtests passed。未部署NAS，合成数据结果不替代真实V0.1升级验收。

## 2026-11-11 P0-09更正离线发现器错误分类
- 将state、HTML、seen-ID输入及链接解析阶段拆开处理；辅助文件错误不再误报为HTML读取错误。HTML UTF-8失败返回固定摘要，不回显样本文本/字节。
- 新增seen-ID缺失和非法ID清单CLI回归；发现状态/CLI标准库测试16 passed。两种输入选项互斥，不涉及状态污染。

## 2026-11-11 P0-01验证002–005事务失败回滚
- PostgreSQL 16隔离库中，对002–005各自生成测试副本，在事务COMMIT前注入除零SQL；逐项确认失败后新增schema对象/列/索引/触发器均无残留，再执行原版迁移成功。
- 4份迁移回滚断言通过，临时容器已删除；不替代真实V0.1备份升级或NAS PG17验收。

## 2026-11-11 P0-09避免结果管道中断后跳过链接
- 分页CLI改为先写出并flush JSON结果，成功后再保存seen IDs/next cursor；stdout出错时返回非零并保留原state，便于安全重试。
- 新增标准库BrokenPipe回归，状态字节保持不变且重跑可输出链接；P0-09仍依赖来源许可和真实列表样本。

## 2026-11-11 P0-08运行当前备份脚本的PG16往返恢复
- 临时Compose调用适配器将当前`backup.sh`连接到断网PG16测试容器；实际生成custom dump、执行`pg_restore --list`、打包synthetic raw-pages，并在另一PG16容器恢复。3条含中文/JSONB记录逐字段匹配，SHA256、tar内容和700/600权限通过。
- 临时容器及合成目录已清理；没有使用项目Compose/NAS/生产数据，P0-08仍需NAS复验当前脚本。

## 2026-11-11 P0-01合成V0.1数据迁移保真复核
- PostgreSQL 16临时隔离容器中，以合成V0.1记录执行002–005并重复执行；12张旧业务表逐表核对行数及代表字段，健康指标回填和条件单新增列默认值断言通过。
- 容器断网、无端口映射/主机挂载，完成后定向删除。迁移事务静态测试3 passed；打包器自检113个源文件与包内SHA256通过。pytest未安装，`test_package_dev.py`未能运行。未运行应用集成、未连接NAS或业务库；真实V0.1备份仍缺，P0-01继续blocked。

## 2026-11-11 P0-06对齐DTK帖子字段长度边界
- Worker的DTK规范化现在与`VideoIn`一致限制帖子ID、标题、作者名和位置字段长度；超长分享URL退回规范链接。DTK/Worker专项80 passed，全量547 passed、14项数据库集成跳过。

## 2026-11-11 同步README验证状态
- README更新为当前离线542 passed、14 skipped及DTK/Worker 75 passed，并区分此前NAS 144 passed历史验收与当前未部署代码；列明P0-01/02/04/06/07未完成项。

## 2026-11-11 P0-06拒绝DTK不可持久化文本
- `normalize_post`在DTK文本字段及帖子ID进入视频写入前拒绝NUL和孤立Unicode surrogate并抛出`DtkError`；分享URL含不可存储字符时回退到帖子ID规范链接。Worker保存脱敏失败摘要，合法Unicode保留。DTK/Worker专项75 passed，全量542 passed、14项数据库集成跳过。

## 2026-11-11 P0 API拒绝NUL文本输入
- 请求模型统一拒绝所有字段及嵌套数组中的NUL，避免PostgreSQL TEXT/JSONB写入错误；页面解析器和样本校验器也在保存/评估前拒绝普通或gzip HTML中的NUL。页面API返回422且不触碰数据库/原始证据存储。解析器版本`generic-labelled-v0.2.51`。
- 模型/采集模型/解析器/API专项233 passed，全量离线pytest 534 passed、14 skipped；3个subtests通过，保留1条既有弃用警告。

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

## 2026-11-11 P2-02机会候选分组与单次历史读取
- 按小区和户型预分组挂牌，只比较同组候选，减少无关遍历；价格历史在请求中只读取一次。
- 新增历史查询次数和异小区排除回归；pytest及依赖在本机和uv离线缓存均不可用，未执行pytest。依赖桩smoke确认历史查询一次、跨平台候选计算及异小区排除。`compileall`、JSON、差异/空白检查及109文件ZIP/包内哈希校验通过。
- 仅本地离线修改，未部署或连接真实数据源。

## 2026-11-11 P0-03防止空挂牌文本清空既有值
- 挂牌upsert的可选文本先裁剪，纯空白归一为`None`；避免空字符串通过`COALESCE`覆盖已有值。
- 新增回归；全量479 passed、14项PostgreSQL集成因缺少`TEST_DATABASE_URL`跳过。未部署。

## 2026-11-11 P0-03清除抖音账户链接空分隔符
- 账户资料URL现在识别并移除空`?`/`#`分隔符，与有值query/fragment统一规范化。
- URL规范化专项5 passed；全量478 passed、14项DB集成跳过。未部署。

## 2026-11-11 P0-03规范条件单可选筛选文本
- 条件单区域/小区可选字段裁剪首尾空白，纯空白归一为未设置，防止无效筛选意外排除挂牌。
- 新增回归；全量474 passed、14项PostgreSQL集成因缺少`TEST_DATABASE_URL`跳过。未部署。

## 2026-11-11 P0-03规范账户/视频/条件单必填文本
- 账户标识现在先裁剪再按长度校验；视频作品ID与条件单名称裁剪后拒绝纯空白。
- 新增9条回归先失败后通过；全量473 passed、14项PostgreSQL集成因缺少`TEST_DATABASE_URL`跳过。API说明同步，未部署。

## 2026-11-11 P0-03修正数据库集成来源ID样本
- 将4个贝壳/安居客API集成fixture的非数字来源ID改为随机数字ID，以匹配挂牌模型约束；V0.1迁移的直接SQL历史样本保持原值。
- 离线全量464 passed、14项PostgreSQL集成因缺少`TEST_DATABASE_URL`跳过；本轮未实际连库。

## 2026-11-11 P0-09离线链接发现基础
- 新增本地HTML挂牌链接发现器与CLI，支持来源详情URL识别、ID去重、已发现ID过滤和安全`rel="next"`路径；不联网。来源URL拒绝空`?`/`#`分隔符。
- 发现器/CLI与解析器专项146 passed；全量464 passed、14项数据库集成跳过。站点专用分页与持久失效状态待获准页面样本，P0-09未完成。

## 2026-11-11 P0-03规范正式挂牌与小区名称输入
- 正式挂牌写入会裁剪来源ID及小区名的首尾空白并拒绝纯空白；新建小区名执行相同规范化，贝壳/安居客ID格式限制继续生效。
- 新增12条回归先失败后通过；全量451 passed、14项数据库集成因缺少`TEST_DATABASE_URL`跳过。仅离线验证，未部署。

## 2026-11-11 P0-03限制挂牌写入的来源ID格式
- 贝壳/安居客挂牌ID在`ListingIn`及候选审批时验证为ASCII数字，长度分别至少8/7位，最大220位；`agent`/`other`ID仍可用自有格式。
- 无效旧候选审批409及来源边界/自有ID兼容回归通过；当时全量439 passed、14项数据库集成跳过。仅离线验证，未部署。

## 2026-11-11 P0-03校验人工纠正挂牌ID格式
- 人工纠正来源挂牌ID现限数字字符，贝壳至少8位、安居客至少7位，最多220位。
- 非数字拒绝及来源边界回归通过；全量430 passed、14项数据库集成跳过。仅离线验证，未部署。

## 2026-11-11 P0-03规范人工纠正文本字段
- 候选纠正的来源ID、标题、小区、区域、楼层、装修和审核备注统一裁剪首尾空白并拒绝纯空白值，避免无意义文本绕过非空校验。
- 新增模型回归；全量427 passed、14项数据库集成跳过。更新API说明，未部署。

## 2026-11-11 P0-03校验人工标题纠正
- 候选标题人工纠正拒绝纯空白值，并规范首尾空格。空白回归先失败后通过；全量419 passed、14项数据库集成跳过。
- 更新API契约说明；仅离线验证，未部署。

## 2026-11-11 P0-03人工纠正标题证据
- 回归锁定人工更改标题后将`field_evidence.title.source`更新为`manual_review`，不保留旧机器来源。全量418 passed、14项数据库集成跳过。
- 仅桩化数据库离线验证，未部署。

## 2026-11-11 P0-03验证标题证据进入待审队列
- 服务层回归确认`stage_html`将`field_evidence.title`来源和引用文本随候选字段保存。定向回归通过；全量418 passed、14项数据库集成跳过。
- 仅桩化数据库离线验证，未部署。

## 2026-11-11 P0-03将标题加入样本评估
- 样本清单新增必需`title`人工标签，限制500字符；缺标题必须标记`missing_fields`。评估器现按来源报告9项字段指标。
- 新增标题准确率/缺失/超长场景回归；专项233 passed，全量418 passed、14项数据库集成跳过。仅虚构样本验证工具逻辑。

## 2026-11-11 P0-03记录标题字段来源
- `field_evidence.title`记录最终采用的元数据来源（`og:title`、`h1`或`head title`）和引用文本，保持标题可追溯。解析器版本`generic-labelled-v0.2.49`。
- 三种标题来源回归通过；专项230 passed，全量415 passed、14项数据库集成跳过。仅合成HTML离线验证，未部署。

## 2026-11-11 P0-03跳过空白标题来源
- 空白`og:title`或`h1`不再阻断标题回退；选择首个非空值，优先级为`og:title`→`h1`→`head title`。解析器版本`generic-labelled-v0.2.48`。
- 空白og标题失败回归先复现后通过；专项227 passed，全量412 passed、14项数据库集成跳过。
- 仅合成HTML离线验证，未部署。

## 2026-11-11 P0-03使用head title作为备用标题
- 页面没有`og:title`或`h1`时，解析器现从`head title`提取标题；优先级为`og:title`→`h1`→`head title`。
- 失败回归先复现后通过，解析器版本`generic-labelled-v0.2.47`。专项225 passed，全量410 passed、14项数据库集成跳过。
- 仅合成HTML离线验证，未部署；刷新清单并生成新开发包。

## 2026-11-11 P0-03排除详情页交互表单
- 修复：页面`main`内筛选/询价表单的社区、面积、价格不再混入挂牌详情解析；同时排除独立按钮、选择框和文本区。
- 失败回归先复现后通过；解析器版本升至`generic-labelled-v0.2.46`。解析器/评估器/样本清单224 passed，全量409 passed、14项数据库集成跳过。
- 仅合成HTML离线验证，未部署。
- 刷新`MANIFEST.sha256`并生成同级开发包`ningbo-re-ai-v0.2-dev-2026-11-11-form-controls.zip`，由构建器验证ZIP完整性和包内哈希。

## 2026-11-11 P0-03限制页面身份元数据在head内
- 修复：canonical link、og:url和og:title只从`head`读取，避免body里的非标准伪元数据误改房源ID或标题。
- 失败回归先复现后通过；解析器版本升至`generic-labelled-v0.2.45`。解析器/评估器/样本清单223 passed，全量408 passed、14项数据库集成跳过。
- 仅合成HTML离线验证，未部署。
- 刷新`MANIFEST.sha256`并生成同级开发包`ningbo-re-ai-v0.2-dev-2026-11-11-head-metadata.zip`，由构建器验证ZIP完整性和包内哈希。

## 2026-11-11 P0-03大小写不敏感识别canonical rel token
- 修复：canonical link type按HTML标准以ASCII大小写不敏感匹配；`rel="alternate CANONICAL"`现在会参与来源ID冲突保护。
- 失败回归先复现后通过；解析器版本升至`generic-labelled-v0.2.44`。解析器/评估器/样本清单222 passed，全量407 passed、14项数据库集成跳过。
- 仅合成HTML离线验证，未部署。
- 刷新`MANIFEST.sha256`并生成同级开发包`ningbo-re-ai-v0.2-dev-2026-11-11-canonical-rel-case.zip`，由构建器验证ZIP完整性和包内哈希。

## 2026-11-11 P0-03排除template惰性元数据
- 修复：解析前移除`template`子树，避免其中的canonical/og:url或og:title覆盖真实页面房源ID和标题。
- 回归先复现后通过；解析器版本升至`generic-labelled-v0.2.43`。解析器/评估器/样本清单221 passed，全量406 passed、14项数据库集成跳过。
- 仅合成HTML离线验证，未部署。
- 刷新`MANIFEST.sha256`并生成同级开发包`ningbo-re-ai-v0.2-dev-2026-11-11-template-metadata.zip`，由构建器验证ZIP完整性和包内哈希。

## 2026-11-11 P0-03过滤折叠details摘要中的隐藏文本
- 修复：折叠`details`中的`summary`先前会在隐藏节点过滤前转成纯文本；现在隐藏的摘要子内容不会污染挂牌字段，嵌套折叠区按内层到外层处理。
- 失败回归先复现后通过；解析器版本升至`generic-labelled-v0.2.42`。折叠详情8 passed，解析器/评估器/样本清单220 passed，全量405 passed、14项数据库集成跳过。
- 仅合成HTML离线验证，未部署。
- 刷新`MANIFEST.sha256`并生成同级源码开发包`ningbo-re-ai-v0.2-dev-2026-11-11-details-summary-visibility.zip`，由构建器验证ZIP完整性和包内哈希。

## 2026-11-11 P0-03过滤content-visibility隐藏文本
- 修复：`content-visibility:hidden`及其后代不再作为可见挂牌文本；隐藏祖先下的子节点不能通过本地`visible`值恢复渲染。
- 解析器版本升至`generic-labelled-v0.2.41`。专项215 passed，全量400 passed、14项数据库集成跳过。
- 仅合成HTML离线验证，未部署。
- 刷新`MANIFEST.sha256`并生成同级源码开发包`ningbo-re-ai-v0.2-dev-2026-11-11-content-visibility.zip`，由构建器验证ZIP完整性和包内哈希。

## 2026-11-11 P0-03尊重hidden属性的display覆盖
- 修复：普通`hidden`元素含有效内联非`none` `display`时，浏览器会呈现其内容；解析器现纳入文本解析。仍排除`display:none`以及`hidden="until-found"`内容。
- 失败回归先复现后通过；解析器版本升至`generic-labelled-v0.2.40`。专项213 passed，全量398 passed、14项数据库集成跳过。
- 仅合成HTML离线验证，未部署。
- 刷新`MANIFEST.sha256`并生成同级源码开发包`ningbo-re-ai-v0.2-dev-2026-11-11-hidden-display.zip`，由构建器验证ZIP完整性和包内哈希。

## 2026-11-11 P0-08同步已确认留存策略
- 验收清单改为备份90天、原始页面证据随关联记录保留；报告工具仅列出严格早于90天的备份候选，不自动删除。
- 移除验收清单中与用户决策冲突的“正式留存期限待决定”及“待批准具体期限”表述。

## 2026-11-11 P0-03固定template惰性内容过滤
- 新增回归确认`<template>`里的广告报价不会污染可见挂牌字段；当前BeautifulSoup解析行为已满足，无需增加过滤逻辑。
- 定向1 passed，全量393 passed、14项数据库集成跳过；仅合成HTML验证。
- 刷新`MANIFEST.sha256`并生成同级源码开发包`ningbo-re-ai-v0.2-dev-2026-11-11-template-content.zip`，由构建器验证ZIP及包内哈希。

## 2026-11-11 P0-03跳过已脱离的嵌套DOM节点
- 修复：批量移除父节点后不再访问已被`decompose()`的后代标签，避免嵌套隐藏内容触发`AttributeError`。
- 覆盖`display:none`、`hidden`、关闭`dialog/details`及导航节点；专项5 passed，全量392 passed、14项数据库集成跳过。
- 仅合成HTML离线验证，未部署。
- 刷新`MANIFEST.sha256`并生成同级源码开发包`ningbo-re-ai-v0.2-dev-2026-11-11-parser-nested-removal.zip`，由构建器验证ZIP及包内哈希。

## 2026-11-11 P0-03深层HTML遍历改为显式栈
- 修复：可见性/透明度遍历遇到1,200层嵌套HTML时触发`RecursionError`；现用显式栈处理，不依赖Python递归深度。
- 定向17 passed，全量387 passed、14项数据库集成跳过；仅合成HTML离线验证。
- 刷新`MANIFEST.sha256`并生成同级源码开发包`ningbo-re-ai-v0.2-dev-2026-11-11-parser-depth.zip`，由构建器验证ZIP及包内哈希。

## 2026-11-11 P0-03过滤内联opacity零文本
- 修复：`opacity:0`和`opacity:0%`节点文本不再影响解析；零透明祖先会隐藏整个后代树，子节点不透明度不能覆盖；普通声明顺序及`!important`按内联CSS级联处理。
- 解析器升至`generic-labelled-v0.2.39`；透明度/可见性专项10 passed，全量386 passed、14项数据库集成跳过。
- 仅合成HTML离线验证，未部署。
- 刷新`MANIFEST.sha256`并生成同级源码开发包`ningbo-re-ai-v0.2-dev-2026-11-11-parser-opacity.zip`，由构建器验证ZIP及包内哈希。

## 2026-11-11 P0-03过滤内联visibility隐藏文本
- 修复：隐藏广告文本不再污染挂牌字段；对`visibility:hidden/collapse`递归移除隐藏文本，并保留后代显式`visibility:visible`的内容。
- 解析器版本升至`generic-labelled-v0.2.38`。覆盖隐藏广告、可见后代和三种`!important`级联组合；定向11 passed，全量380 passed、14项数据库集成跳过。
- 仅合成HTML离线验证，未部署。
- 刷新`MANIFEST.sha256`并生成同级源码开发包`ningbo-re-ai-v0.2-dev-2026-11-11-parser-visibility-cascade.zip`，由构建器验证ZIP及包内哈希。

## 2026-11-11 P0-03精确比较解析精确率门槛
- 修复：95%达标判定不再依赖四舍五入后的显示值，改为基于抽取正确数和抽取总数的整数比较，避免94.997...%被显示成95.00%后误报达标。
- 验证：1,899/1,999回归先失败后通过；门槛专项4 passed，全量375 passed、14项数据库集成跳过。
- 仅合成数据离线验证，未部署。
- 刷新`MANIFEST.sha256`并生成同级源码开发包`ningbo-re-ai-v0.2-dev-2026-11-11-precision-threshold.zip`，ZIP及包内哈希由构建器验证。

## 2026-11-11 P0-04 HTTP响应有界读取
- 修复：受控HTTP客户端改为流式读取页面与robots响应，按64 KB分块分别限制1 MB和256 KB；超限时提前停止，避免读取后才限长造成不必要的内存占用。
- 验证：超大页面/robots模拟流回归先失败后通过；HTTP专项17 passed，全量374 passed、14项数据库集成跳过；compileall通过。
- 未联网或部署，来源在线状态不变。

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

## 2026-11-11 — 拒绝会被数据库静默舍入的数值输入
- 挂牌、条件单和候选纠错数值现在校验PostgreSQL两位小数精度；等价尾随零接受并规范化，超出精度且数值会变化的输入返回验证错误。
- 模型专项7 passed；全量356 passed、14项数据库集成跳过。未部署NAS。

## 2026-11-11 — 静态复核P0-01迁移的非破坏性
- 阅读002–005确认迁移仅添加采集结构、健康汇总和条件单字段；未发现删表/删业务行语句。
- TEST_DATABASE_URL未配置，本机无PostgreSQL响应；未执行迁移。此检查不替代真实V0.1备份升级。

## 2026-11-11 — 固定可比面积10%阈值的Decimal边界
- 面积差改用Decimal计算；±10%边界纳入、±10.01%排除，修复float舍入不对称。
- `tests/test_opportunities.py` 16 passed；全量349 passed、14项数据库集成跳过。NAS未部署。

## 2026-11-10 — 修复可比面积10%边界的浮点误差
- 相对面积差改用Decimal和目标挂牌面积作分母，使恰好+10%与−10%边界处理一致。
- 先失败后通过回归；全量347 passed、14项数据库集成跳过。NAS未部署。

## 2026-11-10 — 排除户型未知挂牌的可比价信号
- 修复目标户型和可比挂牌户型都为空时仍被当作相同户型、误生成折价机会的问题。
- 先失败后通过回归；全量345 passed、14项数据库集成跳过。NAS未部署。

## 2026-11-10 — 锁定证据上限后的字段冲突检测
- 添加回归，确认第21条报价/面积命中即使不在候选的前20条展示证据中，仍参与冲突判定并阻止候选ready。
- 定向2 passed；全量344 passed、14项数据库集成跳过。解析器实现未改，真实页面未验证。

## 2026-11-10 — 复核P0-03评估器并刷新离线回归
- 审阅样本标注与评估安全边界，未发现可复现误通过，不改解析器代码。
- 全量离线测试342 passed、14项数据库集成跳过；仅本地合成输入，真实样本/数据库/NAS未验证。

## 2026-11-10 — 对齐健康指标验收状态
- 发现健康API当前提供来源计数，但验收要求的四种比率没有实现；将P0-07标为进行中并记录口径待确认，不擅自定义解析成功/字段完整规则。
- 本轮仅更新项目状态文档和目标记录；未改代码、数据库或部署状态。

## 2026-11-10 — 评估器拒绝截断后漏检的多报价样本
- 增加回归覆盖第二个标注报价出现在35,000字符文本上限之后的情形；`multiple_prices`场景不会误计通过。
- 样本清单/评估专项95 passed，全量342 passed、14项数据库集成跳过。仅合成HTML验证。

## 2026-11-10 — 验证上传API返回不完整解析状态
- 新增`POST /api/collection/pages`端到端路由回归，确认截断HTML候选返回pending、`visible_text_truncated`和`ready_for_review=false`。
- 专项136 passed，全量341 passed、14项数据库集成跳过；API真实执行、数据库使用假连接。

## 2026-11-10 — 验证截断警告经候选存储返回
- 服务层回归确认`visible_text_truncated`随候选持久化，且从持久化字段/警告计算`ready_for_review=false`。
- 专项135 passed，全量340 passed、14项数据库集成跳过；服务测试使用假连接，不代表真实PostgreSQL/NAS验收。

## 2026-11-10 — 标记可见正文截断并阻止候选报为ready
- 正文超过35,000字符抽取上限时新增`visible_text_truncated`警告，且`ready_for_review`返回false，避免截断后的字段冲突漏检；解析器版本`generic-labelled-v0.2.35`。
- 新增截断点后含第二个报价的回归；专项125 passed，全量339 passed、14项数据库集成跳过。仅合成HTML离线验证。

## 2026-11-10 — 识别含CSS注释的隐藏挂牌区域
- 内联样式解析先移除CSS注释，再按声明顺序及`!important`识别`display:none`；解析器版本升至`generic-labelled-v0.2.34`。
- 新增注释内含分号、display覆盖顺序及隐藏广告伪冲突回归；专项124 passed，全量338 passed、14项数据库集成跳过。仅离线合成HTML验证。

## 2026-11-10 — 排除嵌入元素备用文本
- HTML解析器不再把iframe、object、embed、canvas中的备用内容混入挂牌可见文本；解析器版本升至`generic-labelled-v0.2.33`。
- 新增iframe/object/canvas伪报价冲突回归；专项121 passed，全量335 passed、14项数据库集成跳过。仅离线合成HTML验证。

## 2026-11-10 — 清除抖音账户URL的query和fragment
- 通过域名/协议校验的Douyin主页URL在作为`account_ref`保存或传给DTK前移除query和fragment，避免保留分享跟踪参数；路径身份不变。
- 模型/DTK专项75 passed，全量离线332 passed、14项数据库集成跳过；真实账号联调未做。

## 2026-11-10 — 修复抖音主页URL大小写校验绕过
- 主页URL现统一校验HTTPS方案、douyin.com域名、userinfo、端口和控制字符；修复大写`HTTPS://`绕过检查后被DTK当成URL发送的问题。
- 模型/DTK专项74 passed，全量离线331 passed、14项数据库集成跳过；未连接DTK或真实账号。

## 2026-11-10 — 防止已领取任务越过来源许可撤销
- 执行端重读并共享锁定最新来源策略至抓取及暂存结束；新增旧任务遇撤销时HTTP前阻断及有效策略正向服务回归。另添加双连接PostgreSQL锁集成回归，但因没有`TEST_DATABASE_URL`本轮跳过。
- 服务/模型/策略专项19 passed，全量离线328 passed、14项数据库集成跳过；在线来源保持关闭。

## 2026-11-10 — 在线抓取前重读并锁定来源权限
- 任务执行时重新读取`source_registry`权限，不信任领取目标时的旧快照；对当前策略行加`FOR SHARE`锁并保持到抓取与样本暂存完成，防止已领取任务越过并发撤销。新增撤销竞态与有效策略正向服务回归。
- 服务/模型/策略专项19 passed，全量离线328 passed、13项数据库集成跳过。未在真实PostgreSQL执行锁并发测试，未启用在线来源。

## 2026-11-10 — 验证在线任务在权限关闭时不发HTTP请求
- 服务层`run_collection_target`增加离线回归：全局/来源开关关闭、策略未批准或许可引用空白时均返回`blocked_policy`且不调用HTTP抓取器。批准状态的引用仍仅是非空文本，不证明授权效力。
- 服务/模型/策略专项17 passed，全量离线326 passed、13项数据库集成跳过。

## 2026-11-10 — 批准来源策略必须带非空许可引用
- `PolicyReviewIn`现在拒绝仅含空白的`policy_reference`与`approved`状态，避免策略状态误导；这不验证许可内容真实性，也不会启用在线采集。
- 模型/策略专项10 passed，全量离线322 passed、13项数据库集成跳过。

## 2026-11-10 — 解析评估报告显示样本构成
- `sample_composition`按来源公开各挂牌状态及场景标签计数，便于检查数据构成；清单校验规则未改。样本指南与验收标准同步。
- 专项175 passed，全量离线322 passed、13项数据库集成跳过。仅合成清单验证，未得到真实准确率结论。

## 2026-11-10 — 补齐解析评估快照竞态与零覆盖率回归
- 校验与计分共用同一清单快照，竞态回归覆盖替换清单后恢复原文件；零抽取时精确率为null、覆盖率为0，95%门槛不达标。
- 专项175 passed，全量离线322 passed、13项数据库集成跳过。仅合成输入验证；真实样本准确率仍未验证。

## 2026-11-10 — 解析评估校验与计分共用清单快照
- evaluator将清单内容读为不可变快照；validator和评估指标都使用同一版本，并在结束时复查磁盘清单与报告指纹一致。新增替换清单后恢复原文件的竞态回归，防止评分读取另一个版本。
- 专项174 passed，全量离线321 passed、13项数据库集成跳过。仅合成输入验证；真实样本准确率仍未验证。

## 2026-11-10 — 给解析评估增加输入指纹与竞态保护
- 报告记录manifest SHA-256；评估前后检查清单未变化，逐个验证样本字节仍匹配清单哈希，避免校验后文件变化造成报告不可复现。
- 解析器/样本/评估专项173 passed，全量离线320 passed、13项数据库集成跳过。仅离线验证；真实样本准确率仍未验证。

## 2026-11-10 — 验证千分位数值跨格式等值
- 页面/人工候选间`1,234`与`1234`等值核对；重复候选`1,234|1234.0`按数值去重并拒绝。合法千分位与未分组页面提及不触发假冲突。
- 专项171 passed，全量离线318 passed、13项数据库集成跳过；仅合成页面回归。

## 2026-11-10 — 集中共享严格数值格式
- `NUMERIC_TEXT_PATTERN`现在由parser模块统一提供，parser、样本validator和评估器共用，防止千分位规则漂移。
- Parser/样本/评估专项169 passed，全量离线316 passed、13项数据库集成跳过；原有合法/错误分组回归维持通过。

## 2026-11-10 — 统一面积/报价候选的千分位解析
- 样本validator与解析evaluator现接受严格三位分组的千分位面积/报价数值，并按Decimal去逗号后的数值对账；`12,34`等畸形分组拒绝。人工标注文档同步。
- 专项169 passed，全量离线316 passed、13项数据库集成跳过；真实页面仍未校准。

## 2026-11-10 — 增加单个越界户型评估场景
- 新增`invalid_bedrooms`及`invalid_bedroom_candidates`，要求一个21–99整数、字段置空并核验`invalid_bedrooms_mentions`证据；与`multiple_bedrooms`互斥。最终有效户型仍限0–20。模板/validator为29列。
- 专项83 passed，全量311 passed、13项数据库集成跳过。仅虚构页面回归。

## 2026-11-10 — 保留越界户型冲突候选
- `bedroom_candidates`现在允许0–99整数原始页面提及，使`3室/21室`能按`multiple_bedrooms`完成证据对账；最终人工`bedrooms`仍限制为0–20。
- 专项75 passed，全量离线303 passed、13项数据库集成跳过。仅合成页面验证。

## 2026-11-10 — 将URL与canonical房源ID冲突纳入样本评估
- 新增`source_id_conflict`/`source_listing_id_candidates`，记录冲突ID并保持正式ID为空；校验器核验来源格式、去重及包含详情URL ID，评估器逐一对账完整解析证据并拒绝截断。模板/validator同步为28列。
- 专项154 passed，全量离线301 passed、13项数据库集成跳过；仅合成HTML验证，未完成真实样本校准。

## 2026-11-10 — 将建筑面积冲突纳入解析评估
- 新增`multiple_areas`与`area_candidates_sqm`；validator拒绝非有限、非正数和超过20000㎡的候选，evaluator精确核对解析证据集合及截断状态。样本人工标注指南同步更新，模板与validator均为27列。
- 专项148 passed，全量离线295 passed、13项数据库集成跳过；只用合成页面验证，真实解析准确率仍未知。

## 2026-11-10 — 解析评估显式报告95%抽取精确率门槛
- 每字段评估结果新增`precision_target_pct`/`precision_target_met`；95%阈值只针对已抽取值的严格匹配率，覆盖率与每站20份样本门槛独立报告。
- 边界回归确认19/20=95%达标、18/20=90%未达标；专项59 passed，全量离线287 passed、13项数据库集成跳过。真实样本指标仍未验证。

## 2026-11-10 — 补齐小区歧义样本标注约束
- `SAMPLE_DATASET.md`现在明确列出`multiple_communities`及其人工候选要求；样本清单回归覆盖小区候选重复和未标对应场景标签两种拒绝条件。模板与validator仍为26列精确一致。
- 专项138 passed，全量285 passed、13项数据库集成跳过。未获得获准真实样本；无网站/NAS/数据库操作。

## 2026-11-10 — 将小区歧义候选纳入样本对账
- 样本模板/validator新增`community_candidates`并支持`multiple_communities`；评估器要求证据候选集合与人工候选一致，缺证据、集合不符或证据截断均判失败。样本数据说明同步覆盖小区候选列。
- parser/样本/评估专项136 passed；全量离线pytest 283 passed、13项数据库集成跳过。没有真实站点准确率结论；未访问网站/NAS或部署。

## 2026-11-10 — 兼容DTK空字符串游标哨兵
- metadata中的`next=""`现在表示无游标；空格/Tab游标仍作为格式错误拒绝。保留显式`has_more=false`优先级。
- DTK/Worker/模型专项72 passed，全量离线267 passed、13项DB集成跳过。真实DTK联调未进行。

## 2026-11-10 — 拒绝DTK空白分页游标
- 解析器现在拒绝空格/Tab构成的游标，避免把空令牌发给DTK；数字游标`0`仍合法并转为`"0"`。
- DTK/Worker/模型专项71 passed，全量离线266 passed、13项DB集成跳过；未连接真实DTK/NAS。

## 2026-11-10 — DTK仅给游标时继续分页
- 缺少`has_more`的响应曾因默认false而静默结束，即使响应提供下一页游标。现在仅当payload和cursor metadata均未给`has_more`时由游标存在性推断；明确false仍停止。
- DTK/Worker/模型专项68 passed，全量离线263 passed、13项DB集成跳过。真实DTK联调未进行。

## 2026-11-10 — 修正DTK对大小写HTTPS主页URL的识别
- 模型接受大小写合法的HTTPS scheme，但DTK客户端曾仅识别小写`https://`，导致合法主页URL被错传为`sec_user_id`。现在按URL scheme解析且忽略大小写，URL值保持不变。
- 回归先失败后通过；DTK/Worker/模型专项66 passed，全量离线261 passed、13项DB集成跳过。未联调真实DTK或NAS。

## 2026-11-10 — 覆盖正式20份样本门槛边界
- 增加恰好20份/来源的离线评估用例：默认验收参数下两站`sample_requirements.met`均为true；5份/来源诊断结果仍为false。虚构样本不作为真实准确率。
- 样本/评估/留存专项57 passed；全量离线259 passed、13项DB集成跳过。未连接或写入NAS。

## 2026-11-10 — 复核NAS 90天备份库存与留存报告版本
- 只读扫描确认超期备份0个/0字节、raw-pages仅占位文件2个/249字节、关联候选0行，没有清理文件。NAS报告脚本仍为仅汇总旧版本，且`sheng`无raw-pages读取权限时显式失败；工作区逐路径列报版仍未同步。
- `tests/test_storage_report.py` 12 passed；NAS未写入、未改ACL或清理数据。

## 2026-11-10 — NAS只读复核API-only更新边界
- 只读确认DXP4800上的API/Worker运行、PostgreSQL 17 healthy，`/healthz`=200；贝壳/安居客在线关闭，候选/挂牌/条件单为空；现有V0.2备份清单哈希验证通过，未发现V0.1数据库备份。
- 当前运行API镜像缺少工作区最新按来源解析模块，且候选服务/解析器哈希不匹配；部署需要整体构建API镜像，不能只替换单文件。本轮没有NAS写入、备份、传输或容器操作。

## 2026-11-10 — 解析报告显示正式样本门槛
- 解析评估结果现在逐站显示正式最低样本数20、实际数量及是否达标。降低CLI校验门槛进行小样本诊断时，也不会让输出看起来像满足了正式样本量。
- 回归先失败后通过；样本校验/评估专项44 passed，全量离线pytest 258 passed、13项数据库用例跳过。未验证真实页面准确率或NAS部署。

## 2026-11-10 — 为来源房源ID记录出处并最小化canonical证据
- 候选ID现标记来自提交URL或canonical/og:url；冲突仍不采信ID。canonical evidence quote仅保留标准房源路径后缀和ID，去掉query/fragment及路径前缀。
- 解析器版本升至`generic-labelled-v0.2.27`；专项122 passed，全量离线pytest **258 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`）。未运行数据库集成或NAS部署，未取得真实样本。

## 2026-11-10 — 为冲突网页字段保留有限原文证据
- `field_evidence`现在为冲突/越界字段记录最多20条候选值、可见文本片段和偏移，并标记总数及截断；解析字段仍留空。解析器版本升至`generic-labelled-v0.2.26`。人工更正清除对应旧解析命中并标记`manual_review`。
- 相关专项121 passed；全量离线pytest **257 passed、13 skipped**（均需数据库URL）。本机uv缓存依赖运行，未联网安装；未运行数据库集成、真实样本或NAS部署。
- 开发包`ningbo-re-ai-v0.2-dev-2026-11-10-p0-03-conflict-evidence.zip`由项目打包脚本生成并完成ZIP/包内SHA校验。

## 2026-11-10 — 为网页候选记录逐字段证据出处
- 贝壳/安居客保守解析器现在为可见文本命中的挂牌属性保存原文片段、归一化文本偏移和`not_calibrated`状态；解析器版本升至`generic-labelled-v0.2.25`。人工改正字段改标为`manual_review`。
- 解析器/候选修正/评估器/样本清单专项120 passed；全量离线pytest **256 passed、13 skipped**，均为需`TEST_DATABASE_URL`的数据库集成用例。未联网安装pytest，使用本机uv缓存。临时PG16测试环境预检时socket绑定被沙箱拒绝，未启动数据库集群；未获得真实样本、未部署NAS。
- 按项目交付流程刷新`MANIFEST.sha256`并生成经过完整性/包内SHA校验的开发ZIP。

## 2026-11-10 — 为视频规则提示记录字段证据来源
- `extracted_fields`提示现在保存匹配字段、值、OCR/转写/标题/描述来源、匹配原文及来源内字符偏移，并标明置信度未校准；不把提示升级成挂牌事实。
- 新增两个pytest回归用例；当前环境缺pytest无法启动。3条等价直接断言及`compileall`通过。未连接NAS或真实视频样本，无数据库迁移/配置变化。

## 2026-11-10 — 报告90天外备份的相对路径
- 只读留存报告现在列出每个超期文件的相对路径及数量/体积，按路径稳定排序，便于人工核对具体备份集；保留严格早于90天边界，脚本不会删除文件。
- storage_report专项12 passed；全量默认测试252 passed、13个数据库用例跳过。尚未同步NAS。

## 2026-11-10 — 核实P0-03本地修复尚未部署
- NAS只读复核确认当前API/Worker运行、DB healthy、业务表为空、两来源OFF；NAS旧版`collection_service.py`哈希与本地修复版不同。
- 本轮无NAS写入/备份/容器重建；264 passed为本机PG16隔离测试结果。

## 2026-11-10 — 修复候选重提SQL的psycopg百分号占位符
- PostgreSQL集成测试发现候选重提查询中的`LIKE 'operator_note:%'`被psycopg误解析。将SQL字面百分号改为`%%`，并同步更新SQL构造回归断言。
- 临时PostgreSQL 16隔离库完整测试：264 passed、0 skipped；停止并清理临时实例。无生产数据库、NAS或配置变更。

## 2026-11-10 — P0-03修复来源解析器重构调用点
- 测试改用统一`parse_listing_html`分发入口；HTTP客户端改从`url_policy`导入`check_source_url`，防止旧符号引用导致导入/测试失败。
- 来源ID边界及按source路由的8项桩化smoke、Python 3.12语法编译通过；HTML解析pytest未运行（项目依赖缺失）。

## 2026-11-10 — P0-03同步站点解析器架构说明
- 架构文档和README说明当前站点路由适配器、通用解析基线和真实样本校准缺口，避免把路由拆分误读为已完成站点解析。

## 2026-11-10 — P0-03添加下架/缺字段合成失败fixture
- 新增明确标识为合成的贝壳下架页和安居客缺字段页，并增加站点分发入口回归，检查不臆造挂牌字段/未知ID且不能进入审核。
- 测试语法编译通过；pytest未运行（环境缺少pytest），不代表真实样本解析或授权。

## 2026-11-10 — P0-03拆出贝壳/安居客解析入口
- 新增Beike/Anjuke解析器模块与按来源分发器，并将候选采集、离线评估和负载测试切换到统一入口。
- 适配器现阶段明确委托通用保守解析器，不以演示fixture冒充站点专用准确率。语法编译和两个桩化路由smoke通过；项目依赖缺失，未运行真实HTML解析pytest。

## 2026-11-10 — P0-03修正解析器版本断言
- 将canonical冲突测试的`.2.23`字面量改为导入`PARSER_VERSION`并按当前解析器版本断言，修复版本升级后测试必然失败的问题。
- py_compile通过；完整/定向pytest未运行，当前环境缺pytest。

## 2026-11-10 — P0-06拒绝首尾C0/C1分享链接控制字符
- 原始分享URL现在在`strip()`前拒绝所有C0/C1控制字符，包括首尾Tab和换行，避免清洗后接受；普通首尾空格仍会裁剪。
- 6个直接函数smoke场景和`py_compile`通过；完整pytest因缺少pytest/httpx未运行。

## 2026-11-10 — P0-03优先选择非空语义内容区
- HTML解析器改为优先使用非空`<main>`/`<article>`，避免导航中更早出现的`.content`抢先入选，也避免空`<main>`挡住后续文章内容。
- 新增两项合成HTML回归，版本升至`generic-labelled-v0.2.24`。当前环境缺pytest/BeautifulSoup，未运行解析器测试；不代表真实页面布局准确率。

## 2026-11-10 — P0-01迁移命令采用单事务
- V0.1升级指南对没有内建事务的002/003/005加`psql --single-transaction`，任一SQL失败时整份文件回滚；004自带`BEGIN/COMMIT`，避免嵌套包装。
- 仅更新运行手册，未运行PostgreSQL/NAS迁移。
- 标准库静态断言通过002/003/005单事务包装及004内建事务边界；未执行SQL运行时验证。

## 2026-11-10 — P0-01强化V0.1迁移字段保真回归
- 隔离V0.1→V0.2数据库用例现在对核心旧表核对代表性字段内容，不止检查记录数；包含账号/视频、社区/房源/挂牌、价格证据、匹配、条件单及通知状态，并重复执行迁移。
- Python语法编译通过；因当前环境无pytest/httpx/psycopg依赖及`TEST_DATABASE_URL`，本轮没有运行PostgreSQL集成用例。该测试不替代真实V0.1备份升级验收。

## 2026-11-10 — P0-06拒绝首尾C1控制字符
- U+0085属于Python空白字符，会被`str.strip()`移除；原实现因此漏过首尾C1。现于裁剪前拒绝原始输入中的C1控制字符，同时保留普通首尾空白裁剪。
- 新增前置C1回归；5个直接函数smoke场景通过。完整pytest因环境缺少pytest/httpx未能启动，前序240 passed记录不视作本轮独立验证。
- 仅本机离线验证，未连接DTK/NAS或访问来源网站。

## 2026-11-10 — P0-06 DTK分享URL空白/C1控制字符拒绝
- `_safe_post_url`在URL拆分前拒绝内部空格、Tab和C1控制字符，防止原始分享链接含不可见分隔字符；首尾普通空白继续裁剪，无效值回退到作品ID规范URL。
- DTK/Worker专项56 passed；全量pytest 240 passed、13 skipped（需`TEST_DATABASE_URL`）。保留既有Starlette/httpx弃用警告。
- 仅本机离线验证，未连接DTK/NAS或访问房源来源网站。
- 离线开发包已重建，包含98个源码/文档文件；ZIP和包内SHA256清单校验通过。

# 目标驱动开发路线图 / 可追踪任务池

> 任务状态由测试事实决定。`[x]` 表示本地实现/静态或单元测试完成，**不代表已在NAS上线或已对网站真实采集成功**。每轮结束在 `docs/PROJECT_STATUS.md` 写结果。

## V0.2 已实现（仍需NAS集成验收）
- [x] Docker Compose API+Worker+PostgreSQL基础原型（源自V0.1，容器启动未验证）
- [x] 指定抖音作者账号登记、增量轮询适配器、历史策略；等待 DTK 真实联调
- [x] 微信视频号导出JSON导入工具；尚未实现无人值守持续监控
- [x] 小区表、来源挂牌表、价格历史、同套候选复核、条件单和提醒 outbox
- [x] 贝壳/安居客来源矩阵及权限状态、默认关闭的在线采集任务框架
- [x] 保存的HTML样本解析 → gzip/SHA256证据 → 待审核候选 → 人工更正/批准/拒绝
- [x] 候选审批与挂牌快照在同一数据库事务中执行；不会把网页自动解析直接写正式挂牌
- [x] robots检查、HTTPS域名白名单、对403/429中止的单元测试
- [x] 主提示词、AGENTS.md、数据字典、PRD、验收清单、迁移指南

## P0｜工程可用性和真实数据质量（第一开发优先级）
- [blocked] **P0-01 NAS升级实测**：V0.1数据库备份→执行 `002_collection_pipeline.sql`→V0.2 Compose→API/Worker健康，重启后数据保留；记录真正执行结果。2026-11-09已在NAS完成空库V0.2新装、API/Worker/DB运行与DB容器重启持久化验证，但NAS没有既有 `ningbo-re-ai` V0.1项目或同名卷，无法完成V0.1备份升级。NAS的8787端口由 `nas-image-manager` 占用，新实例绑定127.0.0.1:8788；2026-11-10 Mac解锁后已在UGREEN详情页确认项目运行中、Compose路径正确且API/PostgreSQL 17/Worker均运行。补充本机隔离PostgreSQL 16合成旧库schema迁移测试10 passed，不能替代真实NAS旧库和备份验收。
- [ ] **P0-02 采集样本集**：各平台至少20份经允许使用的宁波详情页样本，涵盖在售/下架/字段缺失/同页多个价格/未知ID；保存时间和来源。已提供离线清单模板及本地元数据/哈希/标签覆盖校验器；`.html.gz`按解压内容去重并拒绝损坏流。真实获准样本仍缺，fixture不计数。
  - 2026-11-10补充：API样本提交与在线目标共享URL校验，拒绝来源URL query/fragment，避免跟踪信息或临时令牌持久化/被请求；canonical的query/fragment仅在来源ID比较时去除。离线测试通过，来源仍保持OFF。
  - 2026-11-10补充：解析入口、API模型、在线目标和本地样本清单统一限制来源URL为12–2000字符，拒绝离线评估中不可能经API提交的超长URL。
  - 2026-11-10补充：主来源URL解析错误归一化为输入异常；畸形canonical URL不会中断合法页面的字段解析。解析器版本`generic-labelled-v0.2.15`，离线验证通过。
  - 2026-11-10补充：面积、挂牌价和户型按数值等值比较，避免`160`/`160.0`等表示误触发字段冲突；解析器版本`generic-labelled-v0.2.16`。仅离线验证，真实站点数据质量仍待获准样本。
  - 2026-11-10补充：格式损坏的数值标注不再因Decimal解析异常中断；与有效值并存时保守保留冲突告警。解析器版本`generic-labelled-v0.2.17`，仅离线验证。
  - 2026-11-10补充：面积/价格的逗号分组按千分位语法校验，避免畸形数字被压缩成另一个有效数值；标准千分位仍可解析，版本`generic-labelled-v0.2.18`。
  - 2026-11-10补充：来源URL出现userinfo段即拒绝，包括空用户名/密码形式；共享URL校验与样本清单一致，版本`generic-labelled-v0.2.19`。
  - 2026-11-10补充：来源主机只允许规范化单个DNS根尾点，额外尾点不通过allowlist；版本`generic-labelled-v0.2.20`，仅本地验证。
  - 2026-11-10补充：样本校验器的贝壳/安居客详情URL ID长度边界与解析器统一为8–220/7–220位；221位URL ID可正确标注为unknown_id，专项81 passed。
  - 2026-11-10补充：解析准确率的面积/挂牌价数值比较取消两位小数舍入，避免亚分位差异被计成严格匹配；专项83 passed，无真实样本准确率结论。
  - 2026-11-10补充：提交URL无ID时可由唯一合法同源canonical/og:url详情ID补足；相互冲突仍留空并告警，解析器generic-labelled-v0.2.21，专项87 passed。
  - 2026-11-10补充：样本校验器调用解析器共享的房源ID URL提取函数，避免重复规则漂移；项目虚拟环境CLI与全量202 passed通过。
  - 2026-11-10补充：API、采集目标及离线解析共享校验只允许宁波主机nb.ke.com/ningbo.anjuke.com，防止其他城市页面进入本地候选；专项109 passed，解析器v0.2.22。
  - 2026-11-10补充：样本清单复用解析器共享URL/ID校验，移除重复维护的宁波主机规则；专项96 passed、全量211 passed/11项数据库用例跳过。
  - 2026-11-10补充：共享URL校验拒绝原始空白/控制字符，清单不再先strip URL，在线请求前阻断；专项117 passed、全量223 passed。解析器generic-labelled-v0.2.23。
  - 2026-11-10补充：同一URL/HTML重提会刷新解析器版本变化后的待审未更正候选，人工更正/已审核候选保留不变；可运行专项123 passed，PG集成用例因本机环境限制尚未运行。 ready_for_review依据最终返回的已存字段计算。
  - 2026-11-10补充：样本路径仅允许`.html`或`.html.gz`；不支持的`.txt`扩展名新增拒绝回归，样本校验/评估专项30 passed。
  - 2026-11-10补充：CSV表头拒绝模板未定义的额外列，防止错字段被静默忽略或个人联系信息随清单混入；回归先失败后通过，P0-02仍待获准真实样本。
  - 2026-11-10补充：清单CSV无效UTF-8现在返回可读错误并将计数归零，不再抛未处理解码异常；真实样本仍待获准。
  - 2026-11-10补充：样本`html_path`在构造Path前拒绝C0/C1控制字符，覆盖换行、NUL及C1，避免静默清洗或未处理路径异常。
  - 2026-11-10补充：样本清单启用严格CSV引号语法，畸形引号明确报错且计数归零；修复前回归复现宽松解析误收。
  - 2026-11-10补充：本地样本校验/评估共享有界读取，HTML解压体≤1,000,000字节、gzip输入≤2,000,000字节；超限前置拒绝，样本路径根或组件符号链接拒绝。专项15 passed。真实获准样本仍缺，不报告站点准确率。
  - 本地导入CLI现在在API请求前以有界读取拒绝超过1,000,000字节的非UTF-8 HTML；专项1 passed，未访问来源网站。
  - API在鉴权/模型解析前将HTML上传请求体限制为6,100,000字节；清单、CLI、API字段和解析器统一将HTML限制为1,000,000 UTF-8字节，超限请求返回413。全量默认133 passed、11项数据库测试跳过；NAS部署待连接恢复；本轮LAN SSH超时，Tailscale CLI无法读取偏好且App可执行文件缺失。
  - 样本校验器拒绝人工复核时间早于页面采集时间的记录，并按时区偏移比较；专项11 passed。此校验不替代许可核验或真实样本验收。
- [in_progress] **P0-03 站点解析器**：`app/collectors/beike.py`、`anjuke.py`，基于P0-02样本做字段提取、布局版本处理和失效检测；不把fixture演示当生产可用。现有通用基线已增加canonical/og:url与提交URL房屋ID冲突时的保守阻断；新增离线清单评估器，可按字段报告准确率/覆盖率并验证异常场景。每站20份获准真实样本仍缺，当前不生成真实站点准确率结论。
  - 2026-11-10补充：解析器将0至20作为卧室数输出范围；`21室`等超范围值留空并告警`invalid_bedrooms_mentions`，版本`generic-labelled-v0.2.10`。仅离线回归，真实样本仍缺。
  - 2026-11-10补充：URL来源ID最长按正式模型220字符处理；超长ID留空、不能使候选ready，样本人工ID标签也拒绝超长。解析器版本`generic-labelled-v0.2.11`，相关离线测试62 passed；真实页面准确率仍未验证。
  - 2026-11-10补充：解析器排除语义`aside`、HTML隐藏属性、`aria-hidden=true`及内联`display:none`内容，避免可识别的推荐/隐藏报价污染详情候选；规则版本为`generic-labelled-v0.2.3`，专项18 passed。外部CSS、真实布局与准确率仍待获准样本验收。
  - 2026-11-10补充：内联`display`按声明顺序及`!important`优先级判断最终值，避免把`display:none;display:block`的可见详情误删；版本为`generic-labelled-v0.2.5`，解析器专项24 passed。外部样式表、真实布局和字段准确率仍待获准样本。
- [in_progress] **P0-04 在线采集可行性及政策核验**：2026-11-10复核贝壳当前协议及安居客官网协议入口/官方PDF；两者均没有本项目书面许可，安居客PDF未标版本日期。贝壳协议标注2026-09-24更新、09-25生效；通过nas-lan核验实际origin robots：`nb.ke.com` 对项目UA详情路径 `can_fetch=False`，`ningbo.anjuke.com` 为 `True`，但robots允许不等于使用授权。安居客官网协议中心展示协议及历史版本目录；官方静态域名PDF明确要求抓取取得特别书面许可并遵守Robots，但文件无版本日期且中心正文未被解析，尚不能确认当前有效版本；未绕过、未访问详情页。采集器已增加HTTP 200验证码/挑战页识别并记`blocked_upstream`，不重试、不把挑战正文送入解析。在线采集保持OFF，须取得明确用途许可并核实适用协议后才能完成。已准备[`SOURCE_PERMISSION_REQUEST_TEMPLATE.md`](SOURCE_PERMISSION_REQUEST_TEMPLATE.md)供逐平台填写与复核，尚未发送。
- [x] **P0-05 完整数据库API集成测试**：NAS隔离PostgreSQL 17专用测试库运行数据库集成用例7项全部通过，覆盖索引与汇总迁移幂等/回填、候选审批事务回滚/幂等、健康触发器插入/更新/删除及挂牌观察时间回退/来源迁移、历史价格保护、通知去重和连接错误脱敏。另完成10k run/10k candidate批量触发器一致性验证。隔离资源已清理；未迁移或写入生产库。
  - 2026-11-10本轮完整套件在一次性本机PostgreSQL 16 `rehouse_test`中144 passed、0 skipped；只监听Unix socket，测试后已停止并清理。该结果不替代NAS PostgreSQL 17/生产部署验收。
- [ ] **P0-06 DTK联调**：在NAS单独启动DTK，检查作者ID、接口版本/权限，连续监控至少3个有权限的抖音账号24小时。`app/dtk.py`离线增强了上游响应结构校验和异常类型处理；`app/worker.py`遇到`has_more=true`却无游标时记录`partial`而非误报成功。以上本机逻辑仍不代表真实版本/权限验证或账号联调。
  - 2026-11-10补充：分享URL在`urlsplit`前拒绝内部空格、Tab与C1控制字符，无效链接回退canonical；专项56 passed，全量240 passed、13项PostgreSQL集成跳过。仅本机验证，真实DTK/账号联调仍待完成。
  - 2026-11-10补充：异步任务轮询遇到缺失/空白/非字符串`state`时立即结构失败，失败详情不回显上游内容；DTK专项30 passed。真实接口状态语义、NAS版本/权限和3个获准账号24小时联调仍未验证。
- [x] **P0-07 运营指标**：新增并在NAS验证 `GET /api/collection/health`，按来源提供成功/失败/阻断、候选审核状态、挂牌数量、最近尝试/成功/观察时间、最新状态/原因和双重在线开关；合成集成数据验证后已清理。
- [x] **P0-08 容灾/安全**：NAS备份恢复、日志脱敏、内网控制与隔离业务负载/容量边界验收已完成；用户确认数据库/raw-pages备份保留90天、原始页面证据随关联记录保留。工作区只读盘点工具报告90天外备份文件候选，不自动删除；过期项需人工核对备份可恢复性与引用后清理。NAS既有备份恢复/负载证据见`docs/PROJECT_STATUS.md`及`docs/LOAD_TEST_2026-11-10.md`；本轮新脚本因LAN SSH连接超时尚未同步。合成测试不构成生产容量SLO。
- 2026-11-10补充：`storage_report.py --check-evidence-references`只读对比内容寻址raw-pages与`collection_candidates.raw_storage_path`，报告孤立文件及缺失文件，不自动删除；需数据库连接权限才能运行。当前仅本地验证，尚未同步NAS。
- 2026-11-10补充：HTTP 200验证码/反爬挑战已增加fail-closed识别，归类`blocked_upstream`；全量回归54 passed、7 skipped；NAS Worker-only部署后容器内源码哈希及检测函数通过，来源OFF、启用目标0。
- [ ] **P0-09 区域/小区房源链接发现器**（依赖P0-04）：经允许的列表页发现详情URL、分页游标、去重、失效标记；受限则以用户链接和可用替代来源输入。
- 2026-11-10 P0-08补充：新增安全的隔离闭环负载脚本；NAS隔离栈连续30分钟、4并发完成10,199工作流/61,194请求、0错误，候选/挂牌/价格历史对账一致。仅合成数据，DB单核CPU成为压力边界；报告存于`docs/LOAD_TEST_2026-11-10.md`。该记录生成时留存期限待定，后续用户确认备份保留90天、页面证据随关联记录保留。2026-11-10补充NAS ACL安全：发现源码/Compose真实other写权限，已收紧项目源码/配置目录755、普通文件644；.env/data/backups仍为600/700/700，保护区外world-writable复查0，Compose config与API/Worker/DB健康通过，未重启容器。
- 2026-11-10 P0-08补充备份权限：NAS复核发现旧`worker.py`源码快照777，已改600；当前`source-snapshots`文件均600、目录700，数据库备份文件/目录600/700。

- 2026-11-10 P0-08只读刷新NAS备份库存：1.1MiB/29文件/6个一级子目录，`/volume3`可用405GiB、使用率56%；API/Worker运行、DB healthy、`/healthz`=200。该盘点当时留存期限待决定；用户随后确认备份90天、页面证据随关联记录保留。无自动清理，本轮未改动NAS数据。
- 2026-11-10 P0-04状态一致性修正：GOAL_STATE此前错误标记`verified_on_NAS`，与无项目书面许可/目标未完成的证据矛盾；现已改为`in_progress`。Robots核验不等于来源授权，在线仍OFF。
- 2026-11-10 P0-02/P0-03样本审计：`data/raw-pages/`仅有占位文件，`fixtures/`只有两份虚构演示HTML；无获准真实页面，因此不满足20+20样本回归，也不报告解析准确率。
- 2026-11-10 P0-01/P0-08桌面核验续：用户解锁Mac后，在UGREEN Docker详情页确认项目运行中、登记Compose路径正确，API、PostgreSQL 17、Worker均运行；nas-lan CLI独立复核API/Worker运行、DB healthy。此前锁屏待核验事项关闭；P0-01仍因无V0.1旧项目/数据库备份而blocked。P0-08留存期限已由用户确认：备份90天、页面证据随关联记录保留。

## P1｜房产情报能力
- [ ] FFmpeg抽音频/关键帧 + FunASR逐字稿 + RapidOCR画面文字（NAS低并发任务队列）。
- [ ] 解析宁波小区和别名、分期、楼栋，标注字段出处与置信度。
- [ ] 用户录入房源视频后自动生成同小区候选，图片/户型图相似度辅助人工复核。
- [ ] 网页目标定时采集的增量发现与稳定暂停/恢复能力（仅限经允许的来源）。
- [ ] 视频号指定账号的实际可行性测试，明确纯NAS与桌面微信限制及业务备份路径。
- [ ] 通过官方公开数据补充行政区域、小区、成交量和宏观价格数据，按来源注明统计口径。
- [x] 条件单增加多区域硬筛选、偏好/排除小区、挂牌最近观察时效；NAS隔离PostgreSQL 17集成测试8 passed；2026-11-10生产备份后执行005并更新API/Worker，认证列表API=200、0条，数据库healthy，采集保持OFF。
- [x] 条件单匹配执行 API：只读匹配正式挂牌，按硬条件过滤、偏好小区优先并标记，返回总数与limit结果；NAS隔离PostgreSQL集成9 passed，API-only部署后OpenAPI/认证边界/健康状态核验通过，生产条件单和挂牌仍为0行。
  - 2026-11-10工作区增补`match_reasons`，说明实际命中的区域、价格、面积、户型、挂牌时效与偏好小区；PostgreSQL 16完整测试76 passed。此增补尚未同步NAS，不能视为已部署。
- [ ] 审核后台：来源权限、采集状态、候选纠错、同套候选、账户/条件单与数据删除。

## P2｜自动寻找价格机会
- [ ] 同源7/30/90日有效降幅榜、降价额、观察证据和异常检测。
  - [x] 本机实现7/30/90日窗口、同一挂牌平台报价首末金额/幅度、观察时间及末次证据链接；排除agent_claim、source=agent及未来/窗口外报价。NAS部署、异常检测及更完整机会评分仍待完成。
- [ ] 可比池分层（分期、面积、楼层、装修、楼龄、历史时点），样本不足不报估值。
  - [x] 当前挂牌可比样本按不同`property_id`计数；同套多渠道挂牌先折算为套内单价中位数，少于5套不产生折价信号。楼层、装修、楼龄与历史时点分层仍待完成。
- [x] 跨平台疑似同套报价差异“待核实”提示：仅比较贝壳/安居客不同来源、同小区同户型、面积差≤5%的挂牌；单价差≥10%按低价为分母生成候选，绝不自动确认同套。本机离线回归通过，NAS验收待连接恢复。
- [ ] 计算机会得分同时展示理由、风险、可比样本数、数据更新时间。
  - [x] `/api/opportunities` 返回可比折价信号理由、挂牌/可比单价（万元/㎡）、独立可比房屋数及挂牌最近观察时间；本机回归测试通过，NAS尚未同步。
- [ ] 消息发送通道（企业微信/邮件或其他合规渠道），去重、幂等、失败重试与免打扰。

## P3｜用户与商业闭环
- [ ] 多用户登录、隐私授权、数据隔离、访问审计、公众端安全。
- [ ] AI自然语言找房/讲价辅助/同小区竞品比较及多轮条件单。
- [ ] 用户授权后的中介线索分配、核房、带看和成交追踪；佣金/归属规则独立设计。
- [ ] 商业化法律、平台数据使用权及隐私合规评估。

## 建议优先迭代顺序
**先保真，再增量，再分析，再商业化**：NAS迁移和数据库正确性 → 保存页面样本真实解析 → 账号监控与视频文本 → 跨源候选审核 → 降价与条件单 → AI咨询和消息提醒。
- 2026-11-10 P0-08留存策略确认：用户指定备份保留90天、页面证据随关联数据库记录保留；`storage_report.py`增加只读过期候选计数与测试，不执行删除；本机56项测试通过，NAS同步仍待LAN连接恢复。

- 2026-11-10 P2-01：机会接口降幅计算只采用同挂牌平台报价，拒绝未来/窗口外快照并限定7/30/90日；返回降价金额、前后价格与观察时间、末次证据链接。本机测试通过，NAS同步待LAN直连恢复。

- 2026-11-10 P0-02样本 intake 工具：新增本地CSV模板和校验脚本，要求每站20份不同HTML、许可引用/范围、带时区捕获时间、人工标签、ID与URL一致性，并检查必要状态/场景覆盖；面积/户型/报价校验与项目数据模型范围对齐，拒绝重复冲突报价。仅用临时虚构文件测试工具，不构成真实样本验收；P0-02仍todo。
  - 最新回归：65 passed、8 skipped；NAS `nas-lan`连接超时，未同步工具。

- 2026-11-10 P0-08留存报告补充：增加91/90/89天边界回归，严格早于90天才进入人工候选统计；专项5 passed，默认全量65 passed、9项数据库测试因缺`TEST_DATABASE_URL`跳过。NAS仍不可达，工具尚未同步、实际候选数未读取。


## 2026-11-10 部署核验补充
- P0-02的API请求体与解析器UTF-8字节限制已在NAS仅API部署并验收：隔离PostgreSQL 17完整套件144 passed/0 skipped；健康200、未认证401、超限413。
- 全局和两站在线采集开关均关闭；生产业务表仍为空。Worker、PostgreSQL、数据卷、Compose登记路径未改变；生产新鲜备份与回滚源码快照已保留。
- P0-02仍缺每站20份获准真实样本，P0-03仍无实际准确率；P0-01仍缺V0.1旧库/备份。后续继续按来源权限、真实样本优先，不因部署成功而放宽来源策略。


## 2026-11-10 P0-08留存盘点补充
- NAS只读库存：raw-pages 2文件/249字节；备份34文件/1,056,619字节；90天超期候选0文件/0字节；`/volume3`可用约406.9GiB。未删除文件。
- 修复盘点脚本在权限不足时静默报告空目录的问题，新增回归；`tests/test_storage_report.py` 8 passed。新版脚本已同步NAS；匹配属主读取成功，无权身份显式失败。


## 2026-11-10 P0-02样本清单CSV结构边界
- 校验器现拒绝重复/空列头及行字段数不匹配，避免CSV错列让来源或人工标签被静默覆盖；异常行不计入样本数。专项含样本校验和解析评估 **19 passed**。
- 工作区没有真实获准页面，P0-02仍待每站20份样本和许可/人工标签证据；不使用演示夹具代替。


## 2026-11-10 P0-03可选挂牌字段歧义
- 对户型、行政区域、楼层、装修的多值冲突保持字段空值，并新增对应审核告警；解析器版本`generic-labelled-v0.2.6`。
- Parser / evaluator / sample-validator组合专项44 passed。仍待每站20份获准真实样本，未报告实际字段准确率。


## 2026-11-10 P0-02/P0-03标签分母与歧义场景评估
- 清单新增`floor_text`/`decoration`人工标签；所有空标签必须对应缺失、未知ID、冲突报价或相应字段歧义标签，避免空值静默退出准确率分母。
- 评估器按来源报告8项字段指标，并在标注歧义时验证户型/区域/楼层/装修均空值且相应警告存在。样本/解析器/评估器专项49 passed。真实样本仍缺，准确率未报告。

## 2026-11-10 P0-03关闭弹层内容隔离
- 成功标准：默认关闭的`dialog`中推荐挂牌价不影响详情挂牌解析；`open`弹层仍保留可见内容解析。
- 回归先复现关闭弹层中的第二个总价会令详情价格变为`None`；解析器现仅移除没有`open`属性的`dialog`，版本升至`generic-labelled-v0.2.7`。另覆盖`template`惰性内容和显式打开弹层。
- `tests/test_collection_parser.py tests/test_parser_evaluation.py tests/test_sample_set.py`：**52 passed**；`compileall`与GOAL_STATE JSON解析通过。未运行全量测试。
- 仅本机离线逻辑验证；真实页面、CSS/JS浏览器渲染、NAS部署及真实准确率未验证。无数据库迁移或配置变化。下一步仍需获准真实样本与旧库备份材料。

## 2026-11-10 P0-03折叠详情区内容隔离
- 成功标准：默认折叠的`details`只保留可见首个摘要；内部隐藏内容不污染挂牌字段；显式`open`内容继续解析。
- 回归先复现折叠推荐价令挂牌价变为`None`；解析器现保留首个直接子级`summary`文本并移除其余折叠内容，无摘要则移除整个区块。版本升至`generic-labelled-v0.2.8`。
- `tests/test_collection_parser.py tests/test_parser_evaluation.py tests/test_sample_set.py`：**54 passed**；`compileall`与GOAL_STATE JSON解析通过。未运行全量测试。
- 仅本机离线逻辑验证；真实页面、浏览器脚本/CSS状态、NAS部署及真实准确率未验证。无数据库迁移或配置变化。

## 2026-11-10 P0-06 DTK异常时间戳防护
- 成功标准：不可表示或无法转换的数字时间戳不应使整轮账号同步崩溃，而应作为未知发布时间处理。
- 回归先复现超大整数在`float()`转换处抛出`OverflowError`；`normalize_datetime`现捕获数值转换的`OverflowError`/`ValueError`并返回`None`。覆盖超大整数、Unicode上标数字和超长数字字符串。
- `tests/test_dtk.py tests/test_worker.py`：**34 passed**；`compileall`通过。未运行全量测试。
- 仅本机离线验证；未连接DTK实例或测试获准账号。P0-06仍需核对DTK版本/权限并完成3个账号24小时联调。

## 2026-11-10 P0-06 DTK文本字段类型校验
- 成功标准：上游文本字段类型异常时不把列表/对象的Python表示写入视频元数据；优先回退到同字段的有效字符串。
- 回归先复现：列表型作者名被写为`['unexpected']`；新增`_first_text`仅接纳非空字符串，标题、作者名、描述采用有效候选回退，非字符串`poi_name`置空。
- `tests/test_dtk.py tests/test_worker.py`：**35 passed**；`compileall`通过。未运行全量测试。
- 仅本机离线验证；未连接DTK实例或测试获准账号。未更改DB字段/配置；真实DTK版本、权限和24小时账号联调仍未验证。

## 2026-11-10 P0-06毫秒时间戳单位边界
- 成功标准：时间戳恰好等于`10^12`时按毫秒解释；整数和数字字符串行为一致。
- 回归先复现阈值边界被按秒解释并返回未知时间；毫秒判定由`>`改为`>=`。
- `tests/test_dtk.py tests/test_worker.py`：**37 passed**；`compileall`通过。未运行全量测试。
- 仅本机离线验证；真实DTK服务/账号联调未做，P0-06仍需接口版本/权限核验及3个获准账号24小时运行。

## 2026-11-10 P0-06 DTK分享链接校验
- 成功标准：视频来源链接仅接受有效HTTPS URL，拒绝脚本/数据/明文HTTP、用户密码、非法端口或控制字符；无效值回退至作品ID对应的HTTPS抖音链接。
- 回归先复现`javascript:`、`data:`、HTTP与含凭据HTTPS链接被原样保存；现按URL结构校验并裁剪空白，fallback将作品ID编码为单一路径段。
- `tests/test_dtk.py tests/test_worker.py`：**43 passed**；`compileall`通过。未运行全量测试。
- 仅本机离线验证；未连接DTK服务或测试获准账号。HTTPS外部域名仍可作为上游分享链接保留；本轮不做平台域名鉴真。

## 2026-11-10 P0-06 DTK分享链接主机校验
- 成功标准：保存为Douyin作品来源的HTTPS链接必须属于`douyin.com`或`iesdouyin.com`根域/子域；其他主机回退canonical链接。
- 回归先复现任意HTTPS域（含`douyin.com.example`伪后缀）会被原样接受；现使用边界明确的域后缀匹配，保留两类平台域名及短链`v.douyin.com`。
- `tests/test_dtk.py tests/test_worker.py`：**46 passed**；`compileall`通过。未运行全量测试。
- 2026-11-10补充：分享主机仅剥离一个DNS根尾点，拒绝多个尾点伪域名；单尾点保持接受。DTK/Worker专项53 passed；真实DTK域名清单及账号联调仍未验证。
- 仅本机离线验证；允许域名基于已知分享链接形式，未在线核实其当前完整清单，亦未连接DTK/NAS。未知但合法的外部分享域会回退canonical地址。

## 2026-11-10 全量离线回归复核
- 对当前工作区执行全量`pytest -q -rs`：**163 passed、11 skipped**；11项均为需`TEST_DATABASE_URL`的PostgreSQL集成用例。另有1条Starlette/httpx弃用警告。
- 覆盖近期DTK时间戳、字段类型和分享URL保护，以及解析器、API、worker、脚本等离线测试；编译、ZIP构建和GOAL_STATE JSON结构另行校验。
- 本轮仅验证工作区，不连接真实DTK/NAS、未访问来源网站、未运行数据库集成；生产部署状态未变化。

## 2026-11-10 P0-03 aria-hidden与视觉隐藏区分
- 成功标准：`aria-hidden="true"`本身不得使仍可见的详情文本从解析输入中消失；真正隐藏的元素仍由`hidden`属性或可识别的内联`display:none`规则排除。
- 回归先复现可见`aria-hidden`价格被误忽略，导致解析器错误保留另一个价格；现解析器仅把`hidden`视为HTML隐藏标记，不再把ARIA可访问性标记等同于视觉隐藏。版本升至`generic-labelled-v0.2.9`。
- 全量本机`pytest -q -rs`：**164 passed、11 skipped**；跳过项需`TEST_DATABASE_URL`，另有1条Starlette/httpx弃用警告。`compileall`、GOAL_STATE JSON解析通过。
- 仅离线回归验证，不代表真实页面字段准确率；无DB迁移/配置变化，未部署NAS。

## 2026-11-10 P0-06 DTK响应分页大小上限
- 成功标准：请求页大小与解析器上限使用同一常量；超过请求数的响应显式失败，不让异常大页被Worker整批落库。
- 新增20条边界接受与21条超限拒绝回归；`PAGE_SIZE=20`同时用于请求参数和响应校验，超限抛`DtkError`。
- 全量本机`pytest -q -rs`：**166 passed、11 skipped**；跳过项需`TEST_DATABASE_URL`，另有1条Starlette/httpx弃用警告。`compileall`及GOAL_STATE JSON解析通过。
- 仅离线逻辑验证，不代表真实DTK响应规格；未连接DTK/NAS或获准账号，不涉及数据库迁移。

## 2026-11-10 P0-06 DTK分页上限路径覆盖
- 补齐页大小上限的两处遗漏验证：异步任务嵌套`data.items`超限和实际请求参数`count`。
- 现在普通页/任务结果都拒绝21条，20条正常；请求参数断言与`PAGE_SIZE`同源。
- 全量本机`pytest -q -rs`：**168 passed、11 skipped**；跳过项需`TEST_DATABASE_URL`，另有1条Starlette/httpx弃用警告。`compileall`和目标JSON解析通过。
- 只验证本地模拟响应，不证明真实DTK遵循请求页大小；未连接DTK/NAS。

## 2026-11-10 PostgreSQL 16隔离全量回归
- 在本机临时PostgreSQL 16 `rehouse_test`库执行全量pytest：**179 passed、0 skipped**；保留1条Starlette/httpx弃用警告。
- 测试期间集群只监听Unix socket，实例/schema使用专用隔离库；测试后停止集群，`pg_isready`返回no response，`/private/tmp`临时集群目录已删除。
- 该结果验证当前工作区全套DB与离线用例，不替代NAS PostgreSQL 17/生产运行验收，也不替代真实V0.1数据库备份升级或DTK联调。

## 2026-11-10 P0-02样本HTML编码前置校验
- 成功标准：清单校验通过的普通/gzip HTML必须能以评估器使用的UTF-8严格解码，避免校验通过后才在解析阶段报错。
- 回归先复现：哈希正确的非UTF-8普通与gzip文件均被清单校验接受；现于样本完整性校验时拒绝并给出`HTML sample must be valid UTF-8`。
- 样本校验/解析评估专项 **27 passed**；全量默认`pytest -q -rs`为**171 passed、11 skipped**（跳过项需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。`compileall`和目标JSON解析通过。
- 仅本机离线验证，不判断来源授权、不代表真实页面质量；本轮未运行数据库集成或NAS部署。V0.2样本工具不自动猜编码/转码。

## 2026-11-10 PostgreSQL 16隔离全量回归（含样本编码校验）
- 当前工作区全量pytest在本机临时PostgreSQL 16 `rehouse_test`执行：**182 passed、0 skipped**；保留1条Starlette/httpx弃用警告。
- 数据库只监听Unix socket；测试后停止，`pg_isready`确认no response，临时集群目录已删除。
- 验证覆盖当前样本UTF-8前置校验和数据库集成用例；不替代NAS PostgreSQL 17/生产运行、真实V0.1数据库升级，也不证明样本授权或解析准确率。



## 2026-11-10 P0-04官方协议入口在线复核
- 重新核对贝壳官方现行服务协议与安居客官方协议中心入口，并在来源政策复核文档中记录页面状态和版本不确定性。
- 未取得安居客当前协议正文或任何项目书面许可；网页工具也未能读取目标robots URL。来源保持OFF，不访问房源详情页，不推断授权。
- 解析器/样本工具专项：120 passed。此测试只证明离线代码回归。


## 2026-11-10 P0-03建筑面积与套内面积区分
- 建筑面积、套内面积、使用面积同页出现时，避免把套内/使用面积当成建筑面积冲突；保留建筑面积值，解析器版本升至`generic-labelled-v0.2.28`。
- 回归先复现后通过。解析器/样本/评估专项121 passed，全量268 passed、13项数据库集成跳过。
- 仅验证合成输入，不代表真实页面准确率；真实获准样本仍缺。


## 2026-11-10 P0-01本机隔离PostgreSQL启动受限
- 尝试启动一次性PG16隔离库以重跑数据库集成测试；sandbox限制`shmget`，mmap配置也未解除。Docker daemon socket拒绝访问。
- 清理临时PG目录并确认端口无响应；未连接远端或业务数据库，DB集成仍待可用隔离环境。


## 2026-11-10 PG16启动提升权限重试
- 提升权限后重试本机隔离PG16仍受系统`shmget`限制；mmap配置未解决，内核IPC参数查询也被系统拒绝。临时实例清理并核实无服务残留。
- 未运行DB集成、未连接NAS或业务库。


## 2026-11-10 P0-03挂牌语义根节点选择
- 语义根节点现在按小区、面积、总价标签证据数选取，避免非空加载提示`main`遮蔽挂牌详情`article`；无信号/同分时保持既有回退顺序。解析器版本升至`generic-labelled-v0.2.29`。
- 专项122 passed，全量269 passed/13项数据库集成跳过；仅为离线合成结构验证。


## 2026-11-10 P0-03多报价场景评估完整性
- 多报价评估现在逐项核对解析证据中的候选价格集合与人工标注；报价集合不匹配、证据缺失或受20条证据上限截断均判为未通过。
- 两条新回归先失败后通过。评估器专项16 passed，全量271 passed、13项数据库集成跳过；仅合成数据验证。


## 2026-11-10 P0-03歧义字段候选集合验收
- 样本模板新增户型/区域/楼层/装修候选列；清单校验要求与场景tag对应，评估器将人工候选集合与解析证据精确对账并拒绝截断证据。
- parser-evaluation/sample-set专项51 passed，全量275 passed、13项数据库集成跳过。只验证合成输入，不表示真实站点准确率。


## 2026-11-10 P0-03小区标签紧凑分隔符
- 小区标签解析支持常见标点紧邻分隔，不再要求前面必须有空格；无标签文本仍不作推断。解析器版本升至`generic-labelled-v0.2.30`。
- 专项129 passed，全量276 passed/13项数据库集成跳过；仅合成离线验证。


## 2026-11-10 P0-03小区字段紧凑值终止符
- 常见标点既可紧邻小区标签前，也可作为小区值的终止分隔符；避免将后续面积/总价字段并入社区名。解析器升至`generic-labelled-v0.2.31`。
- parser/sample/evaluator专项130 passed，全量277 passed、13项数据库集成跳过；仅合成页面验证。


## 2026-11-10 P0-03楼层装修紧凑字段分隔
- 楼层/装修值采用常见紧凑标点作为字段终止符，防止后续标签并入字段值；小区名括号保留。解析器版本升至`generic-labelled-v0.2.32`。
- 专项131 passed，全量278 passed、13项DB集成跳过；仅合成离线验证。


## 2026-11-10 P0-02锁定清单模板与validator schema
- 增加样本清单模板列集合一致性回归，避免P0-02/P0-03字段新增后模板漂移。
- 定向1 passed，全量279 passed、13项数据库集成跳过；不代表真实样本已提供。


## 2026-11-11 P0-01迁移事务边界统一
- 为001/002/003/005补充文件内`BEGIN`/`COMMIT`，与已有事务化的004一致。
- NAS部署手册的升级命令移除`--single-transaction`，避免嵌套事务；新增静态契约回归。
- 2项标准库断言、compileall、Compose配置与差异空白检查通过。pytest和PostgreSQL执行未验证。


## 2026-11-11 P0-09限制已发现ID文件读取
- `--seen-ids`改为有界读取（2 MB）并拒绝无效UTF-8，避免无界文本载入。
- 标准库发现状态/CLI测试12 passed；完整pytest及真实HTML解析未验证。


## 2026-11-11 P0-01锁定迁移初始化顺序
- 静态回归覆盖每份001–005脚本仅有一条独立事务边界、Compose挂载顺序一致及手动命令不叠加事务包装。
- 3项标准库检查通过；未执行PostgreSQL迁移。


## 2026-11-11 P0-09拒绝特殊seen-ids输入
- `--seen-ids`拒绝非普通文件，避免FIFO造成阻塞。新增标准库回归；发现器状态/CLI测试13 passed。


## 2026-11-11 P0-09校验seen-ids挂牌ID
- 已发现ID文件按贝壳/安居客来源ID长度与数字规则校验；忽略空行、裁剪首尾空格并去重，非法行拒绝。
- 标准库发现状态/CLI测试14 passed。


## 2026-11-11 P0-08备份拒绝raw-pages符号链接
- 备份前在容器内校验`/data/raw-pages`是非符号链接目录，防止tar成功但没有归档关联证据内容。
- 标准库回归覆盖正常归档及符号链接拒绝；16项标准库测试通过。NAS尚未同步/复核。


## 2026-11-11 P0-08完整备份脚本隔离回归
- 标准库测试以临时假Docker入口运行`backup.sh`，覆盖成功发布、归档/哈希/权限与符号链接失败时无半成品。数据库命令为模拟；NAS未复验。
- 标准库测试总计18 passed。


## 2026-11-11 P0-01扩展旧库完整迁移集成用例
- V0.1合成数据用例现在对002–005逐份重复执行并核对旧业务字段、004健康汇总回填、005新增条件默认值。
- Python语法编译通过；PostgreSQL集成未运行，真实备份升级未验收。


## 2026-11-11 P0-08拒绝raw-pages内部符号链接
- 备份脚本打包前扫描证据目录树；链接或扫描失败都会阻止归档发布。
- 新增嵌套链接失败清理回归；标准库测试19 passed。尚未在NAS运行。


## 2026-11-11 P0-01迁移契约标准库测试
- 迁移静态契约3项改为标准库unittest，纳入无pytest依赖的测试组；22项stdlib测试通过。
- PostgreSQL 16单用户初始化仍受`shmget`限制，未执行SQL迁移。
## 2026-11-11 P0-04 来源协议复核
- 复核贝壳官网当前协议日期及书面许可/自动化/Robots要求；确认安居客官方PDF标示2021年5月更新，同时记录其与协议中心当前版本的对应关系未确认。
- 未访问房源页或采集；两来源在线继续关闭。Robots只沿用2026-11-10 NAS实读证据，没有新文本。
# 2026-11-11

- P0-03：静态复核混合HTML可见文本遍历及字段证据偏移契约，新增跨越1,000字符摘录边界的offset回归并补充API说明。解析器/评估器/样本集269 passed；全量离线套件596 passed、15 skipped、13 subtests passed。未改解析器实现。真实样本准确率仍待每站20份获准页面及人工标签。
- P0-09：分页页身份比较现规范化未保留字符百分号编码（如`%70age1`与`page1`），保留路径大小写和保留字符语义（如`%2F`不等于`/`）；发现器/状态/CLI定向40 passed，全量离线617 passed、15项数据库集成跳过、13 subtests passed。仅离线合成验证，许可、真实分页样本和自动Worker流程仍缺。

- P0-09：修复已访问页人工重放失败时污染`next_page_url`并令本地状态无法加载的问题。该失败现在只更新错误追踪，保留已有游标；未访问页失败仍设置重试游标。状态/CLI专项18 passed，全量离线618 passed、15项数据库集成跳过、13 subtests passed。

- P0-08：`backup.sh`现在拒绝符号链接形式的`BACKUP_ROOT`，避免跟随链接改动目标目录权限或将备份写入非预期目录。假Docker端到端回归验证失败时目标权限和内容未变；备份专项6 passed、标准库组合27 passed、全量离线619 passed/15项数据库集成跳过/13 subtests passed。未在NAS运行。

- P0-08：留存盘点CLI遇到符号链接形式的`--raw-pages`或`--backups`根目录时明确失败，不再把未扫描结果显示成0文件或0个超期备份。留存报告专项14 passed，全量离线621 passed/15项数据库集成跳过/13 subtests passed；仅本机临时目录验证。

- P0-03：按CSS opacity计算边界将负有限透明度视为透明，防止隐藏广告挂牌价进入字段候选；限制数值语法，避免无效`-Infinity`误作透明。解析器升至`generic-labelled-v0.2.60`，解析器/链接发现器专项195 passed，全量离线625 passed/15项数据库集成跳过/13 subtests passed。仅合成输入验证。

- P0-09：分页身份比较现将裸Unicode IRI路径规范为UTF-8百分号编码，与HTTPX请求路径对齐；保留大小写与`%2F`/`/`差异，拒绝非法surrogate。发现器专项18 passed，全量离线628 passed、15项数据库集成跳过、13 subtests passed。仅离线验证。

- P0-09：补充API状态模型和本地state对Unicode IRI/UTF-8百分号路径别名的分页回环回归。模型/发现器44 passed，标准库状态/CLI19 passed，全量离线630 passed/15项数据库集成跳过/13 subtests passed。未连接外部环境。

- P0-08复验路径复查：nas-lan与已授权notedock-nas均连接超时，Tailscale CLI偏好无法读取且本机未安装Tailscale App；未建立NAS连接，无远端命令或写操作。

- P0-03：修复块级HTML分隔后“折后 总价”等限定词漏拦截，以及“使用 建筑面积”退化匹配末尾“面积”的问题；负向前缀同时覆盖一个规范化空格与面积标签复合前缀。解析器升至`generic-labelled-v0.2.61`，解析器/评估/样本集292 passed，全量离线636 passed/15项数据库集成跳过/13 subtests passed。仅合成验证。

- P0-08：新增NAS只读续核记录，确认Compose服务/PG卷及顶层备份目录权限与文件数；标明顶层清单不覆盖子目录，并记录后续SSH复用失败。未执行NAS写操作。

- P0-08：新增原始HTML gzip证据完整性报告，可检查解压内容哈希是否与内容寻址文件名一致，并报告坏gzip/哈希不符；只读流式检查，临时合成标准库回归3 passed，未在NAS执行。

- P0-08：备份脚本拒绝文件系统根、当前/父目录及含项目工作区的目录作为BACKUP_ROOT；用假命令回归确认失败发生在mkdir/chmod/Docker之前。完整stdlib测试33 passed，未在NAS执行。

- P0-08：证据完整性检查区分内容损坏与文件读取权限/系统I/O错误；不可读文件显式失败，不再误报损坏。标准库测试共34 passed。

- P0-08/P0-03：复用本机缓存Python 3.12依赖恢复完整离线pytest：651 passed、15个数据库集成跳过、13 subtests passed；另验证2,000–8,000层合成页面无递归异常。未连接NAS/网站，真实解析准确率未验证。

- P0-09：本地发现CLI在样本读取/解析失败且重试state无法保存时，现同时明确报告重试状态未保存，避免静默丢失重试游标。状态层/CLI回归21 passed；完整pytest 653 passed、15 skipped、13 subtests passed。
- NAS复验重试：LAN超时，Tailscale CLI/App不可用，授权公网SSH超时；没有远端命令或写操作。

- P0-09：`record_failure(path=None, state=...)`现在安全返回未保存，并保留内存失败计数；定向状态/CLI测试22 passed，全量pytest654 passed/15 skipped/13 subtests passed。

- P0-03/P0-09：HTML字符串超1,000,000字符时在UTF-8编码前拒绝；保留编码字节数限制，避免多字节输入绕过。定向206 passed，全量pytest656 passed/15 skipped/13 subtests passed。

- P0-08：备份根目录保护现在也拒绝物理规范化为`/`的路径别名（如`/tmp/..`），确保失败发生在mkdir/chmod/Docker之前。stdlib37 passed，全量pytest656 passed/15 skipped/13 subtests passed；未部署NAS。

- P0-08：备份脚本根据`cd -P`后的物理根路径拒绝`/tmp/..`等根目录别名，确保拒绝先于mkdir/chmod/Docker。危险路径回归通过，stdlib37 passed、全量pytest656 passed/15 skipped/13 subtests passed；未在NAS运行。

- P0-08：备份脚本新增已有祖先目录符号链接检测，逻辑/物理路径不一致时在mkdir/chmod/Docker前失败；覆盖已有目标及未创建下级路径。脚本专测8 passed，全量pytest656 passed/15 skipped/13 subtests passed，未部署NAS。

## 2026-11-11
- P0-09 离线发现器过滤 `<menu>` 导航链接，避免详情导航项误入挂牌候选；保留主列表链接。
- 验证：发现器13 passed；完整离线pytest 657 passed、15 skipped、13 subtests passed；标准库37 passed。用户暂无真实备份、许可样本和标注，按要求继续离线开发；未连接NAS或部署。

## 2026-11-11
- P0-03 页面解析过滤`<menu>`导航子树，避免菜单里的促销/其他房源信息污染挂牌字段；解析器升至`generic-labelled-v0.2.64`。
- 回归先失败后通过；完整离线pytest 658 passed、15 skipped、13 subtests passed，标准库37 passed。真实页面准确率与NAS部署未验证。

## 2026-11-11
- P0-09 `--seen-ids`现拒绝符号链接输入，避免沿链接读取目标文件；添加离线回归。
- 验证：完整离线pytest 659 passed、15 skipped、13 subtests passed；标准库38 passed。未连接网站/NAS或部署。

## 2026-11-11
- P0-09 `--seen-ids`现拒绝符号链接输入，避免沿链接读取目标文件；添加离线回归。
- 验证：完整离线pytest 659 passed、15 skipped、13 subtests passed；标准库38 passed。未连接网站/NAS或部署。

## 2026-11-11
- P0-09 将Worker列表目标接入分页发现和持久游标；上限为每轮5个列表页和20个详情页，详情失败有可追溯重试游标，robots/upstream阻断会暂停目标并停止自动重试，仍受来源许可门控制。
- mock定向服务测试26 passed；完整离线pytest 664 passed、16 skipped、13 subtests passed；标准库38 passed。未连接网站、PostgreSQL或NAS，未部署。
- 新增PostgreSQL集成用例覆盖两页游标与详情候选；因未设置`TEST_DATABASE_URL`而跳过，未声称通过。
## 2026-11-11 P0-09同步Worker分页文档
- 修正文档将Worker列表分页误写为未实现的状态，明确当前每轮页数/详情数上限、详情候选隔离、游标续跑及阻断后的操作员处理要求。
- 标注仍未实现的失效/下架跟踪、独立待发现队列及真实站点模板；没有改变在线采集开关或权限策略。
- 文档核对与GOAL_STATE JSON校验通过；未运行测试，本轮无代码、数据库、NAS或部署变更。


## 2026-11-11 P0-08备份路径安全
- `backup.sh`拒绝`BACKUP_ROOT`中的`..`路径组件，防止缺失中间目录与父目录组件组合后绕过项目根保护。
- 临时目录回归复现并确认目录权限未变化；备份脚本9 passed，stdlib39 passed，完整离线pytest670 passed、16 skipped、13 subtests passed。NAS新版脚本仍未实机复验。

## 2026-11-11校准目标模式交接提示
- 将`prompts/NEXT_ITERATION.md`更新为当前P0状态、解析器版本、离线测试结果及用户确认/待定决策，防止后续轮次引用过时进度。
- 仅本地文档交叉核对；未连接NAS、数据库或房源网站。


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
- 在NAS运行当前备份脚本并完成哈希校验、权限核验及断网临时PG17恢复；P0-08状态更新为`verified_on_NAS`。
- 未改生产服务/数据库/卷或部署工作区代码；P0-01因缺真实V0.1备份仍blocked。

## 2026-11-11 P0-09路线图状态对齐
- 将路线图主条目与当前GOAL_STATE及NAS隔离PG17的17项数据库集成结果对齐，补充测试隔离边界。
- 保留P0-09进行中：真实来源许可、分页样本及生产部署仍未验收；本轮仅改文档。

## 2026-11-11 P0-03限制离线评估清单大小
- 为解析器评估器的CSV快照读取和评估后哈希复核设置2,000,000字节上限，拒绝超限或评估期间持续增长的清单。
- 新增两项pytest回归；当前环境缺pytest及项目依赖，未执行pytest。标准库隔离smoke 2 passed，Python 3.12 compileall通过。真实样本准确率仍未验证。


## 2026-11-11 P0-03锁定评估器损坏CSV诊断
- 复核确认样本校验器已将无效UTF-8和畸形CSV映射为清晰验证错误；撤销评估器中冗余的异常转换，保留两项回归验证评估调用链报告这两类错误。
- 定向pytest 6 passed，覆盖两类清单诊断、初始快照超限、恰好2,000,000字节、哈希拒绝超限及超限时只多读取1字节（临时pytest运行时与占位BeautifulSoup类型，所测路径不解析HTML）；标准库套件39 passed。全量pytest因宿主缺项目依赖未运行。哈希复核读取循环每次最多读剩余预算+1字节，防止超限后额外消耗一个64KiB分块。开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-03-evaluator-hash-read-cap.zip`。


## 2026-11-11 P0-03文本评估与歧义候选统一Unicode NFC
- 失败回归复现组合字符等价文本被评估为不匹配、歧义候选去重将其当作不同值；评估器文本字段和样本校验器歧义候选现空白折叠后统一Unicode NFC。数值字段仍按Decimal比较。
- `tests/test_sample_set.py` 63 passed；评估器清单/大小/NFC/CLI错误诊断子集（含替身解析结果端到端计分）10 passed。两项失败回归先失败后通过；仅离线合成标签验证，真实样本准确率未验证。
- 补充端到端评估回归：解析器替身返回NFD标题、人工标签为NFC标题时，标题准确率和精确率均正确计为100%；评估器相关定向测试现10 passed；新增CLI用例确认两类损坏清单均返回状态码1、stdout给出拒绝原因且stderr为空。开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-03-evaluator-cli-diagnostics.zip`。


## 2026-11-11 P0-03解析器文本候选使用Unicode规范身份
- 失败回归复现：社区/标题文本仅在空白或Unicode NFC形式上不同会被原始字符串判重误报歧义。解析器复用比较键判重并保留首次原文值/证据，版本升至`generic-labelled-v0.2.65`。
- 解析器候选归一辅助2 passed、样本集63 passed、评估器清单/NFC/CLI子集10 passed、标准库42 passed，新增3项无依赖Unicode比较键回归。解析器测试未运行BeautifulSoup HTML解析；真实页面准确率未验证。

## 2026-11-11 P0-03评估报告解析器版本契约
- 为解析器评估端到端测试补充报告版本断言，确保JSON报告中的`parser_version`与当前解析器版本一致。
- 评估器专项54 passed；解析器和样本清单专项260 passed；标准库42 passed；Python 3.12 compileall通过。未运行全量pytest/数据库集成，未使用真实页面样本。


## 2026-11-11 P0-03全量离线回归复核
- 现有临时Python 3.12环境运行完整`pytest -q`：**688 passed、16 skipped、13 subtests passed**；16项数据库集成因未配置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 本轮包括评估报告解析器版本契约及合成HTML解析路径；真实页面准确率仍未验证。未访问网站、NAS或数据库，未部署。


## 2026-11-11 P0-07指标建模边界核查
- 代码/SQL审阅确认`collection_runs`的`failed`合并网络与解析失败，没有HTML取得或解析尝试阶段计数，不能可靠计算解析成功率。已在交接文档标出需用户确认口径和迁移范围；本轮未改API、SQL或数据库。


## 2026-11-11 P0-08留存候选按完整备份集分组
- 防止数据库dump与raw-pages归档作为单独文件出现在留存候选中：备份脚本生成的`ningbo-re-ai-...`目录仅在目录与全部普通文件均超期时整体列报；散落旧式文件仍按单文件列报。仅输出人工复核候选，不删除。
- 留存报告专项22 passed；全量pytest689 passed、16 skipped、13 subtests passed。未设置`TEST_DATABASE_URL`，数据库集成跳过。本轮未同步或运行NAS新版工具。


## 2026-11-11 P0-03补齐畸形HTML结构回归
- 新增3组未闭合/错配标签解析回归，确认标签明确的字段仍可抽取且继续标注人工审核。
- 解析器专项200 passed；全量离线pytest692 passed、16 skipped、13 subtests passed。16项数据库集成需`TEST_DATABASE_URL`；未访问真实来源或NAS。


## 2026-11-11 P0-03用Decimal检查面积与总价的范围
- 防止极精细的超界面积/报价被float舍入回最大允许值；现在范围校验使用Decimal，确认在合法范围后再转换为float。解析器版本更新为`generic-labelled-v0.2.66`。
- 失败回归先复现再修复；解析器/评估器/样本集318 passed，全量pytest693 passed、16 skipped、13 subtests passed。未验证真实页面准确率。


## 2026-11-11 P0-03覆盖数值范围下界
- 增加高精度下界外面积/报价回归，确保不会因float舍入被误报为10㎡/1万元；复用已实现的Decimal精确范围检查。
- 下界/上界专项2 passed；全量pytest694 passed、16 skipped、13 subtests passed。


## 2026-11-11 P0-03固定精确数值端点行为
- 覆盖面积10/20,000㎡和挂牌总价1/200,000万元的包含边界，精确合法端点仍可审核就绪；上下界专项6 passed。
- 全量pytest698 passed、16 skipped、13 subtests passed。版本保持`generic-labelled-v0.2.66`。


## 2026-11-11 P0-09保留许可撤销前已完成分页进度
- 许可在一页多个详情中途撤销时，已成功暂存详情的seen ID和列表页重试游标现在会持久保存，避免下轮重复请求已完成详情；策略阻断不计为抓取失败。
- 失败回归先复现后修复；定向3 passed，全量pytest699 passed、16 skipped、13 subtests passed。Mock离线验证，未运行DB/NAS集成。


## 2026-11-11 P0-09端到端锁定撤销策略后的分页重试
- 扩展两轮回归，确认保存的seen ID阻止对已成功详情的重复请求，且剩余详情可在许可恢复后继续处理。collection-service专项28 passed，全量pytest699 passed、16 skipped、13 subtests passed；Mock测试，未做PG/NAS验收。


- 2026-11-11 P0-09：新增PostgreSQL集成回归，覆盖分页详情处理期间策略撤销后的seen ID/重试游标持久化，以及许可恢复后的续抓行为。全量离线pytest 699 passed、17 skipped、13 subtests passed；该数据库用例因无`TEST_DATABASE_URL`跳过，未声称PG验收通过。


- 2026-11-11 P0-09：本机临时PostgreSQL 16上完整数据库集成测试18 passed；全量pytest 716 passed、0 skipped、13 subtests passed。新断点用例验证许可撤销时的详情候选与分页状态落库，以及许可恢复后的续抓。临时数据库和资源已清理；未访问NAS或来源网站。


- 2026-11-11：同步目标模式续开发提示中的P0-09状态，区分本机PG16断点验证与历史NAS PG17结果，避免后续误报为NAS已验收。挂牌失联阈值/自动下架规则仍待确认。


- 2026-11-11 P0-02：样本清单validator转义诊断中的C0/C1控制字符并拒绝含控制字符的`sample_id`，防止终端控制序列污染本地错误输出。新回归先失败后通过；全量pytest在临时PG16上719 passed、0 skipped、13 subtests passed。


- 2026-11-11 P0-02：补齐清单控制字符诊断边界。首尾控制码在裁剪前检测；sample_id、重复列名及未支持列名中的C0/C1在错误输出中转义。控制字符诊断13 passed，样本集/评估127 passed，全量临时PG16 pytest 726 passed、0 skipped、13 subtests passed。


- 2026-11-11 P0-03：解析器不再把“口播总价/口播挂牌价”当作平台挂牌价，也不因此误判多报价冲突；PARSER_VERSION升至`generic-labelled-v0.2.67`。解析器专项216 passed，全量临时PG16 pytest 736 passed、0 skipped、13 subtests passed。

## 2026-11-11 P0-09连续缺失阈值确认
- 用户确认同一目标连续2次完整分页遍历未见后转待人工核验，不自动下架。失败、阻断、处理上限、分页回环或歧义不算完整遍历。
- 迁移007/008与Worker/API流程实现已记录；本轮标准库42 passed，compileall及静态检查通过。pytest未安装，PostgreSQL SQL/API集成未执行；在线采集关闭，未连接网站/NAS或部署。

## 2026-11-11 P0-09锁定完整遍历边界与不自动下架
- 新增PostgreSQL集成用例验证页数上限、页面失败和许可阻断不计缺失扫描；恢复并完成遍历后才计数。
- 扩展两次缺失回归，预置正式`available`挂牌，断言转人工核验后状态不变。当前未能运行pytest/数据库集成；仅compileall及标准库42项通过。

## 2026-11-11 P0-09按页面DOM顺序发现挂牌并完成PG16回归
- 修复列表发现结果反向于页面DOM顺序的问题，保持页面排序并更新依赖处理顺序的策略阻断测试夹具。
- PostgreSQL集成20 passed，全量pytest739 passed、0 skipped、15 subtests passed；覆盖连续两次缺失进入人工核验、不自动下架，以及上限/请求失败/许可阻断不计为完整扫描。临时PG16容器和网络已清理。
- 安全开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-09-dom-order-pg16.zip`。


## 2026-11-11 P0-09追加挂牌失联人工核验记录
- 新增迁移009、数据模型和认证API：对`pending_review`观察记录保存固定结论`still_listed`、`confirmed_withdrawn`或`inconclusive`及可选备注，并提供分页历史查询。记录只改变观察队列状态为`reviewed`，不修改正式挂牌状态；重现后可再次进入核验流程。
- 修正路由函数签名中必填请求体位于带默认值`Path`参数后的语法错误，并保留挂牌ID格式422校验。
- 本机临时PostgreSQL 16全量pytest **739 passed、0 skipped、16 subtests passed**；新增集成场景覆盖认证、结论校验、历史读取、复核状态和正式挂牌状态不变。容器仅使用tmpfs并绑定127.0.0.1，测试后清理。
- 未访问NAS、真实数据库或房源网站，未部署；在线采集保持关闭。PG16验证不替代NAS PG17/生产验收，来源许可与真实分页样本仍缺。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-09-review-api-pg16.zip`（121个源码/文档文件，包内SHA-256与ZIP完整性校验通过）。


## 2026-11-11 P0-09验证人工核验历史跨周期追加
- 扩展PostgreSQL集成回归：挂牌重新出现后再次连续缺失两轮，追加第二条结论并确认历史接口返回两条记录；正式挂牌状态仍为`available`。
- 数据库集成20 passed，全量pytest739 passed、0 skipped、16 subtests passed；保留1条Starlette/httpx弃用警告。仅临时PG16/tmpfs/127.0.0.1验证，未访问NAS、来源网站或生产数据库，也未部署。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-09-review-history-pg16.zip`。


## 2026-11-11同步目标模式提示的P0-09现状
- 更新`prompts/NEXT_ITERATION.md`中P0-09当前状态、复核结论API、跨周期历史测试数量和最新开发包，清除会被误读为当前状态的旧验证摘要。仅文档同步。


## 2026-11-11 P0-07实现四项累计健康率
- 用户确认采集/解析/字段完整/审核通过口径后，新增010迁移与collection_parse_attempts记录。触发器增量维护解析尝试、成功和四必需字段完整计数；健康API派生累计百分比，零分母返回null。采集率排除blocked，审核率排除pending。
- 解析阶段覆盖手动HTML和在线采集进入解析器的页面；解析器返回结果即成功，字段缺失或警告另计入完整率。字段完整必需来源ID、小区、总价、面积。
- PG16全量pytest741 passed、0 skipped、17 subtests passed（含21项数据库集成）；健康/服务定向30 passed，标准库42 passed；compileall、备份脚本语法、GOAL_STATE JSON及差异检查通过。迁移/新API尚未部署NAS。
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-p0-07-health-rates-pg16.zip`，122个源码/文档文件，ZIP与包内SHA-256校验通过。

## 2026-11-11 文档同步健康率与跨平台候选状态
- README补充跨平台价差候选已实现范围及“候选不等于确认同套”的限制，标注面积差分母待确认；迁移清单更新至010。
- 修正README验证摘要：当前工作区完整离线pytest为734 passed、21 skipped、17 subtests passed；21项数据库集成未运行。将此前PG16 741 passed、0 skipped定位为健康率迁移010的较早代码快照验证。
- 用户确认的四项健康率口径已落实在P0-07目标说明；NAS PG17及生产版本差异验收继续待办。
- 验证：完整pytest 734 passed、21 skipped、17 subtests passed；保留1条Starlette/httpx弃用警告。开发包为`../ningbo-re-ai-v0.2-dev-2026-11-11-readme-health-cross-platform.zip`，包内SHA-256与ZIP完整性校验通过。未访问NAS/网站/生产数据库，未部署。

## 2026-11-11 说明健康率的历史覆盖起点并只读复核NAS
- README和P0-07目标记录说明：旧运行表不区分网络失败/解析失败，迁移010前无法重建解析尝试；解析成功率和字段完整率仅从010启用后累计。
- 经已授权`notedock-nas`成功只读会话确认DXP4800登记路径、API/Worker运行及PostgreSQL 17 healthy；后续DNS间歇失败，生产010应用状态与API健康端点未能确认。本轮无NAS写入或部署。
- 全量离线pytest 734 passed、21 skipped、17 subtests passed；21项数据库集成因缺少`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-health-metric-window-nas-audit.zip`，安全打包器校验包内SHA-256与ZIP完整性。

## 2026-11-11 P0-07 NAS隔离PG17迁移010烟雾验证
- 当前开发包SHA-256在NAS传输核对一致；隔离PG17.11（断网、tmpfs、无宿主端口/持久卷）顺序应用001–010成功，010幂等重跑成功。合成解析事件触发器计数2次尝试、1次成功、1次完整，重跑010后仍为2/1/1。
- 生产PG17只读查询发现`collection_parse_attempts`不存在；生产API三个源码模块哈希均与工作区不一致。`/healthz`=200、未认证健康业务API=401。未访问业务行，未修改生产。
- 测试容器、临时归档和由Docker属主创建的源码目录均清理并复核。完整PG17数据库测试及生产部署仍未完成。开发包：`../ningbo-re-ai-v0.2-dev-2026-11-11-pg17-isolation-evidence.zip`。


## 2026-11-11 P0-07隔离PG17数据库集成
- 当前工作区在NAS隔离PostgreSQL 17测试库执行完整`tests/test_db_integration.py`：**22 passed**；测试schema残留0，自动清理后临时容器、网络、归档与解压目录均已复核不存在。
- 测试使用internal Docker网络、tmpfs和只读源码挂载，无宿主端口/持久卷；未连接生产数据库或部署。


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

## 2026-11-11 P0-03排除noscript惰性样式表
- 失败回归复现：`<noscript>`内的`<style>`和`rel="stylesheet"`会触发`unresolved_stylesheet_visibility`，尽管当前解析器随后移除整个noscript子树。样式表门禁现与文本提取的惰性内容处理一致，跳过template及noscript后代；解析器升至`generic-labelled-v0.2.97`。
- 新增两种noscript回归均先失败后通过；样式表/noscript定向 **9 passed**，collection parser/service **314 passed**，全量离线pytest **793 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。


## 2026-11-11 P0-03识别CSS裁剪造成的未知文本可见性
- 失败回归复现：`clip-path:inset(100%)`可将推荐报价完整裁出视口，但解析器既未移除该文本，也未给候选可见性告警。现在内联`clip`/`clip-path`声明及活动`<style>`中的同类规则触发人工复核告警；解析器升至`generic-labelled-v0.2.98`。
- 两项裁剪回归先失败后通过；裁剪/样式表定向 **7 passed**，collection parser/service **316 passed**，全量离线pytest **795 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。配置无变化。
- 下一轮优先继续P0-03对CSS裁剪/遮罩类可见性属性的离线边界审计；以复现测试和定向、全量离线测试通过作为验收。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。


## 2026-11-11 P0-03识别CSS遮罩造成的未知文本可见性
- 失败回归复现：`mask-image:linear-gradient(transparent,transparent)`及`-webkit-mask`可使推荐报价完全透明，但解析器此前未添加可见性告警。现在内联标准/WebKit mask及活动样式表mask声明触发人工复核；解析器升至`generic-labelled-v0.2.99`。
- 三项遮罩回归先失败后通过；遮罩/样式表定向 **10 passed**，collection parser/service **319 passed**，全量离线pytest **798 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。配置无变化。
- 下一轮继续P0-03视觉裁剪/遮罩类属性边界审计；验收要求先由失败回归证明漏判，再使定向与全量离线测试通过。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。


## 2026-11-11 P0-03忽略CSS字符串中的伪可见性声明
- 失败回归复现：样式表扫描直接对CSS原文做正则搜索，会把`content:"display:none"`和`content:"@import"`中的字符串误判为样式规则/外部导入，造成无需人工复核的候选被拦截。现扫描前跳过CSS注释与引号字符串，再解码并检查真实声明；解析器升至`generic-labelled-v0.2.101`。
- 两种字符串误报回归先失败后通过，且既有转义属性、活动`@import`、遮罩及惰性内容用例通过；CSS字符串/样式表定向 **13 passed**，collection parser/service **321 passed**，全量离线pytest **800 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。配置无变化。
- 下一轮继续P0-03 CSS token/selector边界审计，寻找会把有效声明漏掉或误报的具体输入；验收要求回归先复现、再通过定向和全量离线测试。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。


## 2026-11-11 P0-03区分CSS声明与自定义属性文本
- 失败回归复现：样式表扫描把自定义属性`--display:none`及`--label:display:none`中的词元误识别为实际`display`声明，即使这些变量未使用也会阻止有效候选审核。现仅按规则块内声明起始位置识别可见性属性和`@import`，并避开注释、引号字符串及函数/属性选择器内部的分隔符。
- 两项自定义属性误报回归先失败后通过；CSS词法/样式表定向 **18 passed**，collection parser/service **323 passed**，全量离线pytest **802 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。配置无变化。
- 下一轮继续P0-03 CSS词法边界审计；验收要求新增漏报/误报回归先证明问题，再通过定向与全量离线测试。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。


## 2026-11-11 P0-03区分嵌套自定义属性块与样式规则
- 失败回归复现：CSS自定义属性允许花括号块值；`--label:{display:none;}`中的`display:none`不是实际声明，却被规则分段器误报。现在自定义属性值花括号块内不再按声明分段；另加嵌套`@media`与`@supports`正例，确保其中真实可见性声明仍触发复核。解析器升至`generic-labelled-v0.2.102`。
- 自定义属性与嵌套规则词法回归 **14 passed**；collection parser/service **326 passed**；全量离线pytest **805 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。配置无变化。
- 下一轮继续P0-03 CSS转义token与嵌套声明边界审计；验收要求具体漏报/误报先由回归复现，再通过定向和全量离线测试。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。


## 2026-11-11 P0-03覆盖嵌套CSS与转义属性组合
- 扩展样式表门禁回归，验证嵌套`@media`中的转义`display`属性，以及自定义属性花括号块之后继续出现的嵌套真实隐藏规则；前者必须识别为可见性未决，后者不能被自定义属性块状态吞掉。应用实现与解析器版本`generic-labelled-v0.2.102`不变。
- CSS词法组合定向 **16 passed**，collection parser/service **328 passed**，全量离线pytest **807 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。配置无变化。下一轮继续P0-03词法边界验证；真实页面准确率仍待获准样本与人工标注，P0-01真实V0.1备份及P0-02来源材料仍缺。


## 2026-11-11 P0-03避免CSS自定义属性嵌套块重复解码前缀
- 性能回归复现：100层自定义属性花括号块让扫描器重复解码不断增长的同一前缀 **101次**，可通过小于1 MB的输入造成二次方工作。现仅在进入自定义属性值块时解码并判型一次，内层花括号只更新深度；解析器升至`generic-labelled-v0.2.103`。
- 调用次数回归先失败后通过，解码次数降为 **1**；性能/词法定向 **8 passed**，collection parser/service **329 passed**，全量离线pytest **808 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标注。配置无变化。
- 下一轮继续P0-03对有界HTML输入下的解析时间/内存热点审计；用确定性复杂度回归证明线性或有界增长，并跑定向及全量离线测试。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。


## 2026-11-11 P0-03缓存同级run-in分析避免超线性扫描
- 复杂度回归复现：80个连续`display:run-in`兄弟节点调用`_text_with_inline_boundaries`时，重复向前/向后扫描产生 **183,763次display查询**。现按父节点一次性构建同级run-in布局，文本边界结果保持不变；解析器升至`generic-labelled-v0.2.104`。
- 新增确定性规模回归要求80节点不超过 **350次display查询**；run-in/显示边界专项 **19 passed**，collection parser/service **330 passed**，全量离线pytest **809 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。配置无变化；真实页面解析准确率仍待获准样本和人工标注。
- 下一轮继续P0-03按1 MB输入上限审计树遍历/证据提取复杂度，优先寻找确定性二次方或重复子树扫描；用调用次数/处理节点数回归验收。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。


## 2026-11-11 P0-03避免可见性检查反复展开嵌套文本子树
- 复杂度回归复现：80层嵌套、每层均含文字的样式节点让`_has_unresolved_inline_visibility`反复调用`get_text(strip=True)`，累计遍历 **3,240个后代字符串**。现改为一次迭代后序遍历汇总子树文本状态，只扫描直接子节点并在有文本的样式节点上检查声明；空文本节点仍不触发告警。解析器升至`generic-labelled-v0.2.105`。
- 后代字符串访问与直接子节点访问均有确定性规模上限回归；解析器/采集服务 **331 passed**，全量离线pytest **810 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。配置无变化；真实页面准确率仍待获准样本与人工标注。
- 下一轮继续P0-03在1 MB上限下审计证据提取的重复正则扫描和内存放大；用确定性匹配/节点计数回归验证并修复。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。


## 2026-11-11 P0-03流式判定字段值歧义并保留完整证据计数
- 失败回归复现：`_first_unique`与`_first_unique_numeric`先物化全部正则匹配，再决定是否存在冲突；前两项已不同的字段仍继续生成并保存后续候选列表。现在改为流式归一化，发现第二个不同值即停止核心歧义判定，候选集合最多保留2项；field_evidence仍单独遍历全文，准确统计全部命中数并仅保留前20条。解析器升至`generic-labelled-v0.2.106`。
- 1,002条报价回归确认解析字段被冲突阻断、`mention_count=1002`、证据保留20条；歧义扫描调用计数回归确认在第二个不同值处停止。collection parser/service **333 passed**，全量离线pytest **812 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、目标状态JSON、`git diff --check`及开发包校验通过。仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。配置无变化；真实页面准确率仍待获准样本和人工标注。
- 下一轮继续P0-03检查H1/title候选提取和字段证据序列化的输入放大/重复文本处理；用确定性节点或匹配计数回归验收。P0-01真实V0.1备份与P0-02获准样本/许可/标签仍待提供。


## 2026-11-11 P0-03 H1候选按需遍历
- 80层嵌套H1回归先失败：当前解析器对每个标题反复展开其子树，共访问13,306个子节点。现将H1文本候选改为惰性生成，并在找到第二个不同标题后停止；保留冲突告警、head:title回退和标题文本规则。解析器升至`generic-labelled-v0.2.107`。
- 解析器/采集服务 **334 passed**；全量离线pytest **813 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。新回归要求80层输入总子节点访问≤1,280。
- 仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实解析准确率仍待获准页面及人工标签；P0-01真实V0.1备份和P0-02样本/许可/标签仍缺。


## 2026-11-11 P0-03流式处理页面身份与标题元数据
- 失败回归覆盖1,002个canonical链接和1,002个`og:url`标签：原实现通过多个BeautifulSoup结果列表及URL/ID列表暂存整组命中，再截断最终证据。现对样式链接、canonical/og URL及标题元数据直接迭代DOM；不同ID检测最多保留两个代表值，但逐项检查所有命中。解析器升至`generic-labelled-v0.2.108`。
- 新回归确认2,005条挂牌ID提及完整计数、证据仅保留20条且截断标志正确；重复匹配ID之后出现的冲突ID仍阻止审核。collection parser/service **336 passed**；全量离线pytest **815 passed、22 skipped、23 subtests passed**。22项数据库集成因缺少`TEST_DATABASE_URL`跳过；保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包完整性/manifest校验通过。仅合成HTML离线验证；未访问网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本与人工标签；P0-01真实V0.1备份和P0-02样本/许可/标签仍缺。


## 2026-11-11 P0-03合并挂牌字段判定与证据匹配扫描
- 失败回归复现同一挂牌价pattern被`_first_unique_numeric`与证据构造各扫描一次；1,002条相同挂牌价触发2次完整匹配遍历。现单遍同时计算冲突唯一值、完整`mention_count`和最多20条证据；字段值、Decimal等值判定、冲突状态与证据内容保持原语义。解析器升至`generic-labelled-v0.2.109`。
- 新回归确认1,002次命中时只调用一次该字段pattern，价格保留365万元、完整计数1002、证据20条且截断标志正确。解析器/采集服务 **337 passed**；全量pytest **816 passed、22 skipped、23 subtests passed**。22项数据库集成因缺少`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 证据序列化压力探针：36,025字节合成HTML产生74,790字节fields JSON；可见文本按35,000字符截断，价格/面积各保留最多20条证据。本探针记录实际输出规模，不代表真实页面或全输入极限。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包完整性/manifest校验通过。仅合成HTML离线验证；未访问网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本与人工标签。


## 2026-11-11 P0-03复用重叠列表根的可见文本
- 失败回归复现：嵌套`main`、`article`、`.content`候选会各自生成评分文本，选中的根随后再被完整提取一次；80层嵌套内联节点中选中的`main`被遍历2次。现每个唯一候选根只抽取一次，候选评分和最终字段解析复用该规范化文本；相同Tag只评分一次，候选优先级与信号分数不变。解析器升至`generic-labelled-v0.2.110`。
- 回归确认80层嵌套候选根的文本提取调用各为1次，社区/面积/总价与原来一致。解析器/采集服务 **338 passed**；全量pytest **817 passed、22 skipped、23 subtests passed**。22项数据库集成因缺少`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`与开发包完整性/manifest校验通过。仅合成HTML离线验证；未访问网站、NAS或生产数据库，无迁移/部署；真实页面准确率仍待获准样本与人工标签。


## 2026-11-11 P0-03合并明确排除节点的DOM扫描
- 失败回归统计到文档根节点11次完整后代遍历，其中脚本/样式/导航等排除、dialog、`[hidden]`和`style`隐藏内容分别触发整树查询。现用一次迭代树遍历判定并移除这些子树；跨层联动规则不变。相同合成文档的根级完整遍历降到7次上限。
- 回归同时检查可见挂牌价不被hidden/dialog/details广告污染，样式表可见性告警仍保留；解析器/采集服务 **339 passed**，全量pytest **818 passed、22 skipped、23 subtests passed**。22项数据库集成因缺少`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及开发包完整性/manifest校验通过。仅合成HTML离线验证；未访问网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标签。

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
# 2026-11-12 P0-04 官方条款与门禁状态同步
- 同步贝壳2026-11-12生效协议、安居客当前协议正文/版本无法确认及目标Robots当前不可读取的证据边界至路线图与项目状态。
- 两站无本项目书面许可；来源和全局在线采集继续关闭。仅文档更新，无代码、数据库、NAS或部署变化。
- GOAL_STATE JSON、文档空白与`git diff --check`通过；开发包包含124个文件，ZIP完整性和包内SHA-256清单校验通过。

## 2026-11-12 P0-03字段证据窗口边界回归
- 候选根文本窗口边界回归现在还断言字段证据偏移切片与独立`quote`完全一致，且候选值可在原文片段中定位；不改变候选根选择或跨语义区域合并行为。
- 精确边界用例2 passed；解析器专项340 passed；全量离线pytest 855 passed、26 skipped、25 subtests passed，26项PostgreSQL集成因未配置`TEST_DATABASE_URL`而跳过；有1条既有Starlette/httpx弃用警告。
- 仅测试断言变更；未访问来源网站、NAS或生产数据库，无迁移/部署。用户已确认同套面积差按较小面积为分母；社区名与详情字段跨语义根合并策略仍待确认，现有行为保持不变。

## 2026-11-12 P2-02同步面积差分母契约
- API跨平台候选说明补充面积差公式`abs(a-b)/min(a,b)`，明确使用较小挂牌面积作分母，和用户确认的业务口径及`app/services.py`实现一致；未改机会算法。
- `tests/test_opportunities.py` **21 passed**，包含较大/较小面积两种方向和5%边界；未运行数据库集成测试。
- 仅更新契约与状态文档，无应用代码、数据库、NAS或部署变化。

## 2026-11-12 P0-08留存与备份保护当前工作区测试复验
- 基于当前源码重跑`tests/test_storage_report.py`与`tests/test_backup_script_stdlib.py`，**31 passed**；标准库证据完整性组合`python3.12 -m unittest discover -s tests -p 'test_storage_report_stdlib.py' -v`为**4 passed**。覆盖90天边界、备份集路径与权限/软链接保护、证据gzip大小/哈希校验及错误传播。
- 仅使用本机合成临时目录；未读取NAS实际库存、未上传/运行当前工作区版本、未清理任何文件。P0-08既有NAS备份恢复验收仍是历史部署证据；留存报告逐路径版尚未在NAS复验。

## 2026-11-12 P0-08 NAS只读留存库存与版本差异复核
- 按NAS技能先试`nas-lan`（超时），Tailscale CLI提示无法读取偏好且本机未安装Tailscale App；随后使用已授权的`notedock-nas`，确认身份`DXP4800/sheng`。
- NAS现有`storage_report.py` SHA-256为`54b39480b8b2a2f6b3f45b19ede649c5ba1f8e29c033bd4253c1db4727f648ac`，工作区版本为`5668942a72c493bc81591afdcadc5a586378001b65ce8a0af9eee897d8b21b1b`，版本不一致。NAS旧版留存函数只读返回90天外备份候选0个/0字节；当前backups库存37文件、1,123,531字节，最早/最新文件修改时间分别为2026-11-09 13:38:21Z、2026-11-11 03:07:37Z。
- 宿主SSH用户直接盘点raw-pages遇到权限拒绝；通过现有API容器的只读挂载统计为2个普通文件/249字节，无符号链接。未读取页面正文或数据库业务行，没有上传/运行工作区脚本、改权限、清理文件、迁移、改Compose/卷/服务或部署。NAS运行的是旧报告版本；本轮结果不能视为工作区逐路径版已部署/验收。

## 2026-11-12 P0-03修正候选根越界数值评分
- 先添加兄弟`main`/`article`复现：`main`含小区名但面积5㎡、总价0万时，旧评分仅按标签匹配选中它，导致后续有效`article`被忽略。
- 候选根的面积/总价信号现在要求首个匹配值落在解析器支持范围（面积10–20,000㎡、总价1–200,000万）才计分；社区名、面积、总价最终仍全部来自同一个选中根。已有同根多值冲突仍保留并阻止审核。解析器版本更新至`generic-labelled-v0.2.114`。
- 新回归先失败后通过；候选根和外层冲突保护定向3 passed，解析器专项**341 passed**，全量离线pytest **856 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因无`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、文档空白检查、`git diff --check`及开发包校验通过。仅离线合成HTML；未访问来源网站、NAS或生产数据库，无迁移/部署。真实标注页面仍缺，跨语义根字段合并策略仍待用户确认。
## 2026-11-12 P0-03区间与单值冲突证据
- 修复区间值与同字段单值同现时静默选取单值的问题。现在保留区间原文mention并标记`multiple_area_mentions`/`multiple_price_mentions`，字段留空；仅区间时追加`missing_*`。解析器升至`generic-labelled-v0.2.116`。
- 新回归先失败后通过；范围/冲突定向15 passed、解析器358 passed、保存证据1 passed、全量离线pytest874 passed/26 skipped/25 subtests。30条范围证据上限回归确认只保存20条、总数及截断标志正确。
- API响应定向回归确认范围冲突证据和未就绪状态对外可见；1 passed，全量离线pytest更新为875 passed/26 skipped/25 subtests。

## 2026-11-12 候选根评分歧义边界
- 候选根评分要求唯一、无范围且位于支持区间内的社区/面积/挂牌价信号；冲突字段不抬高噪声兄弟根评分。
- 保留嵌套外层`main`的语义边界及文本截断后的详情根回退；新增失败回归，解析器版本为`generic-labelled-v0.2.117`。
- 解析器定向 **359 passed**，全量离线pytest **876 passed、26 skipped、25 subtests passed**；compileall、GOAL_STATE JSON与差异空白检查通过。26项DB集成未设置`TEST_DATABASE_URL`而跳过。

## 2026-11-12 候选根评分对齐规范化等值
- 候选根信号按规范化社区名和Decimal数值判断不同值；等值格式重复保持信号，扫描至真实冲突时停止加分。解析器升至`generic-labelled-v0.2.118`。
- 解析器 **361 passed**；全量离线pytest **878 passed、26 skipped、25 subtests passed**。26项DB集成未设置`TEST_DATABASE_URL`而跳过。

## 2026-11-12 范围mention纳入样本集评估
- 样本清单和评估器可将面积/挂牌价范围作为一个完整证据候选，并与同字段单值一起对账；不将范围端点拆开。范围端点严格校验且与解析器共用分隔符规则。
- 校验器/评估器139 passed、解析器361 passed、全量离线pytest885 passed/26 skipped/25 subtests passed；26项DB集成未设置`TEST_DATABASE_URL`而跳过。

## 2026-11-12 防止截断范围提取首端点
- 面积/挂牌价范围分隔符被可见文本上限截断时，不再把首端点提取为单值；解析器升至`generic-labelled-v0.2.119`。
- 截断边界20 passed、解析器381 passed、全量离线pytest905 passed/26 skipped/25 subtests passed；26项DB集成因未设置`TEST_DATABASE_URL`跳过。

## 2026-11-12 增加范围证据专属评估场景
- 样本标签增加可选`area_ranges`和`price_ranges`，复用现有候选列核验完整范围mention，不拆分端点、不增加CSV列。
- 校验/评估144 passed、解析器381 passed、全量pytest910 passed/26 skipped/25 subtests passed。
- 范围专属评估对面积和价格证据截断各新增回归，均确认不完整证据判失败；校验/评估146 passed，全量离线pytest912 passed/26 skipped/25 subtests passed。
- `price_ranges`独立评估路径新增回归（不依赖`multiple_prices`标签）；范围校验/评估147 passed，全量离线pytest913 passed/26 skipped/25 subtests passed。

## 2026-11-12 P0-03离线基线复验
- Python 3.12虚拟环境全量离线pytest复验：913 passed、26 skipped、25 subtests passed；26项数据库集成因未配置`TEST_DATABASE_URL`跳过。
- compileall、目标状态JSON解析和差异空白检查通过；source-only开发包124文件，ZIP与逐文件SHA-256校验通过。
- 仅复验和打包，无应用逻辑、数据库、配置变化；未访问来源网站、NAS或生产数据库，无部署。

## 2026-11-12 P0-03防止中文数字范围首端点误报
- 范围符后出现常见中文数字时，面积/挂牌价单值正则不再提升范围首端点；解析器升至`generic-labelled-v0.2.120`。新增两项失败回归；范围/截断/字段边界35 passed、解析器383 passed、全量离线pytest915 passed/26 skipped/25 subtests。
- API说明同步。仅合成HTML离线验证；无数据库迁移/配置变化，未访问来源网站、NAS或生产数据库，无部署。

## 2026-11-12 P0-03修正修饰价格冒号边界
- `口播:总价`、`成交:总价`、`折后:挂牌价`等修饰价格不再被算作挂牌报价；负向前缀同时识别英文/中文冒号和冒号后空格。解析器升至`generic-labelled-v0.2.121`。
- 连同中文数字范围首端点保护，解析器391 passed、全量离线pytest924 passed/26 skipped/25 subtests passed；26项数据库集成未配置`TEST_DATABASE_URL`而跳过。
- 仅合成HTML离线验证；无数据库/配置迁移，未访问来源网站、NAS或生产数据库，无部署。

## 2026-11-12 P0-03阻止修饰复合标签的挂牌价后缀误匹配
- 修复口播/成交/折后修饰的`挂牌总价`或`出售总价`被降级匹配为末尾`总价`、造成真实挂牌价冲突的问题；解析器升至`generic-labelled-v0.2.122`。
- 跨来源相关解析器回归54 passed、评估器1 passed、解析器397 passed、全量离线pytest930 passed/26 skipped/25 subtests passed。
- 仅合成HTML离线验证；无数据库或配置迁移、无来源/NAS/生产数据库访问及部署。

## 2026-11-12 P0-03挂牌价标签正向回归
- 在贝壳/安居客上新增`总价`、`挂牌总价`、`挂牌价`、`出售总价`正向解析回归；仅测试变更，解析器版本保持`generic-labelled-v0.2.122`。
- 标签定向58 passed、解析器405 passed、全量离线pytest938 passed/26 skipped/25 subtests passed。

## 2026-11-12 P0-03挂牌价语境组合矩阵
- 增加672种自动化输入回归，覆盖14类非挂牌价格修饰语、6种分隔写法、4种价格标签与贝壳/安居客两来源。解析器版本不变。
- 组合矩阵2 passed、解析器407 passed、全量离线pytest940 passed/26 skipped/25 subtests passed。仅测试变更，无生产访问或部署。

## 2026-11-12 P0-03挂牌价别名评估回归
- 样本评估器验证`挂牌总价`、`挂牌价`、`出售总价`别名的准确率/精确率；评估器69 passed、解析器407 passed、全量离线pytest943 passed/26 skipped/25 subtests passed。
- 仅测试及文档记录，无应用逻辑/数据库/配置变更，无来源或NAS访问与部署。

## 2026-11-12 P0-03隔离交易总价
- `交易总价`不再误计为挂牌价；新增单独与并列两种情境回归，解析器升至`generic-labelled-v0.2.123`。
- 720种价格语境组合通过；解析器411 passed、评估器67 passed、全量离线pytest948 passed/26 skipped/25 subtests passed。
- 仅合成HTML与测试/文档更新，无数据库迁移、来源访问、NAS访问或部署。

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
- 为两个来源的口播价/交易价场景添加零样本报告回归，保证`pass_rate_pct`为`null`。
- 评估器92 passed；全量离线pytest 988 passed、26 skipped、25 subtests passed。
- 生成124文件源码/文档开发包并通过ZIP与包内摘要校验。
- 仅离线测试与文档/目标状态记录；未修改应用逻辑或数据库，未连接网站、NAS、生产库或部署。

## 2026-11-12 P0-03排除连接词后的非挂牌金额
- 修复口播/合同/交易/签约限定词通过“的/中/中的/里/里的”连接价格标签时仍被当作挂牌价的误提取；解析器版本升至`generic-labelled-v0.2.125`。
- 两来源16项解析回归和价格类型评估回归通过；全量pytest **1012 passed、26 skipped、25 subtests passed**。
- 生成并校验124文件源码/文档开发包。仅离线合成样本，无数据库迁移或部署。

## 2026-11-12 P0-03覆盖空白分隔的价格限定词
- 修复HTML文本节点间空白使口播/合同/交易/签约价格限定词漏检的问题；单价及范围证据均按有界上下文过滤。解析器升至`generic-labelled-v0.2.126`。
- 空白连接语境40项回归通过；全量pytest **1044 passed、26 skipped、25 subtests passed**。
- 生成并校验124文件源码/文档开发包。仅离线合成样本；无数据库迁移、来源访问、NAS访问或部署。

## 2026-11-12 P0-03评估空白连接词后的价格范围
- 为口播价/交易价评估增加两来源的空白连接词范围场景，验证非挂牌范围不会进入挂牌价证据。
- 新增回归8 passed；全量pytest **1052 passed、26 skipped、25 subtests passed**。
- 生成并校验124文件源码/文档开发包；仅测试变更，无数据库、来源访问、NAS操作或部署。

## 2026-11-12 P0-06修复历史补采分页续跑
- 新增迁移013记录DTK历史补采游标与固定截止时间；Worker每轮5页后保留进度，仅读到末页才完成首次同步。历史模式切换/显式重启会清空旧进度。
- 新增续跑、截止时间稳定、进度清理与模式重置回归。全量pytest **1055 passed、26 skipped、26 subtests passed**；跳过项均需TEST_DATABASE_URL。迁移事务与Compose顺序静态校验通过，PostgreSQL实际迁移未执行。
- 仅离线开发；未连接DTK、NAS或生产数据库，无部署。

## 2026-11-12 P0-09持久化待抓详情URL队列
- 新增迁移014和Worker队列：详情URL发现后先持久化；单条详情普通失败会记录尝试与错误类型，保留重试并继续其他详情/列表分页。每轮仍最多尝试20个详情；许可、Robots、403/429阻断仍停止目标。成功暂存后删除队列行，由挂牌ID ledger保障幂等恢复。
- 发现状态API最多返回100条待抓URL及总数/截断标记。新增跨轮失败恢复回归，相关发现/服务/状态65 passed；403/429阻断不处理队列下一项的回归通过；全量pytest **1060 passed、26 skipped、27 subtests passed**。本机TEST_DATABASE_URL未设置；Docker socket权限拒绝，临时PG16仍因系统shmget限额无法启动，故PostgreSQL实际迁移/API集成未运行。临时数据库目录已清理。
- 本轮仅离线工作区改动；未访问来源网站、NAS或生产数据库，无迁移/部署。
## 2026-11-12 P0-09持久化详情URL队列
- 新增迁移014及目标级待抓详情URL持久化队列；详情临时失败保留并跨轮重试，不阻断其他详情和列表分页。认证发现状态API提供最多100条待抓URL、总数和截断标记。
- 离线回归覆盖跨轮恢复、列表扫轮继续，以及403/429阻断后保留失败项且不请求下一条。全量pytest 1060 passed、26 skipped、27 subtests passed；26项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过，迁移014和真实数据库API查询尚未验证。
- 仅本机离线/mock验证；未访问网站、NAS或生产数据库，无迁移/部署。P0-09仍需隔离PostgreSQL 17验证，并待获准来源样本校准选择器。

## 2026-11-12 P0-03候选根评分挂牌价语义回归
- 新增回归确认“合同总价”不计入候选根的挂牌价信号，兄弟内容根中的明确挂牌价仍可选中并解析。
- 定向测试1 passed；全量离线pytest **1061 passed、26 skipped、27 subtests passed**。26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过；保留1条Starlette/httpx弃用警告。
- 仅测试变更，无应用逻辑、数据库或配置变化；未访问来源网站、NAS或生产数据库，无迁移/部署。P0-03真实解析准确率仍待每站20份获准页面与人工标签。

## 2026-11-12 P0-03评分后续已知类内容根
- 失败回归复现：当首个`.houseInfo`只含“推荐阅读”、后续`.content`包含小区/面积/挂牌价时，解析器只检查首个类容器并漏掉完整候选。现分别检查`.houseInfo`、`.house-info`和`.content`各自首个节点，再按既有分数选根；不跨根拼字段。解析器升至`generic-labelled-v0.2.127`。
- 根选择定向 **5 passed**，解析器专项 **464 passed**，全量离线pytest **1065 passed、26 skipped、27 subtests passed**。26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过；保留1条Starlette/httpx弃用警告。
- 仅本机合成HTML验证，无数据库配置变更；未访问来源网站、NAS或生产数据库，无迁移/部署。P0-03真实准确率仍待每站20份获准页面及人工标签。

## 2026-11-12 P0-04官方来源协议复核
- 贝壳协议现标示2026-11-11更新、2026-11-12生效；继续要求书面许可并限制自动化获取、授权范围外用途，且要求遵守Robots。安居客官方中心列出消费者/经营者协议及历史版本入口，但当前消费者协议正文未能读取。
- 尝试刷新两站实际目标主机Robots未成功：网页工具无法读取，NAS别名公网DNS失败且未发出robots请求。2026-11-10的NAS结果明确仅为历史快照，不外推为当前规则。
- 来源仍无本项目书面许可，在线采集保持OFF。仅更新政策证据与状态文档，未访问房源页或采集。详见`docs/SOURCE_POLICY_REVIEW_2026-11-12.md`。

## 2026-11-12 P0-09补充详情队列PG级联回归
- 新增PostgreSQL集成回归：确认详情失败的`attempt_count/last_error_type`可持久读取，删除关联挂牌观察后详情队列按外键级联清理。
- 全量离线pytest **1065 passed、27 skipped、27 subtests passed**；27项均因未设置`TEST_DATABASE_URL`跳过，其中本条级联回归尚未实际运行。保留1条Starlette/httpx弃用警告。
- 仅测试变更，无应用逻辑、数据库或配置变化；未访问房源网站、NAS或生产数据库，无迁移/部署。P0-09迁移014仍需隔离PostgreSQL 17验证。

## 2026-11-12 P0-09本机PostgreSQL替代路径复核
- 尝试在临时目录初始化本机PostgreSQL 16，以便评估无需后台daemon的单用户数据库验证；`initdb`在bootstrap阶段即因System V `shmget`共享内存限制失败，未建立数据库。initdb清理了数据文件，本轮生成的临时目录也已删除；未执行任何迁移。
- 全量pytest **1065 passed、27 skipped、27 subtests passed**；27项均因未设置`TEST_DATABASE_URL`跳过，包含详情队列级联回归。保留1条Starlette/httpx弃用警告。
- 迁移014真实PostgreSQL执行仍待隔离PG17环境；NAS源码传输/临时容器授权尚未得到答复。本轮未访问来源网站、NAS或生产数据库，无部署。

## 2026-11-12 P0-03候选根排除连接式合同挂牌价
- 失败回归复现：候选 `.houseInfo` 中的“合同中的挂牌价”被根评分当作挂牌价信号，导致评分提前停止，漏掉后续 `.content` 的真实挂牌价；贝壳、安居客两项回归在修复前均失败。
- 候选根评分与字段抽取现在使用相同的连接式非挂牌语境排除规则；解析器升至 `generic-labelled-v0.2.128`。解析器专项 **466 passed**，全量离线pytest **1067 passed、27 skipped、27 subtests passed**；27项数据库集成跳过，因本机未设置`TEST_DATABASE_URL`。保留1条Starlette/httpx弃用警告。
- 仅离线合成HTML验证；无迁移、数据库或配置变化，未访问来源网站、NAS或生产数据库，无部署。真实准确率仍待每站20份获准页面及人工标签。

## 2026-11-12 P0-03检查全部同类候选内容根
- 新增贝壳/安居客回归：首个 `.content` 是“推荐阅读”时，后续同类 `.content` 的完整挂牌信息必须仍可被选择；旧逻辑两项均失败。
- 现在按文档顺序评分所有已知类候选根，仍选择一个根、保留首个满分及平分先后规则，不跨根合并字段。解析器升至 `generic-labelled-v0.2.129`；候选根定向 **15 passed**、解析器专项 **468 passed**、全量离线pytest **1069 passed、27 skipped、27 subtests passed**。
- NAS只读检查确认目标主机与PG17镜像可用；未传输源码或创建测试容器。无生产变更、迁移或部署；数据库集成仍因未设置`TEST_DATABASE_URL`跳过，真实解析准确率仍待获准样本与人工标签。

## 2026-11-12 P0-03保留嵌套内容根冲突并避免重复遍历
- 两站合成回归发现：独立评分嵌套`.content`可只选内层挂牌价，从而隐藏外层冲突证据。现在同一已知类根只由最外层候选评分；外层可见文本包含子树，冲突继续可见，兄弟类根仍按文档顺序比较。另以40层嵌套断言候选文本只遍历一次，解析器升至`generic-labelled-v0.2.130`。
- 嵌套候选回归2 passed，候选根17 passed，解析器专项470 passed，全量离线pytest **1071 passed、27 skipped、27 subtests passed**。27项数据库集成因没有`TEST_DATABASE_URL`跳过；无NAS写入、网站访问、数据库迁移或部署。

## 2026-11-12 P0-03记录article与嵌套content冲突口径待确认
- 离线复现：外层`article`写300万、嵌套`.content`写320万时，当前两来源解析器只返回内层320万。跨根冲突应保留还是优先更具体内层根尚待用户选择；答复前保持现有代码。
- 仅合成HTML只读复现，无代码/数据/配置变化或部署；结果不代表真实准确率。

## 2026-11-12 P0-04从NAS复核贝壳/安居客目标Robots
- `notedock-nas`只读连接确认为 `DXP4800/sheng`。使用代码中的 UA 对 `nb.ke.com/robots.txt` 与 `ningbo.anjuke.com/robots.txt` 发起直接HTTPS GET，不跟随重定向，读取最多65,537字节；两者HTTP 200。
- 6,676字节贝壳robots使示例详情路径`/ershoufang/109900001234.html`的RobotFileParser结果为拒绝；372字节安居客robots允许示例`/sale/1234567.html`。SHA-256分别记入来源政策复核文档。
- 未请求房源页面、未写NAS文件、未采集或部署。安居客协议正文及两站本项目书面许可缺失，因此在线采集仍双重关闭。


## 2026-11-12 P0-09详情队列静态复核
- 静态检查队列重试、上游限制中止、分页/详情上限续跑和完整扫轮计数；未发现可确认的新缺陷。
- 本轮pytest复跑未能启动（系统Python缺pytest，uv缓存被沙箱拒绝读取）；最近已记录结果1071 passed、27 skipped、27 subtests passed，本轮未复验。
- 记录用户确认的面积差公式与当前实现一致；仅更新文档，无代码、数据库或部署变化。


## 2026-11-12 P0-09全量离线回归复验
- 使用已有Python 3.12临时测试环境全量运行：1071 passed、27 skipped、27 subtests passed；27项PostgreSQL集成未运行。
- Docker本机daemon权限受限；未进行NAS写入或部署。迁移014真实PG17验证仍待授权。
- 更新目标/状态记录并重新生成开发包；无应用代码变更。


## 2026-11-12 P0-09 NAS隔离测试资源只读核验
- 使用此前获准的`notedock-nas`确认目标为`DXP4800/sheng`；LAN路径超时，Tailscale CLI/应用当前不可用。
- 只读Docker盘点确认PG17与Python 3.12镜像已存在，未发现命名为rehouse/p009的临时容器。未上传源码、创建容器或写NAS。
- 隔离PG17迁移014验证仍需远端临时Docker写入及源码传输授权。


## 2026-11-12 P0-04补充安居客协议正文证据
- 读取安居客官方静态域名用户协议PDF：正文包含Robots、书面许可、抓取与商业利用限制。
- 协议中心提供当前消费者协议/历史版本目录；既有核读记录PDF更新于2021年5月，但与当前版本映射未核实；两站继续OFF。
- 同步来源政策矩阵、目标与项目状态；仅政策文档变更，没有房源请求、采集、代码或部署操作。


## 2026-11-12 同步项目当前状态摘要
- 在状态与路线图首页汇总最新离线测试结果、未完成P0门槛、协议证据版本不确定性及在线采集OFF策略。
- 明确PG集成仍跳过，NAS本轮只读；远端源码传输/临时Docker写入未授权。
- 仅文档更新，无代码、数据库、配置或部署变化。
## 2026-11-12 文档同步健康指标统计边界与验证摘要
- README验证摘要同步至当前解析器`generic-labelled-v0.2.131`、解析器专项472 passed、评估器专项116 passed及全量离线pytest 1073 passed/27 skipped/27 subtests；跳过项为未连接PostgreSQL的集成测试。
- API健康指标文档补充解析成功率与字段完整率从迁移010启用后累计，旧运行数据不回填解析历史；与README和P0-07验收口径一致。
- 仅文档同步；本轮未修改应用代码、数据库、NAS或部署状态。

## 2026-11-12 P0-09重新运行离线回归并尝试本机隔离PostgreSQL
- 全量pytest实跑 **1073 passed、27 skipped、27 subtests passed**；27项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过。迁移/Compose标准库检查 **3 passed**。
- 本机PG16一次性集群在`initdb` bootstrap阶段因System V `shmget`共享内存限制失败；临时目录清理，没有执行迁移。Docker daemon不可访问。
- PG17隔离执行需通过`notedock-nas`传输源码并创建/清理临时Docker资源，已向用户请求明确授权；未访问NAS或生产环境、未部署。
- README文件导航同步到当前迁移001–014，GOAL_STATE与项目状态记录当前回归及未完成的PG17验收。
- 按NAS技能复核连接路径后，通过已获准的`notedock-nas`只读确认DXP4800/sheng；生产API/Worker运行、PG17 healthy，所需PG17/Python镜像存在，未发现测试容器。未查询数据库schema或进行写入。

## 2026-11-12 P0-04安居客官方消费者协议入口再核验
- 官方协议中心列出消费者协议及历史版本目录；官方帮助链接`faqId=104`重定向回目录，未能提供协议正文/版本标识。官方静态PDF含Robots、商业利用及抓取/使用限制条款，但无可读版本日期，不能证明其为协议中心现行版本。
- 更新来源政策与P0-04状态记录；安居客协议适用版本和本项目书面许可仍未确认，两站在线采集保持OFF。只读官方协议资料，未访问房源页或执行采集。

## 2026-11-12 P0-04贝壳协议正文续核
- 直接核对贝壳官方协议页面，确认最新更新日期为2026-11-11、生效日期为2026-11-12；第七条限制未经书面许可读取/自动化获取平台内容，并要求遵守许可范围和Robots。
- 安居客官方协议中心仍未提供当前消费者协议正文/版本映射；现有PDF只作为风险证据。两站均无本项目书面许可，在线采集保持OFF。
- 仅读取官方协议资料；未请求Robots或房源页，未采集、访问NAS或生产数据库，也未部署。

## 2026-11-12 P0-09复核详情URL队列安全边界
- 静态追踪发现列表链接在入队前按来源域名/HTTPS URL校验，详情抓取再次校验来源并执行全局/来源许可和Robots门禁；403/429会停止队列，普通失败保留错误类别并可下轮重试。相同原始页面由`(source, source_url, raw_sha256)`候选唯一约束去重。
- 定向发现/详情队列/状态API **55 passed、7 subtests passed**。PostgreSQL唯一约束、迁移014队列表和级联行为未在本机运行，仍需隔离PG17验收。未发现新可复现问题；本轮未改应用代码。

## 2026-11-12 P0-03离线解析器边界复核
- 静态复核当前内容根评分、显式挂牌价格标签与非挂牌价格排除、面积范围、来源ID和35,000字符窗口；未发现无需未决跨根冲突口径即可确认的新缺陷，未改应用代码。
- `PYTHONPATH=. /private/tmp/ningbo-re-ai-venv312/bin/pytest -q tests/test_collection_parser.py`：**472 passed**。全部为离线测试，不代表真实页面准确率；真实样本和人工标签仍缺。
- 未访问网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-02样本校验与评估工具回归
- 对照模板/校验器/评估器的列定义和场景门槛；专项回归覆盖标签、来源与状态覆盖、内容去重、范围/多值证据及评估门禁。
- `PYTHONPATH=. /private/tmp/ningbo-re-ai-venv312/bin/pytest -q tests/test_sample_set.py tests/test_parser_evaluation.py`：**203 passed**。均为合成数据测试，不代表真实页面准确率或许可有效性；真实获准样本仍缺。未改应用代码。



## 2026-11-12 P0-03支持“装修状态”标签
- 解析器现识别“装修状态”并将其作为相邻字段边界。贝壳/安居客两来源失败回归修复后通过；版本`generic-labelled-v0.2.138`。
- 定向6 passed、解析器498 passed、全量pytest1099 passed/27 skipped/27 subtests passed。仅合成HTML离线验证；真实页面准确率仍待获准样本与人工标签。



## 2026-11-12 P0-03独立同分候选根冲突留空待审
- 用户确认独立候选根同分且字段互相矛盾时，冲突字段留空待审。此前首根优先会静默保留冲突值；现仅比较同分且互不嵌套的根，逐字段检测冲突，保留无冲突字段，不拼接跨根缺失字段。
- 贝壳/安居客覆盖小区、面积、挂牌价、区域、户型、楼层和装修冲突；冲突字段保留双方证据引用偏移。等值数值格式（120/120.0㎡、320/320.00万）不会误报，嵌套根不当作独立根。
- 解析器版本`generic-labelled-v0.2.139`；解析器专项 **512 passed**，全量离线pytest **1113 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未连接数据库。
- 仅合成HTML离线验证；真实准确率仍待获准页面和人工标签。未访问网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-04安居客消费者协议入口复核
- 官方`faqId=104`本轮重定向到协议中心`/helpcenter/policy?id=44`；协议中心显示消费者/经营者协议和历史版本目录，但当前文本提取仍未返回消费者协议正文或版本标识。官方`faqId=155`新三网协议将安居客用户服务协议指向该入口。
- 只确认当前入口链路，没有确认具体适用文本；官方静态PDF仍只能作为风险条款证据。安居客无本项目书面许可，在线采集继续OFF。未访问房源页或执行采集。

## 2026-11-12 P0-03候选根评分拒绝畸形千分位
- 失败回归复现：候选根评分将`12,34㎡`/`12,34万`直接移除逗号转成有效Decimal，导致含畸形数字的后续根压过先前有效根，最终丢失有效面积或挂牌价。
- `_number_str`现在先按解析器共享数值格式校验，再做Decimal范围判断；候选根评分与字段值接受的千分位格式一致。贝壳/安居客面积、挂牌价共4项回归由失败转通过；解析器版本`generic-labelled-v0.2.140`。
- 全量离线pytest **1117 passed、27 skipped、27 subtests passed**；27项PostgreSQL集成未连接数据库。仅合成HTML验证；真实页面准确率仍待每站20份获准页面和人工标签。未访问来源网站、NAS或生产数据库，无迁移/部署。
- 下一步继续P0-03离线解析边界复核；获准页面材料到位后再按人工标注集报告精确率与覆盖率。

## 2026-11-12 P0-03统一面积与挂牌价正数下限
- 对照模型、样本校验器和解析器后发现：模型及清单允许面积/挂牌价大于0，但解析器分别要求至少10㎡/1万元。用户确认统一为大于0；解析与候选根评分现使用同一正数边界，0仍拒绝。
- 新增两来源面积/挂牌价正值、零值及小数下溢回归。Decimal正数转float若下溢为`0.0`，现在留空并待审，避免违反正值约束。解析器版本`generic-labelled-v0.2.141`；解析器专项 **529 passed**，全量离线pytest **1130 passed、27 skipped、27 subtests passed**。
- 27项跳过为未连接PostgreSQL的集成测试。仅合成HTML验证，真实准确率仍待每站20份获准页面和人工标签；未访问来源网站、NAS或生产数据库，无迁移/部署。
- 下一步继续P0-03离线边界复核；获准页面到位后按人工标签评估。

## 2026-11-12 P0-02校验样本挂牌ID来源格式
- 样本清单对无可识别ID的列表URL仅检查`source_listing_id`长度，可能接受`listing-123`或Unicode全角数字，造成不符合平台ID格式的人工真值进入评估。校验器现对普通ID和冲突候选共用来源格式：贝壳8–220位、安居客7–220位ASCII数字；`unknown_id`/`source_id_conflict`仍要求标签ID留空。
- 5项两来源回归覆盖非数字、过短数字及全角数字，旧逻辑失败，修复后通过；样本集专项 **92 passed**，全量离线pytest **1135 passed、27 skipped、27 subtests passed**。
- 27项跳过为未连接PostgreSQL的集成测试。仅合成清单验证；真实获准页面与人工标注仍缺，P0-02保持todo。未访问网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-02统一missing_fields场景判定
- 样本校验器此前允许某行仅因`multiple_prices`而挂牌价留空时，同时标记`missing_fields`；评估器会排除该挂牌价，不认为缺失字段场景成立，造成清单校验通过但场景评估失败。现在校验器与评估器一致：此组合必须另有一个可计入missing_fields的空标签。
- 新增失败回归；样本集专项 **93 passed**，全量离线pytest **1136 passed、27 skipped、27 subtests passed**。
- 跳过为未连接PostgreSQL的集成测试。仅合成清单验证；真实获准页面和人工标注仍缺，P0-02保持todo。未访问网站、NAS或生产数据库，无迁移/部署。


## 2026-11-12 P0-03挂牌单价不能充当挂牌总价
- 离线复现贝壳/安居客“挂牌价：2万/㎡”会将单价写入`asking_price_wan`；扩展回归也覆盖`/m²`、`/平米`、`/平方米`、`/平`、`每平方米`及每面积范围值。
- 解析器在总价标签后排除单位面积后缀；同页明确总价保留，单位价格不造成第二个挂牌价冲突。解析器升至`generic-labelled-v0.2.142`。
- 单价专项 **26 passed**；全量离线pytest **1162 passed、27 skipped、27 subtests passed**。跳过项为未连接PostgreSQL的集成测试；仅合成HTML验证，未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本和人工标注。



## 2026-11-12 P0-03覆盖全角斜杠单位面积报价
- 在上一轮单位面积价格保护基础上发现全角斜杠`／`仍会使“挂牌价：2万／㎡”落入`asking_price_wan`；贝壳/安居客的单值、区间写法均复现。现ASCII与全角斜杠均识别，短写`每平`也在回归覆盖内。
- 解析器版本`generic-labelled-v0.2.143`。单价专项 **38 passed**；解析器专项 **567 passed**；全量pytest **1174 passed、27 skipped、27 subtests passed**。27项为未连接PostgreSQL的集成测试。
- 仅合成HTML离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实样本准确率仍待每站20份获准页面和人工标签。
- 文件：`app/collectors/parser.py`、`tests/test_collection_parser.py`、`docs/API.md`、`docs/PROJECT_STATUS.md`、`docs/ROADMAP.md`、`docs/TEST_REPORT.md`、`docs/GOAL_STATE.json`、`README.md`、`CHANGELOG.md`。无配置变化。
- 下一步：继续P0-03离线边界回归；获准材料到位后完成真实样本准确率验收；获得真实V0.1备份后推进P0-01旧库升级。



## 2026-11-12 P0-03全角斜杠单位价API端到端验证
- API回归验证贝壳/安居客提交`挂牌价：2万／㎡`后候选保持pending、挂牌总价为空、不伪造挂牌价字段证据，原始HTML gzip逐字节完整保留。
- 解析器`generic-labelled-v0.2.143`；单位价解析专项 **38 passed**、API专项 **2 passed**、解析器专项 **567 passed**；全量pytest **1176 passed、27 skipped、27 subtests passed**。27项为未连接PostgreSQL的集成测试。
- 仅合成HTML/mock API离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实样本准确率仍待每站20份获准页面和人工标签。
- 文件：`app/collectors/parser.py`、`tests/test_collection_parser.py`、`tests/test_collection_api.py`、`docs/API.md`、`docs/PROJECT_STATUS.md`、`docs/ROADMAP.md`、`docs/TEST_REPORT.md`、`docs/GOAL_STATE.json`、`README.md`、`CHANGELOG.md`。无配置变化。
- 下一步：继续P0-03离线边界回归；获准材料到位后完成真实样本准确率验收；取得真实V0.1备份后推进P0-01旧库升级。



## 2026-11-12 P0-03单位面积报价纳入缺失总价评估
- 新增贝壳/安居客评估器回归：页面仅含“挂牌价：2万／㎡”而人工真值总价为空时，asking_price字段指标与`missing_fields`场景都要求解析结果为空，避免单位价误报未被准确率指标捕获。
- 两来源评估回归 **2 passed**；解析器版本`generic-labelled-v0.2.143`，解析器专项 **567 passed**、评估器专项 **118 passed**、API专项 **2 passed**；全量pytest **1178 passed、27 skipped、27 subtests passed**。跳过项为未连接PostgreSQL的集成测试。
- Python 3.12 compileall、GOAL_STATE JSON及diff检查通过。仅合成HTML/mock离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。
- 文件：`tests/test_parser_evaluation.py`、`docs/PROJECT_STATUS.md`、`docs/ROADMAP.md`、`docs/TEST_REPORT.md`、`docs/GOAL_STATE.json`、`README.md`、`CHANGELOG.md`。无运行配置/数据库迁移变化。
- 下一步：继续P0-03离线边界回归；获准材料到位后完成真实样本准确率验收；取得真实V0.1备份后推进P0-01旧库升级。



## 2026-11-12 P0-03兼容“万元/㎡”报价格式
- 复现“挂牌价：2万元/㎡”会误填2万总价、“2-3万元/㎡”会被判为多个总价。单位面积后缀检测现允许`万`与面积单位之间有`元`；单值/范围均排除，独立“挂牌价：200万元”仍保留为总价。
- 解析器版本`generic-labelled-v0.2.144`；单位价与万元正向/反向定向 **76 passed**；解析器专项 **605 passed**、评估器专项 **118 passed**、API专项 **2 passed**；全量pytest **1216 passed、27 skipped、27 subtests passed**。27项为未连接PostgreSQL的集成测试。
- Python 3.12 compileall、GOAL_STATE JSON、diff及开发包校验通过。仅合成HTML/mock离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。
- 文件：`app/collectors/parser.py`、`tests/test_collection_parser.py`、`docs/API.md`、`docs/PROJECT_STATUS.md`、`docs/ROADMAP.md`、`docs/TEST_REPORT.md`、`docs/GOAL_STATE.json`、`README.md`、`CHANGELOG.md`。无配置变化。
- 下一步：继续P0-03离线边界回归；获准材料到位后完成真实样本准确率验收；取得真实V0.1备份后推进P0-01旧库升级。



## 2026-11-12 P0-03排除括号包裹的单位面积报价
- 复现“挂牌价：2万（元/㎡）”“2万（每平方米）”仍误填总价。单位面积后缀现支持金额与单位之间的括号、括号中的“元/㎡”以及“万元（每平方米）”；范围报价同样排除。独立“挂牌价：200万元”仍保留总价。
- 解析器版本`generic-labelled-v0.2.145`；单位价/括号/万元边界定向 **96 passed**，解析器专项 **625 passed**，评估器专项 **118 passed**，API专项 **2 passed**；全量pytest **1236 passed、27 skipped、27 subtests passed**。27项为未连接PostgreSQL的集成测试。
- Python 3.12 compileall、GOAL_STATE JSON、diff及开发包校验通过。仅合成HTML/mock离线验证；未访问网站、NAS或生产数据库，无迁移/部署。
- 文件：`app/collectors/parser.py`、`tests/test_collection_parser.py`、`docs/API.md`、`docs/PROJECT_STATUS.md`、`docs/ROADMAP.md`、`docs/TEST_REPORT.md`、`docs/GOAL_STATE.json`、`README.md`、`CHANGELOG.md`。无配置变化。
- 下一步：继续P0-03离线边界回归；获准材料到位后完成真实样本准确率验收；取得真实V0.1备份后推进P0-01旧库升级。



## 2026-11-12 P0-03保留挂牌价近似/上下限语义
- 复现“挂牌价：200万左右/以上/以下/起”等被当作精确总价且候选就绪。对挂牌金额后接近似或上下限词的情况，解析器现将`asking_price_wan`置空并追加`non_exact_asking_price`；字段证据仍保留数值命中，独立精确总价根优先于带限定词的候选根。
- 回归覆盖两来源19种“左右/上下/以上/以下/以内/起/约/大约/大概/不超过”等后缀、精确值冲突和候选根评分。解析器版本`generic-labelled-v0.2.146`；解析器专项 **665 passed**，评估器专项 **120 passed**，API专项 **12 passed**；全量pytest **1280 passed、27 skipped、27 subtests passed**。27项为未连接PostgreSQL集成测试。
- Python 3.12 compileall、GOAL_STATE JSON、diff检查通过。仅合成HTML/mock离线验证；未访问网站、NAS或生产数据库，无迁移/部署。
- 文件：`app/collectors/parser.py`、`tests/test_collection_parser.py`、`tests/test_collection_api.py`、`tests/test_parser_evaluation.py`、`docs/API.md`、`docs/PROJECT_STATUS.md`、`docs/ROADMAP.md`、`docs/TEST_REPORT.md`、`docs/GOAL_STATE.json`、`README.md`、`CHANGELOG.md`。无配置变化。
- 下一步：继续P0-03离线边界回归；获准材料到位后完成真实样本准确率验收；取得真实V0.1备份后推进P0-01旧库升级。


## 2026-11-12 P0-03户型边界回归补齐
- 对照样本规则与API模型确认`bedrooms`允许0（开间/无独立卧室），上限20。解析器行为一致；新增贝壳/安居客两来源的0与20边界回归，验证字段证据保持且不报越界。
- 户型边界专项 **4 passed**；解析器专项 **669 passed**，评估器专项 **120 passed**，API专项 **12 passed**；全量pytest **1284 passed、27 skipped、27 subtests passed**。27项为未连接PostgreSQL集成测试。
- Python 3.12 compileall、GOAL_STATE JSON、diff检查通过。仅合成HTML/mock离线验证；未访问网站、NAS或生产数据库，无迁移/部署。
- 文件：`tests/test_collection_parser.py`、`docs/PROJECT_STATUS.md`、`docs/ROADMAP.md`、`docs/TEST_REPORT.md`、`docs/GOAL_STATE.json`、`README.md`、`CHANGELOG.md`。无运行配置或数据库变化。
- 下一步：继续P0-03离线语义边界回归；获准材料到位后完成真实样本准确率验收；取得真实V0.1备份后推进P0-01旧库升级。

## 2026-11-12 P0-03避免“起始摘要”误伤精确挂牌价
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-12-approx-price-summary.zip`；打包器已校验ZIP完整性及包内SHA-256清单。
- 全量回归复现精确`总价：300万`后紧邻折叠`<summary>起始...`时，之前新增的独立“起始”限定词会错误清空挂牌价。移除过宽的独立匹配，仅保留明确的“起始价”；对应限定价测试不再把单独“起始”当作报价修饰语。
- 精确挂牌价与折叠摘要回归及限定价矩阵定向 **51 passed**；全量离线pytest **1296 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成测试未连接。
- 仅合成HTML/mock离线验证；无来源网站、NAS或生产数据库访问，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标签。

## 2026-11-12 P0-03扩展挂牌价语义评估门禁
- 评估器回归原先只覆盖“200万左右”，未覆盖其余已支持的近似/上下限后缀，也没有锁定折叠摘要“起始”不得清空精确价格。现新增两来源评估矩阵，覆盖约、大约、大概、左右、上下、出头、以上、以下、以内、附近、不到、不足、不超过、不高于、不低于、起、起价、起售、起售房源、起步、起步价、起始价、封顶及ASCII/全角加号，并新增折叠摘要精确总价评估回归。
- 评估器定向 **52 passed**；全量离线pytest **1346 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未连接；仅合成HTML和清单验证。
- 无来源网站、NAS或生产数据库访问，无迁移/部署。真实字段准确率仍待每站20份获准页面和人工标签。

## 2026-11-12 P0-03端到端验证限定挂牌价不进入候选精确总价
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-12-price-e2e-guard.zip`；打包器与独立`sha256sum -c MANIFEST.sha256`、`unzip -t`均通过。
- 页面提交API此前只对“左右”覆盖单一近似价；现将两来源端到端回归扩展为25种报价限定后缀，检查API候选保持pending、asking_price_wan为空、保留`non_exact_asking_price`及原始HTML压缩证据逐字节一致。
- API定向 **50 passed**；完整离线pytest **1394 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成因未配置本机隔离数据库跳过；保留1条既有Starlette/httpx弃用警告。
- 仅合成HTML/mock验证；无来源网站、NAS或生产数据库访问，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标签。

## 2026-11-12 P0-07 NAS生产版本与健康只读复核
- 按NAS连接技能尝试LAN：`nas-lan`超时；Tailscale CLI无法载入偏好且本机未安装Tailscale App。使用此前获准的`notedock-nas`后确认宿主为`DXP4800/sheng`，只执行只读检查。
- UGREEN Compose项目`ningbo-re-ai`显示运行3个容器：API/Worker运行、PostgreSQL healthy；`http://127.0.0.1:8788/healthz`返回`ok=true`及schema v0.2。容器登记的Compose路径为`/volume3/docker/ningbo-re-ai/docker-compose.yml`，当前容器仅将SQL 001–004作为初始化脚本挂载。
- NAS API容器解析器为`generic-labelled-v0.2.5`，与工作区`generic-labelled-v0.2.148`不一致；parser、collection_service、main、worker四个源码SHA-256均与工作区不一致。`/api/collection/health`未携认证请求返回401；本轮未读取凭据，也未验证认证后的指标正文。未查询生产业务行或迁移目录表，因此不能据此断言生产库迁移状态。
- P0-07仍`in_progress`：运行态健康已确认，但健康指标契约及工作区新代码仍未在生产验证/部署。全程只读，无配置、容器、卷、数据库或代码写入。

## 2026-11-12 P0-03 API保留折叠摘要前的精确挂牌价
- 新增两来源`POST /api/collection/pages`回归：精确总价后紧邻折叠`<summary>起始摘要</summary>`时，API仍返回精确挂牌价及其证据，不产生`non_exact_asking_price`或`multiple_price_mentions`，原始HTML gzip内容保持一致。
- 定向 **2 passed**；全量离线pytest **1396 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未连接；保留1条既有Starlette/httpx弃用警告。
- 仅合成HTML/mock离线验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标签。

## 2026-11-12 P0-03识别数字前的近似/上下限挂牌价
- 开发包：`../ningbo-re-ai-v0.2-dev-2026-11-12-leading-price-qualifiers.zip`；项目打包器、包内清单哈希及ZIP完整性检查通过。
- 新回归复现“挂牌价约200万”“总价不超过200万”等前置限定词此前未进入价格命中：字段虽为空，但缺少`non_exact_asking_price`且没有数值证据。现于挂牌标签后识别金额前限定词；候选评分排除该金额，最终字段留空并保留命中证据。价格范围也接受前置限定词并保留完整范围，不提升端点。
- 首次全量运行还发现新增警告检查多扫描整段价格文本一次；现把判断合并进既有证据扫描，重复价格扫描次数维持原契约。两来源前置限定词/范围解析专项 **50 passed**，API前后置限定词与摘要专项 **98 passed**，评估器前后置限定词专项 **96 passed**；解析器测试文件 **732 passed**。
- 全量离线pytest **1539 passed、27 skipped、27 subtests passed**；27项PostgreSQL集成未连接。解析器版本`generic-labelled-v0.2.149`。仅合成HTML/mock离线验证；未访问网站、NAS或生产数据库，无迁移/部署。真实准确率仍待每站20份获准页面和人工标签。

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
