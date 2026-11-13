## 2026-11-13 ZCode PR #8/#7合并前GitHub Actions双模块组合验证
- PR #8新Head `e29e6c3`：Quick **1959 passed**，隔离PG17 Integration **31 passed**。价格后接“每月还贷/每年物业费”两来源新增6项正向回归，单位周期报价两来源新增12项排除回归。
- PR #7先单独Quick **1853 passed**、PG17 **31 passed**；随后合并最新main（含PR #8）到其审查分支，最终Head `9d561a6`：Quick **1963 passed**，PostgreSQL17 Integration **31 passed**，无失败；审查P2线程全部解决。
- 验证地点为GitHub Actions独立测试环境，不是NAS生产DB。未进行真实贝壳/安居客页面准确率、DTK服务24小时巡检或NAS生产迁移验收。

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
## 2026-11-12 P0-03验证限定挂牌价区间证据穿过提交API
- 贝壳和安居客`POST /api/collection/pages`回归覆盖“挂牌价：300-320万左右”和“挂牌价：300万-320万以上”。候选保持pending且挂牌价为空；`multiple_price_mentions`与`non_exact_asking_price`告警、完整范围候选、含限定词quote及`is_non_exact=true`均在响应和数据库JSONB写入参数中一致，gzip原始HTML完全一致。
- 端到端定向 **4 passed**；全量离线pytest **1735 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有弃用警告。解析器版本`generic-labelled-v0.2.162`。
- 使用Mock数据库和合成HTML；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率未验证。

## 2026-11-12 P0-03评估器校验非精确值引用中的限定词
- 模拟解析器返回`is_non_exact=true`但证据`quote`遗漏“左右”后缀，原`non_exact_prices`评估仍错误通过。评估器现对非精确面积与挂牌价逐条检查：quote必须包含候选值和近似/上下限限定词；损坏的面积/价格证据回归均判失败。
- 非精确评估场景定向 **43 passed**；全量离线pytest **1731 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机；保留1条既有Starlette/httpx弃用警告。解析器版本`generic-labelled-v0.2.162`。
- 仅合成HTML/Mock验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率未验证。

## 2026-11-12 P0-03保留挂牌价连接词与完整限定证据
- 两来源回归发现“挂牌价为约200万”“挂牌价约为200万”“挂牌价在200万左右”原先漏挂牌价证据，而“挂牌价为200万”也未解析。现识别“为/在”连接词，并保留“为”精确、“在”非精确的差别。
- 挂牌价近似/上下限单值与区间证据的`quote`现在包含完整限定后缀；区间中带限定词会同时标记`is_non_exact=true`并追加`non_exact_asking_price`。相关解析器/API/评估器测试 **327 passed**；全量离线pytest **1729 passed、28 skipped、27 subtests passed**。解析器版本`generic-labelled-v0.2.162`。
- 28项PostgreSQL集成未连接本机，保留1条既有弃用警告。只使用合成HTML/Mock；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率未验证。

## 2026-11-12 P0-03处理面积“在”限定并保留“为”精确语义
- 失败回归发现“建筑面积在100㎡左右”此前无面积证据/`non_exact_area_sqm`告警；现将“在”识别为非精确限定，候选数字与完整引用保留并待审。同时支持精确写法“建筑面积为100㎡”，不把“为”误判成近似限定。
- 解析器/API/评估器相关定向 **119 passed**；全量离线pytest **1705 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有Starlette/httpx弃用警告。解析器版本`generic-labelled-v0.2.160`。
- 仅合成HTML与Mock验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率未验证。

## 2026-11-12 P0-03补齐估算/参考面积限定词
- 两来源失败回归发现：“建筑面积：参考/估算/预估100㎡”只报缺字段而不保留数值证据/限定告警；“100㎡参考/估算/预估”则会输出精确面积。面积限定词现覆盖前置和后置的参考、估算、估计、预估表达，按统一待审契约留空并保存完整证据。
- 解析器/API/评估器相关定向 **111 passed**；全量离线pytest **1697 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有Starlette/httpx弃用警告。解析器版本`generic-labelled-v0.2.159`。
- 仅合成HTML和Mock验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率未验证。

## 2026-11-12 P0-03确认近似/上下限面积待审契约
- 按用户确认的“留空待审、保留候选证据并告警”核对现有实现；贝壳/安居客解析器及API回归覆盖`100㎡左右`、`100㎡以上`，并检查`area_sqm=null`、`non_exact_area_sqm`、完整证据和`ready_for_review=false`。样本校验/评估器也要求相同的待审门禁。
- 定向相关用例 **69 passed**；全量离线pytest **1649 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有Starlette/httpx弃用警告。
- 这是对既有实现的业务口径确认和验证，本轮未改应用代码、未访问来源网站/NAS/生产数据库，也未迁移或部署。真实页面准确率仍未验证。

## 2026-11-12 P0-03评估器阻止核心字段缺失却审核就绪
- 失败回归复现：评估器仅核对“字段留空+歧义警告”，即使来源ID/小区/面积/挂牌价等核心必需字段冲突或缺失、解析器却给出`ready_for_review=true`，仍会把样本判为通过。
- 对会使核心必需字段无值的场景，评估器现同时要求`ready_for_review=false`：来源ID冲突/未知、社区/面积/价格冲突及范围、多值价格、核心字段缺失和没有挂牌价的口播价格。可选字段（户型/区域/楼层/装修）歧义仍只按其字段为空、警告和证据集合核验，不强制该候选整体未就绪。
- 负向回归在旧逻辑下7项先失败；扩展来源ID冲突和口播价格后共9项通过。评估器文件 **248 passed**；解析器/API/样本集/评估器相关四文件 **1259 passed**；全量离线pytest **1649 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机，保留1条既有Starlette/httpx弃用警告。
- 仅离线模拟解析结果和合成清单，无数据库/运行配置变更；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待获准样本与人工标签。

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

## 2026-11-12 P0-03完整保留“平方”单位证据
- 回归确认“建筑面积：100平方”的单值证据不得截短为`平`；`120平方-130平方`不得同时生成截短单值mention和范围mention。两来源完整quote测试及范围边界通过。
- 定向 **9 passed**；解析器 **759 passed**，全量离线pytest **1562 passed、28 skipped、27 subtests passed**。28项本机数据库集成未连接；隔离PG17最近一次数据库集成29 passed。Python 3.12 compileall、GOAL_STATE JSON、diff检查和129文件包校验通过。

## 2026-11-12 P0-03建筑面积“平”单位回归
- 新增两来源`建筑面积：100平`测试，修复前均漏提取；补齐后解析为100㎡。另将`120平-130平`与`120-130平`加入范围边界回归，确认不从范围提取端点。
- 单值/范围定向 **6 passed**；解析器文件 **736 passed**，全量离线pytest **1559 passed、28 skipped、27 subtests passed**。28项PostgreSQL集成未连接本机数据库，最近一次隔离PG17数据库集成29 passed。Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`及129文件开发包校验通过。保留1条既有Starlette/httpx弃用警告。

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
- 新增`non_exact_prices`样本清单校验与评估回归：恰好一个数值候选；范围、多候选、零值及超范围拒绝；要求挂牌价为空、出现`non_exact_asking_price`、证据完整且与人工候选相等，无限定词时判失败。
- 样本校验与评估器 **323 passed**（新增证据截断边界回归1 passed）；全量离线pytest **1553 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过；保留1条既有Starlette/httpx弃用警告。
- 使用合成HTML和虚构清单；未访问网站、NAS或生产数据库，无迁移/部署。真实页面准确率仍待每站20份获准页面和人工标签。

## 2026-11-12 P0-03独立同分候选根冲突留空待审
- 用户确认独立候选根同分且字段互相矛盾时，冲突字段留空待审。此前首根优先会静默保留冲突值；现仅比较同分且互不嵌套的根，逐字段检测冲突，保留无冲突字段，不拼接跨根缺失字段。
- 贝壳/安居客覆盖小区、面积、挂牌价、区域、户型、楼层和装修冲突；冲突字段保留双方证据引用偏移。等值数值格式（120/120.0㎡、320/320.00万）不会误报，嵌套根不当作独立根。
- 解析器版本`generic-labelled-v0.2.139`；解析器专项 **512 passed**，全量离线pytest **1113 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未连接数据库。
- 仅合成HTML离线验证；真实准确率仍待获准页面和人工标签。未访问网站、NAS或生产数据库，无迁移/部署。


## 本轮回归
- `tests/test_collection_parser.py`：**512 passed**。
- 全量pytest：**1113 passed、27 skipped、27 subtests passed**；27项为未连接PostgreSQL的集成测试。

## 本轮回归
- `tests/test_collection_parser.py`：**504 passed**。
- 全量pytest：**1105 passed、27 skipped、27 subtests passed**；27项为未连接PostgreSQL的集成测试。

## 2026-11-12 P0-03装修标签回归
- “装修状态：毛坯”在贝壳/安居客两来源的新增失败用例修复后通过；定向 **6 passed**，解析器专项 **498 passed**。
- 全量离线pytest **1099 passed、27 skipped、27 subtests passed**；27项为未连接PostgreSQL的数据库集成测试。
- 只用合成HTML；真实页面准确率未验证。

## 2026-11-12 P0-03复合售价标签后缀边界
- 将`售价`、`挂牌售价`纳入所有非挂牌前缀/分隔符组合回归。失败场景`折后挂牌售价：300万`复现短标签从复合标签内部起始，绕过`折后`过滤；现使用负向边界阻止“售价”从`挂牌`之后独立匹配。
- 限定词组合 **82 passed**，解析器 **496 passed**，全量pytest **1097 passed、27 skipped、27 subtests passed**。仅合成HTML离线测试。

## 2026-11-12 P0-03扩展挂牌价标签
- 新增两来源售价标签用例，`售价`和`挂牌售价`均应提取为挂牌价；并新增`成交售价`和`合同售价`限定语用例，保证不提取为挂牌价。
- 相关价签/限定词专项 **82 passed**；解析器 **496 passed**；全量离线pytest **1097 passed、27 skipped、27 subtests passed**。使用合成HTML，真实页面准确率未验证。

## 2026-11-12 P0-03扩展装修标签回归
- 新增两来源×两标签测试，覆盖“装修情况：精装”“装修状况：简装”。修复前均无法提取，修复后均保留正确装修值。
- 新装修/楼层组合定向 **8 passed**；扩展装修标签另外验证完整原文quote和字符偏移；解析器专项 **488 passed**；全量离线pytest **1089 passed、27 skipped、27 subtests passed**。仅合成HTML验证，真实页面准确率未验证。

## 2026-11-12 P0-03挂牌楼层与总楼层区分
- 在贝壳/安居客合成输入中复现“总楼层”被作为挂牌楼层抽取及冲突清空。现排除`总楼层`标签，并让它结束前一`所在楼层`值；保留“楼层：高楼层 14/18层”。
- 两来源4项新回归修复前均失败，修复后 **4 passed**；解析器 **484 passed**；全量离线pytest **1085 passed、27 skipped、27 subtests passed**。27项数据库集成未连接数据库。仅合成页面验证，不代表真实页面准确率。

## 2026-11-12 P0-03区间与单值冲突证据
- 失败回归先复现：区间后出现同字段单值时，旧解析器会静默选择该单值且不记录区间证据。现两个端点区间被作为完整范围mention保留，范围与单值同现时字段置空并警告`multiple_*_mentions`；仅区间时同时警告`missing_*`。
- 面积/价格范围及冲突定向 **15 passed**；解析器 **357 passed**；候选保存 **1 passed**；全量离线pytest **873 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成未设置`TEST_DATABASE_URL`而跳过，保留1条Starlette/httpx弃用警告。
- 范围证据上限回归：30条范围命中完整计数、保留20条、截断标志正确。更新后解析器 **358 passed**、全量离线pytest **874 passed、26 skipped、25 subtests passed**。
- 新增`test_saved_html_api_returns_range_conflict_evidence`：API响应保留完整范围与单值证据、冲突警告及未就绪状态，定向 **1 passed**；全量离线pytest更新为 **875 passed、26 skipped、25 subtests passed**。
- Python 3.12 compileall、GOAL_STATE JSON、文档空白、ZIP完整性及manifest校验通过。未访问来源网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-03数值范围分隔符边界
- 覆盖10种ASCII/Unicode范围分隔符，分别用于面积/总价范围，确认端点不作为单值命中；另断言横线后接楼层/装修标签不会屏蔽合法单值。
- 新增边界定向 **13 passed**；`tests/test_collection_parser.py` **355 passed**；全量离线pytest **870 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成未设置`TEST_DATABASE_URL`而跳过，1条Starlette/httpx弃用警告。
- 仅回归测试变更，解析器v0.2.115无运行代码改动。

## 2026-11-12 P0-03多值冲突证据偏移
- 新增`test_conflicting_field_evidence_offsets_survive_excerpt_truncation`：小区及挂牌价冲突位于1,000字符证据摘录之外，断言候选字段和证据值均为null、告警存在、quote偏移可从完整归一化文本还原。
- 相关冲突/证据用例 **5 passed**；解析器专项 **344 passed**；全量离线pytest **859 passed、26 skipped、25 subtests passed**。26项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 待审核候选重提测试新增持久化断言：小区、面积及总价的证据值与字段一致，并保留quote；service/parser组合 **377 passed**。
- 仅回归测试变更；用户尚未确认可选字段多值冲突是否应阻止`ready_for_review`，暂不改变该行为。

## 2026-11-12 P0-03拒绝范围形式的面积和挂牌价
- 新增`test_numeric_ranges_are_not_parsed_as_single_listing_values`，覆盖无单位首端点及两端都带单位的面积/总价范围；匹配到范围时字段留空、候选不就绪。
- 使用已存在的`/private/tmp/ningbo-re-ai-test-venv`运行：定向 **2 passed**；`tests/test_collection_parser.py` **343 passed**；全量离线pytest **858 passed、26 skipped、25 subtests passed**，保留1条Starlette/httpx弃用警告。26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12 `compileall`、GOAL_STATE JSON、文档空白、`git diff --check`及开发包SHA-256 manifest/ZIP完整性检查通过。没有安装依赖、访问网络、NAS、来源网站或生产数据库。

## 2026-11-12 P0-03候选根评分范围校验
- 新增兄弟根回归：含显式小区名但面积5㎡/总价0万的`main`不应因标签齐全遮蔽包含有效面积/总价的`article`。先复现失败后修复评分；数值首个匹配只有落在解析范围时计为信号。
- 解析器版本`generic-labelled-v0.2.114`；候选根及外层冲突保护3 passed；解析器 **341 passed**；全量离线pytest **856 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成未设置`TEST_DATABASE_URL`而跳过。
- 既有单次全文匹配扫描回归保持通过；未访问来源/NAS/生产库，无迁移/部署。跨语义根仍不做字段合并改动。

## 2026-11-12 P0-08 NAS只读留存库存复核
- 通过已授权`notedock-nas`复核：NAS报告脚本SHA-256与当前工作区不同；NAS现有留存函数返回90天外备份候选0个/0字节，backups为37文件/1,123,531字节。raw-pages通过既有API容器挂载统计为2文件/249字节，无符号链接。
- 宿主SSH用户无法读取raw-pages；未查询数据库记录/内容、未上传/运行工作区版本、未改权限或删除文件。不是新版NAS验收。

## 2026-11-12 P0-08留存与备份保护复验
- 当前工作区`tests/test_storage_report.py`及`tests/test_backup_script_stdlib.py` **31 passed**；标准库证据完整性测试 **4 passed**。覆盖90天边界、备份集路径保护、gzip大小/哈希校验与读错误传播。
- 仅合成临时目录；未访问NAS库存、上传/运行脚本或清理文件。

## 2026-11-12 P2-02跨平台面积差API口径同步
- `docs/API.md`补充用户已确认的面积差公式`abs(a-b)/min(a,b)`，即以较小面积作分母；机会计算代码未改。
- `tests/test_opportunities.py` **21 passed**，覆盖面积两侧方向和5%边界。
- 仅文档同步；没有数据库集成、NAS或生产部署验证。

## 2026-11-12 P0-03字段证据窗口边界一致性
- 扩展候选文本窗口精确边界回归：三项关键字段的证据偏移必须在35,000字符窗口内，偏移切片必须与独立`quote`完全一致，候选值必须能从quote中定位。只强化测试契约，不改变解析行为。
- 边界用例2 passed；解析器专项340 passed；全量离线pytest **855 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过；保留1条Starlette/httpx弃用警告。
- 未访问来源网站、NAS或生产数据库，无迁移/部署。面积差公式已由用户确认为较小面积作分母；跨语义根合并策略仍待确认。

## 2026-11-12 P0-03固定Unicode差分回归有界归一化
- 将之前的临时10,000组Unicode空白差分核验固化为pytest固定种子用例（1,000组，覆盖中文、ASCII、TAB/CR/LF、不换行空格、全角空格、行分隔符、BOM及零宽空格），逐项与完整`re.sub(r'\s+', ' ', text)`输出前缀和截断标志比较。
- 解析器专项 **334 passed**；全量离线pytest **847 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 仅测试变更；有界归一化实现和跨根字段策略均未变。Python 3.12 compileall、GOAL_STATE JSON、空白检查和开发包校验通过。

## 2026-11-12 P0-03覆盖body文本回退的有界截断语义
- 增加无`main/article/.content`时body回退用例：窗口内小区/面积/365万正常提取；窗口后的900万不计入提及数或多价告警；`visible_text_truncated`仍存在、证据偏移不越过35,000字符且审核就绪为false。
- 新回归通过；解析器专项 **333 passed**；全量离线pytest **846 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 未改解析器逻辑，只补回退分支验证。Python 3.12 compileall、GOAL_STATE JSON、空白检查和开发包校验通过。本地合成HTML；未访问网站、NAS或生产数据库，无迁移/部署。
- 跨根字段合并口径仍待用户确认；有界归一化继续保持现有输出语义。

## 2026-11-12 P0-03检查分段文本下的归一化峰值内存
- 对照完整`re.sub`各5次：450,098字节/30,000个短span token页面，有界方法峰值中位34.79 MiB、完整归一化34.50 MiB（+0.29 MiB）；380,098字节/20,000个短段落页面，24.54 MiB对24.40 MiB（+0.14 MiB）。均在测量噪声/小幅开销范围；说明显著内存节省集中于长连续文本，分段页面收益有限。
- 两种输入均为本地合成页面，tracemalloc包含BeautifulSoup DOM等开销，不能视为真实页面内存SLO。本轮无代码修改、未重跑测试。
- 下一轮保持有界实现的简洁性；若真实获准页面可用，再按真实DOM分布复核耗时与内存。跨根字段合并口径仍待用户确认。

## 2026-11-12 P0-03复核有界归一化的多种DOM输入表现
- 同进程交替基准每类30次：500,098字节/大量短span节点，中位181.88 ms（有界）对182.27 ms（完整归一化，−0.2%）；780,098字节/长空白，中位5.28 ms对5.26 ms（+0.5%）；300,098字节/重复段落，中位112.36 ms对112.46 ms（−0.1%）。P90差异均小，未见有意义的回退；长连续文本的16.5%中位改善和峰值内存下降另见前节。
- 所有输入均为本地合成HTML；页面大小受1 MB输入上限约束，测时包含DOM解析，不能代表真实站点或生产SLO。本轮仅做对照测量，无代码变更、未重跑全量测试。跨根字段合并策略仍待用户确认。
- 下一轮维持简单的有界归一化实现，继续验证语义等价和截断边界；不据合成性能推断真实站点指标。

## 2026-11-12 P0-03复用候选根的有界归一化文本
- 新增`_normalize_text_prefix`：文本按与`re.sub(r'\s+', ' ', ...)`等价的规则归一化，只保留前`MAX_VISIBLE_TEXT_CHARS`字符并返回准确的截断状态。候选根评分和最终字段提取复用同一前缀，避免每个重叠根完整分配归一化后的长字符串；根选择规则及输出字段范围不变。
- 六项边界回归覆盖空串/零上限、空白折叠及截断；另以固定种子对10,000组Unicode空白输入对照完整`re.sub`结果与截断标志，全部一致。解析器专项 **332 passed**；全量离线pytest **845 passed、22 skipped、23 subtests passed**。数据库集成22项因未设置`TEST_DATABASE_URL`跳过。
- 800,144字节重叠main/article合成页，40次交替比较：有界归一化中位数24.80 ms、P90 24.93 ms；完整归一化中位数29.69 ms、P90 29.87 ms，中位数低16.5%。tracemalloc峰值中位数3.86 MiB，对照5.39 MiB。仅为合成实现基准，不代表真实站点。
- Python 3.12 compileall、GOAL_STATE JSON、空白检查和开发包校验通过。未访问网站、NAS或生产数据库，无迁移/部署。跨根是否允许合并社区名的策略仍待用户确认，本优化不改变该行为。

## 2026-11-12 P0-03跨语义根字段拼接诊断
- 用合成HTML确认：推荐卡仅提供小区名、详情`article`仅提供面积和总价时，当前解析器会跨兄弟区域组合三个值，并返回`ready_for_review=true`。页面标题/面包屑也可能合法提供小区，因此是否禁止跨根合并需要明确的产品口径；问题已向用户提出，不擅自改变代码。
- 独立性能探针在约800 KB页面上测得`main`与重叠`article`分别完整归一化约800 KB文本，随后选择27字符的`.content`；15次解析中位数约29.92 ms。该合成结果只说明重复归一化工作量，不代表真实页面性能。
- 本轮无应用代码修改、未运行完整测试；未访问网站、NAS或生产数据库。

## 2026-11-12 P0-03锁定混合候选根的冲突留空
- 新增合成回归：外层`main`同时含推荐卡与详情`article`，两处小区/面积/总价值不一致；解析结果将三字段留空并输出对应多值告警，不因缩小到子树而消除同页冲突。
- 该行为符合精确率优先、覆盖率另报的验收口径；未改根选择逻辑。解析器专项 **326 passed**；全量离线pytest **839 passed、22 skipped、23 subtests passed**。22项数据库集成未配置`TEST_DATABASE_URL`，保留1条Starlette/httpx弃用警告。
- 仅增加合成HTML回归，未访问网站、NAS或生产数据库，无迁移/部署。真实页面仍待每站20份授权样本和人工标签。
- 下一轮评估根信号评分与字段歧义在更多有标注合成场景下的精确率/覆盖率取舍；在线采集保持关闭。

## 2026-11-12 P0-03核对评估器的截断场景判分
- 审查`scripts/evaluate_parser.py`确认：`missing_fields`场景要求无`visible_text_truncated`；`multiple_prices`要求完整候选提及、未截断证据且与人工候选价格集合完全相等；相近的歧义候选与来源ID场景也有截断失败回归。评估器已有防漏扫误通过保护，本轮无需重复改业务逻辑。
- 本轮新增解析器断言锁定窗口外价格不进入证据计数、窗口内offset不越界；解析器325 passed，全量离线pytest838 passed/22 skipped/23 subtests。
- 下一轮检查候选根信号评分面对混合/歧义字段时的选择边界，保持不确定字段留空和人工复核原则。

## 2026-11-12 P0-03验证截断后的字段证据范围
- 加强35,000字符截断回归：窗口后的第二个报价不计入`mention_count`、不生成`multiple_price_mentions`；保留窗口内的365万证据，`end_char`不越界，同时`visible_text_truncated`仍阻止审核就绪。精确上限用例也检查社区/面积/总价证据偏移均不超过窗口。
- 定向截断/上限回归 **3 passed**；解析器专项 **325 passed**；全量离线pytest **838 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 本轮只加强合成HTML回归断言，没有业务逻辑变更；未访问网站、NAS或生产数据库，无迁移/部署。真实页面与人工标签仍缺。
- 下一轮继续检查采样评估器如何区分截断导致的不可见冲突和真实缺失字段，避免漏扫样本被误记为通过。

## 2026-11-12 P0-03锁定可见文本上限的包含边界
- 增加35,000字符精确边界回归：恰好达到上限时保留字段且不告警；仅多1字符时保留窗口内字段、增加`visible_text_truncated`并令`ready_for_review=false`。
- 两项边界回归通过；解析器专项 **325 passed**；全量离线pytest **838 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 未改业务逻辑，仅锁定评分/截断/审核边界语义。Python 3.12 compileall、GOAL_STATE JSON、空白检查和源码包校验通过。仅合成HTML验证；未访问网站、NAS或生产数据库，无迁移/部署。真实样本和人工标签仍缺。
- 下一轮继续P0-03审查截断点两侧的字段标签、证据引用和解析器评估场景。

## 2026-11-12 P0-03候选根评分与字段提取使用同一字符窗口
- 失败回归复现：40,000字符前置导航文本位于`main`，房源字段在其后的`article`；旧评分查看完整候选，因后段字段让`main`先得满分，随后字段提取截断前35,000字符，导致三个关键字段均为空。现仅以字段实际可见的前35,000字符给候选根评分，后续`article`凭其窗口内完整字段胜出。
- 回归先失败后通过；候选根专项 **4 passed**；全量离线pytest **836 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 评分与截断共用`MAX_VISIBLE_TEXT_CHARS=35_000`。解析器专项 **323 passed**；全量离线pytest **836 passed、22 skipped、23 subtests passed**。解析器保持`generic-labelled-v0.2.113`。Python 3.12 compileall、GOAL_STATE JSON、空白检查和开发包校验通过。仅用合成HTML；未访问网站、NAS或生产数据库，无迁移/部署。P0-03真实准确率仍待每站20份获准页面和人工标签。
- 下一轮继续审查有界输入下的解析准确性与重复工作，优先复核长前缀截断/候选评分组合；真实样本到位后转入标注评估。

## 2026-11-12 P0-03避免选中候选文本二次空白归一化
- 计数回归先失败：完整`main`候选正文在评分后被再次执行同一`re.sub(r'\s+', ...)`，唯一候选文本归一化2次。选中候选时复用已归一化文本，仅在回退到body时做归一化；字段结果不变。
- 解析器专项 **322 passed**；全量离线pytest **835 passed、22 skipped、23 subtests passed**，22项数据库集成因未设置`TEST_DATABASE_URL`跳过；保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON及差异空白检查通过，开发包已重建并校验。只使用合成HTML；未访问网站、NAS或生产数据库，无迁移/部署。真实准确率与性能仍需每站20份获准样本和人工标签。
- 用户再次确认P2-02面积差按较小挂牌面积作分母；现有`abs(a-b)/min(a,b)≤5%`实现符合口径，无需业务改动。
- 下一轮继续P0-03计数驱动审查，优先检查有内容分支标题或字段证据上限附近的重复文本工作。

## 2026-11-12 P0-03优化候选根搜索与折叠摘要空白裁剪
- 候选内容根现按证据分数惰性搜索：外层`main`若具备小区、面积、总价全部信号则不再查询/文本化重叠的`article`和`.content`；未满分时继续搜索，维持同分先选外层根。计数回归覆盖停止与继续两条路径。
- `_text_with_inline_boundaries`对折叠`details`摘要曾逐项`pop(0)`移除前置空白片段，合成测量显示节点数翻倍时耗时明显超比例增长。现以索引定位前置空白段，再一次切片删除；4,000/8,000/16,000/32,000节点中位数由旧版约5.46/12.03/29.52/94.16ms降为4.80/9.83/19.77/40.20ms。计数单测确认0次头部pop和1次批量删除，摘要结果保持。
- 解析器专项 **321 passed**；全量离线pytest **834 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`和开发包校验通过。
- 仅合成HTML/离线验证，未访问来源网站、NAS或生产数据库，无迁移/部署。计时不代表真实页面性能；P0-03仍需每站20份获准页面与人工标签核验准确率。
- 下一轮继续P0-03计数驱动的DOM/文本遍历审查；真实页面材料到位后按标注集评估。

## 2026-11-12 P0-03惰性选择最高证据内容根
- `_parse_generic_listing_html`此前先运行`find(main)`、`find(article)`和内容类`select_one`，再把所有重叠候选根分别完整文本化后评分。计数回归确认嵌套main/article/.content且字段齐全时执行3次根查询和3次文本化。现在按原顺序惰性查找候选；一旦当前候选命中小区、面积、总价全部3项最高分即停止。分数未满时继续搜索；同分仍保留先出现的外层根。
- 回归先失败后通过：满分main路径现在只查询/文本化main；外层信号不足时仍检查article并选择更强证据。解析器专项 **320 passed**，全量离线pytest **833 passed、22 skipped、23 subtests passed**；22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`和开发包校验通过。仅合成HTML/Mock验证；未访问来源网站、NAS或生产数据库，无迁移/部署。P0-03仍待每站20份获准页面与人工标签验证真实页面准确率。
- 下一轮继续P0-03以节点/文本计数定位重复DOM工作；发现具体可复现问题后再做小幅优化，真实样本到位后转入标注集评估。

## 2026-11-12 P0-03合并同一样式跨阶段的属性解析
- 现有回归将`_inline_css_values`调用次数误当作声明扫描次数。用`_scan_inline_css_values`重新计数后，同一带`display`、`visibility`、`opacity`和`content-visibility`的span样式在一次页面解析中实际扫描3次。新增断言先失败（3次），再把单次解析缓存改为按原始style缓存全部受审属性的结果；同一样式按不同属性请求时复用同一解析结果。缓存仍仅限单次解析、保留1024项上限及FIFO淘汰。
- 解析器专项 **319 passed**；全量离线pytest **832 passed、22 skipped、23 subtests passed**，22项数据库集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。编译、GOAL_STATE JSON、差异与开发包校验通过。
- 合成微基准30次取中位数：300种唯一style页面，旧行为13.25ms/约901次声明扫描，新行为9.41ms/约301次；300个重复style页面6.13ms对6.16ms，整体近似持平。结果仅用于合成输入的实现比较，不代表真实页面或生产性能。
- 仅处理本地合成HTML；未访问网站、NAS或数据库，无迁移/部署。P0-03仍待每站20份获准页面及人工标签进行真实性能和准确率评估。
- 下一轮继续P0-03有计数证据的离线DOM/文本遍历审查；先用回归复现真实重复工作，再决定是否需要最小优化。真实页面材料到位后转入标注集评估。

## 2026-11-11 P0-09当前工作区 PostgreSQL 17 集成续验
- NAS `DXP4800/sheng` 上的隔离测试库再次执行完整 `tests/test_db_integration.py`：**23 passed**，含分页上限、策略撤销后的跨轮续跑、已发现 ID 去重、扫轮状态和迁移/API回归。测试前后的临时数据库仅有 `public` schema，测试通过后无残留 schema。
- NAS SSHD 对端配置 `AllowTcpForwarding no`，SSH隧道请求被明确拒绝；未修改SSH配置。改为在现有 `ningbo-re-ai-api` 镜像中启动一次性测试运行器，将当前工作区源码只读挂载，并与临时 PostgreSQL 17 接入本轮 Docker internal 网络。数据库目录使用512 MiB tmpfs，无持久卷、无宿主端口，测试请求均由 Mock 替代。
- 测试容器、internal 网络、临时运行器和NAS暂存文件均已清理。复查生产 `ningbo-re-ai-db-1` 为healthy，API/Worker仍运行，生产卷 `ningbo-re-ai_pgdata` 未改变。未写生产数据库、未改生产服务/Compose、未部署，未访问房源网站。
- 这验证的是只读挂载的当前工作区与 NAS PostgreSQL 17 的集成兼容性，不代表工作区代码已部署。P0-09保持 `in_progress`；真实来源许可、获准列表/详情页面和生产版本差异验收仍未完成。

## 2026-11-11 P0-09组合验证页数/详情上限与策略恢复
- 新增多轮Worker mock：第一页同时达到每轮页数上限和详情上限并保留第二页游标；第二轮在第二页暂存一条后模拟策略撤销，保存当前页游标与已完成ID；第三轮恢复后重读第二页、跳过已暂存ID，只暂存剩余挂牌并完成同一轮扫轮。验证无重复暂存、无漏抓，完成计数仅增加一次。
- 组合回归通过；全量离线pytest **831 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过；Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。
- 仅使用合成HTML和mock，未联网采集、未访问NAS或生产数据库，也未部署。生产数据库/PG17验收仍待做。

## 2026-11-11 P0-09验证详情上限命中时保留跨页游标
- 新增多轮Worker mock：第一页刚好包含20条详情并指向第二页时，首轮只暂存20条、保存第二页游标且保持扫轮活动；第二轮从第二页继续，仅暂存新挂牌，完成后扫轮计数增加一次。确认没有重抓或漏抓；现有实现符合约定。
- 新回归通过；全量离线pytest **830 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过；Python 3.12 compileall、GOAL_STATE JSON和`git diff --check`通过。
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

## 2026-11-11 P0-07 NAS隔离PostgreSQL 17.11迁移010验证
- 用户授权的`notedock-nas`经`nas-ssh-connect`只用于NAS只读核验/隔离测试；传输当前开发包至`/tmp`后在NAS端核对SHA-256一致。
- 使用独立PostgreSQL 17.11容器：`--network none`、512MiB tmpfs数据目录、无宿主端口、无持久卷，限1 CPU/512MiB。由当前开发包顺序执行001–010，均成功；单独重复010也成功。
- 在临时库插入1条成功且四字段完整、1条失败解析事件，触发器汇总为parse_attempt_count=2、parse_success_count=1、complete_field_count=1；重复010后计数仍为2/1/1。
- 生产库只读查询显示PostgreSQL 17.11但`collection_parse_attempts`不存在；生产健康接口未认证请求返回401、`/healthz`为200。生产容器`collection_service.py`、`models.py`、`main.py`哈希与当前工作区均不同，故迁移010和本轮实现不在生产版本上；未读取业务行、未写生产库、未部署。
- 临时DB容器已移除。源码解压目录因Docker容器属主不能由SSH普通用户删除，随后通过一次性`--network none`容器定向清除并复核临时目录不存在、测试容器不存在。测试脚本首轮退出码反映清理权限问题；迁移/计数检查本身均执行成功，清理复核通过。
- 限制：这是迁移/触发器烟雾验证，不是完整`tests/test_db_integration.py`在PG17通过；也不替代API容器构建或生产迁移验收。

## 2026-11-11 P0-07落实四项健康率与解析阶段记录
- 按用户确认的累计口径实现：采集成功率=success/(success+failed)，blocked排除；解析成功率=解析器成功返回/成功获取且进入解析器的页面；字段完整率=来源挂牌ID、小区、总价、面积均非空的成功解析结果/成功解析结果；审核通过率=approved/(approved+rejected)，pending排除。百分比保留两位小数，分母为0返回null。
- 新增迁移010、collection_parse_attempts追加记录及触发器计数；记录manual_html_snapshot和public_page_collection采集方式。健康API按来源返回四项累计比率和阶段计数。解析警告/字段缺失不算解析失败；完整率按解析初始结果计算。
- PG16全量pytest 741 passed、0 skipped、17 subtests passed；含21项数据库集成。健康/服务定向30 passed，标准库42 passed。Python 3.12 compileall、GOAL_STATE JSON、备份脚本语法、迁移顺序静态检查、git diff --check和安全开发包校验通过；保留1条Starlette/httpx弃用警告。
- 临时PG16使用tmpfs和127.0.0.1绑定，已清理。仅离线源码、文档和迁移修改；未访问NAS、生产数据库或房源网站，未部署。P0-07仍需隔离NAS PG17及生产版本差异验收。

## 2026-11-11 P0-09复核历史跨失联周期留存回归
- 扩展`tests/test_db_integration.py`：挂牌记录经首次人工结论后重新出现，再连续两轮完整遍历缺失并追加第二条复核结论；分页历史返回两条记录，正式挂牌状态仍为`available`。
- PostgreSQL 16数据库集成 **20 passed**；全量pytest **739 passed、0 skipped、16 subtests passed**，保留1条Starlette/httpx弃用警告。`compileall`、标准库42项、GOAL_STATE JSON、备份脚本语法和`git diff --check`均通过；开发包已重新生成并通过包内SHA-256与ZIP完整性校验。
- 临时PG16容器使用tmpfs且仅绑定127.0.0.1，结束后清理；没有NAS、网站或生产数据库访问与部署。真实许可/样本和NAS PG17/生产验收仍待完成。

## 2026-11-11 P0-09人工核验结论API
- 按用户确认的固定结论`still_listed`（仍在列表）、`confirmed_withdrawn`（已确认撤牌）、`inconclusive`（无法确认）和可选备注新增认证POST记录接口及GET历史接口。记录仅将观察队列状态设为`reviewed`；正式挂牌`source_listings.status`不变。重复处理非待核验记录返回409，非法挂牌ID返回422。
- 新增迁移009扩展观察状态并追加保存结论，外键保留关联观察记录。同步API、数据模型、发现器和NAS升级文档。
- 本机一次性PostgreSQL 16全量`pytest -q`：**739 passed、0 skipped、16 subtests passed**；包括20项数据库集成。`compileall`、标准库测试42 passed、GOAL_STATE JSON、备份脚本语法和`git diff --check`均通过；开发包已由安全打包器生成并校验包内SHA-256清单。保留1条Starlette/httpx弃用警告。
- 本次临时PG16数据库使用tmpfs，仅绑定127.0.0.1；测试完成后容器已清理。未连接NAS、生产数据库或房源网站，未部署。真实许可/样本与NAS PostgreSQL 17/生产验收仍待完成。

## 2026-11-11 P0-09恢复列表DOM顺序并完成PG16回归
- 失败回归发现列表发现器在反向压入遍历栈时先追加锚点，导致返回顺序与页面DOM顺序相反；现改为节点出栈时追加锚点，保持页面顺序，也让详情上限优先处理页面前部挂牌。相关Mock与数据库策略撤销夹具已调整为“先处理首条、再阻断第二条”。
- 连续2次完整分页遍历未见后进入`pending_review`、不自动下架的规则已由用户确认。集成回归现在预置正式`available`挂牌并核对状态保持；另验证页数上限、请求超时和许可阻断不计入缺失扫描，恢复后完成遍历才计数。
- 使用本机一次性PostgreSQL 16（tmpfs、临时网络、仅127.0.0.1端口、无持久卷）运行`tests/test_db_integration.py`：**20 passed**；全量pytest：**739 passed、0 skipped、15 subtests passed**。保留1条Starlette/httpx弃用警告。发现器专项19 passed，采集服务+发现器专项47 passed；标准库42 passed，compileall、GOAL_STATE JSON、备份脚本语法和`git diff --check`通过。
- 临时容器、网络和数据库已清理。未访问房源网站、NAS或生产数据库，未部署；PG16合成环境结果不替代NAS PG17/生产代码验收。在线采集仍关闭，真实许可及分页样本仍缺。

## 2026-11-11 P0-09确认连续缺失阈值并实现人工核验状态
- 用户确认：同一采集目标连续 **2 次完整分页遍历**未见挂牌后转为`pending_review`；不自动下架。列表/详情请求失败、许可/robots阻断、页数或详情数上限、分页回环或歧义均不构成完整遍历。
- 迁移007记录目标级挂牌观察和列表页原始证据引用；迁移008保存遍历轮次。完整遍历结束时才递增缺失次数；重新观察清零连续缺失次数，但已经进入`pending_review`的记录不自动恢复，正式挂牌状态不变。
- 验证：Python 3.12标准库套件 **42 passed**；`compileall`、备份脚本语法、GOAL_STATE JSON和Compose迁移挂载静态检查通过。pytest未运行（模块未安装）；007/008 SQL与Worker/API数据库集成未运行（PG16启动受shmget限制，Docker socket permission denied）。未访问网站/NAS/数据库，未部署；在线采集仍关闭。
- 当前实现为离线代码完成、数据库运行验证待补。P0-09仍需许可范围、真实获准分页样本及隔离PG17/生产差异验收；当前轮不自动下架任何正式挂牌。

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

## 2026-11-11 P0-08留存盘点CLI错误诊断
- `tests/test_storage_report.py`：**17 passed**；新增普通文件根路径（两种参数）及权限错误诊断回归，3项先失败后通过。
- 全量离线pytest：**639 passed、15 skipped、13 subtests passed**；15项数据库集成需要未配置的隔离数据库。Python AST语法检查通过。
- `bash -n scripts/backup.sh`通过。仅合成目录验证；没有NAS、网站或数据库连接，没有删除文件或部署。

## 2026-11-11 P0-03锁定template惰性内容过滤行为
- 回归验证`<template>`内的挂牌价不会进入解析文本或造成多价告警；原因是当前BeautifulSoup `stripped_strings`不遍历template惰性内容，本次无需改动解析器。
- 定向`tests/test_collection_parser.py -k template_fallback_price`：**1 passed**；全量：**393 passed、14 skipped**（需`TEST_DATABASE_URL`）；compileall及GOAL_STATE JSON解析通过。
- 仅合成HTML离线验证；真实站点HTML、数据库集成与NAS部署未验证。

## 2026-11-11 P0-03嵌套隐藏节点移除不再访问已脱离标签
- 回归复现：父节点`decompose()`后，预先收集的子节点仍在遍历列表中，访问其属性会触发`AttributeError`。
- 批量删除DOM的循环现跳过`parent is None`的节点；覆盖嵌套CSS隐藏、HTML `hidden`、关闭`dialog/details`及嵌套导航容器。
- `tests/test_collection_parser.py -k nested_hidden_nodes`：**5 passed**；全量pytest：**392 passed、14 skipped**（需`TEST_DATABASE_URL`）；`compileall -q app scripts`及GOAL_STATE JSON解析通过。
- 仅合成HTML离线验证；未连接数据库、网站或NAS，未部署。

## 2026-11-11 P0-03深层HTML可见性遍历不递归
- 回归先复现1,200层嵌套HTML导致可见性遍历`RecursionError`；现改用显式栈，并保留hidden/visible继承与opacity祖先状态。
- `tests/test_collection_parser.py -k 'deeply_nested_html or inline_opacity or inline_visibility or inline_display_uses_cascade_result'`：**17 passed**；全量pytest：**387 passed、14 skipped**（需`TEST_DATABASE_URL`）；`compileall -q app scripts`及GOAL_STATE JSON解析通过。
- 仅合成HTML离线验证；数据库集成、真实页面和NAS部署未验证。

## 2026-11-11 P0-03过滤内联opacity零文本
- 回归先复现内联`opacity:0`广告报价污染挂牌价，并覆盖透明祖先下`opacity:1`后代仍不可见；同时验证百分比值、声明顺序及`!important`级联。
- 解析器将透明度归零的祖先状态传递到后代，版本为`generic-labelled-v0.2.39`。
- `tests/test_collection_parser.py -k 'inline_opacity or inline_visibility'`：**10 passed**；全量pytest：**386 passed、14 skipped**（需`TEST_DATABASE_URL`）；`compileall -q app scripts`及GOAL_STATE JSON解析通过。
- 仅合成HTML离线验证；真实站点CSS/布局、数据库集成和NAS部署未验证。

## 2026-11-11 P0-03内联visibility隐藏文本
- 回归先复现内联`visibility:hidden`广告报价被计入挂牌冲突；另验证`visibility:hidden`父元素内的`visibility:visible`后代仍会被保留。
- 解析器按CSS可见性继承处理隐藏文本，版本为`generic-labelled-v0.2.38`。
- `tests/test_collection_parser.py -k 'inline_visibility_hidden_ad_price or inline_visible_descendant_overrides or inline_display_uses_cascade_result or inline_visibility_uses_cascade_result'`：**11 passed**；全量：**380 passed、14 skipped**（需`TEST_DATABASE_URL`）；`compileall -q app scripts`及GOAL_STATE JSON解析通过。
- 仅合成HTML离线验证；真实站点CSS/布局、数据库集成和NAS部署未验证。

## 2026-11-11 P0-03精确率门槛不使用四舍五入值
- 回归先复现：1,899/1,999的实际精确率低于95%，但显示为95.00%，旧逻辑据此误标`precision_target_met=true`。
- 达标判定现用整数计数直接比较；显示的`precision_pct`仍四舍五入到两位，样本数达标状态仍独立报告。
- 定向`tests/test_parser_evaluation.py -k precision_target`：**4 passed**；全量pytest：**375 passed、14 skipped**（需`TEST_DATABASE_URL`）；`compileall -q app scripts`及GOAL_STATE JSON解析通过。
- 仅合成数据离线验证；真实页面准确率、数据库集成与NAS部署未验证。

## 2026-11-11 P0-04 HTTP响应有界读取
- 回归先复现：原HTTP客户端在检查大小前完整缓冲超限页面/robots响应（模拟8 MB流被全部读取）。现页面与robots均按64 KB分块，分别限制1,000,000/256,000字节，超限后停止读取，并预检合法Content-Length。
- `tests/test_collection_http.py`：**17 passed**；全量pytest：**374 passed、14 skipped**（需`TEST_DATABASE_URL`）；`compileall -q app scripts`通过；1条既有Starlette/httpx弃用警告。
- 使用本地MockTransport，无真实网络、NAS或数据库连接。未部署；来源许可仍待核实，在线采集保持OFF。

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

## 2026-11-10 P0-03冲突报价在正文上限之后的评估回归
- 新增`multiple_prices`评估用例，将第二个人工标注报价放在35,000字符文本上限之后；评估器不会把漏扫的冲突记为场景通过。
- `tests/test_parser_evaluation.py tests/test_sample_set.py`：95 passed；全量`pytest -q`：342 passed、14 skipped（数据库用例需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 仅合成清单/HTML验证；真实20+20样本准确率和数据库集成未验证。

## 2026-11-10 P0-03上传API返回截断警告
- 新增FastAPI `TestClient`回归，通过带API Key的`POST /api/collection/pages`提交截断样本；响应候选仍为pending，警告包含`visible_text_truncated`，`ready_for_review=false`。
- 专项`tests/test_collection_api.py tests/test_collection_service.py tests/test_collection_parser.py tests/test_parser_evaluation.py`：136 passed；全量`pytest -q`：341 passed、14 skipped（数据库用例需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- API和应用服务真实执行，数据库为假连接；未连接PostgreSQL/NAS或访问来源网站，未部署。

## 2026-11-10 P0-03截断警告候选持久化回归
- 新增`stage_html`服务层回归：含截断点后第二个报价的HTML会持久化`visible_text_truncated`，并基于返回的pending候选计算`ready_for_review=false`。
- 专项`tests/test_collection_parser.py tests/test_parser_evaluation.py tests/test_collection_service.py`：135 passed；全量`pytest -q`：340 passed、14 skipped（数据库用例需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 服务测试采用假数据库连接；未连接PostgreSQL/NAS或访问来源网站，真实页面准确率未验证。

## 2026-11-10 P0-03解析文本截断标记
- 回归先复现：正文第35,000字符后的第二个挂牌报价未被扫描，结果仍返回`ready_for_review=true`。现超限时添加`visible_text_truncated`并令该状态为false；解析器版本`generic-labelled-v0.2.35`。
- `tests/test_collection_parser.py tests/test_parser_evaluation.py`：125 passed；全量`pytest -q`：339 passed、14 skipped（数据库用例需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 仅虚构HTML离线验证，不代表真实页面准确率；未连接数据库/NAS、未访问来源或部署。

## 2026-11-10 P0-03内联CSS注释解析
- 回归先复现：`display:none /* tracking; ad */`未被视为隐藏，导致隐藏的900万报价与正文365万冲突；现先剔除CSS注释再计算display声明级联。解析器升至`generic-labelled-v0.2.34`。
- `tests/test_collection_parser.py tests/test_parser_evaluation.py`：124 passed；全量`pytest -q`：338 passed、14 skipped（数据库用例需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 仅合成HTML离线验证，不代表真实页面准确率；未连接数据库/NAS、未访问来源或部署。

## 2026-11-10 P0-03嵌入元素备用文本过滤
- 回归先复现：iframe、object、canvas中的备用挂牌价被误读为可见字段，导致正文365万因伪900万冲突而置空；修复后这些节点内容不参与字段解析。解析器升至`generic-labelled-v0.2.33`。
- `tests/test_collection_parser.py tests/test_parser_evaluation.py`：121 passed；全量`pytest -q`：335 passed、14 skipped（需`TEST_DATABASE_URL`的数据库用例），保留1条Starlette/httpx弃用警告。
- 仅离线合成HTML验证，不代表真实页面准确率；未连接数据库/NAS、未访问来源或部署。

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
- Parser/样本/评估专项：**148 passed**；全量离线pytest：**295 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。覆盖场景通过、不匹配、证据截断、重复候选和非有限/越界数值拒绝。compileall、GOAL_STATE JSON和`git diff --check`通过。
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

## 2026-11-10 P0-06空字符串游标终止值兼容
- 空字符串metadata游标回归为无游标；由空格/Tab构成的游标仍拒绝，数字0仍有效。
- DTK/Worker/模型专项 **72 passed**；全量离线pytest **267 passed、13 skipped**，13项数据库集成需`TEST_DATABASE_URL`。保留1条Starlette/httpx弃用警告。
- 仅本机离线验证，真实DTK协议/账号联调未做。

## 2026-11-10 P0-06拒绝空白游标并保留数值零游标
- 新增空格/Tab游标拒绝及数值`0`仍转成`"0"`的回归；仅有游标、没有`has_more`时继续分页。
- `tests/test_dtk.py tests/test_worker.py tests/test_models.py` **71 passed**；全量离线pytest **266 passed、13 skipped**（数据库集成需要`TEST_DATABASE_URL`）。
- 仅本机离线验证；真实DTK协议、账号权限及NAS均未验证。

## 2026-11-10 P0-06 DTK游标-only分页边界
- 修复缺少`has_more`但存在游标时的漏页风险；新增游标推断继续及明确`has_more=false`仍停止的回归。
- `tests/test_dtk.py tests/test_worker.py tests/test_models.py` **68 passed**；全量离线pytest **263 passed、13 skipped**，数据库集成需`TEST_DATABASE_URL`。保留1条Starlette/httpx弃用警告。
- 仅本机离线验证；真实DTK服务及账号联调未验证。

## 2026-11-10 P0-06 HTTPS scheme大小写兼容
- 复现已校验通过的大写`HTTPS://`主页URL被适配器误判为`sec_user_id`；修复后请求以`url`字段发送，原始URL不变。
- `tests/test_dtk.py tests/test_worker.py tests/test_models.py` **66 passed**；全量离线pytest **261 passed、13 skipped**（数据库集成需`TEST_DATABASE_URL`）。保留1条Starlette/httpx弃用警告。
- 仅本机离线验证；真实DTK服务、权限、NAS部署和账号24小时联调均未验证。

## 2026-11-10 P0-03正式20份样本量边界回归
- 构造每来源恰好20条有效且内容不同的虚构测试页面，默认门槛下报告显示两来源均`met=true`；低样本诊断测试仍为false。
- 样本清单/解析评估/留存专项 **57 passed**；全量离线pytest **259 passed、13 skipped**，跳过项需要`TEST_DATABASE_URL`。保留1条Starlette/httpx弃用警告。
- 仅离线回归；虚构测试数据不代表获准真实页面或字段准确率，未连接NAS、未运行DB集成。

## 2026-11-10 P0-03评估报告显示正式样本数门槛
- 回归先因`sample_requirements`缺失而失败；新增字段逐来源报告正式要求20份、观察数量及达标布尔值，测试用低门槛不改变正式标准。
- 样本校验/解析评估专项 **44 passed**；全量离线pytest **258 passed、13 skipped**，13项均需`TEST_DATABASE_URL`。Python 3.12 compileall、GOAL_STATE JSON和`git diff --check`通过；保留1条Starlette/httpx弃用警告。
- 仅离线验证；无真实授权样本或真实字段准确率，无DB/NAS部署验证。

## 2026-11-10 P0-03来源房源ID出处
- 解析器/候选/评估器/清单专项 **122 passed**；全量离线pytest **258 passed、13 skipped**。13项均需`TEST_DATABASE_URL`，未运行数据库集成。
- 覆盖source_url/canonical ID来源、ID冲突留空、canonical query/fragment剥除及敏感前缀不入字段证据；`compileall`、GOAL_STATE JSON与`git diff --check`通过。
- 使用本机uv缓存pytest/依赖，未联网安装；未访问网站或NAS。保留Starlette/httpx弃用警告。

## 2026-11-10 P0-03歧义字段证据留存
- 解析器/人工更正/评估器/样本清单专项 **121 passed**；全量离线pytest **257 passed、13 skipped**，13项均需`TEST_DATABASE_URL`。测试通过本机uv缓存运行，未联网安装。
- 覆盖多值字段保留候选片段但不选值、越界户型证据、每字段最多20条及总数/截断标志；`compileall`、GOAL_STATE JSON和`git diff --check`通过。
- PostgreSQL集成未运行：本地临时PG测试环境预检时socket绑定受沙箱限制；无真实页面或NAS验证。保留1条Starlette/httpx弃用警告及pytest-asyncio loop-scope默认提示。

## 2026-11-10 P0-03网页候选逐字段出处
- 解析器、候选人工更正、评估器、样本清单专项 **120 passed**；全量离线pytest **256 passed、13 skipped**，跳过项均需`TEST_DATABASE_URL`。测试通过本机uv缓存的pytest/依赖执行，未联网安装。
- `compileall`、GOAL_STATE JSON与`git diff --check`通过。保留1条Starlette/httpx弃用警告及pytest-asyncio loop-scope默认值弃用提示。
- PostgreSQL集成未运行；`TEST_DATABASE_URL`未设置，临时PG16测试环境预检时本地socket绑定被沙箱拒绝，数据库集群未启动。无NAS/生产库测试。

## 2026-11-10 P0-08过期备份文件定位
- 新增`expired_backup_files`，统一计算严格早于保留期限的普通文件并按路径排序；报告增加`backup_retention_candidate`相对路径行，不进行删除。
- 91天文件被列出、恰好90天和89天文件不列出；CLI输出候选路径后文件仍存在。存储报告专项**12 passed**；全量默认pytest **252 passed、13 skipped**（DB集成需`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告；compileall通过。
- 仅本机离线验证，NAS脚本未同步，未执行清理。

## 2026-11-10 P0-03 NAS只读部署基线核验
- 使用已授权SSH别名核对DXP4800宿主机、`ningbo-re-ai` Compose项目路径/标签和服务状态；API/Worker运行，PostgreSQL 17 healthy，`/healthz`返回200。
- 生产候选/挂牌/价格历史/条件单行数均为0，两来源关闭、启用目标0。NAS现有`collection_service.py`哈希与本地修复版不同，确认本地SQL修复未部署。
- 只读核验；没有运行备份、传输代码、重建容器或触碰数据库。NAS运行态不由本机PG16测试替代。

## 2026-11-10 P0-03 psycopg占位符缺陷修复及PG16全量验证
- DB集成测试复现`stage_html`候选SQL因`LIKE 'operator_note:%'`中未转义的`%`被psycopg误作占位符，导致页面提交500；SQL改成`%%`转义，SQL构造回归断言同步更新。
- 本机临时PostgreSQL 16隔离库、Unix socket-only运行完整`pytest -q -rs`：**264 passed、0 skipped**，包含13项数据库集成用例；保留1条Starlette/httpx弃用警告。测试后数据库、集群和socket目录已清理。
- `compileall`及GOAL_STATE JSON解析通过。数据库测试使用合成数据，未连接NAS/生产库；不替代真实V0.1备份升级，也不构成真实页面解析准确率证据。

## 2026-11-10 P0-03调用点和ID路由修复
- 将3处已失效测试函数引用改为统一`parse_listing_html`，并修复HTTP客户端共享URL校验导入路径。
- Python 3.12 `compileall -q app scripts tests`及目标`py_compile`通过；桩化来源分发、贝壳8位/安居客7位ID边界、白名单和未知source拒绝共8项断言通过。桩未执行HTML解析。
- 当前环境缺pytest、BeautifulSoup及其他项目运行依赖，pytest和真实fixture解析未执行。未连接网站/NAS，也无获准样本准确率结论。

## 2026-11-10 P0-03下架与缺字段合成页面
- 添加两个显式标注synthetic的本地fixture：贝壳页面已下架但URL含稳定ID、安居客页面缺详情ID及关键字段；测试检查字段留空、告警和不能ready_for_review。
- `py_compile tests/test_collection_parser.py`通过。定向pytest未启动（缺pytest），测试场景尚未运行；fixture不是获准真实样本。

## 2026-11-10 P0-03站点解析器入口分发
- API采集、评估器和负载测试现由统一`app.collectors.parse_listing_html`按source分发至`beike.py`/`anjuke.py`。
- 桩化验证两个适配器分别传入正确source/url/html：2 passed；`compileall`通过。pytest及真实fixture解析未运行（pytest/BeautifulSoup未安装）。适配器仍调用通用基线，无站点准确率结论。

## 2026-11-10 P0-03解析器版本断言维护
- `test_canonical_url_conflicting_listing_id_stays_pending`原硬编码`generic-labelled-v0.2.23`，而解析器已升至`.2.24`；现改用`PARSER_VERSION`常量。
- 测试文件及解析器语法编译通过；仓库未保留`.2.23`代码/测试硬编码。pytest缺失，未执行用例。

## 2026-11-10 P0-06分享URL首尾C0/C1边界
- 增加首Tab、尾换行和其他C0控制字符回归；原始控制字符检查现早于`strip()`，普通首尾空格裁剪保持。
- 6个直接`normalize_post` smoke场景通过，文件语法编译通过。pytest未运行（依赖未安装），未连接DTK。

## 2026-11-10 P0-03语义主内容区选择
- 新增回归：早于`<main>`出现的通用`.content`导航容器不得抢先选中；空`<main>`后面的非空`<article>`应作为解析区。
- 解析器版本`generic-labelled-v0.2.24`。本机`compileall`通过；pytest未启动（缺少pytest/BeautifulSoup依赖），真实页面与准确率未验证。

## 2026-11-10 P0-01旧库迁移字段保真覆盖更新
- 合成V0.1升级用例现逐表核对账号/视频、社区/房源/挂牌、价格证据、匹配、条件单及通知的代表性字段，并对002重复执行；该覆盖尚未在数据库执行。
- 已尝试`python -m pytest -q tests/test_db_integration.py -k v01_schema_migration_preserves_existing_data`，当前Python环境无pytest，命令未启动。`py_compile`可验证测试文件语法，但不能替代PostgreSQL执行结果。
- 升级手册已把无内建事务的002/003/005迁移改为`psql --single-transaction`，004保留自身事务。真实V0.1备份/升级仍未验证。
- 标准库静态断言通过：002/003/005无内部事务且无`CREATE INDEX CONCURRENTLY`，运行手册命令选项与之对应；004包含且仅包含一个`BEGIN/COMMIT`对。此检查不替代PostgreSQL执行。

## 2026-11-10 P0-03候选解析版本升级
- 可运行专项 **123 passed**，覆盖待审候选重解析SQL边界、人工更正和已审核记录保护查询路径。
- 全量pytest **225 passed、13 skipped**；13项为需`TEST_DATABASE_URL`的PostgreSQL测试，含本次新增集成回归。尝试本机临时PG16初始化时系统拒绝`shmget`，Docker API不可访问，因此SQL运行时行为尚未在本机验证。
- compileall、GOAL_STATE JSON和Compose配置校验通过；NAS/生产库未连接。
- 单测确认取回已审核候选时，`ready_for_review`按存储字段为false，不沿用当前重解析结果。

## 2026-11-10 P0-02 URL空白/控制字符边界
- 覆盖前后空格、换行、制表符、NUL和DEL；采集HTTP客户端测试确认错误输入不会触发robots或页面请求，样本CSV不再先清洗输入。
- parser/HTTP/sample/evaluator专项 **117 passed**；全量 **223 passed、11 skipped**，1条Starlette/httpx弃用警告。
- `compileall`、GOAL_STATE JSON与Compose配置检查通过；仅离线验证。

## 2026-11-10 P0-02共享URL校验
- 样本清单改为复用解析器`extract_source_id`所调用的共享URL边界；宁波主机、查询/片段、凭据、端口、尾点和ID长度回归全部通过。
- 专项 **96 passed**；全量 **211 passed、11 skipped**，保留1条Starlette/httpx弃用警告；CLI、compileall、GOAL_STATE JSON与Compose配置通过。
- 仅离线验证，未访问网站/NAS。

## 2026-11-10 P0宁波来源主机范围
- 上海贝壳、杭州安居客及平台根域拒绝回归修复前失败；宁波精确主机和一个DNS根尾点仍可接受，样本清单规则与解析器一致。
- parser/HTTP/models/sample-validator/evaluator专项：**109 passed**；全量：**211 passed、11 skipped**，1条Starlette/httpx弃用警告。
- `compileall`、GOAL_STATE JSON解析和临时占位环境变量Compose配置校验通过。未连接来源/NAS。

## 2026-11-10 P0-03共享房源ID提取逻辑
- 样本校验器CLI在项目Python环境下可直接启动并调用共享来源URL ID提取函数；专项87 passed、全量202 passed、11 skipped。
- compileall、目标JSON及Compose配置通过。系统Python缺少项目BeautifulSoup依赖，脚本验证使用项目虚拟环境；未连接网站/NAS。

## 2026-11-10 P0-03 canonical来源ID回退
- 新增唯一canonical/og:url详情ID补足缺失提交URL ID、多个规范链接ID冲突留空的回归；同时评估器确认识别ID进入字段准确率、unknown_id仍记为缺失覆盖。
- 解析器/评估器/样本清单专项：**87 passed**；全量pytest：**202 passed、11 skipped**，1条Starlette/httpx弃用警告。
- `compileall`、GOAL_STATE JSON解析及临时占位环境变量下Compose配置校验通过。解析器版本`generic-labelled-v0.2.21`；未用真实页面验收。

## 2026-11-10 P0-03严格数值准确率
- 面积与价格标签相差0.004的两项回归修复前错误计为准确，修复后正确计为不匹配；数值格式差异但数值相同继续视为匹配。
- 解析器/样本校验/评估器专项：**83 passed**；全量pytest：**198 passed、11 skipped**，1条Starlette/httpx弃用警告。
- compileall、GOAL_STATE JSON解析、临时占位变量Compose配置校验通过。未使用真实页面或报告真实站点准确率。

## 2026-11-10 P0-03 URL ID范围一致性
- 先复现：贝壳及安居客221位详情URL ID被样本清单误判为可识别ID，拒绝合法的未知ID标注；修复后专项测试 **81 passed**。
- 全量离线pytest：**196 passed、11 skipped**（PostgreSQL集成用例需`TEST_DATABASE_URL`）；保留1条Starlette/httpx弃用警告。
- `compileall`、GOAL_STATE JSON解析与设置临时占位环境变量后的`docker compose config -q`通过。未连接网站/NAS。

## 2026-11-10 P0-02样本扩展名校验
- `tests/test_sample_set.py tests/test_parser_evaluation.py`：**30 passed**，覆盖不支持的`.txt`后缀拒绝。
- 全量离线`pytest -q -rs`：**195 passed、11 skipped**；跳过项均依赖`TEST_DATABASE_URL`，保留1条Starlette/httpx弃用警告。
- compileall、`docs/GOAL_STATE.json`解析及`docker compose config -q`通过。未连接网站/NAS，无真实样本准确率结论。

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
- `nas-lan`沙箱外只读身份检查超时；Tailscale CLI无法读取偏好，App启动返回`kLSNoExecutableErr`。
- 未连接公网别名或Netcatty；等待用户授权使用`notedock-nas`自动化通道。

## 2026-11-10 P0-05全量隔离PostgreSQL 16测试
- 使用 `/private/tmp` 一次性集群和 `rehouse_test` 执行完整pytest：**144 passed、0 skipped**；集群仅监听Unix socket，未配置网络监听。
- 测试后停止服务并删除数据库临时目录；确认该目录不存在且原socket无响应。保留1条既有Starlette/httpx弃用警告；NAS生产库未连接或写入。

## 2026-11-10 P0-02/API样本字节限制
- `tests/test_collection_models.py tests/test_collection_parser.py tests/test_collection_body_limit.py`：31 passed；覆盖UTF-8字节数上限、Content-Length与分块请求体上限、正常正文重放及413响应。
- 全量默认pytest：133 passed、11 skipped（数据库集成需`TEST_DATABASE_URL`）；保留1条既有Starlette/httpx弃用警告。尝试本机PostgreSQL 16隔离初始化时，bootstrap的`shmget`因沙箱权限失败；默认及mmap动态共享内存配置均未能启动，临时目录已清理。
- `compileall`/Compose/JSON/包校验通过；未访问来源网站。NAS LAN SSH超时，Tailscale CLI偏好读取失败且App无法启动，未同步或部署。

## 2026-11-10 P0-02样本时间顺序校验
- `tests/test_sample_set.py`：11 passed；新增复核时间早于采集时间的拒绝用例。
- 全量默认pytest：128 passed、11 skipped（数据库集成需`TEST_DATABASE_URL`）；保留1条既有Starlette/httpx弃用警告。
- 未访问来源网站；nas-lan SSH超时，Tailscale CLI/App不可用，未同步或部署。检查不构成样本许可及真实性验收。

## 2026-11-10 P0-03内联 display 级联回归
- `tests/test_collection_parser.py`：23 passed；覆盖普通声明顺序、`!important`优先级，以及被后续声明恢复可见的详情字段。
- 全量默认pytest：127 passed、11 skipped（数据库集成需`TEST_DATABASE_URL`）；保留1条既有Starlette/httpx弃用警告。
- `compileall`、`docker compose config -q`、GOAL_STATE JSON解析、开发包专项3项和SHA256 manifest校验通过。未做NAS同步/部署；LAN连接超时、Tailscale CLI无法读取偏好。

## 2026-11-10 当前本机回归
- `tests/test_sample_set.py tests/test_parser_evaluation.py`：15 passed；新增样本文件和`data/raw-pages`根目录符号链接拒绝，以及普通HTML/gzip解压体尺寸上限与评估器拒绝超限样本。全量默认pytest：119 passed、11 skipped（需`TEST_DATABASE_URL`）。
- `tests/test_sample_set.py tests/test_parser_evaluation.py`：13 passed；覆盖普通HTML超限、gzip解压后超限及评估器拒绝超限压缩样本。全量默认pytest：117 passed、11 skipped（需`TEST_DATABASE_URL`）。
- `tests/test_storage_report.py`：7 passed；新增文件、目录和根路径符号链接均不跟随/计入报告范围。全量默认pytest：114 passed、11 skipped，跳过项需`TEST_DATABASE_URL`。
- `tests/test_submit_html_snapshot.py`：1 passed；确认超1MB HTML在调用API前由本地脚本拒绝。全量默认pytest：122 passed、11 skipped（跳过项需`TEST_DATABASE_URL`）。
- `tests/test_collection_parser.py`：18 passed；覆盖`aside`、HTML隐藏属性、`aria-hidden`及内联`display:none`隐藏报价排除。当前全量默认pytest：122 passed、11 skipped，均因未设置`TEST_DATABASE_URL`跳过数据库集成。
- `tests/test_dtk.py`：30 passed；新增缺失/无效任务`state`及时失败与恶意/畸形失败详情脱敏用例。默认全量pytest：110 passed、11 skipped；跳过均需`TEST_DATABASE_URL`。
- `tests/test_package_dev.py`：3 passed；覆盖秘密、凭据目录、私钥和符号链接排除，以及示例配置/raw-pages占位保留、输出限制、ZIP完整性和包内哈希。
- `compileall`、Docker Compose配置和目标JSON解析通过。历史隔离PostgreSQL 16套件为115 passed、0 skipped，但未包含之后新增的DTK/解析器/打包器测试。

## 2026-11-10 P0-06 DTK任务ID校验
- 拒绝布尔、对象及空白任务ID；特殊字符按单一路径段编码，避免请求路径被上游值改变。新增回归4项，修复前失败、修复后通过；`tests/test_dtk.py` 25 passed。
- 完整一次性PostgreSQL 16测试：**113 passed、0 skipped**；编译、Compose配置、GOAL_STATE JSON解析通过。真实DTK接口及NAS部署未验证。

## 2026-11-10 P0-06 DTK任务轮询截止时间
- 可控时钟模拟状态接口每次慢响应，回归修复前会跑满35次；修复后最多三次并在52.5秒绝对截止时退出，每次HTTP超时不超过剩余窗口。
- 一次性本机PostgreSQL 16隔离完整测试：**109 passed、0 skipped**；临时库仅Unix socket，结束后清理。编译、Compose配置、目标JSON解析通过。DTK真实服务/账号联调及NAS部署未验证。

## 2026-11-10 PostgreSQL 16隔离完整测试
- 本机一次性PostgreSQL 16集群（`/private/tmp`，仅Unix socket，`rehouse_test`）：完整pytest **108 passed、0 skipped**。新增跨平台候选API集成和未来挂牌排除测试均执行通过。
- 测试后停止服务并删除临时数据库目录；未连接/写入NAS生产库。`compileall`、Compose配置与目标JSON解析通过。保留1条Starlette/httpx弃用警告。

## 2026-11-10 P2-02未来时间戳挂牌边界
- `tests/test_opportunities.py`验证SQL查询存在`last_observed_at <= now()`上界；跨平台机会单测11 passed。
- 新增隔离PostgreSQL API用例，合成当前挂牌与未来挂牌应不产生价差机会；该用例因测试库不可用跳过。全量pytest 97 passed、11 skipped（均需`TEST_DATABASE_URL`）。

## 2026-11-10 P2-02跨平台机会API/数据库集成用例
- 新增隔离PostgreSQL测试：经API写入同小区同户型两条合成挂牌（面积100/105㎡，单价差恰好10%），断言对称候选响应、面积差边界和property未合并。
- 本机全量pytest：96 passed、10 skipped。该新用例因缺少`TEST_DATABASE_URL`跳过；尝试初始化本机PostgreSQL 16时系统拒绝`shmget`，Docker socket亦无权限，故没有数据库执行证据。

## 2026-11-10 P0-06 DTK分页状态
- 新增Worker回归用例；修复前`has_more=true`且`next_cursor=None`会记录`success`，修复后记录`partial`与缺游标原因。专项：1 passed。
- 全量`pytest -q -rs`：96 passed、9 skipped（均需`TEST_DATABASE_URL`）；`compileall`、Compose配置及GOAL_STATE JSON解析通过。
- 变更不包含DTK真实接口联调；NAS连接不可达，未部署。

## 2026-11-10 跨平台挂牌价差机会信号
- 全量`pytest -q -rs`：95 passed、9 skipped（数据库集成需`TEST_DATABASE_URL`），1条Starlette/httpx弃用警告。
- `compileall`、`docker compose config -q`及GOAL_STATE JSON解析通过。机会单测覆盖同小区/同户型/面积5%边界、单价差10%含等号、低价分母和排除条件；本轮无PostgreSQL集成或NAS部署验证。

## 2026-11-10 P2-01可比池房屋去重
- `/private/tmp/ningbo-re-ai-venv312/bin/python -m pytest -q tests/test_opportunities.py`：7 passed；新增回归覆盖少于5套独立房屋不出折价信号，以及同一房屋重复挂牌不重复计数/加权。
- 本机全量`pytest -q -rs`：69 passed、9 skipped；9项数据库集成用例需`TEST_DATABASE_URL`。有1条Starlette/httpx弃用警告。
- `compileall`、占位变量`docker compose config -q`及目标状态JSON解析通过。测试使用假连接。尝试在`/private/tmp`启动PostgreSQL 16 Unix-socket集群时，系统拒绝`shmget`（Operation not permitted），集群未启动且临时目录已清理；数据库集成用例仍跳过。NAS LAN超时且Tailscale状态不可读取，未部署。

## 2026-11-10 P1-08条件单命中理由
- 条件单匹配响应新增`match_reasons`，逐条说明查询中实际启用且满足的区域、精确小区、总价、面积、户型、最近更新时间和偏好小区；无配置条件时使用中性通用说明。
- `tests/test_saved_search.py`覆盖各过滤理由、偏好命中及无过滤条件；数据库集成断言核验API真实命中结果里的理由字符串。
- 本机PostgreSQL 16隔离库完整pytest：76 passed，1条Starlette/httpx弃用警告，无跳过。隔离集群仅Unix socket，测试后已停止并清理；编译与Compose配置解析通过。
- NAS `nas-lan`超时、Tailscale CLI无法读取本机偏好；增强尚未同步NAS，既有P1-08部署验收不代表本次新理由字段已部署。

## 2026-11-10 P0-08备份留存边界回归
- 扩展`test_expired_backup_summary_reports_only_files_older_than_retention`，同时放入91天、恰好90天和89天文件；只有严格早于90天的文件计入人工复核候选，报告不会删除文件。
- `pytest -q tests/test_storage_report.py`：5 passed；本轮完整默认测试：65 passed、9 skipped（数据库集成需`TEST_DATABASE_URL`），1条Starlette/httpx弃用警告。
- 通过NAS `nas-lan`只读连接复查仍超时；没有NAS上的当前超期候选数量，本轮无NAS同步/清理。

## 2026-11-10 P0-01既有V0.1结构迁移验证
- 新增`test_v01_schema_migration_preserves_existing_data`：PostgreSQL 16隔离schema先执行V0.1的`001_init.sql`，在11张V0.1业务表插入账号同步/作品、视频、小区别名、房源挂牌/价格、同套候选、条件单和通知等合成记录，再执行V0.2 `002_collection_pipeline.sql`两次；确认旧数据不变、来源历史标记默认为`manual_import`、新来源线上开关均关闭。
- `/private/tmp/ningbo-re-ai-venv312/bin/python -m pytest -q -rs tests/test_db_integration.py`：10 passed；随后以同一隔离库运行完整套件：74 passed、1条Starlette/httpx弃用警告，无跳过。
- 测试集群仅监听Unix socket，位于`/private/tmp`；测试后已停止并删除。此合成schema验证不能代替NAS实际V0.1备份升级，P0-01仍blocked。

## 2026-11-10 P0-02样本清单校验器
- `tests/test_sample_set.py`有3项临时虚构HTML校验用例及1项CLI启动用例，覆盖来源场景、哈希/URL拒绝、非有限与越界数值、非整数室数和重复冲突报价；不计入真实页面样本。
- 本机全量`pytest -q -rs`：65 passed、8 skipped（需`TEST_DATABASE_URL`）；`compileall -q app scripts tests`、占位变量`docker compose config -q`及目标状态JSON解析通过。
- NAS `nas-lan` SSH连接超时，Tailscale本机状态不可读取；未同步/部署，未访问网站。

## 2026-11-10 P2-01 价格机会降幅与证据字段
- `/private/tmp/ningbo-re-ai-venv312/bin/python -m pytest -q -rs`：61 passed、8 skipped；跳过项均需`TEST_DATABASE_URL`。
- `compileall -q app scripts tests`与占位变量下`docker compose config -q`通过；OpenAPI中`days`枚举为7/30/90。
- 测试覆盖同挂牌平台历史金额/幅度、前后观察时间和末次证据链接，隔离agent_claim、未来/窗口外报价、价格回升以及API SQL过滤。
- NAS LAN SSH连续超时；本次代码仍为本机验证，尚未同步或部署。生产数据库未连接、未写入。

## 2026-11-10 P1-08 条件单匹配 API NAS 验收
- 本机全量：`/private/tmp/ningbo-re-ai-venv312/bin/python -m pytest -q -rs`：54 passed、8 skipped；8项为需`TEST_DATABASE_URL`的数据库集成用例。`compileall`及占位环境变量下Compose配置解析通过。
- NAS `nas-lan`隔离PostgreSQL 17，使用已部署API镜像和当前工作区源码，在`bridge`网络、512MiB/1CPU临时运行器中执行`tests/test_db_integration.py`：**9 passed**。新匹配用例核实硬条件排除、偏好小区优先/布尔标记、`total`在limit截断时保持完整、未知条件单返回404。
- 数据库测试容器仅使用tmpfs（无持久卷），运行器只读挂载源码、未使用生产环境变量；测试后容器、源码临时目录和归档定向删除。生产数据库未连接。
- 生产部署前database/raw-pages备份为`backups/ningbo-re-ai-20261109T232953Z-1351503`，SHA256与归档检查通过；旧API源码/Compose快照SHA-256 `74ee4dce82a31460e53b7a0761c53ba9ca24accee0dc63279b03bf31745d99ac`。
- NAS只重建API镜像`sha256:b2e24f878bbd24b0b62130c4bc02e29fed8ac9336e30f8b22afba9ef19f9a794`。`/healthz`=200，OpenAPI含GET匹配路由，未认证调用401；容器源码哈希匹配工作区。DB healthy，来源OFF，生产条件单/挂牌均0行，未写入合成数据。

## 2026-11-10 P1-07生产部署验收
- 生产备份SHA256通过，执行005后4列与约束存在，saved_searches仍0行。
- API/Worker容器源码哈希与工作区一致；认证GET `/api/saved-searches`返回200/0条，DB healthy，`/healthz`=200；来源OFF、目标0。
- 未向生产插入测试条件单；写入与提醒偏好由此前NAS隔离PostgreSQL集成测试8项覆盖。

## 2026-11-10 HTTP 200验证码/反爬挑战阻断
- `tests/test_collection_http.py`新增58 antibot标记及中文滑动验证码页面回归；确认HTTP 200挑战返回`blocked_upstream`，不重试且不回传响应正文。
- 全量pytest：54 passed、7 skipped（需`TEST_DATABASE_URL`）；保留1条Starlette/httpx弃用警告。
- NAS Worker-only部署后容器内源码SHA-256匹配，挑战检测函数运行通过；API/DB健康、`/healthz`=200，来源OFF、启用目标0。

## 2026-11-10 Dockerfile命名数据卷权限修复
- `Dockerfile` 现在在降权到UID 10001前创建`/data`，设置owner为10001、权限700；Docker创建全新命名卷时可继承可写目录，避免API首次写raw-pages时报PermissionError。
- 本机pytest **43 passed, 6 skipped**；compileall与Compose配置解析通过。NAS隔离测试以现有API镜像派生临时镜像，仅叠加相同目录权限层；全新`/data`命名卷显示`10001:0 700`，人工样本POST返回200，候选pending=1、原始gzip文件1份、线上OFF。
- 完整工作区Dockerfile离线构建因已有`pip install`层在禁网状态退出，故不声称完整镜像已构建；仅镜像权限层通过NAS实测。隔离容器、卷、网络和临时镜像已清理；生产镜像、服务和数据卷未改。

## 2026-11-10 本机全量回归验证
- `/private/tmp/ningbo-re-ai-venv312/bin/python -m pytest -q -rs`：43 passed、6 skipped。6项均因未设置`TEST_DATABASE_URL`而跳过；NAS隔离PostgreSQL 17集成文件另有7 passed验证记录。
- `python -m compileall -q app scripts tests`通过；占位值执行`docker compose config -q`通过。
- 测试输出1条Starlette/httpx弃用警告；本轮没有应用代码或依赖变更。

# V0.2 实际执行测试记录

## 2026-11-10 P0-08挂牌观察时间触发器配对基准
- NAS隔离PostgreSQL 17，101,000条合成挂牌，限1核/512MiB；对1,000条挂牌逐行推进`last_observed_at`。旧触发器开启13,035.919ms，关闭触发器基线61.923ms；执行计划显示旧逻辑每次重扫挂牌表求最大时间，单次约16.273ms。
- 004改为常见时间前进直接维护汇总最大值，并保持来源不变时挂牌计数不变；时间回退/来源迁移仍重新计算。相同负载下，优化后触发器开启146.421ms，对照基线80.371ms；约1.82倍，汇总最大时间与原表相同。
- NAS PostgreSQL 17完整`tests/test_db_integration.py`：7 passed，覆盖最大时间前进、回退、来源迁移与删除重算。该基准是有界合成负载，不代表生产长期吞吐。

## 2026-11-10 P0-08迁移004并发写锁演练
- NAS隔离PostgreSQL 17已有250k run、250k candidate、10k listing；一个合成写事务插入run后持有3秒，迁移约0.4秒后启动。`LOCK TABLE`等待2.608秒后取得锁；回填0.597秒，按psql逐语句耗时累加，BEGIN至COMMIT约3.239秒。
- 迁移后250,001条run（含该并发事务提交行）；对计数、最新状态/原因和所有时间戳逐字段重算，汇总差异0。仅直接观察了旧事务延迟迁移拿锁；未单独计时新写事务在锁已持有时的端到端等待。临时数据库/网络/SQL已清理，生产库未执行迁移。

## 2026-11-10 P0-08迁移004已有数据回填演练
- NAS `nas-lan` 临时 PostgreSQL 17 internal 网络，1核CPU/512MiB；以001–003初始化后，载入250k run、250k candidate、10k listing合成行，再执行004迁移及重复执行。
- 首次迁移0.739秒墙钟（INSERT回填0.550秒，LOCK TABLE语句约1.036毫秒），重复执行0.737秒（回填0.589秒，LOCK约0.695毫秒）。将汇总表的来源计数、最新运行状态/原因和所有时间戳与三个原表聚合逐字段比较，0差异，重复执行未重复计数。
- 该演练没有并发写事务，因此不度量生产锁等待时长。临时容器、网络已删除；没有使用生产数据/卷或执行生产迁移。

## 2026-11-10 P0-08汇总触发器与批量写入NAS验证
- 新增`sql/004_collection_health_metrics.sql`：在迁移事务内锁定来源、运行、候选和挂牌表，回填按来源的健康汇总，然后创建触发器；后续插入、状态更新和删除在原事务中同步汇总。新库Compose初始化加入004，NAS升级指南增加手动迁移步骤。
- `GET /api/collection/health`从小型汇总表读取，响应结构和字段保持不变。NAS隔离PostgreSQL 17集成文件**7 passed**，验证004重复运行/回填、重复候选写入、审核状态变更、运行状态变更/删除、挂牌增删及原有候选审批事务/价格/通知行为。
- 同规模复测使用250,000条run及250,000条candidate合成记录（`.invalid` URL），API/DB各1核CPU、512MiB、内部隔离网络、在线OFF；60秒并发8共**2,702次、0错误、计数全匹配**，平均177.80ms、P50 187.65ms、P95 264.76ms、最大501.49ms（约45次/秒）。相较优化前同规格149次、P95 5,303.34ms，吞吐约18.1倍、P95约降低95%。
- 每2秒采样约22组：DB峰值96.36% CPU/226.4MiB，API峰值104.96% CPU/74.69MiB。限制容器下API成为瓶颈；结果不外推为生产容量。
- 隔离数据库批量写入验证：插入10,000条run耗时1.97秒，插入10,000条candidate耗时3.07秒，5,000条candidate状态转换耗时4.76秒，分别删除1,000条run/candidate耗时2.37/1.76秒。汇总核对合计0.22秒，各阶段与原表聚合计数和时间戳均一致；1核/512MiB下采样峰值约102.75% CPU/53.89MiB。总写入阶段耗时13.93秒。
- 新增挂牌触发器边界断言：`last_observed_at`从较新值回退后重新计算来源最大值；来源由beike转到anjuke再转回时两边listing_count和last_observed_at均正确；删除最后一条挂牌后时间为空。NAS PostgreSQL 17隔离库完整`tests/test_db_integration.py`：**7 passed**。
- 隔离测试容器、网络、数据库卷、API/测试镜像、目录和临时凭据已定向清理。生产API/Worker仍运行、DB healthy，`/healthz` 200/schema=v0.2，生产API镜像ID未变；没有对生产库执行004迁移。
- 本机全量测试43 passed、6 skipped；`compileall -q app scripts tests`和临时占位变量下`docker compose config -q`通过。
- 未验证：更长期/持续负载下的触发器成本、生产库执行004及实际平台数据质量。生产迁移不在本轮范围内。

## 2026-11-10 P0-08 25万行/表隔离NAS容量测试
- 使用当前工作区的Dockerfile、应用代码及001/002/003 SQL，在NAS构建独立 API 镜像并启动隔离 PostgreSQL 17；API/DB各限制1核CPU、512MiB内存，网络为`internal`，不发布宿主机端口，`ENABLE_ONLINE_COLLECTION=false`。
- 每表写入250,000条合成运行/候选记录，来源平均分配；URL均在`.invalid`域名。导入后核对两表行数各250,000、来源在线开关为0，并执行`ANALYZE`。
- 对真实`GET /api/collection/health`持续60秒、并发8：149次、成功149、错误0、所有响应计数正确；平均3,309.82ms、P50 2,999.29ms、P95 5,303.34ms、最大6,789.72ms，约2.40次/秒。
- 每2秒采样约22组：API峰值86.52% CPU/74.25MiB；PostgreSQL峰值110.54% CPU/216.6MiB。数据库CPU约达单核限制，读延迟随表规模增加。本结果是合成数据下的健康聚合查询，不是生产容量或真实房源数据质量验收。
- 测试后Compose定向删除测试容器、内部网络、隔离数据库卷和本轮构建镜像，并删除测试目录/随机凭据；无匹配测试容器、卷、镜像或路径残留。NAS生产API/Worker仍运行、DB healthy，`/healthz`返回200/schema=v0.2，生产API镜像ID保持不变。

## 2026-11-10 P0-05 NAS隔离PostgreSQL集成测试
- 通过 `nas-lan` SSH直连，在NAS独立PostgreSQL 17 Compose数据库运行当前 `tests/test_db_integration.py`：**5 passed**。四个数据库集成用例全部通过，覆盖索引迁移创建/幂等、重复提交和审批幂等、审批失败事务回滚、历史价格保护及通知去重；另含连接错误脱敏检查。
- 测试每条用例在随机schema中运行，结束后清理隔离Compose容器/网络/数据库卷、运行器镜像、临时项目目录及本机临时凭据。15555/15556无监听进程。
- 复核NAS生产API/Worker仍运行、生产DB healthy；从API容器实际访问`127.0.0.1:8000/healthz`返回200、schema=v0.2，生产API镜像ID保持`sha256:165a79ee88fc2d590bbef7ae86f9612807865f10c56b9cbdbad4f2366e287d70`。未执行生产迁移或业务写入。该结果是隔离NAS PostgreSQL 17测试，不等于生产库迁移验收。
- 本机全量 `/private/tmp/ningbo-re-ai-venv312/bin/python -m pytest -q`：**43 passed, 4 skipped**；`compileall -q app scripts tests`与使用一次性占位值的`docker compose config -q`通过。清单校验与新开发包内75个文件的SHA-256校验通过。

## 2026-11-10 P0-08 空库Compose自动初始化
- NAS隔离 PostgreSQL 17 栈仅挂载当前001/002/003 SQL，空volume启动后数据库healthy；`source_registry=2`且所有来源在线关闭，run/candidate表均为0，新索引两项存在。
- 测试栈只有DB服务，随后已移除容器、卷和目录；生产API/DB/Worker运行且API镜像ID不变。

## 2026-11-10 P0-08 10万行规模与索引迁移验证
- 隔离NAS栈每表100,000条合成记录，API/DB各1核、512MiB，30秒并发8：无索引86次/0错误/2.77次每秒/P95 3,697.44ms；覆盖索引后152次/0错误/4.88次每秒/P95 2,099.43ms。输出计数一致。
- 临时索引占约9.1MiB；后续按同定义新增 `sql/003_collection_health_indexes.sql`，在隔离库实跑两次，第一次成功创建、第二次IF NOT EXISTS跳过；API汇总仍通过。没有对生产库执行迁移。
- `docker-compose.yml` 新库初始化挂载003；`docs/NAS_DEPLOYMENT.md` 增加既有数据库的手动迁移命令；数据库集成fixture增加迁移重复执行及索引存在断言。
- 本机 `pytest -q`：43 passed、4 skipped；`compileall`和`docker compose config -q`通过。测试卷、凭据、镜像、文件清理完成，生产服务及API镜像未变。

## 2026-11-10 P0-08 60秒受限资源持续压测
- 隔离API与PostgreSQL容器均设1核CPU、512MiB内存上限；50,000条run+50,000条candidate合成数据；真实`GET /api/collection/health`运行60秒、并发8，357次、0错误、5.86次/秒，平均1,360.64ms/P50 1,304.37ms/P95 1,900.81ms/最大2,392.88ms。每个响应计数均正确。
- 每2秒采样30次：API峰值17.46% CPU/71.37MiB，DB峰值108.36% CPU/87.92MiB；NAS可用内存事后约8.0GiB、PostgreSQL活动/总会话1/1。数据库CPU接近1核限制，说明受限容器是当前瓶颈；该结果不代表生产容器容量。
- 临时项目、卷、密钥、日志、镜像及目录全部清除；生产API、DB、Worker仍运行且API镜像ID不变。

## 2026-11-10 P0-08人工样本写入闭环
- NAS `nas-lan` 隔离Compose项目，独立PostgreSQL、回环8799、随机临时凭据、在线采集OFF；用虚构HTML样本，无外站访问。
- `POST /api/collection/pages` 两次同内容提交均HTTP 200且返回同一候选ID；候选列表GET为1条、状态pending。gzip证据解压后与输入完全一致，SHA256与数据库字段相同。
- 调用审核批准API两次均HTTP 200，第二次幂等；正式挂牌GET与价格历史GET读回成功。隔离DB计数candidate=1/approved=1/listing=1/price_history=1，导入后、批准前listing及price_history均为0。
- 所有在线来源仍关闭。临时栈、数据库卷、凭据、证据文件、测试镜像和目录已删除；端口8799关闭。生产API/DB/Worker运行，生产API镜像ID未变。
- 该项只证明合成HTML的端到端写入/审核/读取，不是实际房源数据或高并发写入验收。

## 2026-11-10 P0-08业务聚合端点NAS负载复测
- NAS `DXP4800` 经 `nas-lan` SSH直连；独立测试 Compose 项目仅含 API、PostgreSQL，固定回环端口8799、随机临时密钥、独立卷；未使用生产库/卷。
- 在独立PostgreSQL中写入50,000条运行和50,000条候选合成数据；访问 `GET /api/collection/health` 20秒、并发8，逐请求校验两来源的run/candidate计数。
- 原查询：90次、0错误，平均1,849.99ms、P50 1,793.99ms、P95 2,460.60ms、最大2,774.18ms（4.50次/秒）。
- 新查询按来源聚合，并仅在当前事务内禁用JIT：596次、0错误，平均270.41ms、P50 257.52ms、P95 411.90ms、最大650.18ms（29.80次/秒）。计数全程一致；观察吞吐约提升6.6倍。
- PostgreSQL执行计划显示旧/新查询估算成本触发JIT；关闭JIT的只读计划耗时56.09ms。该执行计划耗时与API并发压测口径不同，不混作端到端延迟。
- 负载后容器内存API 47.61MiB、DB 142.6MiB，NAS可用内存约7.8GiB；均为事后采样，不代表峰值。测试未覆盖真实房源数据、业务写接口、长时间压力或主机饱和。
- 隔离容器、网络、数据卷、临时密钥、测试镜像与目录均已删除；8799已关闭。生产项目API/DB/Worker仍运行，生产API镜像ID保持 `sha256:165a79ee88fc2d590bbef7ae86f9612807865f10c56b9cbdbad4f2366e287d70`。
- 本机全量测试43 passed、3 skipped；`compileall -q app scripts tests`通过。

## 2026-11-10 P0-08容量盘点工具
- 新增 `tests/test_storage_report.py`，覆盖嵌套文件计数/大小、目录缺失和UTC时间格式。
- `/private/tmp/ningbo-re-ai-venv312/bin/python -m pytest -q`：**43 passed, 3 skipped**。跳过项是需要独立PostgreSQL环境的集成测试。
- `/private/tmp/ningbo-re-ai-venv312/bin/python -m compileall -q app scripts tests`：通过。
- NAS使用 `nas-lan` 直连经标准输入实跑盘点脚本：容器内`/data/raw-pages`为2个文件/249字节，无HTML归档；NAS主机`backups/`为3个文件/50,301字节，`/volume3`可用约437GB。由于访问权限不同，证据与备份分别在容器/主机上下文盘点。
- NAS轻量健康探针：API容器内20次`/healthz`请求、并发4，全部200且schema=v0.2；平均34.77ms、最大67.35ms、总耗时0.193秒。采样前后API/DB/Worker内存分别为47.57/38.22/39.63MiB与48.36/38.47/39.63MiB。该结果不代表资源压力验收。
- NAS有界持续检查：20秒、并发8访问只读`/healthz`，2,801次请求全部成功，平均57.16ms、P95 79.39ms、最大113.89ms；API/DB/Worker内存前后为47.80/38.72/39.63MiB与48.35/38.77/39.63MiB；检查后PostgreSQL活动会话6、NAS可用内存约8.2GiB。只覆盖健康探针，不代表真实业务端点、长时间运行或资源饱和。
- 未读取页面内容、未同步或部署新文件。

日期：2026-11-09，环境：Python 3.12 临时虚拟环境；另在UGREEN DXP4800完成空库新装集成验收。没有V0.1旧项目/数据库可做升级。

已执行：

```bash
/private/tmp/ningbo-re-ai-venv312/bin/python -m compileall -q app scripts
/private/tmp/ningbo-re-ai-venv312/bin/python -m pytest -q
```

结果：38 tests passed（此前37项 + `tests/test_collection_health.py` 新增1项）。

测试覆盖：账号入参、DTK响应解析、视频文字提取、视频号导入字段、HTML样本解析、无效网址、冲突价格、内容缺失、网站robots阻断、403拒绝、HTML内容类型、来源政策字段校验，以及按来源健康汇总结果的单元逻辑。

已执行：以仅用于配置校验的临时值运行 `docker compose config -q`，通过；`sha256sum -c MANIFEST.sha256`通过。

NAS空库新装实测：在 `/volume3/docker/ningbo-re-ai` 执行Compose构建和启动，PostgreSQL healthy、API和Worker运行；`/healthz`返回`schema=v0.2`。真实API `GET /api/collection/health`在空库返回贝壳/安居客两来源且所有线上开关为false。插入临时合成的3条run和3条candidate后，接口准确返回成功/失败/阻断、三类审核计数和最新阻断状态；随后清理全部临时记录并确认候选、运行、挂牌表计数为0。仅重启该项目的PostgreSQL容器后，schema及默认来源策略仍存在。UGREEN登记记录已写入且登记库修改前备份的完整性检查通过；Mac锁定，项目页3/3视觉复核未做。

未执行/未声称：旧V0.1数据库迁移和旧数据持久化 / UGREEN项目页视觉3/3检查 / 备份恢复演练 / 上游抖音接口真实访问 / 贝壳和安居客在线采集 / 视频号连续采集 / 真正房源数据质量回归。NAS本次新装容器运行和新卷重启持久化已验证，但不能替代旧库升级验收。

NAS验收命令见 `docs/NAS_DEPLOYMENT.md`。集成验收用例见 `docs/ACCEPTANCE.md`。

## 2026-11-09 P0-05 数据库API集成用例
- 新增 `tests/test_db_integration.py`，严格要求 `TEST_DATABASE_URL` 指向 `rehouse_test`；每条用例仅在随机 schema 中建表并清理。
- 覆盖：未审核候选列表隔离、相同HTML候选去重、重复审批幂等、审批事务异常回滚、历史回填不覆盖最新价、降价通知唯一键去重。
- 本机一次性 PostgreSQL 16 隔离集群：`TEST_DATABASE_URL=... /private/tmp/ningbo-re-ai-venv312/bin/python -m pytest -q`，完整套件42 passed。集群仅监听Unix socket，完成后停止并删除；`compileall -q app scripts tests` 通过。
- NAS额外复测：临时 `rehouse_test` 创建成功，但SSH隧道测试连接返回数据库角色不存在，发生于 schema 初始化之前；临时库已删除，业务库没有被测试写入。该结果不是NAS端数据库API验收证据。
- 连接错误的详细诊断意外包含数据库凭据，按暴露处理；后续测试停止使用该凭据，并需先完成凭据轮换及API/Worker连接重配。

## 2026-11-09 P0-08异常日志脱敏
- `worker`账号同步、主循环及网页采集失败的日志/状态文本改为安全摘要，不写入异常原文；策略阻断分类与固定原因保留。
- `tests/test_log_safety.py` 验证合成令牌/手机号标记不会进入错误摘要。
- 一次性本机PostgreSQL 16完整测试：43 passed；临时集群仅监听Unix socket，结束后停止并删除。静态编译通过。
- `scripts/backup.sh` 在本机一次性PostgreSQL 16集群中完成验证：生成custom dump和raw-pages archive，SHA256通过，恢复到隔离数据库后合成标记一致；临时集群、备份和原始文件均已清理。
- 未完成：NAS备份恢复、原始页面容量/保留策略及资源验收；新日志处理和备份脚本尚未在NAS运行环境验收。
- 2026-11-09续接：复用Netcatty局域网会话确认UGREEN项目页显示 `ningbo-re-ai` 3/3运行，详情列出API、PostgreSQL 17、Worker，配置路径为 `共享文件夹/docker/ningbo-re-ai/docker-compose.yml`。首轮备份因脚本误将主机侧受限 `data/raw-pages` 当作必需目录而中止；移除该检查后同步修正版，远端SHA256与本机一致。
- NAS备份目录 `backups/ningbo-re-ai-20261109T133821Z-273669`：`database.dump`与`raw-pages.tar.gz`的SHA256均通过，custom dump目录列表检查通过；备份目录权限700，文件权限600。恢复至临时隔离库后，`source_registry`包含beike/anjuke且两者 `online_enabled=false`，`source_listings`、`collection_candidates`、`collection_runs`均为0；临时库已删除。原始证据归档结构校验通过，仅包含占位文件。没有重启容器、Docker服务或改动数据卷。

# 本轮追加验收（2026-11-10）
- 本机：`pytest -q -rs` 为 **47 passed, 7 skipped**；跳过项均需`TEST_DATABASE_URL`。`PYTHONPYCACHEPREFIX=/private/tmp/ningbo-re-ai-pycache python -m compileall -q app scripts tests`通过；`POSTGRES_PASSWORD=local-check-only APP_API_KEY=local-check-only docker compose config -q`通过。
- NAS隔离PostgreSQL 17：通过`nas-lan`将不含`.env`/数据的测试源码临时传至`/tmp`，使用现有API运行镜像作为一次性测试运行器，执行`tests/test_db_integration.py`：**8 passed**。覆盖005重复迁移、条件单API字段落库及偏好小区提醒标记。临时容器、网络、源码目录和测试归档已删除。
- 生产数据库、API/Worker镜像与服务未变。第一次本机SSH数据库隧道受本地沙箱网络限制，之后改在NAS隔离网络内运行测试；不把该限制记为代码失败。
# 2026-11-10 P0-08 NAS隔离业务负载30分钟
- `docs/LOAD_TEST_2026-11-10.md`记录完整方法与限制；NAS隔离PostgreSQL 17、API/DB各1核/512MiB、internal网络无宿主端口，使用当前工作区`app/`只读挂载运行。
- 1,800.61秒/4并发：10,199完整工作流、61,194请求、0错误；候选approved=挂牌=价格历史=10,199，pending=0，健康指标逐来源一致且在线关闭。
- 端点P95：导入186.54ms、待审列表165.52ms、审批272.59ms、挂牌222.71ms、价格历史165.83ms、健康指标123.76ms。资源284组采样，API/DB峰值CPU 106.37%/108.60%，内存65.69/65.15MiB。
- 原始报告与资源文件复制至工作区后SHA-256核对相同；临时Compose、网络、卷、源码和密钥已定向清理。生产服务保持运行、DB healthy。
- 本机全量回归：51 passed、7 skipped（均需`TEST_DATABASE_URL`）；编译及Compose配置解析通过。



## 2026-11-10 P0-08生产日志只读抽查
- `nas-lan`确认DXP4800生产API/DB/Worker运行、DB healthy；只读获取API和Worker日志尾部，实际13行。
- 本机内存扫描手机号、邮箱、Bearer凭据、URL用户信息、凭据赋值、JWT六类模式均0命中；原始日志正文未输出/落盘。
- 范围限制：仅代表本次尾部样本及上述规则；未覆盖其他敏感字段、已轮转日志或未来事件。未改NAS配置、容器、数据库或文件。


## 2026-11-10 外部字段名日志脱敏回归
- `store_page`遇到缺少稳定ID的DTK条目时，原日志输出完整上游字段名列表；改为固定对象类型和字段数量。
- 新用例以异常字段名注入API key/手机号样式标记，验证标记不进入日志。
- 本机全量：`/private/tmp/ningbo-re-ai-venv312/bin/python -m pytest -q -rs`：**52 passed, 7 skipped**（需`TEST_DATABASE_URL`）；`compileall -q app scripts tests`通过。
- 当时只改工作区代码；随后已按Worker-only方式部署，记录见同文件后续条目。已知弃用警告仍为1条。


## 2026-11-10 Worker-only NAS部署验证
- 活动账号和目标为0后，先备份原NAS源码`backups/source-snapshots/worker.py.pre-log-fields-20261110`（SHA-256 `f227bd4411196ddfa3d90c2f9147690a937dd4327cba2ee7945a6795d534d907`）。
- 经`nas-lan`上传并核对修复版`app/worker.py` SHA-256 `150a09bae9a74a82489761dd86107189d0902f2c5a138afeb71de33b8f9a040d`；Compose配置通过，只构建`worker`，镜像ID `sha256:e89b2d440d989969c722a84673b804499b05d6437fd309b2e968da4da581073a`。
- `docker compose up -d --no-deps worker`仅替换Worker容器；API/DB容器与卷未重启/修改。部署后Worker running，容器内源码哈希匹配，启动标记存在；日志尾部1行、六类敏感模式均0命中，原文未输出。API `/healthz`=200、schema=v0.2，DB healthy。


## 2026-11-10 P0-04实际源主机robots只读核验
- NAS `nas-lan` 访问项目代码对应的两个robots origin：`nb.ke.com`与`ningbo.anjuke.com`，均HTTP 200；请求后计算SHA-256，并用项目实际UA及标准`RobotFileParser`判定示例详情URL。
- Beike：6,676字节，哈希`9827f8cc…cb9d2db9`，通配组`Disallow: /`，项目UA不可抓取。Anjuke：372字节，哈希`6815680c…bac9cde`，通配组`Allow: /`，项目UA不匹配特定禁用组，可抓取。
- 仅请求robots文件，未请求详情页；robots结果不表示平台授予数据使用权。贝壳书面许可缺失；安居客协议当前版本/范围及许可未确认；在线开关保持关闭。


## 2026-11-10 NAS项目权限审计与收紧
- `getfacl`确认NAS项目`app/`、源码/迁移/脚本/测试/文档及Compose/Dockerfile等存在真实`other::rwx`；`.env`为600，`data/`和`backups/`为700。修改前96条目标路径的模式/属主清单保存在`backups/source-snapshots/permissions-before-20261110.txt`，SHA-256 `c24a855275c2ffcdafa26b1ca7ce0c7650e02a9b9e0b00bf88f1837872e9b8a9`，文件权限600。
- 源码/配置目录改为755、普通文件644，所有属主不变；`.env`、数据卷、备份和Compose登记未动。复查项目保护区外0条world-writable文件/目录。
- NAS `docker compose config -q`通过，API/Worker running、DB healthy，`/healthz`=200。只改权限元数据，未重启容器；未重跑pytest。


## 2026-11-10 NAS隔离PostgreSQL 17完整回归与API生产冒烟
- `pytest`完整套件在NAS隔离PostgreSQL 17：**144 passed、0 skipped**。测试运行器自动移除；隔离数据库容器在生产部署前由本轮定向清理。
- API-only部署后冒烟：`GET /healthz` 200；无API Key的业务请求401；`POST /api/collection/pages`上传6,100,001字节返回413。API镜像内`app/*.py`源码树SHA-256与NAS源码树一致。
- 只读核对：全局采集false、Beike/Anjuke均`online_enabled=false`；12张账号/视频/房产/采集业务表均为0行。Worker和PostgreSQL容器ID、数据库卷、UGREEN Compose登记路径均未改变。
- 部署不含数据库迁移或生产测试写入；不代表真实站点样本、权限或解析准确率验收。

- 生产PG17备份`database.dump`与raw-pages归档SHA-256均通过；`pg_restore --list`使用`postgres:17-alpine`临时只读容器通过。NAS主机旧版pg_restore不支持PG17格式，此工具版本差异不影响备份校验。


## 2026-11-10 P0-08留存报告权限错误防护
- NAS首次以权限不足的容器身份运行报告时输出0文件；确认是目录不可读造成的错误空结果，并用目录属主分别只读运行取得真实盘点。
- `scripts/storage_report.py`递归扫描改用`os.scandir`并传播权限错误；新增权限错误回归，修复前失败、修复后通过。`tests/test_storage_report.py` **8 passed**。
- NAS只读实数：raw-pages 2文件/249字节；backups 34文件/1,056,619字节；备份早于90天的人工复核候选0文件/0字节；`/volume3`可用436,787,408,896字节。未删除或修改任何NAS文件。


## 2026-11-10 P0-02样本清单CSV结构防错
- 新增重复表头、额外列和缺少字段的行回归；三项先在旧实现失败。
- `validate_sample_set.py`拒绝重复/空表头，并报告字段数量不匹配，畸形行不计入样本数量。`tests/test_sample_set.py tests/test_parser_evaluation.py`：**19 passed**；`compileall -q app scripts tests`与GOAL_STATE JSON解析通过。
- 仅验证离线清单结构，不证明许可效力或真实页面标签。工作区无获准真实样本；未访问网站/NAS/生产数据库。


## 2026-11-10 P0-03 可选字段冲突告警
- 新增户型/区域/楼层/装修多值冲突用例；旧实现已留空相关字段，但不向审核者报告冲突，回归先失败。现输出稳定告警且不选择任何值，解析器版本`generic-labelled-v0.2.6`。
- `tests/test_collection_parser.py tests/test_parser_evaluation.py tests/test_sample_set.py`：**44 passed**；compileall与GOAL_STATE JSON解析通过。虚构HTML仅验证逻辑，不代表真实样本准确率。


## 2026-11-10 P0-02/P0-03人工标签完整分母与歧义场景
- 新增回归发现未标记空人工字段会从报告分母中消失；模板也未包含解析器已有的楼层/装修输出，歧义警告没有场景评分。
- 清单加入floor_text/decoration并拒绝未标记空值；支持字段专属多值场景标签。评估器纳入楼层/装修准确率/覆盖率，并对每类可选字段冲突检查“解析为空+警告存在”。
- `tests/test_sample_set.py tests/test_collection_parser.py tests/test_parser_evaluation.py`：**49 passed**；`compileall -q app scripts tests`和GOAL_STATE JSON解析通过。全为本地虚构HTML逻辑测试，不等同真实站点指标。
## 2026-11-10 P0-03 UTF-8 BOM解析回归
- `tests/test_collection_parser.py -k utf8_bom`：**1 passed**；UTF-8 BOM页面的小区首字段、面积与挂牌价均解析成功。
- 全量本机离线`pytest -q -rs`：**172 passed、11 skipped**；11项PostgreSQL集成用例因未设置`TEST_DATABASE_URL`跳过，另有1条Starlette/httpx弃用警告。
- 本次没有修改解析规则或数据库；解析器版本仍为`generic-labelled-v0.2.9`。没有获准真实页面，因此不产生站点准确率结论。

## 2026-11-10 P0-03户型字段范围保护
- 新增`21室`超范围回归，旧解析器失败并返回21。现留空该值、添加`invalid_bedrooms_mentions`告警，解析器版本为`generic-labelled-v0.2.10`。
- `tests/test_collection_parser.py tests/test_parser_evaluation.py tests/test_sample_set.py`：**60 passed**；全量`pytest -q -rs`：**173 passed、11 skipped**，跳过项需`TEST_DATABASE_URL`，保留1条Starlette/httpx弃用警告。
- 无真实获准页面；本结果不构成站点字段准确率验收。无数据库或配置变化。

## 2026-11-10 P0-03来源ID长度边界
- 新增221位详情路径ID及人工标签回归，旧逻辑会提取/接受超出`ListingIn`的220字符上限的ID。现解析器不提取超长数字ID，清单校验拒绝超长标注。
- `tests/test_collection_parser.py tests/test_parser_evaluation.py tests/test_sample_set.py`：**62 passed**；全量`pytest -q -rs`：**175 passed、11 skipped**，保留1条Starlette/httpx弃用警告。
- 解析器版本`generic-labelled-v0.2.11`。没有真实获准样本；不构成准确率或线上验收。

## 2026-11-10 P0-02来源URL query/fragment拒绝
- 新增query中令牌样例、fragment样例及确保在线fetch在首个HTTP请求前拒绝的回归；旧逻辑曾继续发请求。
- 共享来源URL校验拒绝query/fragment；canonical链接在ID比较时去掉二者，避免隐私策略改变ID冲突检查。
- 解析器版本升至`generic-labelled-v0.2.13`。
- `tests/test_collection_parser.py tests/test_collection_http.py`：**46 passed**；全量`pytest -q -rs`：**180 passed、11 skipped**，有1条Starlette/httpx弃用警告。
- 未请求外部站点、未部署或连接NAS；真实性/授权状态不变。

## 2026-11-10 P0-02来源URL长度限制统一
- 新增离线解析器及样本清单拒绝超过API 2000字符上限的来源URL回归；旧逻辑两处均接受超长值。
- 现共享URL校验和样本清单校验均限制12–2000字符；解析器版本升至`generic-labelled-v0.2.14`。
- parser/HTTP/sample-validator/evaluator专项 **76 passed**；全量测试结果记录在本轮目标状态。

## 2026-11-10 P0-02 malformed URL异常边界
- 不完整IPv6源URL此前让`urlsplit()`原生`ValueError`逃出服务层的`CollectionError`处理；现将主URL解析错误归一化为项目输入异常。畸形canonical声明在URL组合时忽略。
- `tests/test_collection_parser.py tests/test_collection_http.py tests/test_sample_set.py tests/test_parser_evaluation.py`：**78 passed**；全量pytest **184 passed、11 skipped**，1条Starlette/httpx弃用警告。
- 解析器版本`generic-labelled-v0.2.15`；仅本地验证，未访问网站或NAS。

## 2026-11-10 P0-03数值格式等值处理
- 新增面积、价格和卧室数的等值格式重复标注回归；旧实现因字符串不相同产生冲突并清空字段。现按Decimal数值比较，仍保留不同数值的冲突检测。
- 解析器版本`generic-labelled-v0.2.16`。parser/HTTP/sample-validator/evaluator专项 **79 passed**；全量pytest **185 passed、11 skipped**，保留1条Starlette/httpx弃用警告。
- 合成HTML逻辑测试，不构成真实站点准确率验收。

## 2026-11-10 P0-03损坏数值标注容错
- 新增逗号-only数值及损坏值与有效值并存回归；旧逻辑在Decimal转换时抛出`InvalidOperation`。现无效值不会中断解析，且与有效值共存时保守报冲突。
- 解析器版本`generic-labelled-v0.2.17`；parser/HTTP/sample-validator/evaluator专项 **81 passed**；全量pytest **187 passed、11 skipped**，1条Starlette/httpx弃用警告。

## 2026-11-10 P0-03数字千分位分组
- `12,34`面积/价格标注现不会被去逗号后误读成1234；标准`1,234.5`仍正常解析。损坏值与有效值共存会触发冲突，不选其中一个。
- 解析器版本`generic-labelled-v0.2.18`；parser/HTTP/sample-validator/evaluator专项 **83 passed**；全量pytest **189 passed、11 skipped**，保留1条Starlette/httpx弃用警告。

## 2026-11-10 P0-02空userinfo URL边界
- 为空用户名/密码userinfo链接增加拒绝回归；旧共享校验将空字符串误当作“无凭据”，样本清单原本会拒绝。
- 现共享校验判断userinfo是否存在，`https://@host`与`https://:@host`均拒绝。解析器版本`generic-labelled-v0.2.19`。
- parser/HTTP/sample-validator/evaluator专项 **85 passed**；全量pytest **191 passed、11 skipped**，1条Starlette/httpx弃用警告。

## 2026-11-10 P0-02来源主机尾点处理
- 主机规范化只移除一个DNS绝对根尾点；额外尾点将导致白名单不匹配，避免宽泛`strip('.')`误放行。
- parser/HTTP/sample-validator/evaluator专项 **88 passed**；全量pytest **194 passed、11 skipped**，1条Starlette/httpx弃用警告。解析器版本`generic-labelled-v0.2.20`。


## 2026-11-10 P0-08证据引用只读审计
- `tests/test_storage_report.py`：**11 passed**，覆盖按内容寻址文件名对照数据库引用、无引用候选、记录引用但文件缺失、非证据文件名、符号链接和数据库不可用时失败。
- 全量pytest：**228 passed、13 skipped**；跳过项均需设置隔离库`TEST_DATABASE_URL`。保留1条Starlette/httpx弃用警告。
- 本机Python 3.12离线执行；`compileall`、`GOAL_STATE.json`解析及使用占位变量的`docker compose config -q`通过。未连接数据库/NAS，故未运行生产盘点。

## 2026-11-10 P0-02样本清单列边界
- `tests/test_sample_set.py -k unsupported_manifest_columns`：**1 passed**；CSV增加`contact_phone`列的回归修复前失败，现清单在读取数据行前拒绝未知列。
- `tests/test_sample_set.py tests/test_parser_evaluation.py`：**39 passed**。全量pytest：**229 passed、13 skipped**（均需隔离库`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- Python 3.12离线执行；未连接数据库/NAS、未使用真实获准页面。


## 2026-11-10 P0-02损坏CSV编码处理
- `tests/test_sample_set.py -k non_utf8_manifest`：**1 passed**；非法UTF-8清单此前在表头读取时抛出`UnicodeDecodeError`，现返回明确错误且来源计数为0。
- `tests/test_sample_set.py tests/test_parser_evaluation.py`：**40 passed**。全量pytest：**230 passed、13 skipped**（需隔离库`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 本机Python 3.12离线执行；未连接数据库/NAS或使用真实获准页面。


## 2026-11-10 P0-02严格CSV引号语法
- `tests/test_sample_set.py -k malformed_csv_quoting`：**1 passed**；引号闭合后出现额外文本此前被宽松`DictReader`接受，现严格解析并返回格式错误。
- `tests/test_sample_set.py tests/test_parser_evaluation.py`：**41 passed**。全量pytest：**231 passed、13 skipped**（需隔离库`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 本机Python 3.12离线执行；未连接数据库/NAS或使用真实获准页面。


## 2026-11-10 P0-06分享URL尾点边界
- 新增双尾点`douyin.com..`、三尾点`iesdouyin.com...`拒绝与单DNS根尾点接受回归；前两者修复前被`rstrip('.')`误接受，现回退canonical作品URL。
- `tests/test_dtk.py tests/test_worker.py`：**53 passed**。全量pytest：**234 passed、13 skipped**（需隔离库`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 本机Python 3.12离线验证；没有真实DTK/NAS/账号联调。


## 2026-11-10 P0-02 HTML路径控制字符
- `tests/test_sample_set.py -k control_characters_in_html_path`：**3 passed**。换行曾被strip后接受，NUL曾触发未处理`ValueError`；现路径字段在Path构造前拒绝C0/C1控制字符。
- `tests/test_sample_set.py tests/test_parser_evaluation.py`：**44 passed**。全量pytest：**237 passed、13 skipped**（需隔离库`TEST_DATABASE_URL`），保留1条Starlette/httpx弃用警告。
- 本机Python 3.12离线执行；未连接数据库/NAS或使用真实获准页面。


## 2026-11-10 P0-03建筑面积与套内面积区分
- 专项命令：`pytest -q tests/test_collection_parser.py tests/test_parser_evaluation.py tests/test_sample_set.py` → **121 passed**。
- 全量离线：`pytest -q -rs` → **268 passed、13 skipped**；13项需`TEST_DATABASE_URL`，另有1条Starlette/httpx弃用警告。
- 新增用例覆盖建筑面积120㎡、套内面积100㎡、使用面积95㎡共存；套内/使用值不再触发建筑面积冲突，建筑面积与原文证据保持一致。
- 不含真实页面；P0-03真实站点准确率尚未验证。


## 2026-11-10 PostgreSQL隔离测试环境启动受限
- 尝试命令：一次性PostgreSQL 16实例（Unix socket专用，数据库名`rehouse_test`）运行`pytest -q tests/test_db_integration.py`。`initdb`成功，PostgreSQL服务启动失败：System V `shmget`受sandbox共享内存限制；设置`shared_memory_type=mmap`和`dynamic_shared_memory_type=mmap`后仍失败。
- Docker daemon socket访问返回`permission denied`，未能用容器替代。清理钩子移除临时PG目录；确认测试端口无响应。
- 结果：数据库集成用例没有运行；不报告为通过。无NAS/业务数据库连接或写入。


## 2026-11-10 PG16提升权限重试结果
- 提升权限重试启动全新PG16（Unix socket only）仍在`shmget`系统调用处失败；mmap参数无效。`ipcs`未列出存量IPC对象，查询系统IPC上限被拒绝。
- 自动清理临时目录，确认55442端口无响应。数据库集成测试仍未运行；无NAS/业务数据库连接。


## 2026-11-10 P0-03挂牌语义根节点选择
- 专项`pytest -q tests/test_collection_parser.py tests/test_parser_evaluation.py tests/test_sample_set.py`：**122 passed**。
- 全量`pytest -q -rs`：**269 passed、13 skipped**；跳过均需`TEST_DATABASE_URL`，另有1条Starlette/httpx弃用警告。
- 新回归：非空加载提示`main`与带挂牌字段`article`并存时选择后者；若显式挂牌证据同分则保留原候选顺序。真实站点页面和准确率未验证。


## 2026-11-10 P0-03多报价候选集合核验
- 新增两项回归：解析报价与人工候选不一致、超过20条报价证据导致截断；两者修复前均被错误计为多报价场景通过。
- 评估器专项 **16 passed**；全量`pytest -q -rs` **271 passed、13 skipped**，13项需`TEST_DATABASE_URL`，有1条Starlette/httpx弃用警告。
- 多报价场景现核对解析证据和人工`price_candidates_wan`的Decimal集合并要求证据完整。此改进不产生真实页面准确率结论。


## 2026-11-10 P0-03歧义字段候选证据对账
- parser/evaluator/sample-validator专项：`pytest -q tests/test_parser_evaluation.py tests/test_sample_set.py` → **51 passed**。
- 全量离线：`pytest -q -rs` → **275 passed、13 skipped**；13项均需`TEST_DATABASE_URL`，有1条Starlette/httpx弃用警告。
- evaluator现对户型、区域、楼层、装修候选集合与人工标注精确对账；缺少、错误或20条证据上限截断均不会报告场景通过。没有真实页面准确率结论。


## 2026-11-10 P0-03紧凑分隔小区标签回归
- parser/sample/evaluator专项：`pytest -q tests/test_collection_parser.py tests/test_parser_evaluation.py tests/test_sample_set.py` → **129 passed**。
- 全量离线`pytest -q -rs`：**276 passed、13 skipped**（PostgreSQL集成需`TEST_DATABASE_URL`），1条Starlette/httpx弃用警告。
- `小区`标签前紧邻竖线/标点不再漏提；标签词与冒号仍是必要证据。解析器v0.2.30。无真实站点准确率结论。


## 2026-11-10 P0-03小区值紧凑分隔符终止
- parser/sample/evaluator专项：**130 passed**；全量`pytest -q -rs`：**277 passed、13 skipped**（跳过均需`TEST_DATABASE_URL`），有1条Starlette/httpx弃用警告。
- 新回归覆盖小区值后紧邻竖线/斜线；匹配值在分隔符处停止，面积和总价仍可解析。解析器v0.2.31。未使用真实页面。


## 2026-11-10 P0-03楼层装修值紧凑分隔
- parser/sample/evaluator专项：**131 passed**；全量离线：**278 passed、13 skipped**（数据库用例需`TEST_DATABASE_URL`），1条Starlette/httpx弃用警告。
- 楼层、装修现于常见紧凑标点处结束当前值；回归确认后续装修、价格字段不再并入楼层值。社区名括号保留。解析器v0.2.32。


## 2026-11-10 P0-02清单模板与validator字段同步
- 新增测试确保`docs/SAMPLE_MANIFEST_TEMPLATE.csv`无重复列且与`REQUIRED_COLUMNS`完全一致。定向：**1 passed**。
- 全量`pytest -q -rs`：**279 passed、13 skipped**；跳过项需`TEST_DATABASE_URL`，有1条Starlette/httpx弃用警告。
- 这仅防止清单schema漂移，不构成真实样本或许可验收。

## 2026-11-11 P0-03排除菜单导航内容污染挂牌字段
- 失败回归复现：`<main>`内的`<menu>`包含另一套小区/面积/总价时，解析器把不同来源的字段合并并将社区字段置空。解析前现移除`menu`子树；解析器版本升至`generic-labelled-v0.2.64`。
- 回归先失败后通过，原正文中的挂牌字段保留，菜单字段不再参与候选和冲突判断。完整离线pytest **658 passed、15 skipped、13 subtests passed**；标准库测试**37 passed**。15项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- 仅合成HTML验证，未访问网站/NAS或部署；未进行当前版本的PG16集成回归。P0-03仍依赖每站20份获准真实页面和人工标签，当前准确率未验证。
- 下一步：继续离线核对解析器的语义/可见内容边界；获准样本到位后运行评估器并报告逐来源逐字段精确率/覆盖率；NAS连接可用后复核新版本部署。

## 2026-11-11 P0-09拒绝seen-ids符号链接
- 失败回归复现：`read_seen_ids`用`Path.is_file()`检查输入时会跟随符号链接，仍读取链接目标文件。现在打开前明确拒绝符号链接；普通文件限额、UTF-8和来源ID校验保持不变。
- 新增回归先失败后通过；完整离线pytest **659 passed、15 skipped、13 subtests passed**，标准库测试**38 passed**。15项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- 仅临时文件和离线输入验证，未读取NAS/房源网站或部署。P0-09仍需来源许可、真实分页样本和自动Worker流程；P0-03真实页面准确率仍未验证。
- 下一步：继续按P0顺序推进离线分页状态/重试边界；获准页面到位后验证真实分页和解析字段，NAS可连接后复验备份恢复。

## 2026-11-11 P0-09拒绝seen-ids符号链接
- 失败回归复现：`read_seen_ids`用`Path.is_file()`检查输入时会跟随符号链接，仍读取链接目标文件。现在打开前明确拒绝符号链接；普通文件限额、UTF-8和来源ID校验保持不变。
- 新增回归先失败后通过；完整离线pytest **659 passed、15 skipped、13 subtests passed**，标准库测试**38 passed**。15项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- 仅临时文件和离线输入验证，未读取NAS/房源网站或部署。P0-09仍需来源许可、真实分页样本和自动Worker流程；P0-03真实页面准确率仍未验证。
- 下一步：继续按P0顺序推进离线分页状态/重试边界；获准页面到位后验证真实分页和解析字段，NAS可连接后复验备份恢复。

## 2026-11-11 P0-09 Worker分页发现与候选入队
- `run_collection_target`现区分详情目标与列表目标：列表目标在全局及来源许可门通过后读取已持久化游标，最多抓取5个列表页、20个详情页；只把详情页HTML送入候选解析，保存已见ID/访问页/下页URL。429/来源阻断会记录状态和安全错误类别、禁用目标以停止自动重试；详情失败时回退到失败列表页，超限则保留继续游标。直达详情目标保持原路径。
- mock服务回归覆盖两页推进、详情页入候选、20详情上限、5列表页上限、已访问页详情429重试游标回退，以及全局策略关闭时列表目标零请求。定向`tests/test_collection_service.py` **26 passed**；完整离线pytest **664 passed、16 skipped、13 subtests passed**；标准库测试**38 passed**。
- 本地Docker socket返回permission denied，没有`TEST_DATABASE_URL`；16项数据库集成跳过。mock没有访问网站、PostgreSQL或NAS，也未部署；Worker分页状态写入及迁移006仍待隔离PG验证，真实列表/详情HTML和来源许可仍缺，P0-09调整为in_progress，待隔离数据库和获准样本验收。 已新增`tests/test_db_integration.py::test_worker_paginates_list_targets_and_persists_detail_candidates`覆盖该端到端路径，但本轮因缺TEST_DATABASE_URL跳过，尚无数据库运行证据。
- 下一步：在隔离PostgreSQL `rehouse_test`运行Worker分页状态端到端用例；获准样本和许可到位后核对真实站点分页/详情链接；恢复NAS通道后再验证PG17部署和备份。


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

## 2026-11-11 P0-08当前版NAS备份及隔离PG17恢复
- 当前`scripts/backup.sh`在NAS生成`ningbo-re-ai-20261111T030737Z-3584908`；脚本SHA-256 `5353fc94ce3ae356e1f67c9aba78be46487a24f3542b826061219440a3ddcc43`。`bash -n`及脚本专项**9 passed**。
- 备份目录/文件权限700/600；database.dump SHA-256 `4555836d9f002dafb1d516f411bf9fea5ca62281dde334983ad332e9f729e46a`，raw-pages.tar.gz SHA-256 `edf08bd9e0cdce5c638164daf3e08a376d3089e3c19654c5ec116b6a09daaf8a`。SHA校验通过。
- `pg_restore`在断网、tmpfs、无宿主端口/挂载的临时PostgreSQL 17容器内完整成功；`source_registry=2`，collection_runs/candidates/source_listings/collection_targets均0，raw-pages归档成功解压。临时容器和辅助脚本已清理。
- 生产库、卷、服务和Compose登记未改，未部署或访问房源网站。P0-08验收已满足；90天超期候选盘点仍未执行，P0-01真实V0.1迁移仍blocked。

## 2026-11-11 P0-09路线图状态一致性复核
- 对照`docs/GOAL_STATE.json`、`docs/PROJECT_STATUS.md`和`tests/test_db_integration.py`已有记录，确认NAS隔离PG17用例为17 passed、0 skipped，且使用只读工作区源码、Mock HTTP、internal网络/tmpfs，无生产数据写入。
- 更正`docs/ROADMAP.md`主条目，使其不再把已通过的数据库集成写成未运行；同时保留真实许可/页面与生产部署未验收状态。本轮未重跑数据库集成；执行文档一致性断言、GOAL_STATE JSON解析及安全开发包校验。

## 2026-11-11 P0-03解析评估清单读取上限
- `evaluate_parser.py`对CSV manifest快照与评估后SHA-256复核增加2,000,000字节上限；初次读取最多取上限+1字节，后续哈希按流式读取并在越界时停止。
- `tests/test_parser_evaluation.py`新增三项回归：评估前拒绝超限文件、恰好2,000,000字节可通过哈希核验、文件在清单校验后增大时由最终哈希复核拒绝。
- 当前宿主缺pytest和应用依赖，定向pytest未运行；uv离线缓存因权限拒绝无法初始化。通过标准库隔离smoke **3 passed**及Python 3.12 `compileall`。此结果不替代pytest测试或真实页面解析准确率。


## 2026-11-11 P0-03文本比较键
- 将解析器社区与标题候选判重对齐到评估器/样本校验器共享的空白折叠+Unicode NFC比较键；字段值和证据仍保留首次页面文本。解析器版本`generic-labelled-v0.2.65`。
- 解析器候选归一辅助2 passed；样本校验63 passed；评估器清单/NFC/CLI子集10 passed；标准库39 passed。当前环境缺少BeautifulSoup/完整项目依赖，未执行HTML解析端到端或完整pytest。

- 补充：新增`tests/test_text_normalization_stdlib.py`三项标准库回归，覆盖NFC等价、Unicode空白折叠及不做NFKC兼容转换；stdlib测试总数42 passed。


## 2026-11-11 当前工作区全量离线pytest
- 临时Python 3.12环境执行`pytest -q`：**688 passed、16 skipped、13 subtests passed**；16项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 覆盖本轮评估报告解析器版本契约测试和合成HTML解析测试；不包含真实站点HTML或真实准确率校准。未访问网站、NAS或数据库，未部署。


## 2026-11-11 P0-08完整备份集留存候选
- `ningbo-re-ai-...`备份目录现按整体列报；须目录和其中全部普通文件都严格早于90天，若成员较新则不列出整套。散落文件仍逐文件列报，不执行删除。
- 混合新旧成员回归通过；留存报告专项**22 passed**，全量离线pytest **689 passed、16 skipped、13 subtests passed**。16项数据库集成因未配置`TEST_DATABASE_URL`跳过；保留1条Starlette/httpx弃用警告。
- 本机临时目录验证；未同步或运行NAS新版工具，未盘点/清理NAS备份。


## 2026-11-11 P0-03未闭合/错配HTML标签
- 三种未闭合或错配闭合标签的合成页面均可解析出标签明确的小区、面积、挂牌价和URL来源ID，并包含人工审核警告。解析器专项**200 passed**。
- 全量离线pytest **692 passed、16 skipped、13 subtests passed**；16项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。仅合成HTML验证，真实页面准确率仍未知。


## 2026-11-11 P0-03 Decimal范围检查避免float舍入误报
- 上限外超高精度数字曾先转float舍入为合法上限，回归确认面积/总价会被错误填成最大允许值。现在用Decimal精确判断范围后再转float；超界输入字段为空并阻止候选就绪，PARSER_VERSION为`generic-labelled-v0.2.66`。
- 回归修复前失败、修复后通过。解析器/评估器/样本清单专项318 passed；全量pytest693 passed、16 skipped、13 subtests passed，16项数据库集成未配置`TEST_DATABASE_URL`跳过。仅合成输入，不代表真实页面准确率。


## 2026-11-11 P0-03 Decimal范围下界舍入回归
- 新增面积略低于10与挂牌价略低于1的高精度样本，二进制float原先会舍入回下界；当前Decimal校验拒绝并置空两字段。上下界专项2 passed。
- 全量离线pytest **694 passed、16 skipped、13 subtests passed**；16项数据库集成需`TEST_DATABASE_URL`而跳过。解析器版本维持`generic-labelled-v0.2.66`。


## 2026-11-11 P0-03数值范围精确端点
- 面积10/20,000㎡、总价1/200,000万元作为包含端点均可通过解析和审核就绪检查；四项回归通过。数值上下界专项6 passed。
- 全量离线pytest **698 passed、16 skipped、13 subtests passed**；16项数据库集成因未配置`TEST_DATABASE_URL`跳过。解析器版本`generic-labelled-v0.2.66`。


## 2026-11-11 P0-09策略撤销时保存成功进度
- 列表分页一轮中有详情成功暂存后，若后续详情请求前许可撤销，现持久化已成功`seen_ids`和当前列表页重试游标，且不将策略阻断累加为失败尝试。回归修复前失败、修复后通过。
- 策略/分页相关3 passed；全量离线pytest699 passed、16 skipped、13 subtests passed。16项数据库集成需`TEST_DATABASE_URL`，本轮未运行数据库或NAS验证。


## 2026-11-11 P0-09策略恢复后的分页重试
- 两轮Mock回归确认策略撤销时保存的seen ID在下一轮从同列表页恢复后生效：已完成详情不再发请求，尚未完成详情会继续请求并暂存。collection-service专项28 passed；全量pytest699 passed、16 skipped、13 subtests passed。数据库集成未运行。


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
## 2026-11-11 P0-09跨周期挂牌观察状态（静态验证）
- 新增迁移007、观察记录读接口以及Worker对每个成功解析列表页的观测写入；解析结果区分本页可识别ID和未发现详情队列，重复卡片单页只计一次，旧seen ID仍可更新最近观察时间。
- `python3.12 -m unittest discover -s tests -p '*_stdlib.py' -v`：**42 passed**（迁移/Compose检查3 passed）；`python3.12 -m compileall -q app scripts tests`通过。
- pytest和FastAPI/psycopg/BeautifulSoup/httpx依赖当前不可用，Docker daemon权限拒绝；Homebrew PostgreSQL 16 initdb在bootstrap时因shmget共享内存限制失败，未执行SQL。定向解析/Worker/API/PG集成均未执行。没有访问网站、NAS或生产数据库，也没有部署。



## 2026-11-11 P0-07当前工作区隔离NAS PostgreSQL 17集成
- 将工作区测试源码只读挂载到NAS临时运行容器，通过internal Docker网络连接tmpfs PostgreSQL 17测试库；执行`tests/test_db_integration.py`：**22 passed**。该结果覆盖当前数据库集成快照，并与此前001–010迁移/010幂等和合成计数器烟雾结果互补。
- 数据库无宿主端口、无持久卷；集成schema残留0。清理后核实临时容器、网络、归档、解压目录均不存在。
- 未连接生产DB进行测试、未运行生产迁移或部署；生产PG17当前仍缺`collection_parse_attempts`且容器源码哈希与工作区不一致。


## 2026-11-11 P0-07逐字段完整率回归
- 补齐`source_listing_id`、`community_name`、`asking_price_wan`、`area_sqm`逐项缺失/None时必须判为不完整的回归；文本字段空白也必须判为不完整。应用逻辑未需修改。
- `tests/test_collection_health.py`：**3 passed**；全量离线pytest：**735 passed、21 skipped、17 subtests passed**，21项数据库集成因未配置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。当前数据库集成上一轮在NAS隔离PG17为22 passed。
- 本轮仅测试和文档变更；无迁移、生产数据库/NAS/Compose或来源网站变更，未部署。P0-07仍因生产未迁移/版本未同步而`in_progress`。


## 2026-11-11 P0-07隔离PG17模拟生产基线升级
- 经用户授权的`notedock-nas`在NAS内部Docker网络及tmpfs PostgreSQL 17运行纯合成演练：应用001–005，插入代表性source listing、collection target/run/candidate和saved search，再按顺序运行006–010并重复一次。
- 迁移后旧挂牌/候选/运行/条件单关键值保留，迁移默认字段正确；discovery state、sweep columns、observation/review及parse attempt均可用。解析触发器汇总为2次尝试、1次成功、1次四字段完整，重复迁移后仍为2/1/1。
- 测试容器无宿主端口、无持久卷，网络为internal；所有数据均为本轮合成数据。自动清理并复核容器、网络、归档、解压目录均不存在。未读取生产业务行、未创建备份或修改生产schema/容器/Compose/数据卷，未部署。该演练不代替V0.1真实备份或生产恢复验收。

## 2026-11-11 P2-02面积差分母确认
- 用户确认面积差公式后核对`app/services.py`确以`abs(a-b)/min(a,b)`判定，机会定向测试 **21 passed**；无需改业务逻辑。
- 用户确认面积差≤5%使用较小挂牌面积作分母，即`abs(a-b)/min(a,b)≤0.05`；现有实现与用户口径一致，无应用代码变更。

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

## 2026-11-12 候选根评分歧义回归
- 新增兄弟`main`/`article`合成用例，复现范围/冲突字段信号把噪声`main`误判为满分；修正后候选根与外层冲突定向 **5 passed**，解析器版本为`generic-labelled-v0.2.117`。
- 解析器专项 **359 passed**；全量离线pytest **876 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。PG集成、真实页面、NAS/生产版本未在本轮范围内。
- Python 3.12 compileall、`docs/GOAL_STATE.json`解析、`git diff --check`通过。安全开发包由`scripts/package_dev.py`校验ZIP和包内SHA-256 manifest；最终ZIP及哈希记录在项目状态文档。

## 2026-11-12 候选根规范化等值与延迟冲突
- 新增两个候选根回归：规范化后等值的面积/价格重复不会使完整根失分；等值重复后出现第三个不同数值仍会被识别为歧义。另锁定范围冲突/兄弟详情选择、外层语义根保护及价格证据扫描次数。
- 候选根相关定向 **8 passed**，解析器 **361 passed**，全量离线pytest **878 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成未设置`TEST_DATABASE_URL`而跳过；有1条Starlette/httpx弃用警告。解析器`generic-labelled-v0.2.118`。
- Python 3.12 compileall、GOAL_STATE JSON解析、`git diff --check`通过。未运行数据库集成、未访问真实页面/NAS/生产数据库，无迁移/部署。

## 2026-11-12 数值范围歧义样本标注与评估
- 失败回归复现范围mention无法通过现有样本候选验证/评估。现在`area_candidates_sqm`与`price_candidates_wan`可用完整范围文本表达一个证据命中，端点必须在字段范围内、格式须符合解析器；范围不按端点拆分。评估器以Decimal端点元组匹配完整证据集合；解析器与校验器共用范围分隔符集合。
- 校验器/评估器专项 **139 passed**，解析器专项 **361 passed**；全量离线pytest **885 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过，1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON解析、`git diff --check`和开发包校验通过。仅合成HTML/临时文件，无真实页面、数据库、NAS或部署验证。

## 2026-11-12 文本截断处范围首端点保护
- 失败回归证明窗口在`120㎡-`或`300万-`后截断时，单值正则会提取范围首端点。现在单值正则排除分隔符一直延伸到当前可见文本末尾的命中；10种ASCII/Unicode分隔符分别覆盖面积和挂牌价，共 **20 passed**。
- 解析器专项 **381 passed**；全量离线pytest **905 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过，1条Starlette/httpx弃用警告。解析器`generic-labelled-v0.2.119`。
- Python 3.12 compileall、GOAL_STATE JSON解析、`git diff --check`和开发包校验通过。无真实页面、NAS或生产数据库验证，无迁移/部署。

## 2026-11-12 单独范围mention评估场景
- 增加可选`area_ranges`及`price_ranges`标签并复用既有候选列；校验要求至少一个完整有效范围候选，评估对账字段留空、歧义告警及Decimal端点对。可与多值数值标签并用，不新增清单列。
- 样本校验/评估专项 **144 passed**，解析器 **381 passed**，全量离线pytest **910 passed、26 skipped、25 subtests passed**。26项PostgreSQL集成未设置`TEST_DATABASE_URL`而跳过；1条Starlette/httpx弃用警告。
- 仅临时合成样本验证，无真实页面、数据库、NAS或部署验证。

## 2026-11-12 范围场景证据截断保护
- `area_ranges`和`price_ranges`各增加超20条范围命中的回归；即使保留候选集合与人工标签相同，证据截断也使场景失败。定向 **2 passed**，校验/评估专项 **146 passed**，全量pytest **912 passed、26 skipped、25 subtests passed**。26项数据库集成未设置`TEST_DATABASE_URL`而跳过，1条Starlette/httpx弃用警告。
- 无生产代码、数据库、NAS、来源网站或部署变更。

## 2026-11-12 独立price_ranges场景端到端回归
- 单独设置`price_ranges`（不带必需`multiple_prices`标签）的合成样本通过验证，确认范围场景可独立标注与评估。该回归 **1 passed**；范围校验/评估专项 **147 passed**；全量pytest **913 passed、26 skipped、25 subtests passed**。26项数据库集成未设置`TEST_DATABASE_URL`而跳过。
- 兼容性边界：完整测试在Python 3.12.13通过；当前环境无Python 3.11解释器，且uv缓存目录不可读取，因此未执行Python 3.11验证。


## 2026-11-12 中文数字范围端点保护回归
- 先复现并修复：范围符后的中文数字端点（面积`120㎡-一百三十㎡`、价格`300万-三百二十万`）不被范围值提取器支持时，单值提取器曾采用首端点。现在按范围前缀保守拒绝，解析器版本`generic-labelled-v0.2.120`。
- 范围/截断/字段边界专项35 passed，解析器383 passed；全量离线pytest915 passed、26 skipped、25 subtests passed。26项数据库集成因未配置`TEST_DATABASE_URL`跳过。
- 仅合成HTML；真实页面样本准确率、Python 3.11及数据库集成未在本轮验证。


## 2026-11-12 中文数字范围与冒号修饰价格回归
- 范围符后为常见中文数字时不提升前一个阿拉伯数字端点；口播/成交/折后等负向价格前缀在英文/中文冒号格式下仍被排除。新增测试先复现失败再通过，解析器版本`generic-labelled-v0.2.121`。
- 价格语境专项50 passed；解析器391 passed；全量离线pytest923 passed、26 skipped、25 subtests passed。26项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- Python 3.12运行；未验证Python 3.11、真实来源页面或数据库集成。


## 2026-11-12 修饰复合价格标签后缀冲突回归
- 失败用例复现前缀被正确拦截后，正则仍退回匹配复合标签末尾`总价`；补充标签边界保护，完整`挂牌总价`/`出售总价`仍可正常提取。解析器版本`generic-labelled-v0.2.122`。
- 跨来源解析器相关回归54 passed，样本评估器相关回归1 passed，解析器397 passed；全量离线pytest930 passed、26 skipped、25 subtests passed。26项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- 仅合成HTML验证，未验证真实来源准确率或数据库集成。


## 2026-11-12 挂牌价标签正向回归
- 在两来源上锁定`总价`、`挂牌总价`、`挂牌价`、`出售总价`均保持正向解析与证据唯一；标签定向58 passed、解析器405 passed。
- 全量离线pytest938 passed、26 skipped、25 subtests passed。26项数据库集成因未配置`TEST_DATABASE_URL`跳过；仅合成HTML验证。


## 2026-11-12 价格语境组合矩阵回归
- 自动组合14种非挂牌前缀、6种分隔形式、4种挂牌价标签及两来源，共672种输入。所有组合均保留有效挂牌价且不引入修饰价格冲突。矩阵测试2 passed，解析器407 passed。
- 全量离线pytest940 passed、26 skipped、25 subtests passed；26项数据库集成未配置`TEST_DATABASE_URL`而跳过。仅合成HTML验证。


## 2026-11-12 挂牌价标签别名评估回归
- 评估器通过含人工400万标签的合成清单分别验证`挂牌总价`、`挂牌价`、`出售总价`，三个别名的字段准确率与精确率正确。新增评估器测试3项；评估器专项69 passed，解析器407 passed。
- 全量离线pytest943 passed、26 skipped、25 subtests passed。26项数据库集成因未设置`TEST_DATABASE_URL`而跳过；仅合成样本验证。


## 2026-11-12 交易总价与挂牌价隔离回归
- `交易总价`被识别为非挂牌价格语境；验证单独出现时不填挂牌价、与挂牌价并列时不触发冲突。范围扩展到720种修饰语/分隔/标签/来源组合。
- 解析器411 passed、评估器67 passed；全量离线pytest948 passed、26 skipped、25 subtests passed。26项数据库集成未配置`TEST_DATABASE_URL`而跳过。
- 仅合成HTML离线验证，无真实页面准确率或NAS部署验收。

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


## 2026-11-12 P0-03排除单位面积报价误作挂牌总价
- 失败回归复现两来源“挂牌价：2万/㎡”被抽成总价；覆盖常见面积单位、单价范围，以及同页明确总价与单位价共存。
- 当前解析器只把总挂牌价写入`asking_price_wan`，单位面积后缀的单值/范围均排除；同页明确总价不会被单位价误报为冲突。解析器版本`generic-labelled-v0.2.142`。
- 单价专项 **26 passed**；完整离线pytest **1162 passed、27 skipped、27 subtests passed**。27项为未连接PostgreSQL的集成测试。仅合成HTML验证；无网站/NAS/生产库访问，无迁移或部署。


## 2026-11-12 P0-03拒绝全角斜杠单位面积报价
- 新增贝壳/安居客回归后复现“挂牌价：2万／㎡”与“2-3万／平米”仍被误判为总价/总价冲突。扩展覆盖ASCII及全角斜杠、每平方米/每平写法和区间值。
- 单位面积后缀现同时识别ASCII与全角斜杠；解析器版本`generic-labelled-v0.2.143`。单价专项 **38 passed**，解析器专项 **567 passed**，全量离线pytest **1174 passed、27 skipped、27 subtests passed**。
- 27项PostgreSQL集成测试未连接；仅合成HTML离线验证，未访问来源网站、NAS或生产库，无迁移/部署。


## 2026-11-12 P0-03单位面积报价API端到端回归
- 增加两来源`/api/collection/pages`回归，提交全角斜杠单位价后，候选保持pending、`asking_price_wan`为空、字段证据不含伪造挂牌价命中，原始HTML gzip证据逐字节一致。
- API专项 **2 passed**；完整离线pytest **1176 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成测试未连接。
- 使用合成HTML与mock数据库；未访问来源网站、NAS或生产数据库，无迁移/部署。


## 2026-11-12 P0-03评估器覆盖单位面积报价误报
- 为两来源新增合成评估清单场景：只出现“挂牌价：2万／㎡”且挂牌总价标注为空；断言挂牌价字段精确率/准确率及`missing_fields`场景通过，保证单位价若被误抽将使字段指标失败。
- 新回归 **2 passed**；评估器专项 **118 passed**；完整离线pytest **1178 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成测试未连接。
- 无真实网页样本；仅合成评估数据，未访问网站、NAS或生产数据库，无迁移/部署。


## 2026-11-12 P0-03排除“万元/㎡”误抽及范围误报
- 失败回归复现`挂牌价：2万元/㎡`会填总价2万；`2-3万元/㎡`会引发multiple_price_mentions。扩展两来源单值/区间与单位后缀矩阵，修复后全部通过。
- 单独`挂牌价：200万元`仍能提取200万。定向 **76 passed**，解析器专项 **605 passed**，全量pytest **1216 passed、27 skipped、27 subtests passed**。
- 27项为未连接PostgreSQL的集成测试。仅合成HTML验证，未访问网站、NAS或生产数据库，无迁移/部署。


## 2026-11-12 P0-03处理括号形式单位面积报价
- 扩展两来源回归覆盖`2万（元/㎡）`、`2万（每平方米）`、`2万元（每平方米）`及范围形式；另确认没有面积单位的`挂牌价：200万元`保持可解析。
- 单位价/括号/万元边界专项 **96 passed**，解析器专项 **625 passed**，全量pytest **1236 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成测试未连接。
- 仅合成HTML离线验证；未访问网站、NAS或生产数据库，无迁移/部署。


## 2026-11-12 P0-03阻止近似/上下限挂牌价进入精确总价字段
- 复现“挂牌价：200万左右/以上/以下/起”等误填为精确挂牌价。现这些后缀追加`non_exact_asking_price`、挂牌价置空、数值证据保留；独立精确价候选根可以正常胜出。
- 两来源限定词回归、冲突与根评分均通过；解析器 **665 passed**、评估器 **120 passed**、API **12 passed**，全量pytest **1280 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成测试未连接。
- Python 3.12 compileall、GOAL_STATE JSON、diff检查通过。仅合成HTML/mock验证，未访问来源网站、NAS或生产数据库，无迁移/部署。


## 2026-11-12 P0-03户型计数边界回归
- 样本校验和API模型均允许0至20间卧室计数（0表示无独立卧室）。新增两来源对0与20边界的解析/证据回归，均保留数值且不产生`invalid_bedrooms_mentions`。
- 定向 **4 passed**；解析器专项 **669 passed**；全量pytest **1284 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成测试未连接。
- 仅合成HTML离线验证；无网站、NAS、生产数据库或迁移/部署操作。

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

## 2026-11-12 人工改价证据与价格正数边界回归
- 命令：`PYTHONPATH=. /private/tmp/ningbo-re-ai-venv312/bin/python -m pytest -q tests/test_collection_service.py::test_manual_correction_relabels_field_evidence_as_operator_review tests/test_collection_parser.py::test_parser_accepts_positive_prices_below_one_wan tests/test_collection_parser.py::test_parser_rejects_zero_area_and_price`：**9 passed**。
- 全量命令：`PYTHONPATH=. /private/tmp/ningbo-re-ai-venv312/bin/python -m pytest -q`：**1554 passed、27 skipped、27 subtests passed**，13.48秒；27项PostgreSQL集成测试未连接，保留1条既有Starlette/httpx弃用警告。
- 仅mock数据库和合成HTML回归；无真实页面准确率结论。未访问来源网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-03人工改价PATCH API证据回归
- 新增`PATCH /api/collection/candidates/{id}`回归，经真实FastAPI路由和mock数据库写入/返回验证：人工改价后的响应数值与证据一致，证据来源为`manual_review`、旧`is_non_exact`命中清空、`manually_corrected=true`；`non_exact_asking_price`仍作为解析审计警告保留。
- 定向API回归 **1 passed**；全量离线pytest **1555 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未连接，保留1条既有Starlette/httpx弃用警告。
- Python 3.12 `compileall`、目标状态JSON、文档空白检查和开发包完整性/清单校验通过。仅mock数据库与合成候选验证，无真实页面准确率结论；未访问来源网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-03人工改正非精确挂牌价后审批闭环（隔离PG17）
- 新增PostgreSQL集成回归，覆盖近似挂牌价页面提交、候选待审、PATCH人工改价、manual_review证据与解析审计警告落库、审批进入正式挂牌及价格历史。审批后正式挂牌和历史价格均为人工确认值200万元，旧非精确mention清空，`non_exact_asking_price`警告仍在候选审计记录中。 修正后重放同一HTML仍返回同一候选及manual_review数值/证据，不被解析器覆盖。
- NAS隔离PostgreSQL 17完整`tests/test_db_integration.py` **29 passed**，源码SHA-256与本机开发包一致。测试仅用internal网络、PostgreSQL 512 MiB tmpfs，无宿主端口/持久卷；源码只读挂载。临时容器、网络、测试源码/依赖及上传ZIP均已清理。 测试使用NAS现有API运行时镜像和只读源码；pytest 9.2.0纯Python模块以只读挂载提供，启动时仅将pytest内部兼容`LocalPath`映射为`py.path.local`，未改应用或测试代码。
- 本机全量pytest **1555 passed、28 skipped、27 subtests passed**；28项PostgreSQL集成未设置本机`TEST_DATABASE_URL`而跳过，隔离PG17运行覆盖完整数据库集成文件。保留1条既有Starlette/httpx弃用警告。
- Python 3.12 `compileall`、GOAL_STATE JSON、更新文档空白检查和开发包校验通过。未访问来源网站；生产API、Worker、DB容器保持运行，未修改生产数据库、Compose、卷或部署。真实准确率仍待获准页面及人工标签。
