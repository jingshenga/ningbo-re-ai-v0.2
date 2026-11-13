## 2026-11-13 Issue #4 migration preflight synchronized with main
- PR #10 synchronized with latest main `054786c`; P2 schema-signature review was resolved. After synchronization, GitHub Actions passed: quick suite 1962 passed, 0 skipped, 27 subtests; PostgreSQL 17 integration 31 passed, 0 skipped.
- Isolated synthetic rehearsal applied migrations 001–014, reran 006–014, checked selected legacy business fields and transaction rollback. Migration 012 sweep-only ID risk is tracked independently in Issue #13.
- No NAS production database, volume, Compose file, or container was modified. Real production schema and V0.1 backup remain unverified.

## 2026-11-13 P0-03/P0-06 已合并代码与下一轮目标
- PR #8：解析器v0.2.168的评估价/租金/原价排除及周期价紧贴判断通过测试并合并；真实站点校准仍待P0-02获准的20+20样本，不视为P0-03完成。
- PR #7：DTK状态与失败恢复离线契约测试合并，真实3个账号/24小时巡检及403/429专用阻断/退避仍缺；P0-06不视为实测完成。
- GitHub Actions双分支组合最终 **1963快速通过 + 31 PostgreSQL17集成通过**。Issue #1关闭，Issue #3保留，Codex下一轮Issue #4隔离迁移预演、Issue #5管理后台、Issue #9安全扫描分诊；严禁误将PR合并视为NAS已部署。

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
- 解析器文件 **777 passed**；Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`通过。129文件开发包通过包内SHA清单及ZIP完整性校验。仅合成HTML/模拟API验证；未访问来源网站、NAS或生产数据库，无迁移/部署。真实页面准确率未验证，在线采集保持关闭。

## 2026-11-12 P0-03建筑面积下限“起”留空待审
- 将“建筑面积：100㎡起”纳入非精确面积口径。两来源解析器回归先失败，修复后建筑面积字段留空、保留候选与完整证据、添加`non_exact_area_sqm`并阻止审核就绪；API暂存和评估器也覆盖该表达。
- 解析器版本升至`generic-labelled-v0.2.155`。解析器/API/样本集/评估器相关四个测试文件 **1212 passed**；全量离线pytest **1602 passed、28 skipped、27 subtests passed**。28项本机PostgreSQL集成未连接，既有Starlette/httpx弃用警告1条。
- 本轮无数据库/运行配置变化；未访问来源网站、NAS或生产数据库，无迁移或部署。全部验证使用合成页面/模拟API；真实页面准确率仍未验证，在线采集保持关闭。

## 2026-11-12 P0-03保留“平方”完整面积证据
- 两来源回归锁定`建筑面积：100平方`证据必须包含完整单位；面积范围`120平方-130平方`不得产生额外的截短单值命中。此前正则回溯到短单位`平`造成证据不完整及范围被污染。
- 修复后面积单值证据/范围专项 **9 passed**，解析器文件 **739 passed**，全量pytest **1562 passed、28 skipped、27 subtests passed**。28项本机数据库集成未连接；隔离PG17最近一次完整集成29 passed。解析器版本`generic-labelled-v0.2.153`。
- Python 3.12 compileall、GOAL_STATE JSON、`git diff --check`与129文件开发包校验通过。仅合成HTML验证，无真实页面准确率结论。

## 2026-11-12 P0-03接受“平”作为建筑面积单位
- 两来源合成回归复现`建筑面积：100平`被漏提取；解析器现接受`平`并将数值作为平方米面积。现有范围路径同步接受`120平-130平`和`120-130平`完整证据，面积字段留空、进入待审。
- 修复前单值用例2项失败；修复后单值及范围专项 **6 passed**。解析器文件 **736 passed**，全量离线pytest **1559 passed、28 skipped、27 subtests passed**；28项数据库集成未连接本机PostgreSQL，最近一次隔离PG17完整数据库集成29 passed。解析器版本`generic-labelled-v0.2.152`。编译、GOAL_STATE JSON和diff检查通过，保留1条既有弃用警告。
- 仅使用合成HTML；无获准真实页面准确率结论、数据库变更、来源访问、NAS操作或部署。

## 2026-11-12 P0-07生产schema迁移边界只读核验
- 使用此前获准的`notedock-nas`确认`DXP4800/sheng`及API/Worker/PG运行态；通过PostgreSQL `information_schema`只读核对关键结构，没有读取业务行或秘密。
- 基础业务表和005条件单新增字段/约束可见；006–014的核心发现/观测/复核/解析账本/暂存ID/详情队列对象以及008、013新增列缺失，解析健康计数列也缺失。未逐项核对001–005的全部索引和触发器。
- 因工作区API/Worker所需schema未部署，不进行API-only部署。未备份、迁移、改Compose/卷/服务或部署；P0-07保持`in_progress`。生产升级前置为新鲜备份、恢复验证及隔离迁移评估。
- 用户再次确认面积和挂牌价下限均为大于0；现有实现与该口径一致，无代码改动。
- 本机全量离线pytest **1555 passed、28 skipped、27 subtests passed**；28项数据库集成未连接本机PostgreSQL，本轮生产schema查询为只读。编译、JSON及diff检查通过，保留1条既有弃用警告。

## 2026-11-12 P0-03核验限定价证据穿过API暂存
- 扩展`POST /api/collection/pages`回归，确认近似价场景中每条挂牌价mention的`is_non_exact`既保留于待审响应，也保留在数据库写入参数的`extracted_fields` JSONB对象中。
- `tests/test_collection_api.py` **108 passed**；全量pytest **1554 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未连接，保留1条既有Starlette/httpx弃用警告。
- 仅mock数据库与合成HTML验证；未访问网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-03补齐价格区间逐条限定标记
- 失败回归发现：挂牌价证据契约已新增`is_non_exact`，但合并区间扫描路径漏写该标记，导致区间mention缺字段。
- 单值与区间证据现一致携带`is_non_exact`；普通范围为false，带近似/上下限限定的范围为true。同分根冲突证据扫描也保留标记，解析器版本升至`generic-labelled-v0.2.151`。
- 区间、限定区间和同分根冲突定向 **19 passed**；全量pytest **1554 passed、27 skipped、27 subtests passed**，27项数据库集成未连接。仅合成HTML验证，未访问网站、NAS或生产数据库。

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

- 工作区解析器版本为`generic-labelled-v0.2.158`；解析器测试文件783 passed，最新全量离线pytest为1649 passed、28 skipped、27 subtests passed；面积限定词覆盖上下限同义表达，“起”的边界同时排除“起居室”误报并接受顿号/括号后的下限写法。28项PostgreSQL集成测试在本机未连接数据库；当前工作区此前在隔离PostgreSQL 17.11完整运行数据库集成文件为29 passed，覆盖迁移001–014及详情队列相关数据库行为，但这不代表工作区已部署到生产。
- 挂牌价限定词已覆盖近似价、上下限、单位面积价和价格范围；“起始价”按非精确报价处理，折叠摘要中的独立“起始”不会清空紧邻的精确价格。同页嵌套报价及独立同分根的冲突字段按用户确认留空待审。面积、挂牌价下限均为大于0；跨平台面积差以较小面积作分母，挂牌价差以低价作分母。
- P0-01仍缺真实V0.1数据库备份；P0-02/P0-03仍缺每站20份获准页面及人工标签，真实解析准确率未验证。P0-04的许可证据仍不足，P0-06等待获准DTK账号联调；P0-07生产健康率正文及工作区代码未部署，/api/collection/health认证后内容未验证；P0-09仍需真实来源验收。所有网站在线采集开关继续关闭。
- 最近开发包`../ningbo-re-ai-v0.2-dev-2026-11-12-qualified-price-range-api.zip`通过项目打包器的ZIP完整性和包内SHA-256清单校验。当前迭代只做离线代码、测试与文档更新；没有访问网站、NAS或生产数据库，也没有迁移或部署。
## 2026-11-12 P0-03评分后续 article 根
- 失败回归复现首个`article`仅含推荐文本、后续独立`article`含完整挂牌信息时漏字段；现评分所有未嵌套于其他`article`的候选，维持单根解析及文档顺序，不跨根拼接。解析器版本`generic-labelled-v0.2.131`；当时嵌套`.content`价格冲突口径仍待用户确认。
- 解析器专项 **472 passed**、全量离线pytest **1073 passed、27 skipped、27 subtests passed**；数据库集成未运行。compileall、GOAL_STATE JSON与diff空白检查通过。仅合成HTML离线验证，无来源/NAS/生产数据库访问、迁移或部署。

## 2026-11-12 P0-03将非挂牌价格场景缺失值纳入字段指标
- 失败回归显示，`oral_prices`/`transaction_prices`标注挂牌价为空时，专门场景能检出非挂牌金额被误抽，但该样本未进入挂牌价字段准确率/精确率分母；错误输出因而未降低字段指标。现将这两类显式空挂牌价作为空真值计分，误报会同时反映在字段指标和专门场景指标；未解析的`multiple_prices`继续只在独立场景计分。
- 两来源promotion回归修复前均失败，修复后通过。评估器专项 **116 passed**；全量离线pytest **1073 passed、27 skipped、27 subtests passed**。27项均需PostgreSQL集成库，未运行。Python 3.12 compileall和`git diff --check`通过。
- 更新`docs/SAMPLE_DATASET.md`与`docs/ACCEPTANCE.md`分母说明。仅使用合成HTML/Mock，没有真实样本准确率结论；未访问来源网站、NAS或生产数据库，无迁移或部署。

## 2026-11-12 P0-09独立持久化详情URL队列
- 详情URL从列表页观测后先进入迁移014的目标级队列，并与挂牌观察记录关联。Worker每轮最多请求20个详情；某条详情发生可恢复错误时，保存错误类型/尝试次数、继续处理其他队列项和列表页，失败项留到后续轮询重试。robots、许可撤回及403/429等阻断仍停止目标，不绕过来源限制。
- 队列成功暂存后删除；暂存ID ledger用于进程中断后的幂等恢复。认证discovery-state新增最多100条待抓URL和总数/截断信息。
- 离线回归覆盖一个详情失败、后续详情成功、扫轮完成、失败项下轮成功重试；相关服务/发现/状态 **65 passed**，追加403/429停止队列回归2项后，全量pytest **1060 passed、26 skipped、27 subtests passed**。26项PostgreSQL集成因缺少TEST_DATABASE_URL跳过；迁移014未在真实PG运行。
- 本轮仅修改工作区；未访问来源网站/NAS/生产库、未执行迁移或部署。P0-09仍待PG17迁移/API验证、获准真实页面及站点专用选择器校准。

## 2026-11-12 P0-06历史补采页数上限后续跑
- 发现DTK 30/90天历史补采每轮最多5页，但partial也会将账号标记为initial_synced，导致超出5页的旧内容被永久跳过。
- 本轮新增迁移013保存分页游标和固定截止时间；Worker每页保存进度，只有自然读到末页才完成首次同步。更改历史模式或显式重新补采会清除旧进度。
- 新增测试覆盖五页上限后的下一轮续跑、固定截止时间、请求失败后按游标恢复、完成时清理进度、模式切换重置和日常增量轮询不写补采游标；Worker定向4 passed；完整定向8 passed、13 subtests passed；全量离线pytest **1057 passed、26 skipped、26 subtests passed**，26项因未设置TEST_DATABASE_URL跳过。compileall、目标JSON、diff空白和开发包完整性/哈希校验通过。PostgreSQL迁移实际执行待验证。
- 仅离线开发；未连接DTK/NAS/生产数据库、未执行迁移或部署。P0-06仍需真实接口版本核验和获准账号24小时联调。

## 2026-11-12 P0离线回归套件重新验证
- 使用已有离线依赖缓存和临时Python 3.12环境重新运行全量pytest：**855 passed、26 skipped、25 subtests passed**；仅有1条Starlette/httpx弃用警告。26项跳过全部为PostgreSQL集成，因为本机未配置`TEST_DATABASE_URL`且`pg_isready`无服务响应。
- Python 3.12 compileall、`docs/GOAL_STATE.json`解析及文档尾随空白检查通过。未改应用代码、未执行迁移、未访问房源网站/NAS或生产数据库。
- 按项目迭代流程生成`../ningbo-re-ai-v0.2-dev-2026-11-12-offline-regression.zip`；开发包包含124个源码/文档文件，ZIP完整性与包内SHA-256清单校验通过。
- P0-09迁移012运行回归仍需PostgreSQL 17隔离库；跨区域解析字段行为继续等待用户选择。

## 2026-11-12 P0-01/P0-07 NAS运行态与迁移挂载只读复核
- 按NAS连接技能依次尝试`nas-lan`、Tailscale，再使用用户此前授权的`notedock-nas`；LAN连接超时、Tailscale CLI无法读取偏好。公网别名通过严格主机校验后连接到`DXP4800/sheng`，Docker权限正常。
- UGREEN Compose路径仍为`/volume3/docker/ningbo-re-ai/docker-compose.yml`；API与Worker运行，PostgreSQL 17 healthy，NAS本机`http://127.0.0.1:8788/healthz`返回`ok=true`。当前Compose仅挂载001–005迁移；工作区006–012没有部署。该只读检查未查询业务行、数据库schema或秘密。
- 未传输文件、创建容器、执行迁移或改动Compose/卷/服务；未部署。P0-01仍缺真实V0.1备份；P0-07仍需经过备份和隔离验证后评估生产更新；P0-09迁移012仍待允许的隔离PG17回归。不得将此运行态检查表述为工作区版本已部署。

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

## 2026-11-12 P0-04官方协议正文续核
- 贝壳协议复核确认2026-11-12生效；第七条限制未经书面许可的数据读取/自动化抓取，并要求许可使用限于书面范围且遵守Robots。
- 安居客当前消费者协议正文与静态PDF的版本映射仍未核实。没有项目书面许可，两站在线采集继续OFF；协议核读不等于授权，也未请求房源页或执行采集。
- 后续门槛：确认安居客适用协议并取得平台针对本项目的书面许可；贝壳取得用途明确的书面许可。仅在门槛满足后复核获准目标的Robots规则。

## 2026-11-12 P0-09长期分页去重ID规范化
- 迁移012将每目标成功暂存挂牌ID从游标JSON回填到独立表；Worker对规范化表去重，扫轮已见ID从挂牌观察记录派生。发现状态API保留有界列表/总量/截断字段；`seen_ids`按挂牌ID字典序返回，利用主键索引确保回填后顺序确定。
- 新增PG集成回归覆盖100,001条历史ID后继续发现新挂牌；本机全量离线pytest **855 passed、25 skipped、25 subtests passed**，compileall、目标JSON及变更文件尾随空白扫描通过。PG17未在本轮重跑：自动审核拒绝未经授权的源码包上传和NAS临时文件写入。
- 仅离线验证，未执行迁移或部署。P0-09仍需来源许可、两站获准真实页面及生产升级/恢复验收。

## 2026-11-12 P0-03流式迭代内联CSS声明
- `_scan_inline_css_values`与`_has_escaped_opacity_math_syntax`原用`style.split(';')`一次性分配全部声明。75,000个合成声明的两条路径都触发内存回归失败，旧峰值分别3.76/3.75 MiB；现通过正则match迭代声明，不保留片段列表。
- 同输入新峰值分别 **0.0067 MiB**、**0.0020 MiB**。CSS/可见性定向 **70 passed**；解析器专项 **340 passed**，全量离线pytest **853 passed、22 skipped、23 subtests passed**。22项数据库集成因未配置`TEST_DATABASE_URL`跳过。
- Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。仅合成CSS离线验证；内存结果不代表真实网页或生产SLO。未访问网站/NAS/生产数据库，无部署。

## 2026-11-12 P0-03合并CSS可见文本扫描并降低分配
- `_css_without_comments_or_strings`原按输入每个字符向列表追加一个字符串；300 KB普通CSS回归峰值2,901,577字节并超出1 MB测试预算。现只在引号/注释边界写入可见片段，普通连续CSS整体写入。
- 600 KB输入峰值由旧版 **5.60 MiB** 降至 **1.29 MiB**；300 KB峰值低于1,000,000字节的回归通过。CSS/可见性定向 **70 passed**，解析器专项 **338 passed**，全量pytest **851 passed、22 skipped、23 subtests passed**。22项数据库集成因未配置`TEST_DATABASE_URL`跳过。
- Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。内存数据只代表合成CSS，不含来源页面分布或生产SLO；未访问网站、NAS或生产数据库，无部署。

## 2026-11-12 P0-03流式扫描样式表规则
- `_css_rule_segments`此前先构造所有CSS片段列表，再由样式表可见性检查逐项扫描；600,000字节、200,000段输入的分段函数单独产生列表时峰值额外内存为 **9.75 MiB**。现改为按需yield，发现首条风险规则即可提前停止。
- 新增惰性回归，原实现取第一个片段前已切片1,001次而失败，流式实现只切片1次；CSS/样式表专项 **23 passed**，解析器专项 **337 passed**，全量离线pytest **850 passed、22 skipped、23 subtests passed**。同一600 KB CSS完整消费200,001段时，流式分段峰值为 **0.0008 MiB**（仅计分段器，不含CSS字符串/DOM）。
- Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。仅合成CSS离线验证；不代表真实网页内存或生产SLO。跨根字段合并策略与真实样本评测仍待确认/提供。

## 2026-11-12 P0-03 DOM遍历复核与样本库存盘点
- 当前`app/collectors/parser.py`仅余一处直接`Tag.children`生成器访问，用于判定标题包装链；不再将children物化为列表。盘点`data/`仅1个占位文件，`fixtures/`为4份演示HTML，工作区无真实样本清单。
- 不含数据库的解析器专项最近一次 **336 passed**，全量离线pytest最近一次 **849 passed、22 skipped、23 subtests passed**；本轮按`python -m pytest`定向运行DOM遍历回归 **1 passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- 样本盘点未达P0-02/P0-03真实页面验收；不把演示fixture计入40份获准页面。未访问来源网站、NAS或生产数据库，也未部署。
- 后续继续离线解析工作；真实精确率评测需每站20份获准页面及人工标注，跨语义根合并行为仍待用户确认。

## 2026-11-12 P0-03复用DOM已有子节点列表
- 失败回归证明可见文本、run-in布局、不可见节点移除、内联可见性检查和隐藏文本裁剪会复制已有子节点列表。现统一从BeautifulSoup的`contents`列表读取；需删除节点/文本时使用逆序迭代，回归验证连续隐藏兄弟节点、隐藏容器内多段文本裁剪后前后可见文本仍在。未改变解析字段或可见性规则。
- 回归先失败后通过。解析器专项 **336 passed**；全量离线pytest **849 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过；保留1条Starlette/httpx弃用警告。
- 先后顺序相反的两批各9次完整解析基准（含tracemalloc）：同一600,098字节/25,000个span页面，上一版本中位数1,224.24/1,230.99ms，当前版本1,122.29/1,138.92ms；两批均低约7.5–8.3%，峰值内存两边均30.02MiB。仅为合成页趋势，不代表真实页面或生产SLO。
- Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。仅离线合成HTML验证，无网站/NAS/生产数据库访问、无迁移或部署；真实页面准确率仍待获准样本与人工标签。

## 2026-11-12 P0-03穷举Unicode空白截断边界
- 新增差分回归，枚举Python正则表达式识别的全部Unicode空白码点；对每个码点构造连续空白，并在规范化输出的每个截断位置核对有界前缀和截断状态与完整`re.sub`一致。未改变解析行为。
- 归一化专项 **8 passed**，解析器专项 **335 passed**；全量离线pytest **848 passed、22 skipped、23 subtests passed**。22项数据库集成因未设置`TEST_DATABASE_URL`跳过；保留1条Starlette/httpx弃用警告。
- Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。仅离线验证，未访问网站、NAS或生产数据库，无迁移/部署。跨语义根合并规则待用户确认；真实页面准确率仍待获准样本和人工标注。
- 下一轮继续P0-03离线解析回归；收到跨根合并口径后补充相应规则和评估用例。

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

## 2026-11-12 P0-03候选根排除连接式合同挂牌价
- 两站回归确认候选 `.houseInfo` 中的“合同中的挂牌价”会让评分误判满分并提前停止，漏掉后续 `.content` 的真实挂牌价。评分现按字段抽取相同规则排除连接式非挂牌价格；解析器版本为 `generic-labelled-v0.2.128`。
- 解析器专项 **466 passed**；全量离线pytest **1067 passed、27 skipped、27 subtests passed**。数据库集成因未设置`TEST_DATABASE_URL`跳过；未访问来源网站、NAS或生产数据库，无迁移/部署。
- P0-03仍需贝壳/安居客各20份获准页面与人工标注，才能报告真实精确率和覆盖率。下一步继续基于失败回归审查离线边界；隔离PG17授权到位后验证P0-09迁移014。

## 2026-11-12 P0-03检查全部同类候选内容根
- 两站失败回归确认：首个 `.content` 只有推荐文本、后续 `.content` 才有完整挂牌字段时，解析器会漏掉后者。现在按文档顺序评分所有 `.houseInfo`、`.house-info`、`.content` 根，仍只选单一根且不合并字段；版本 `generic-labelled-v0.2.129`。
- 候选根定向 **15 passed**、解析器 **468 passed**、全量离线pytest **1069 passed、27 skipped、27 subtests passed**。数据库集成因未设置`TEST_DATABASE_URL`跳过。NAS只读可达，确认PG17镜像存在；本轮未上传文件或创建临时容器。
- P0-03仍需每站20份获准页面和人工标签。P0-09隔离PG17执行待用户批准远端临时写入后继续。

## 2026-11-12 P0-03保留嵌套内容根的冲突证据
- 同类兄弟候选仍按文档顺序评分；嵌套`.houseInfo`/`.house-info`/`.content`不重复评分，因为外层候选已包含其可见文本。此规则保留外层与内层挂牌价冲突，避免挑出单个嵌套价格掩盖歧义，也将嵌套候选文本遍历限制为一次。解析器版本 `generic-labelled-v0.2.130`。
- 嵌套根定向 **2 passed**、候选根 **17 passed**、解析器 **470 passed**、全量离线pytest **1071 passed、27 skipped、27 subtests passed**。本机10,000层/270,012字节嵌套探针约0.072秒；仅为单机合成测量。
- 未获真实页面/人工标签，不能报告真实准确率；未访问网站、未修改NAS生产环境或执行数据库迁移。

## 2026-11-12 P0-03待确认article与嵌套content冲突处理
- 合成回归显示外层`article`价格300万与内层`.content`价格320万并存时，当前解析器选更具体的内层根，丢弃外层价格冲突。该策略关联尚未确认的跨语义根处理口径，已向用户询问；答复前不改代码。
- 本项仅为离线观察，不代表真实页面行为或准确率，也未访问网站、NAS或生产数据库。
- 后续决策已记录在本路线图v0.2.132条目：用户确认不同报价留空待审，现有待确认状态仅保留为历史记录。

## 2026-11-12 P0-04刷新实际目标主机Robots证据
- 已授权 `notedock-nas` 只读连接到 `DXP4800/sheng`；按当前代码UA直连请求两个目标 `/robots.txt`，不跟随重定向，仅限读65,537字节。贝壳示例详情路径由RobotFileParser判为拒绝；安居客示例路径允许。状态、字节数、哈希和示例路径记于来源政策复核文档。
- 这是robots路径判断，不代表协议、商业使用或二次分发许可。贝壳仍OFF；安居客因当前消费者协议正文和本项目书面许可未确认仍OFF。没有访问房源页、采集或NAS写入。

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

## 2026-11-11 P0-09策略撤销前置时保留空详情进度
- 修复列表页成功但首个详情请求前许可被撤销时不保存扫描状态的缺口。现在即使详情暂存数为0，也保留当前扫描号、活动状态、列表页重试游标及页内已观察ID；不增加失败计数、不把详情标记为已抓取。
- 首先失败后通过的Mock回归覆盖此路径；P0-09分页/发现/状态专项78 passed、7 subtests；全量pytest734 passed、21 DB用例跳过、17 subtests；标准库42 passed。PG集成新增回归尚未在数据库运行。

## 2026-11-11 P2-02精确比较跨平台10%单价门槛
- 回归发现循环小数单价在先除面积再比较时会把数学上恰好10%的候选算成不足10%。门槛现由原始Decimal金额/面积交叉相乘判断，展示值仍保留两位小数。
- 机会专项21 passed，全量pytest734 passed/20 skipped/17 subtests，stdlib42 passed。面积差仍以较小面积为分母；公式待用户确认。仅离线验证，无迁移、无NAS/生产写入。

## 2026-11-11 P0-03防止缺失字段上的误报虚增精确率
- `evaluate_parser.py`审计确认标注缺失字段仍在准确率分母内；解析器若输出非空值，计为错误且进入精确率分母。新增桩化回归注入误报面积：5项中4项准确、覆盖100%、精确率80%，missing_fields场景失败。
- 定向1 passed，全量离线pytest737 passed、22 skipped、17 subtests passed。无需评估逻辑改动；获准真实页面与人工标注仍缺。

## 2026-11-11 P0-03修复折叠摘要中的内联字段断裂
- 失败回归复现：折叠`details`只保留`summary`时，`get_text(' ')`为每个内联节点添加空格，导致跨`span`拆分的小区名不准、总价标签无法识别。现复用`_text_with_inline_boundaries`保留相邻行内文本，再折叠空白；hidden摘要和折叠正文仍排除。
- 解析器版本`generic-labelled-v0.2.72`；定向摘要/隐藏内容测试8 passed，全量离线pytest736 passed、22 skipped、17 subtests passed。仅合成HTML验证，真实页面准确率仍待获准样本及人工标注。

## 2026-11-11 P0-03按CSS相邻盒规则解析 `display: run-in`
- 替换上一轮一律块级的保守分类：run-in序列后接普通块级盒时按内联内容处理；无匹配块、后接行内盒或后接`flow-root`等独立格式上下文时仍分隔。解析器版本`generic-labelled-v0.2.71`。
- 相关回归先失败后通过；专项17 passed，全量pytest733 passed/20 skipped/17 subtests，标准库42 passed。仅合成HTML；真实平台准确率仍待获准样本与人工标注。NAS LAN/Tailscale不可用，授权公网别名超时。

## 2026-11-11 P0-03将CSS `display: run-in`作为保守文本边界
- 失败回归复现run-in片段跨块误拼接；因run-in布局依赖相邻盒子而解析器无布局计算，字段文本抽取现在将其作为块级边界，版本`generic-labelled-v0.2.70`。
- 显示边界13 passed，全量离线pytest729 passed、20 skipped、17 subtests，stdlib42 passed；真实平台准确率仍待获准页面和人工标注，未联网、未部署。

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

## 2026-11-11 P0-09记录跨周期挂牌出现时间
- 发现分页状态里的`seen_ids`只用于目标内去重，旧ID在后续列表页重扫时被解析器过滤，因此系统无法记录首次/最近出现时间。发现结果现在分别提供本页所有唯一可识别ID与待抓详情ID；新增幂等迁移007保存首次/最近观察时间、次数和最后目标/列表页，并提供认证只读分页API。
- 不基于列表出现记录判断详情有效、在售或自动下架；用户已确认连续2次完整分页遍历未见后转人工核验，且不自动下架。在线采集仍关闭。
- 标准库测试42 passed（迁移/Compose检查3 passed），Python compileall通过。定向pytest因pytest模块缺失无法启动；Homebrew PostgreSQL 16 `initdb`在bootstrap的`shmget`共享内存阶段失败，SQL未执行；Docker daemon也拒绝访问。Worker/SQL集成未运行；未访问网站/NAS或部署。

## 2026-11-11 P0-09验证许可恢复后的详情续跑
- 两轮Mock用例确认blocked_policy检查点会在下一轮过滤已成功详情ID，仅重新请求未完成详情。collection-service专项28 passed；全量pytest699 passed、16 skipped、13 subtests passed。数据库集成16项未配置`TEST_DATABASE_URL`而跳过。

## 2026-11-11 P0-09保存许可撤销前的分页进度
- 第一条详情成功暂存、下一条详情请求前许可撤销时，原逻辑不保存当前轮seen ID。现在只要有详情成功，就保存已完成ID及当前列表页重试游标；策略阻断不增失败数。回归先失败后通过；定向3 passed，全量pytest699 passed、16 skipped、13 subtests passed。Mock验证，不是PG/NAS集成验收。

## 2026-11-11 P0-03精确数值范围端点回归
- 面积10/20,000㎡和总价1/200,000万元的精确边界均保持包含；数值上下界专项6 passed。全量pytest698 passed、16 skipped、13 subtests passed，16项DB集成缺`TEST_DATABASE_URL`跳过。解析器版本v0.2.66。

## 2026-11-11 P0-03覆盖Decimal数值范围两端
- 补充下界外输入：面积9.999999999999999999及挂牌价0.999999999999999999会被float抬回合法下界，现由Decimal范围校验拒绝；上下界专项2 passed。全量pytest694 passed、16 skipped、13 subtests passed，数据库集成16项因未配置`TEST_DATABASE_URL`跳过。解析器版本保持v0.2.66。

## 2026-11-11 P0-03精确校验数值范围
- 极精细但超出允许上限的面积/挂牌价曾因float舍入变成合法最大值。现先用Decimal精确比范围、再转float；解析器升至`generic-labelled-v0.2.66`。失败回归先复现后修复；相关专项318 passed、全量pytest693 passed/16 DB集成跳过/13 subtests passed。真实页面准确率仍未验证。

## 2026-11-11 P0-03畸形HTML结构回归
- 未闭合与错配HTML标签的3种合成回归均通过：明确标签字段可抽取，人工审核标记保留。解析器专项200 passed；全量离线pytest692 passed、16 skipped、13 subtests passed。真实页面准确率仍待获准样本与人工标签。

## 2026-11-11 P0-08完整备份集留存候选
- 逐文件候选可能把同一备份内的数据库转储和raw-pages归档拆开。现对`ningbo-re-ai-...`备份目录整体判断留存；目录和全部普通成员都严格超期才作为一条候选，旧式散落文件仍逐文件列报。
- 留存专项22 passed；全量pytest689 passed、16 skipped、13 subtests passed。仅本地临时目录验证，未同步/运行于NAS或删除任何备份。

## 2026-11-11 P0-07健康率需要确认数据模型
- 代码核查确认`collection_runs`只有success/failed/blocked状态，无法区分网络失败和解析失败，也未记录取得HTML及解析尝试；解析成功率需新增持久阶段数据，不能由当前运行/候选计数推算。
- 采集成功率的策略阻断分母、关键字段完整率必需项、审核率分母仍待用户确认；问题已提出，当前不改API/SQL。

## 2026-11-11 当前工作区全量离线回归
- 临时Python 3.12环境全量`pytest -q`：**688 passed、16 skipped、13 subtests passed**，16项因未设置`TEST_DATABASE_URL`跳过，保留1条Starlette/httpx弃用警告。
- 合成HTML解析路径已运行；真实站点准确率仍需获准页面与人工标签。未访问网站、NAS或数据库，未部署。

## 2026-11-11 P0-03评估报告解析器版本契约
- 评估器报告的`parser_version`现在由端到端评估回归断言与当前解析器版本一致。专项54 passed；解析器/样本集260 passed；标准库42 passed。真实样本准确率未验证，P0-03继续等待许可样本与人工标注。

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

## 2026-11-11 P0-03识别空白分隔的非挂牌价与非建筑面积标签
- 对空白折叠后仍识别`折后 总价`等限定词，并避免`使用 建筑面积`经后缀回退误作建筑面积；版本`generic-labelled-v0.2.61`。
- 解析器/评估/样本集专项292 passed；全量离线636 passed、15项数据库集成跳过、13 subtests passed。只用合成HTML，未验证真实页面准确率。

## 2026-11-11 P0-08 NAS复验等待SSH路径恢复
- LAN连接超时，Tailscale偏好不可读且本机无Tailscale App，已授权公网SSH别名也超时；没有成功连接或远端操作。
- 留存与备份根目录修复目前只在工作区验证，NAS当前脚本版本尚未核对。

## 2026-11-11 P0-09补齐Unicode URL身份跨入口回归
- API模型和本地state分别覆盖Unicode IRI与UTF-8百分号路径等价时的回环拒绝，确保共享`source_page_key`规则在发现器之外一致生效。
- 模型/发现器44 passed、stdlib状态/CLI19 passed；全量离线630 passed、15项数据库集成跳过、13 subtests passed。

## 2026-11-11 P0-09将Unicode IRI规范到请求路径身份
- 将裸Unicode路径与HTTPX实际发送的UTF-8百分号形式统一比较，避免分页回环漏检及等价next链接冲突；路径大小写、保留转义和路径分隔符语义不变，非法surrogate拒绝。
- 发现器专项18 passed；全量离线628 passed、15项数据库集成跳过、13 subtests passed。只用本地URL构造与合成HTML验证。

## 2026-11-11 P0-03排除负opacity钳制为0的隐藏内容
- 按CSS计算规则将有限负数透明度（含百分比/指数写法）视为透明，避免隐藏广告报价污染解析；无效`-Infinity`不被当成隐藏。版本`generic-labelled-v0.2.60`。
- 解析器/链接发现器专项195 passed；全量离线625 passed、15项数据库集成跳过、13 subtests passed。只做合成HTML验证，不代表真实样本准确率。

## 2026-11-11 P0-08库存报告拒绝符号链接根目录
- `storage_report.py`此前跳过符号链接根目录却可能报告0文件/0个过期备份；现在CLI遇到符号链接形式的raw-pages或backups根目录时明确失败，避免把未检查误报为空库存。
- 留存报告专项14 passed；全量离线621 passed、15项数据库集成跳过、13 subtests passed。仅临时目录回归，未访问NAS或删除文件。

## 2026-11-11 P0-08保护备份根目录权限不被符号链接重定向
- `backup.sh`发现`BACKUP_ROOT`本身为符号链接时现立即失败，不跟随路径执行`chmod 700`或写入备份。假Docker完整脚本回归验证原权限/内容未变化，既有正常发布和raw-pages符号链接拒绝用例通过。
- 备份专项6 passed、标准库组合27 passed、全量离线619 passed/15项数据库集成跳过/13 subtests passed；仅离线验证，NAS脚本版本尚待同步复验。

## 2026-11-11 P0-09保持已访问页失败重放后的状态可续用
- 对已访问快照的人工重放失败时，只记录尝试/错误，不把已访问页改成重试游标；原有未访问失败页仍保存为重试游标。
- 新回归先失败后通过；标准库状态/CLI **18 passed**，全量离线 **618 passed、15项数据库集成跳过、13 subtests passed**。离线合成验证，许可、获准真实分页样本和自动Worker流程仍未完成。

## 2026-11-11 P0-03避免跨块级center拼接字段
- 失败回归复现`<center>小</center><span>区：东湖花园</span>`会因漏记CENTER块边界而误提小区；加入块级边界后跨节点标签不再成立，解析器升至`generic-labelled-v0.2.54`。
- 解析器/评估器/样本集270 passed，全量离线597 passed、15项数据库集成跳过、13 subtests passed。仅合成输入验证，真实页面准确率与NAS部署仍未完成。

## 2026-11-11 P0-09按等价URL身份阻断分页回环
- 主机大小写、DNS尾点、显式默认443端口和未保留字符百分号编码可让同一页出现不同字符串。发现器、数据库状态模型/服务、本地state/CLI共用经校验的source page key；路径大小写保持敏感，保留字符编码（如`%2F`）不等同于路径分隔符。
- 离线发现器/状态/CLI定向40 passed、7 subtests passed；全量离线617 passed、15项数据库集成跳过、13 subtests passed。仅合成快照验证；许可、真实分页样本和Worker仍未完成。

## 2026-11-11 P0-03限制display空白归一化为CSS ASCII空白
- NBSP回归复现无效display值被Python Unicode `split()`误规范为合法多关键字值；现仅按CSS ASCII空白归一，解析器升至`generic-labelled-v0.2.59`。
- 专项282 passed，全量离线609 passed、15项数据库集成跳过、13 subtests passed。仅合成输入验证。

## 2026-11-11 P0-03归一化内联display值的空白
- 失败回归确认多关键字CSS display间隔多个空格时未匹配分类；声明值现折叠连续空白，解析器升至`generic-labelled-v0.2.58`。
- 专项281 passed，全量离线608 passed、15项数据库集成跳过、13 subtests passed。仅合成输入验证。

## 2026-11-11 P0-03支持显式继承display的可见文本边界
- 失败回归复现块级容器下`display:inherit`子元素跨节点拼接字段标签；遍历现向祖先解析继承显示值，解析器升至`generic-labelled-v0.2.57`。
- 专项280 passed，全量离线607 passed、15项数据库集成跳过、13 subtests passed。仅合成HTML验证。

## 2026-11-11 P0-03补齐inline flow list-item分类
- 回归复现遗漏`inline flow list-item`导致内联元素被错误分隔；加入行内display值集合，解析器升至`generic-labelled-v0.2.56`。
- 专项279 passed，全量离线606 passed、15项数据库集成跳过、13 subtests passed。仅合成页面验证。

## 2026-11-11 P0-03按内联CSS显示方式构造可见文本
- 三条失败回归分别覆盖`span display:block`、`div display:inline`及拆分字段标签导致语义根误选推荐房源。现解析和候选根打分共用相同可见文本遍历；解析器升至`generic-labelled-v0.2.55`。
- 增补大小写、`!important`优先级、`table-caption`及多关键字显示值回归；专项278 passed，全量离线605 passed、15项数据库集成跳过、13 subtests passed。仅合成页面验证，真实样本准确率及NAS部署未完成。

## 2026-11-11 P0-03跨行内HTML节点提取字段
- 用合成HTML复现小区、面积、挂牌价标签和数值拆在相邻`span`中时，旧的`stripped_strings`拼接会引入空格并造成漏提。
- 解析器现在保留行内节点文本连续性、在块级节点间分隔，并忽略HTML注释，版本`generic-labelled-v0.2.53`。新增行内分拆与注释假报价回归；解析器/评估器/样本集268 passed，全量离线595 passed、15项数据库集成跳过。
- 只用合成HTML；没有真实获准样本和字段准确率报告，未联网或部署，P0-03保持in_progress。

## 2026-11-11 P0-03证据偏移静态复核
- 核对当前遍历器对行内拼接、块级分隔、HTML注释排除、空白归一化及偏移计算的顺序；证据命中偏移对应解析器内部完整归一化文本，`evidence_excerpt`是其1,000字符预览。
- 新增跨越1,000字符摘录边界的证据offset回归，API文档说明摘录/偏移关系。隔离环境解析器/评估器/样本集 **269 passed**；全量离线pytest **596 passed、15 skipped、13 subtests passed**，保留1条既有弃用警告。15项数据库集成跳过；Docker socket仍不可用。
- 未改代码、未访问NAS/网站、未部署。真实获准样本与准确率仍未验证。

## 2026-11-11 P0-03避免把折后总价当作挂牌价
- 合成复现显示`折后总价`会被通用`总价`标签捕获，既可能单独填入挂牌价，也会和正式挂牌价形成错误冲突。
- 解析器过滤折后/优惠/折扣/降价后/参考/估算/成交/历史/原始/预估/网签总价标签，版本升至`generic-labelled-v0.2.52`。贝壳与安居客分别覆盖12种限定词和仅有折后价；解析器/评估器/样本集266 passed，全量离线593 passed、15项数据库测试跳过。
- 只验证合成HTML。获准真实样本、字段准确率、来源许可和NAS部署均未完成，P0-03保持in_progress。

## 2026-11-11 隔离 PostgreSQL 16全量回归
- 以断网内部网络中的PostgreSQL 16及Python ARM64临时测试容器运行完整pytest：**582 passed、0 skipped、13 subtests passed**；含16项数据库集成和迁移/API验证。
- 通过后确认数据库中`it_*`/`upgrade_*`临时schema均由fixture清理；定向删除临时容器、网络和本地依赖目录。1条既有Starlette/httpx弃用警告。
- 未连NAS生产数据库或房源站点、未部署。PG16合成数据库回归不替代PG17 NAS部署或真实V0.1备份迁移验收。

## 2026-11-11 P0-09防止数据库分页状态单页自环
- 发现数据库状态API只检查`next_page_url`是否出现在`visited_page_urls`；调用方遗漏当前页时，可将下一页写成上一已完成页并反复处理。
- 模型校验现拒绝`next_page_url == last_page_url`，并保留失败页重试游标。新增自环拒绝及失败重试接受回归；全量离线pytest 567 passed、15 skipped、13 subtests passed。
- NAS只读盘点显示当前Compose仍仅挂载001–005；本机006、API及Worker变更未部署。由于本机Docker socket不可用，PG集成15项跳过；未连接生产数据库、修改NAS或部署。
- P0-09继续todo，仍需来源许可和获准真实分页样本；Worker自动分页、重试与失效标记未完成。

## 2026-11-11 P0-06对齐DTK帖子字段持久化边界
- 复现Worker绕过`VideoIn`长度约束，可返回221字符帖子ID、2001字符标题和201字符作者名。
- `normalize_post`现按API模型约束拒绝超限帖子ID、标题、作者名和位置；过长分享URL回退至帖子ID规范链接。此前已有的NUL/孤立surrogate拦截保持不变。
- DTK/Worker专项80 passed，全量离线pytest 547 passed、14 skipped；仅离线模拟响应验证，P0-06真实DTK与账号联调仍未完成。

## 2026-11-11 README验证状态同步
- README旧摘要仍显示本机267 passed、13 skipped，且未区分NAS旧部署验收与当前工作区代码。本轮改为当前离线542 passed、14 skipped及DTK/Worker 75 passed，并明确NAS 144 passed不证明最新工作区代码已部署。
- 同步列出V0.1备份、获准样本/许可、DTK联调及健康指标口径缺口；只更新文档，没有改变运行环境或部署状态。

## 2026-11-11 P0-06拦截DTK不可持久化文本
- 复核发现DTK规范化结果绕过API请求模型直达视频数据库写入；帖子ID、标题、描述、作者名或位置若含NUL或孤立Unicode surrogate，PostgreSQL文本/UTF-8写入会失败；分享URL的孤立surrogate此前可能原样保存。
- `normalize_post`现在在生成可持久化记录前拒绝不可存储的帖子文本并抛出明确`DtkError`，Worker保存脱敏失败摘要；分享URL含不可存储字符时回退为帖子ID规范链接，合法Unicode内容继续保留。
- DTK/Worker专项**75 passed**；全量离线pytest **542 passed、14 skipped**（PostgreSQL集成需`TEST_DATABASE_URL`），另有3个subtests通过和1条既有弃用警告。仅模拟响应离线验证，真实DTK及账号联调仍未完成，P0-06保持`todo`。

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
- 机会候选按小区和户型预分组，每条挂牌只检查本组候选；历史报价改为每次请求读取一次，避免在挂牌循环中重复查询。
- 为历史报价单次加载及异小区候选排除新增回归用例。pytest及依赖在本机/uv离线缓存均不可用；依赖桩的定向smoke验证历史查询仅一次、有效跨平台信号及异小区排除。`compileall`、目标JSON、差异/空白检查和109文件ZIP/包内SHA校验通过。
- 仅离线改动，未连接NAS/数据库/房源网站或部署；线上规模性能未测。

## 2026-11-11 P0-03防止空挂牌文本覆盖已有字段
- `ListingIn`可选标题/URL/区域/楼层/装修/备注裁剪首尾空白，空白归一为`None`，避免 upsert 把已有值替换为空字符串。
- 模型/机会相关专项72 passed；全量479 passed、14项PostgreSQL集成跳过。仅离线模型验证，未部署。

## 2026-11-11 P0-03清除账户URL空query/fragment分隔符
- 抖音账户链接query/fragment清理现在也覆盖空`?`/`#`分隔符；五种后缀回归通过。
- 全量478 passed、14项PostgreSQL集成跳过。仅本机离线验证，未部署。

## 2026-11-11 P0-03规范条件单可选文本筛选
- 可选区域/小区字段现在先裁剪，纯空白视为未设置，防止空格条件把所有房源排除。
- 新增失败回归后通过；全量474 passed、14项数据库集成跳过。离线验证，未部署。

## 2026-11-11 P0-03规范必填身份文本
- `AccountIn.account_ref`改为先裁剪再执行最小长度校验；`VideoIn.source_post_id`和`SavedSearchIn.name`拒绝规范化后的空白值。
- 新增9条回归先失败后通过；全量473 passed、14项数据库集成跳过。离线验证，未部署。

## 2026-11-11 P0-03规范正式挂牌与小区名称输入
- 正式挂牌对来源ID/小区名与新建小区名统一裁剪首尾空白并拒绝纯空白；贝壳/安居客格式校验及`agent`/`other`自有ID格式保持有效。
- 新增12条回归先复现失败后通过；全量451 passed、14项PostgreSQL集成因缺少`TEST_DATABASE_URL`跳过。仅离线验证，未部署。
- 后续静态审阅发现4个PostgreSQL API集成fixture仍使用平台非数字ID，现更新为数字ID；当前离线全量464 passed、14项DB集成跳过，未实际连库验证这些fixture。

## 2026-11-11 P0-03校验挂牌写入和审批入口的来源ID
- `ListingIn`现对贝壳/安居客要求ASCII数字ID并按8/7位最小长度校验；`agent`/`other`格式保持不变。非法旧候选批准被409阻断。
- 新增正反回归与来源ID最小长度/自有ID兼容边界回归；当时全量439 passed、14项数据库测试因缺少`TEST_DATABASE_URL`跳过。API契约同步，仅离线验证，未部署。

## 2026-11-11 P0-03按来源校验人工纠正ID
- 人工纠正挂牌ID只接受数字，并按平台限长：贝壳8–220位、安居客7–220位；7位边界正反向回归通过。
- 全量430 passed、14项DB集成因缺少`TEST_DATABASE_URL`跳过；API文档同步，仅离线验证，未部署。

## 2026-11-11 P0-03规范人工纠正文本
- `CandidateCorrection`文本字段和审核备注现在先strip再检查长度，拒绝纯空白字符串，防止空格小区值通过必填验证；空值需显式提交`null`。
- 新增字段边界回归，定向9 passed；全量427 passed、14项数据库测试因缺少`TEST_DATABASE_URL`跳过。API文档同步，未部署。

## 2026-11-11 P0-03拒绝空白标题纠正值
- `CandidateCorrection`现在拒绝全空白标题，并去除有效标题首尾空格；防止人工纠正覆盖候选标题为空值。回归先失败后通过，全量419 passed、14项数据库集成因缺少`TEST_DATABASE_URL`跳过。
- API文档同步；未迁移数据库或部署。

## 2026-11-11 P0-03人工纠正标题后更新来源标记
- 服务层回归确认人工更正标题后，原机器提取的`h1`证据被替换为`manual_review`证据；定向1 passed，全量418 passed、14项DB集成跳过。
- 仅桩化数据库测试，未部署。

## 2026-11-11 P0-03验证标题证据进入审核候选
- 服务层`stage_html`序列化回归确认标题值、证据来源及引用文本保留在`extracted_fields`中。定向1 passed；全量418 passed、14项DB集成因缺少`TEST_DATABASE_URL`跳过。
- 使用桩化数据库，仅离线验证传递边界；真实数据库、页面与NAS未验证。

## 2026-11-11 P0-03把标题纳入解析器评估
- 解析器输出标题但旧清单/评估器未统计该字段；现新增`title`人工标签（上限500字符，缺失需标记）并输出分来源第9项字段指标。
- 标题准确率、缺失和长度边界回归通过；专项233 passed，全量418 passed、14项数据库测试因缺少`TEST_DATABASE_URL`跳过。评估工具仅用合成样本验证，真实页面准确率未验证，未部署。

## 2026-11-11 P0-03记录标题的来源证据
- `field_evidence.title`现在保留采用的`og:title`、`h1`或`head title`来源及引用文本；三类路径均有回归，解析器版本`generic-labelled-v0.2.49`。
- 专项230 passed，全量415 passed、14项数据库测试因缺少`TEST_DATABASE_URL`跳过。仅合成HTML离线验证，未部署。

## 2026-11-11 P0-03空白标题来源继续回退
- 标题按`og:title`→`h1`→`head title`选择第一个去空白后非空的值；空白og:title失败回归先复现后通过，解析器版本`generic-labelled-v0.2.48`。
- 专项227 passed，全量412 passed、14项数据库测试因缺少`TEST_DATABASE_URL`跳过。仅合成HTML离线验证，未部署。

## 2026-11-11 P0-03为标题增加head备用来源
- 缺少`og:title`和`h1`时，从`head title`读取；提取优先级为`og:title`→`h1`→`head title`。失败回归先复现后通过，解析器版本`generic-labelled-v0.2.47`。
- 专项225 passed，全量410 passed、14项数据库测试因缺少`TEST_DATABASE_URL`跳过。仅合成HTML离线验证，未部署。

# 目标驱动开发路线图 / 可追踪任务池

> 任务状态由测试事实决定。`[x]` 表示本地实现/静态或单元测试完成，**不代表已在NAS上线或已对网站真实采集成功**。每轮结束在 `docs/PROJECT_STATUS.md` 写结果。

## 2026-11-11 P0-03排除详情页交互控件
- 成功标准：`main`中的筛选/询价表单字段不得与挂牌详情字段混合；详情小区、面积和总价保持唯一并可进入人工复核。
- 回归先复现form字段造成冲突；现排除form及独立button/select/textarea，解析器升至`generic-labelled-v0.2.46`。
- 解析器/评估器/样本清单专项224 passed，全量409 passed、14项数据库测试因缺少`TEST_DATABASE_URL`跳过；compileall/目标JSON/diff检查通过。
- 仅合成HTML验证，真实页面与NAS部署未验证；无迁移/配置变化。

## 2026-11-11 P0-03仅从head读取页面身份元数据
- 成功标准：canonical link、og:url、og:title只从head采信，不允许非标准body元数据覆盖来源ID或页面标题。
- 回归先复现body元数据造成ID冲突和标题覆盖；现限定于head，解析器升至`generic-labelled-v0.2.45`。
- 解析器/评估器/样本清单专项223 passed，全量408 passed、14项数据库测试因缺少`TEST_DATABASE_URL`跳过；compileall/目标JSON/diff检查通过。
- 仅合成HTML验证，真实页面与NAS部署未验证；无迁移/配置变化。

## 2026-11-11 P0-03按标准匹配canonical rel token
- 成功标准：canonical link relation token按ASCII大小写不敏感匹配；token必须精确等于`canonical`，再参与页面ID冲突判断。
- 失败回归先复现`rel="alternate CANONICAL"`漏检；现按token精确匹配，解析器升至`generic-labelled-v0.2.44`。
- 解析器/评估器/样本清单专项222 passed，全量407 passed、14项数据库测试因缺少`TEST_DATABASE_URL`跳过；compileall/目标JSON/diff检查通过。
- 仅合成HTML验证，真实页面与NAS部署未验证；无迁移/配置变化。

## 2026-11-11 P0-03排除template惰性元数据
- 成功标准：template内的canonical、og:url和og:title不改变当前页面ID/标题；仍保留真实head元数据处理。
- 回归先复现ID被清空及标题被替换；现解析前移除template子树，解析器升至`generic-labelled-v0.2.43`。
- 解析器/评估器/样本清单专项221 passed，全量406 passed、14项数据库测试因缺少`TEST_DATABASE_URL`跳过；compileall/目标JSON/diff检查通过。
- 仅合成HTML验证，真实页面与NAS部署未验证；无迁移/配置变化。

## 2026-11-11 P0-03清理折叠details摘要的隐藏文本
- 成功标准：折叠`details`仅解析首个直接`summary`中可见文本；摘要内由hidden、display、visibility、opacity或content-visibility隐藏的报价不得参与字段解析。
- 回归先复现摘要被提前纯文本化的问题；现先执行隐藏节点清理，再由内向外保留摘要，解析器升至`generic-labelled-v0.2.42`。
- 折叠详情专项8 passed，解析器/评估器/样本清单220 passed，全量405 passed、14项数据库测试因缺少`TEST_DATABASE_URL`跳过；compileall/目标JSON/diff检查通过。
- 仅合成HTML验证，真实页面渲染及NAS部署未验证；无迁移/配置变化。

## 2026-11-11 P0-03排除content-visibility隐藏内容
- 成功标准：内联`content-visibility:hidden`节点及其后代不参与解析；子节点局部可见声明不能覆盖祖先的内容跳过状态。
- 失败回归先复现；显式栈遍历现传播隐藏祖先状态，解析器升至`generic-labelled-v0.2.41`。
- 解析器/评估器/样本清单专项215 passed；全量400 passed、14项数据库测试因缺少`TEST_DATABASE_URL`跳过；compileall/目标JSON/diff检查通过。
- 仅合成HTML验证，真实页面渲染与NAS部署未验证；无迁移/配置变化。

## 2026-11-11 P0-03解析hidden属性的display级联
- 成功标准：当普通`hidden`元素有有效内联非`none` `display`覆盖时，保留其浏览器可见文本参与字段冲突判断；`display:none`仍排除；`hidden="until-found"`不因`display:block`而变成可见。
- 失败回归先复现；现解析器仅对普通hidden状态尊重常见有效内联`display`值，版本`generic-labelled-v0.2.40`。
- 解析器/评估器/样本清单专项213 passed；全量398 passed、14项数据库测试因缺少`TEST_DATABASE_URL`跳过；compileall/目标JSON/diff检查通过。
- 仅合成HTML验证，真实页面渲染与NAS部署未验证；无迁移/配置变化。

## 2026-11-11 P0-08留存策略文档一致性
- 将验收清单与用户已确认策略统一：备份保留90天；原始页面证据随关联数据库记录保留。
- `storage_report.py`只读列出严格早于90天的备份候选，不自动删除；人工清理仍需核对备份可恢复性或证据数据库引用。
- 本轮为文档一致性修正，不改变留存脚本、数据或NAS部署。

## V0.2 已实现（仍需NAS集成验收）
- 2026-11-11 P0-08补充：原始证据存储目录为软链接时拒绝写入，避免数据落到归档/盘点范围之外；save_html专项4 passed，全量371 passed/14项数据库集成跳过。未部署NAS。
- 2026-11-11 P0-08补充：重复提交仅复用经有界解压并逐字节验证的gzip证据；损坏、内容错配或软链接目标以原子替换修复。定向3 passed，全量370 passed/14项数据库集成跳过；本地改动尚未部署NAS。
- 2026-11-11补充：候选纠错正向验证`120.2300`/`365.1200`仅归一化尾随零，与挂牌长尾零回归共同覆盖无数值变化的精度输入；全量367 passed/14项数据库集成跳过。
- 2026-11-11 P0-03补充：FastAPI TestClient经API Key调用候选审批路由，超精度字段以HTTP 409和字段清单响应；解析器/服务/API专项109 passed，全量365 passed/14项数据库集成跳过。数据库假连接，未部署。
- 2026-11-11 P0-03补充：服务层回归确认面积/价格超精度警告随HTML候选写入而保留，并保持`ready_for_review=false`；解析器/服务专项107 passed，全量364 passed/14项数据库集成跳过。仅假数据库离线验证。
- 2026-11-11 P0-03补充：数据库精度校验直接根据原始页面数字文本执行，避免高精度小数先转float而被掩盖；额外全零小数位仍可接受。解析器`generic-labelled-v0.2.37`，全量363 passed/14项数据库集成跳过；未部署。
- 2026-11-11 P0-03补充：解析数值超过PostgreSQL两位小数精度时保留原值、添加字段警告并阻止ready；审批返回409要求人工纠正，旧候选非法字段也映射为409。解析器`generic-labelled-v0.2.36`，全量361 passed/14项数据库集成跳过；未部署。
- 2026-11-11补充：挂牌/候选纠错/条件单API的面积、价格、降幅输入与PostgreSQL NUMERIC(...,2)精度对齐；会改变数值的第三位小数被拒绝，等价尾随零归一到两位。全量356 passed/14项数据库集成跳过，未部署。
- 2026-11-11 P0-01补充：静态复核002–005未发现删表/删业务行语句；本机未配置TEST_DATABASE_URL且无本地PostgreSQL响应，未执行SQL，P0-01仍需真实V0.1备份/隔离升级验收。
- 2026-11-10 P0-03补充：解析器证据展示最多20条时，第21条不同报价/面积命中仍被完整扫描并阻止候选ready；新增2项解析器回归，全量344 passed/14项数据库用例跳过。仅虚构HTML验证。
- 2026-11-10 P0-03补充：评估器回归将第二个标注报价放在35,000字符解析上限之后，确认`multiple_prices`样本不计为通过；样本清单/评估专项95 passed，全量342 passed/14项数据库集成跳过。仅合成HTML验证。
- 2026-11-10 P0-03补充：FastAPI本地上传路由回归验证截断候选API响应包含`visible_text_truncated`且`ready_for_review=false`，候选保持pending；专项136 passed、全量341 passed/14项数据库集成跳过。端点/服务真实执行、数据库假连接，不替代PG/NAS验收。
- 2026-11-10 P0-03补充：服务层回归验证`visible_text_truncated`在候选写入后仍存在，且按持久化候选返回`ready_for_review=false`；专项135 passed、全量340 passed/14项数据库集成跳过。使用假数据库及合成HTML，不替代PG/NAS验收。
- 2026-11-10 P0-03补充：超过35,000字符的可见正文现在标记`visible_text_truncated`且不报告`ready_for_review`，避免截断后冲突价格未扫描却显示可复核；解析器版本`generic-labelled-v0.2.35`，专项125 passed、全量339 passed/14项数据库集成跳过。仅合成HTML离线验证。
- 2026-11-10 P0-03补充：内联CSS `display:none` 现在能正确处理值前后的注释及注释内分号，避免隐藏报价误参与冲突判断；版本`generic-labelled-v0.2.34`，专项124 passed、全量338 passed/14项数据库集成跳过。仅合成HTML离线验证。
- 2026-11-10 P0-03补充：解析器排除iframe/object/canvas中的备用内容文本，避免与正文挂牌字段形成伪冲突；版本`generic-labelled-v0.2.33`，专项121 passed、全量335 passed/14项数据库集成跳过。仅合成HTML离线验证。
- 2026-11-10 P0-03补充：评估报告新增按来源统计挂牌状态和场景标签数量的`sample_composition`，用于人工复核评估集构成；专项175 passed，全量322 passed/13项数据库集成跳过。仅合成清单回归。
- 2026-11-10 P0-03补充：评估校验和计分共用清单快照；新增替换后恢复竞态及零抽取精确率门槛回归（覆盖率0、精确率null、不达95%）。专项175 passed，全量322 passed/13项数据库集成跳过。
- 2026-11-10 P0-03补充：评估校验与计分共用一次读取的清单快照；报告SHA对应实际评分输入，文件路径在处理中替换/恢复不会形成混合版本。专项174 passed，全量321 passed/13项数据库集成跳过。
- 2026-11-10 P0-03补充：解析评估报告记录清单SHA-256，并在评估前后复核清单及逐个样本的哈希，阻止校验后文件变化产生不可复现结果；专项173 passed，全量离线320 passed/13项数据库集成跳过。真实获准样本仍缺。
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
- [blocked] **P0-01 NAS升级实测**：V0.1数据库备份→执行 `002_collection_pipeline.sql`→V0.2 Compose→API/Worker健康，重启后数据保留；记录真正执行结果。2026-11-09已在NAS完成空库V0.2新装、API/Worker/DB运行与DB容器重启持久化验证，但NAS没有既有 `ningbo-re-ai` V0.1项目或同名卷，无法完成V0.1备份升级。NAS的8787端口由 `nas-image-manager` 占用，新实例绑定127.0.0.1:8788；2026-11-10 Mac解锁后已在UGREEN详情页确认项目运行中、Compose路径正确且API/PostgreSQL 17/Worker均运行。2026-11-11在断网、无端口和宿主挂载的临时PostgreSQL 16容器中，以12张旧业务表合成记录执行002–005及重复迁移，逐表字段、004汇总回填、005默认值均通过断言；这不替代真实V0.1备份升级或PostgreSQL 17验收。
  - 2026-11-11事务故障注入：在临时PG16中分别于002–005的COMMIT前注入SQL错误；确认各自新增表/列/索引/触发器回滚无残留，再执行原版迁移成功。4份断言通过。真实V0.1备份、NAS PG17升级和端到端重启验收仍未完成。
  - 2026-11-10补充：扩大合成V0.1迁移回归，逐表核对账号/视频、房屋与社区、价格证据、条件单和通知等代表性字段值；本机语法编译通过，但当前环境未运行PG集成。
  - 2026-11-10补充：升级手册对无内建事务的002/003/005改用`psql --single-transaction`，而004保持其SQL文件内事务；执行任一SQL失败时整份对应迁移回滚。仅审阅文档命令，未连接NAS执行。
  - 2026-11-10补充：尝试在`/private/tmp`启动一次性PostgreSQL 16并运行`tests/test_db_integration.py`；`initdb`成功，但sandbox中的服务启动在System V共享内存`shmget`处失败（错误文本为No space left on device，详情指向共享内存ID限制），改用mmap参数后仍失败。Docker daemon socket返回permission denied。临时目录已清理，55441端口无响应；未连接NAS或业务数据库。数据库集成仍未运行。
  - 2026-11-10续试：以require_escalated再次启动全新PG16，仅使用Unix socket并使用另一临时端口，服务仍在shmget处失败。只读检查显示System V共享内存/信号量当前列表为空，但sysctl/ipcs管理查询被系统拒绝；临时目录由清理钩子删除，端口55442无响应。说明简单sandbox提权无法解决此隔离运行环境问题；未连接NAS或业务库。
- [ ] **P0-02 采集样本集**：各平台至少20份经允许使用的宁波详情页样本，涵盖在售/下架/字段缺失/同页多个价格/未知ID；保存时间和来源。已提供离线清单模板及本地元数据/哈希/标签覆盖校验器；`.html.gz`按解压内容去重并拒绝损坏流。真实获准样本仍缺，fixture不计数。
  - 2026-11-11离线防护：样本清单的sample_id若含C0/C1控制字符会被拒绝，诊断标签会先转义控制码，避免终端输出被注入。3项失败回归修复后通过；样本集/评估专项120 passed，全量pytest在临时PG16上719 passed、0 skipped、13 subtests passed。真实合法样本和授权仍缺。
  - 同日复查补齐：在`strip()`前检查原始sample_id，覆盖首尾控制码；重复/未支持列名的诊断也转义C0/C1。13项诊断回归通过，样本集/评估127 passed，全量pytest在临时PG16上726 passed、0 skipped、13 subtests passed。真实合法样本和授权仍缺。
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
  - 2026-11-10补充：样本清单模板与validator的列集合新增一致性回归（无重复列且集合完全相同），防止字段增删后复制模板产生必然拒绝或静默缺列。当前25列逐项一致；专项1 passed，全量pytest 279 passed、13项数据库集成因未设置TEST_DATABASE_URL跳过。此项只保障清单schema同步，不代表已获得真实样本/授权。
- [in_progress] **P0-03 站点解析器**：基于P0-02获准页面完成贝壳/安居客字段提取、布局变化回归与真实准确率评估；不把fixture演示当生产可用。当前保守通用解析器`generic-labelled-v0.2.151`，挂牌价/面积只接受大于0，隔离挂牌价与口播/交易/合同/签约价及非精确报价，保留范围与候选证据，并在冲突、截断或可见性未决时阻止审核就绪。样本评估新增可选`non_exact_prices`场景，要求限定价警告和完整证据匹配人工候选；校验/评估324 passed（含限定与逐条证据核对、截断边界），全量离线pytest1555 passed、28 skipped、27 subtests passed，数据库集成未配置TEST_DATABASE_URL而跳过；完整数据库集成文件在隔离PG17为29 passed。真实获准页面及人工标注仍缺，真实准确率未验证；在线采集OFF。
  - 2026-11-11离线语义修复：按PRD禁止将视频口播价混入平台挂牌价。解析器现在忽略`口播总价`/`口播挂牌价`标签，避免口播价独占时误填挂牌价、与挂牌价并列时误报冲突；版本`generic-labelled-v0.2.67`。解析器专项216 passed，全量临时PG16 pytest736 passed、0 skipped、13 subtests passed。合成回归不代表真实页面准确率。
  - 2026-11-11离线评估资源边界：`evaluate_parser.py`在冻结CSV清单快照时此前无大小限制；现对初次读取和评估后完整性复核均限制为2,000,000字节，超限明确拒绝，防止本地评估器无界读入清单。标准库边界smoke 3项通过；pytest及项目依赖当前不可用，新增pytest回归尚未执行。真实页面准确率仍未验证。
  - 2026-11-11诊断回归：定向复核确认样本校验器已将畸形UTF-8/CSV转成可读错误，评估器据此拒绝清单；新增无效UTF-8/畸形CSV诊断与哈希复核超限回归。定向pytest 6 passed，覆盖错误诊断、初始文件上限、SHA复核拒绝超限及超限时读取量最多为上限+1字节（临时pytest运行时与占位BeautifulSoup类型；测试路径不解析HTML）；全量测试仍因缺完整依赖未执行。真实页面准确率仍未验证。
  - 2026-11-11解析器文本身份：社区字段和标题来源判重改用空白折叠+Unicode NFC比较键，保留首次原文输出/证据，避免规范等价值误报歧义；解析器版本`generic-labelled-v0.2.65`。候选归一辅助2 passed，样本集63 passed，评估器清单/NFC/CLI子集10 passed，标准库42 passed（含3项Unicode比较键独立回归）。未运行HTML解析端到端测试；真实样本准确率仍未验证。
  - 2026-11-11文本指标Unicode规范化：评估器文本字段和歧义候选文本在空白折叠后统一Unicode NFC，避免组合字符的等价写法拉低准确率或绕过候选去重；数值继续按Decimal比较。评估、辅助归一、完整清单重复候选拒绝回归3 passed，两项失败复现后通过。仅离线合成标签验证，真实样本准确率未验证。
  - 2026-11-11补充：新增回归确认`<template>`惰性内容不进入解析文本，当前BeautifulSoup行为已满足；无需改解析器。定向1 passed、全量393 passed/14项数据库集成跳过。
  - 2026-11-11补充：DOM批量移除循环跳过父节点已被分解的标签；嵌套CSS隐藏、`hidden`、dialog/details和导航回归5 passed，全量392 passed/14项数据库集成跳过。解析器字段规则未变。
  - 2026-11-11补充：可见性/透明度遍历改用显式栈；新增1,200层嵌套HTML回归，防止输入触发`RecursionError`。专项17 passed、全量387 passed/14项数据库集成跳过。解析器字段输出语义不变。
  - 2026-11-11补充：解析器版本`generic-labelled-v0.2.39`过滤内联`opacity:0`/`0%`文本并将透明祖先状态传播给后代，同时检查声明顺序及`!important`；相关10 passed，全量386 passed/14项数据库集成跳过。仅合成HTML验证。
  - 2026-11-11补充：解析器识别内联CSS `visibility:hidden/collapse`并按继承处理；隐藏祖先下显式可见的后代文本保留，并验证`!important`声明级联。版本`generic-labelled-v0.2.38`，相关11 passed、全量380 passed/14项数据库集成跳过。仅合成HTML验证。
  - 2026-11-11补充：95%精确率门槛改为按整数计数比较，避免94.997...%显示四舍五入为95.00%后误标达标；1,899/1,999边界回归通过，全量375 passed、14项数据库集成跳过。仅合成样本验证。
  - 2026-11-10补充：评估器对每来源恰好20条边界已有默认参数回归，两来源均达正式样本数量门槛；每站5条的诊断结果仍明确未达标。组合专项57 passed、全量离线259 passed/13项DB集成跳过；虚构测试不构成真实样本验收。
  - 2026-11-10补充：评估报告逐来源标出正式20份门槛、样本数及达标状态；诊断用`--minimum-per-source`不能弱化正式要求。44项样本/评估专项与258项全量离线测试通过，13项数据库用例跳过；真实页面仍缺。
  - 2026-11-10补充：source_listing_id现记录提交source_url/canonical/og:url出处；canonical冲突保留两者ID但字段留空，canonical证据去除query/fragment与非必要路径前缀。解析器版本generic-labelled-v0.2.27；专项122 passed、全量258 passed/13项DB集成跳过。真实样本准确率仍待20+20获准页面。
  - 2026-11-10补充：多值/越界字段现在保留最多20条原文命中与归一化文本偏移、总命中数/截断标记，同时解析值继续留空；解析器版本`generic-labelled-v0.2.26`。专项121 passed、全量257 passed/13项DB集成跳过。真实获准样本和准确率仍缺，未连接NAS。
  - 2026-11-10补充：候选已记录可见挂牌文本字段的原文片段/偏移和`not_calibrated`状态；人工更正相应出处改为`manual_review`，解析器版本`generic-labelled-v0.2.25`。解析器、候选修正、评估器和样本清单专项120 passed；全量离线pytest 256 passed、13项数据库集成跳过。使用本机uv缓存依赖，未联网安装。临时PG16本地socket绑定受沙箱拒绝；真实获准样本和准确率仍缺。
  - 2026-11-10补充：解析器选择非空`<main>`/`<article>`优先于早出现的通用`.content`，新增导航容器与空main回归，版本`generic-labelled-v0.2.24`；本机依赖缺失未运行pytest。
  - 2026-11-10补充：新增`beike.py`/`anjuke.py`入口与统一分发，API采集、解析评估及负载测试按source路由；当前仍调用通用保守解析器，真实样本校准/准确率未完成。编译及桩化路由smoke通过。
  - 2026-11-10补充：添加标注为synthetic的贝壳已下架页、安居客缺字段页fixture及不臆造字段/未知ID的站点入口回归；语法编译通过，pytest未运行。
  - 2026-11-10补充：canonical冲突测试的解析器版本断言改用`PARSER_VERSION`常量，避免版本升级后遗留`.2.23`造成必然失败；语法编译通过，pytest未执行。
  - 2026-11-10补充：来源入口重构后审计出3处测试仍调用旧解析函数名，以及HTTP客户端从旧模块导入共享URL校验；已统一入口/导入并拆出站点ID提取。Python 3.12语法编译及桩化smoke 8项通过；缺少pytest/BeautifulSoup，fixture解析未运行。真实样本及准确率仍缺。
  - 2026-11-10补充：PG16 DB集成复现候选重提SQL中未转义`%`导致psycopg占位符解析失败；改为`%%`并更新构造断言。临时PG16隔离库完整pytest 264 passed、0 skipped；真实V0.1备份及获准样本仍缺。
  - 2026-11-10补充：NAS只读核对确认生产API/DB/Worker健康、业务表为空且来源OFF；NAS旧版`collection_service.py`哈希不同，本地SQL修复尚未部署。本轮无NAS写入。
  - 2026-11-10补充：解析器将0至20作为卧室数输出范围；`21室`等超范围值留空并告警`invalid_bedrooms_mentions`，版本`generic-labelled-v0.2.10`。仅离线回归，真实样本仍缺。
  - 2026-11-10补充：URL来源ID最长按正式模型220字符处理；超长ID留空、不能使候选ready，样本人工ID标签也拒绝超长。解析器版本`generic-labelled-v0.2.11`，相关离线测试62 passed；真实页面准确率仍未验证。
  - 2026-11-10补充：解析器排除语义`aside`、HTML隐藏属性、`aria-hidden=true`及内联`display:none`内容，避免可识别的推荐/隐藏报价污染详情候选；规则版本为`generic-labelled-v0.2.3`，专项18 passed。外部CSS、真实布局与准确率仍待获准样本验收。
  - 2026-11-10补充：内联`display`按声明顺序及`!important`优先级判断最终值，避免把`display:none;display:block`的可见详情误删；版本为`generic-labelled-v0.2.5`，解析器专项24 passed。外部样式表、真实布局和字段准确率仍待获准样本。
  - 2026-11-10补充：楼盘详情同时显示建筑面积与套内/使用面积时，通用`面积`标签曾把后两者当成建筑面积冲突并清空字段。新增复现后以固定宽度负向前瞻排除“使用/套内/室内/公摊/占地/赠送面积”；建筑面积保留120㎡且候选可进入人工复核。解析器版本`generic-labelled-v0.2.28`。解析器/样本/评估专项121 passed，全量pytest 268 passed、13项数据库集成因未设置TEST_DATABASE_URL跳过。仅离线合成输入验证，真实页面准确率仍待每站20份获准样本。
  - 2026-11-10补充：非空但只有加载提示的`<main>`曾遮蔽后续包含挂牌字段的`<article>`；新增失败回归后，现按小区/面积/总价三类明确标签的匹配数量选择语义根节点，并在无信号或并列时按既有`main`→`article`→内容类顺序回退。解析器版本`generic-labelled-v0.2.29`。解析器/样本/评估专项122 passed，全量pytest 269 passed、13项数据库集成因无`TEST_DATABASE_URL`跳过。仅合成页面验证，不代表真实页面准确率；20+20获准样本仍缺。
  - 2026-11-10补充：多报价场景评估此前只检查asking_price为空和multiple_price_mentions告警，人工price_candidates_wan错误时仍会报通过。现将解析证据候选值与人工标注按Decimal数值集合精确对账，并要求证据未截断；不匹配、缺失或超过20条截断均判失败。解析评估器回归先失败后通过，评估器专项16 passed，全量pytest 271 passed、13项数据库集成因未设置TEST_DATABASE_URL跳过。此修改提高离线指标可信度，不替代获准页面准确率。
  - 2026-11-10补充：户型/区域/楼层/装修多值场景此前只检查解析字段置空及warning，解析器候选完全错误仍可能通过。样本清单新增`bedroom_candidates`、`district_candidates`、`floor_candidates`、`decoration_candidates`四列；validator要求对应tag下至少两个有效且不同候选，未标tag时不得填写。评估器逐字段将人工候选与`field_evidence`按Decimal/规范化文本集合比较，证据缺失、值不符或20条上限截断均失败。增加候选不符、重复候选、缺标签及截断回归。parser-evaluation/sample-set专项51 passed，全量pytest 275 passed、13项数据库集成因未设置TEST_DATABASE_URL跳过。仅合成数据验证，不替代真实获准样本准确率。
  - 2026-11-10补充：小区标签过去仅允许行首/空白作为前置边界；不带空格的竖线、分号、斜线等紧凑分隔会使小区名漏提。现接受常见中文/ASCII标点边界，仍要求明确“小区/所在小区/小区名称”标签和冒号，不从无标签文本猜小区。版本`generic-labelled-v0.2.30`。parser/sample/evaluator专项129 passed，全量pytest 276 passed、13项数据库集成因无TEST_DATABASE_URL跳过。仅合成离线HTML，真实站点准确率仍待20+20获准样本。
  - 2026-11-10补充：紧凑分隔符既可能位于小区标签前，也可能位于小区值后；仅扩展前置边界会让`东湖花园|建筑面积...`整段被捕获成小区名。现常见标点同时作为标签边界和值终止符，解析器版本`generic-labelled-v0.2.31`。新增值后紧邻竖线/斜线回归；parser/sample/evaluator专项130 passed，全量pytest 277 passed、13项数据库集成跳过。仅合成HTML离线验证，真实页面准确率仍未验证。
  - 2026-11-10补充：楼层、装修自由文本值原先只在空白/逗号/分号终止，紧凑`|`、`/`、冒号等分隔会把后续字段吞入候选，导致值错误或歧义。现使用文本字段终止符在常见标点处停止；小区字段沿用此前标签边界/值终止规则，同时保留社区名中的括号。新增楼层+装修紧凑分隔回归。解析器版本`generic-labelled-v0.2.32`。parser/sample/evaluator专项131 passed，全量pytest 278 passed、13项数据库集成因未设置TEST_DATABASE_URL跳过。仅合成离线验证，真实页面准确率仍待20+20获准样本。
- [in_progress] **P0-04 在线采集可行性及政策核验**：2026-11-12贝壳官方协议已更新为2026-11-11更新、2026-11-12生效；仍要求书面许可、限制自动化获取，并要求已授权使用遵守许可范围和Robots。安居客官方协议中心显示消费者/经营者协议及历史版本目录，但正文未能读取；已找到的经营者协议不替代消费者协议，官方静态PDF无法对应当前版本。网页工具本轮无法读取项目实际目标主机robots正文；2026-11-10 NAS读取结果仅为历史快照（贝壳项目UA目标路径禁止，安居客示例路径允许），不据此推断现状。两站均无本项目书面许可；来源和全局在线采集保持OFF。未访问房源页、未采集或绕过页面限制。验收仍需书面用途许可、确认适用协议并在获准后复核目标Robots。采集器挑战页门禁及许可复核逻辑已实现；许可申请模板已准备，未发送。
  - 2026-11-11补充：HTTP客户端页面与robots响应从完整缓冲改为64 KB分块有界读取（上限分别1 MB/256 KB）；8 MB模拟流确认超限即停止读取。全量离线374 passed、14项数据库集成跳过。未联网/部署，许可审核未改变。
  - 2026-11-10补充：执行采集任务重读并`FOR SHARE`锁定source_registry最新策略至抓取/暂存完成；离线服务回归覆盖领取后撤销阻断及批准正向流程。新增双连接PostgreSQL锁集成用例，但当前无`TEST_DATABASE_URL`而跳过。服务/模型/策略专项19 passed，全量328 passed/14项DB集成跳过；未联网、来源保持OFF。
- [x] **P0-05 完整数据库API集成测试**：NAS隔离PostgreSQL 17专用测试库运行数据库集成用例7项全部通过，覆盖索引与汇总迁移幂等/回填、候选审批事务回滚/幂等、健康触发器插入/更新/删除及挂牌观察时间回退/来源迁移、历史价格保护、通知去重和连接错误脱敏。另完成10k run/10k candidate批量触发器一致性验证。隔离资源已清理；未迁移或写入生产库。
  - 2026-11-10本轮完整套件在一次性本机PostgreSQL 16 `rehouse_test`中144 passed、0 skipped；只监听Unix socket，测试后已停止并清理。该结果不替代NAS PostgreSQL 17/生产部署验收。
- [ ] **P0-06 DTK联调**：在NAS单独启动DTK，检查作者ID、接口版本/权限，连续监控至少3个有权限的抖音账号24小时。`app/dtk.py`离线增强了上游响应结构校验和异常类型处理；`app/worker.py`遇到`has_more=true`却无游标时记录`partial`而非误报成功。以上本机逻辑仍不代表真实版本/权限验证或账号联调。
  - 2026-11-10补充：修复AccountIn中大小写敏感`startswith("http")`导致的大写HTTPS域名校验绕过；并拒绝userinfo、非443端口和控制字符。模型/DTK专项74 passed，全量331 passed/14项数据库集成跳过；真实DTK版本/权限/账号联调仍待完成。
  - 2026-11-10补充：AccountIn对通过校验的Douyin主页URL移除query/fragment，避免将分享跟踪参数存入account_ref或转交DTK；模型/DTK专项75 passed，全量332 passed/14项数据库集成跳过。真实DTK联调仍待完成。
  - 2026-11-10补充：修复账户模型接受的大写HTTPS scheme被DTK客户端误当作`sec_user_id`；适配器现以大小写不敏感方式识别scheme。DTK/Worker/模型专项66 passed，全量离线261 passed/13项DB集成跳过；真实DTK联调仍待完成。
  - 2026-11-10补充：DTK页含下一游标但省略`has_more`时由游标推断继续分页；明确`has_more=false`仍优先停止。专项68 passed，全量离线263 passed/13项DB集成跳过；真实DTK响应协议仍未验证。
  - 2026-11-10补充：空白游标（空格/Tab）现在显式失败，避免把无效令牌传给DTK；数值0游标仍保留为`"0"`。DTK/Worker/模型专项71 passed，全量离线266 passed/13项DB集成跳过；真实响应字段规范仍待联调。
  - 2026-11-10补充：metadata的空字符串`next`作为无游标终止值；纯空白（空格/Tab）仍拒绝。专项72 passed，全量离线267 passed、13项DB集成跳过；真实DTK协议尚未核实。
  - 2026-11-10补充：分享URL在`urlsplit`前拒绝内部空格、Tab与C1控制字符，无效链接回退canonical；专项56 passed，全量240 passed、13项PostgreSQL集成跳过。仅本机验证，真实DTK/账号联调仍待完成。
  - 2026-11-10复核：原始输入中首尾Tab/换行等C0也会先被strip清除；现C0/C1均在裁剪前拒绝，普通首尾空格兼容。6个直接smoke通过；本机缺依赖未运行pytest。
  - 2026-11-10复核修正：`str.strip()`会先移除首尾U+0085，导致尾部C1用例与实现不一致；现先拒绝原始输入的C1，再裁剪普通首尾空格。5个直接smoke通过；全量pytest未能在当前依赖缺失环境运行，前序240 passed记录不作为本轮复验。
  - 2026-11-10补充：异步任务轮询遇到缺失/空白/非字符串`state`时立即结构失败，失败详情不回显上游内容；DTK专项30 passed。真实接口状态语义、NAS版本/权限和3个获准账号24小时联调仍未验证。
- [in_progress] **P0-07 运营指标**：`GET /api/collection/health`按来源返回成功/失败/阻断、候选审核状态、挂牌数量、最近尝试/成功/观察时间、最新状态/原因、双重在线开关和四项累计率。用户已确认分母/阻断口径，迁移010以追加式解析记录维护解析率与字段完整率；迁移011拒绝解析明细UPDATE/DELETE/TRUNCATE，保护累计计数，API派生百分比且分母为0返回null。NAS隔离PG17已执行001–010并重跑；扩展后的V0.2基线集成回归覆盖旧挂牌/采集/条件单及新增发现/观察/核验/解析数据，当前完整`tests/test_db_integration.py`在隔离PG17.11为24 passed（含新增迁移011账本保护），测试schema残留0且临时资源已清理。NAS隔离PG17.11按001–011运行且重复011成功；运行时确认UPDATE/DELETE/TRUNCATE均被拒，明细及1/1/1汇总不变，临时资源已清理。完整数据库集成文件现已在隔离PG17.11运行24 passed。生产只读核验仍显示006–011相关对象缺失、运行代码与工作区不同；生产迁移/API部署未完成。
  - 采集成功率=`success/(success+failed)`，blocked排除；解析成功率=`parse_success/parse_attempt`；字段完整率=四项必需字段（来源挂牌ID、小区、总价、面积）完整的成功解析结果/成功解析结果；审核通过率=`approved/(approved+rejected)`，pending排除。解析率同时统计手动HTML和在线采集进入解析器的页面。
- [verified_on_NAS] **P0-08 容灾/安全**：NAS备份恢复、日志脱敏、内网控制与隔离负载/容量边界验收已完成。2026-11-11已运行当前`backup.sh`在NAS新建备份，并在断网、tmpfs、无宿主端口/挂载的临时PG17中完整恢复；哈希与700/600权限通过。用户确认数据库备份保留90天、原始页面证据随关联记录保留。工作区只读留存工具会列出超期候选但不自动删除；NAS只读复核中旧版函数返回90天外备份候选0个/0字节，库存37文件/1,123,531字节。raw-pages只能经API容器只读挂载统计为2个文件/249字节。NAS报告脚本与工作区哈希不同，逐路径版尚未同步/复验；本轮无清理。合成负载不等于生产容量SLO。
  - 2026-11-10补充：留存报告新增稳定排序的超期文件相对路径输出；12项专测通过，仍不自动删除。该更新尚未同步NAS。
- 2026-11-10补充：`storage_report.py --check-evidence-references`只读对比内容寻址raw-pages与`collection_candidates.raw_storage_path`，报告孤立文件及缺失文件，不自动删除；需数据库连接权限才能运行。当前仅本地验证，尚未同步NAS。
- 2026-11-10补充：HTTP 200验证码/反爬挑战已增加fail-closed识别，归类`blocked_upstream`；全量回归54 passed、7 skipped；NAS Worker-only部署后容器内源码哈希及检测函数通过，来源OFF、启用目标0。
- [in_progress] **P0-09 区域/小区房源链接发现器**（依赖P0-04）：按许可范围发现详情URL、分页去重并追踪错误；在线未获批准时保持禁用。已实现通用发现器、每轮最多5个列表页/20个详情页、数据库持久游标/已见ID与阻断暂停；详情页只进入候选审核。
  - 2026-11-12最新本机全量离线套件为 **1077 passed、27 skipped、27 subtests passed**；随后NAS隔离PostgreSQL 17.11完整数据库集成 **28 passed**，覆盖迁移001–014与详情队列级联/幂等行为。
  - 2026-11-12只读核对NAS：API/Worker运行、PostgreSQL 17 healthy、healthz=200，但正式Compose仍只挂载001–005，工作区006–014未部署。真实来源许可、获准列表/详情页及真实分页准确性仍缺；在线采集保持关闭，P0-09不能宣称完成。
  - 首次/最近列表页观察记录已由007及认证只读API实现。用户已确认连续2次完整分页遍历未见后转`pending_review`、不自动下架；人工结论只记录并保留历史，不修改正式挂牌状态，相关回归已覆盖。迁移012活动扫轮恢复、累计100,000条以上去重路径，以及迁移014详情队列均由2026-11-12隔离PG17完整数据库集成覆盖并通过；站点专用列表选择器仍待获准样本确认。
  - 2026-11-11补充：新增数据库集成回归覆盖一页内详情部分暂存后策略撤销、seen ID/当前页游标真实落库及许可恢复后跳过已完成详情；用例由mock替代HTTP。全量离线pytest 699 passed、17 skipped、13 subtests passed，新增用例因未配置`TEST_DATABASE_URL`而跳过，尚无该场景的PostgreSQL执行证据。用户暂无真实V0.1备份、获准页面/许可/人工标签，要求继续离线开发。
  - 同日后续：该断点用例在本机临时PostgreSQL 16通过；数据库集成文件18 passed，全量pytest 716 passed、0 skipped、13 subtests passed。临时DB为tmpfs、只绑定127.0.0.1，随机schema清理后数量为0；未触碰NAS/生产DB或网站。此证据不替代NAS PG17或真实页面许可验收。
  - 2026-11-11离线流程可靠性补充：CLI现先刷新JSON输出再保存seen IDs/next cursor；BrokenPipe/输出失败时保持旧状态，重跑同一页仍可交付链接。标准库状态/CLI测试15 passed。此项不替代数据库端游标和线上验收。
  - 2026-11-11离线诊断补充：state-file/HTML/seen-ID文件错误分别报告；缺失或非法seen-ID不再误称HTML读取失败，HTML UTF-8错误不回显样本文本。标准库状态/CLI测试16 passed；真实列表页和来源许可仍待用户材料。
- 2026-11-10 P0-08补充：新增安全的隔离闭环负载脚本；NAS隔离栈连续30分钟、4并发完成10,199工作流/61,194请求、0错误，候选/挂牌/价格历史对账一致。仅合成数据，DB单核CPU成为压力边界；报告存于`docs/LOAD_TEST_2026-11-10.md`。该记录生成时留存期限待定，后续用户确认备份保留90天、页面证据随关联记录保留。2026-11-10补充NAS ACL安全：发现源码/Compose真实other写权限，已收紧项目源码/配置目录755、普通文件644；.env/data/backups仍为600/700/700，保护区外world-writable复查0，Compose config与API/Worker/DB健康通过，未重启容器。
- 2026-11-10 P0-08补充备份权限：NAS复核发现旧`worker.py`源码快照777，已改600；当前`source-snapshots`文件均600、目录700，数据库备份文件/目录600/700。

- 2026-11-10 P0-08只读刷新NAS备份库存：1.1MiB/29文件/6个一级子目录，`/volume3`可用405GiB、使用率56%；API/Worker运行、DB healthy、`/healthz`=200。该盘点当时留存期限待决定；用户随后确认备份90天、页面证据随关联记录保留。无自动清理，本轮未改动NAS数据。
- 2026-11-10 P0-04状态一致性修正：GOAL_STATE此前错误标记`verified_on_NAS`，与无项目书面许可/目标未完成的证据矛盾；现已改为`in_progress`。Robots核验不等于来源授权，在线仍OFF。
- 2026-11-10 P0-02/P0-03样本审计：`data/raw-pages/`仅有占位文件，`fixtures/`只有两份虚构演示HTML；无获准真实页面，因此不满足20+20样本回归，也不报告解析准确率。
- 2026-11-10 P0-01/P0-08桌面核验续：用户解锁Mac后，在UGREEN Docker详情页确认项目运行中、登记Compose路径正确，API、PostgreSQL 17、Worker均运行；nas-lan CLI独立复核API/Worker运行、DB healthy。此前锁屏待核验事项关闭；P0-01仍因无V0.1旧项目/数据库备份而blocked。P0-08留存期限已由用户确认：备份90天、页面证据随关联记录保留。

## P1｜房产情报能力
- [ ] FFmpeg抽音频/关键帧 + FunASR逐字稿 + RapidOCR画面文字（NAS低并发任务队列）。
- [ ] 解析宁波小区和别名、分期、楼栋，标注字段出处与置信度。
  - 2026-11-10补充：视频规则提示现记录字段、OCR/转写/标题/描述来源、精确匹配片段与字符偏移，并明确置信度未校准；只覆盖已有的面积、报价、户型、区域、小区提及，不代表分期/楼栋识别已完成。3条直接断言与compileall通过；pytest依赖缺失、未连接NAS，未用真实视频评估。
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
  - 2026-11-10补充：可比挂牌目标的户型未知时不再将`None==None`当作同户型，防止缺少户型的挂牌生成误导性中位数折价；全量345 passed/14项数据库用例跳过，本机修复未部署NAS。
  - 2026-11-11补充：同户型可比面积差10%阈值改为Decimal相对差、以目标面积为分母；±10%边界纳入、±10.01%排除，修复+10% float边界误排而−10%边界能纳入的不对称。专项16 passed、全量349 passed/14项数据库集成跳过，未部署NAS。
- [x] 跨平台疑似同套报价差异“待核实”提示：仅比较贝壳/安居客不同来源、同小区同户型、面积差`abs(a-b)/min(a,b)≤5%`（较小面积为分母）的挂牌；单价差≥10%按低价为分母生成候选，绝不自动确认同套。本机离线回归通过，NAS验收待连接恢复。
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
- 2026-11-10经`notedock-nas`只读复核：当前90天外备份0个/0字节，raw-pages仅两个占位文件/249字节，候选表0行。NAS的storage_report仍是旧汇总版；本地逐路径列报版尚未同步，`sheng`执行报告时因raw-pages目录权限不足显式失败。本机storage_report专项12 passed，无NAS权限变更或清理。


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



## 2026-11-10 P0-02/P0-03小区歧义标注约束补全
- `community_candidates`重复候选与缺少`multiple_communities`标签的validator测试现已覆盖；人工标注文档列全小区多值场景。parser/样本/评估专项138 passed，全量离线285 passed、13项DB集成因缺`TEST_DATABASE_URL`跳过。未获得真实样本或准确率证据。


## 2026-11-10 P0-03解析精确率验收门槛显式化
- 评估报告按字段输出95%抽取精确率目标与达标标志，覆盖率和正式样本数门槛独立；19/20边界达标、18/20不达标。评估/样本专项59 passed，全量离线287 passed、13项数据库集成跳过。真实指标尚待获准页面验证。


## 2026-11-10 P0-03建筑面积冲突样本对账
- 将解析器已有的`multiple_area_mentions`纳入`multiple_areas`标注和评估；候选以Decimal数值对账并校验(0, 20000]㎡，缺失/不匹配/截断证据不通过。专项148 passed、全量离线295 passed/13项数据库集成跳过。仅合成离线验证，真实准确率待获准样本。


## 2026-11-10 P0-03来源ID冲突样本场景
- URL与canonical/og:url ID冲突现在可通过`source_id_conflict`和`source_listing_id_candidates`人工标注；不选定来源ID。评估器对账完整ID证据并拒绝截断。专项154 passed，全量离线301 passed、13项DB集成跳过。真实样本尚缺。


## 2026-11-10 P0-03越界户型候选证据保留
- 分离户型原始候选校验与最终人工标签范围：候选允许0–99整数以保留21室等页面原文冲突，最终值仍为0–20。专项75 passed，全量离线303 passed/13项数据库集成跳过；真实页面尚未验证。


## 2026-11-10 P0-03单值越界户型拒绝验收
- 单个21–99室值由`invalid_bedrooms`单独记录，验证置空、warning及证据一致；与多值户型场景互斥。最终人工户型仍限0–20。专项83 passed，全量离线311 passed、13项数据库集成跳过；真实样本仍缺。


## 2026-11-10 P0-03数值候选千分位一致性
- validator/evaluator共享严格千分位语法语义；合法分组面积/报价按数值对账，畸形分组拒绝。专项169 passed，全量316 passed、13项DB集成跳过。仅合成数据验证。


## 2026-11-10 P0-03统一千分位语法来源
- parser、样本validator和evaluator共用parser模块的`NUMERIC_TEXT_PATTERN`，避免规则副本漂移。专项169 passed，全量316 passed、13项DB集成跳过；真实页面格式仍待验证。


## 2026-11-10 P0-03千分位跨格式数值等值回归
- 验证页面千分位与人工不带逗号候选的数值对账；等值重复候选被拒，页面等值写法不再误报冲突。专项171 passed，全量318 passed/13项数据库集成跳过。真实页面格式仍待样本验证。


### 2026-11-11 P0-01离线迁移原子性
- 001–005初始化/迁移脚本统一由文件自身管理事务；手动升级命令保留`ON_ERROR_STOP=1`且不再增加`--single-transaction`。
- 静态契约断言、Python编译与Compose配置解析通过；pytest及PostgreSQL运行时验收未执行。此项降低新库初始化与手动升级事务行为不一致风险，但不解除缺少V0.1真实备份的阻塞。


### 2026-11-11 P0-09限制seen-ids读取
- 本地发现CLI对`--seen-ids`文本最多读取2,000,000字节并严格解码UTF-8，防止任意大文件被无界载入内存。
- 标准库发现状态/CLI测试12 passed；pytest与BeautifulSoup解析套件未运行。该改动只完善离线工具边界，不改变P0-09仍依赖许可和真实样本的验收状态。


### 2026-11-11 P0-01锁定事务文件与初始化顺序
- 回归现在检查001–005各自只有一条独立事务边界，并确认Compose初始化挂载顺序与迁移顺序一致；避免误改为嵌套包装或漏挂载。
- 3项标准库静态检查通过；实际PostgreSQL迁移/回滚仍待测试环境与V0.1备份。


### 2026-11-11 P0-09拒绝特殊文件作为seen-ids来源
- `--seen-ids`拒绝FIFO等非普通文件，防止CLI在无数据写入端时无限等待；2 MB大小限制和UTF-8校验继续生效。
- 标准库状态/CLI测试13 passed。未运行pytest/解析套件；P0-09仍依赖获准真实列表页及来源范围。


### 2026-11-11 P0-09校验已发现ID清单
- `--seen-ids`与来源适配器ID约束一致：贝壳8–220位数字，安居客7–220位数字；空行/重复ID规范化处理，非法值整份拒绝。
- 标准库状态/CLI测试14 passed。真实列表页面与许可范围仍未提供。


### 2026-11-11 P0-08备份前校验证据目录
- `backup.sh`现在拒绝将`raw-pages`符号链接打包，避免备份看似成功但漏掉实际证据文件。两个标准库回归通过（真实目录与符号链接）。
- NAS旧备份恢复证据仍对应之前版本；最新脚本未同步或实机执行，P0-08当前工作区状态调整为`in_progress`，须重验后再恢复NAS验收状态。


### 2026-11-11 P0-08隔离验证备份脚本完整交付
- 使用假Docker入口和临时本地文件验证备份成功与raw-pages符号链接失败两条完整脚本路径；成功产物目录/文件权限、归档内容、SHA256清单和临时目录发布/清理均核对。数据库dump及`pg_restore`为模拟，不作为数据库恢复证明。
- 18项标准库测试通过；未连接NAS。修改版本仍须在NAS执行新鲜备份并恢复隔离库后才恢复`verified_on_NAS`。


### 2026-11-11 P0-01旧库数据下完整执行002–005
- 扩展合成V0.1数据库集成用例：旧记录插入后，002–005各自重复执行两次，核对11张V0.1业务表字段、健康汇总历史挂牌回填及条件单新增列默认值。
- 只完成测试代码编译和静态审阅，当前没有可用PostgreSQL测试环境，未把该用例描述为通过；真实V0.1备份依然缺失。


### 2026-11-11 P0-08备份检查整棵证据目录
- `backup.sh`现拒绝raw-pages目录树中任一符号链接，并在遍历/检查失败时中止，避免tar只保存链接元数据。
- 假Docker完整流程以真实本地find/tar验证嵌套链接拒绝和无半成品；标准库测试总计19 passed。NAS验收待执行。


### 2026-11-11 P0-01迁移静态契约纳入stdlib回归
- 迁移事务边界、手动升级包装和Compose初始化顺序检查现可通过`unittest discover -p '*_stdlib.py'`运行。标准库测试22 passed。
- PostgreSQL 16单用户路径在`initdb`阶段仍遇系统共享内存`shmget`限制；没有运行SQL。真实V0.1备份缺失依旧阻止正式迁移验收。


## 2026-11-11 机会查询连接生命周期修复
- 修复机会API读取价格历史时数据库连接已关闭的问题；候选更正集成测试断言与当前PATCH响应契约一致。
- 隔离PG16全量测试574 passed、12 subtests passed；无数据库URL离线测试560 passed、14 skipped、12 subtests passed。仅本地/临时隔离验证，未部署NAS；真实V0.1备份、许可样本和线上验收缺口不变。


## 2026-11-11 P0-08 NAS通道重新核验
- Tailscale CLI无法加载偏好且官方App未安装；LAN别名与已授权公网OpenSSH别名均超时。没有NAS读写或部署。当前工作区新版备份脚本仍待NAS端同步和实机复验。
- P0-07健康率口径已由用户确认并在本机PG16实现；NAS PG17/当前生产代码验收仍待完成。P0-01旧库备份、P0-02获准样本仍缺。

## 2026-11-11 P0-04 官方协议版本复核
- 贝壳最新官网协议日期及相关限制已复核；安居客官方静态PDF确认标示2021年5月更新，但当前有效版本对应关系未确认。宁波目标Robots只沿用11-10 NAS读取证据，网页工具未取得新文本。
- 两来源无本项目书面许可，在线保持OFF；P0-04继续等待正式授权与适用协议确认。

## 2026-11-12 P0-04 官方协议与来源门禁复核
- 贝壳协议标示2026-11-11更新、2026-11-12生效；安居客协议中心目录可见但正文未解析，现有静态PDF无法确认对应当前版本。官方协议入口和核验边界详见`docs/SOURCE_POLICY_REVIEW_2026-11-10.md`。
- 本轮网页工具无法读取两宁波目标主机robots正文；11-10 NAS只读结果仅为历史快照。没有本项目书面许可，两个来源及全局在线采集保持OFF；未访问房源页、未采集或绕过页面限制。
- 仅同步政策证据与项目状态，无应用代码、数据库、NAS或部署变更。P0-04仍`in_progress`。

## 2026-11-11 P0-08 NAS只读连接续核
- `notedock-nas`首次只读命令确认SSH身份`DXP4800/sheng`、Compose服务db/api/worker、PG数据卷`ningbo-re-ai_pgdata`，以及`backups/`权限700和顶层7个归档文件。库存命令没有展开子目录，不能据此判断数据库备份是否存在；宿主机身份不能读取`data/raw-pages`。
- 随后的SSH复用连接受本机控制套接字权限限制，公网主机名解析失败；未继续远端操作，没有备份、传输或部署。新版备份/留存脚本仍待实机复验。
- 离线开发环境缺少`bs4`，本轮未运行解析器测试且未改解析器。P0-03仍需获准真实样本与人工标签校准；此阻塞不由合成回归解除。

## 2026-11-11 P0-08核验原始证据内容哈希
- 增加只读`--check-evidence-integrity`，按文件名中的SHA-256校验gzip解压内容，列出坏压缩流或内容不匹配的证据路径；全程流式读取，不自动改名或删除。
- 标准库合成回归3 passed；未安装pytest/bs4，未运行完整套件。没有读取NAS证据，P0-08仍需新版工具在NAS执行并复核，真实V0.1升级仍缺备份。

## 2026-11-11 P0-08拒绝危险备份根目录
- `backup.sh`现在在任何目录创建、权限修改或Docker调用前，拒绝`/`、`.`、`..`、当前项目目录及包含项目工作目录的祖先目录，防止误将系统/项目根目录改为700。
- 隔离失败回归覆盖绝对根、项目根、项目父目录和`.`/`..`；全部stdlib测试33 passed。仍未在NAS执行，既有NAS备份恢复证据不代表当前版本已验收。

### P0-08证据权限错误不再误报为内容损坏
- 流式完整性检查现仅将gzip格式/CRC错误、EOF和zlib解码错误列为证据损坏；文件不可读或系统I/O异常向调用者传播，并由CLI明确报错。
- 新增权限错误传播回归；全部标准库测试34 passed。未访问NAS，完整pytest仍未运行。

## 2026-11-11 离线完整回归环境恢复
- 找到本机缓存Python 3.12测试环境，在不联网安装依赖的情况下完成当前工作区完整pytest：651 passed、15项数据库集成跳过、13 subtests passed；15项跳过原因是未设置隔离`TEST_DATABASE_URL`。
- 深层合成页面2,000–8,000层解析探针均通过。恢复了P0-03合成回归能力，但真实页面/标签及来源许可仍未提供，准确率和NAS状态不变。

## 2026-11-11 P0-09显式报告重试状态未保存
- 本地快照失败后，如果原子state写入失败，CLI现在会在原始失败诊断后明确报告重试状态未保存；state函数返回保存成功标志。
- 标准库CLI/状态定向21 passed，完整离线pytest 653 passed/15项数据库集成跳过/13 subtests passed。未联网、未部署；真实列表页、来源许可和Worker自动分页仍缺。

### P0-09无state文件路径的失败记录契约
- `record_failure`在无保存路径时不再因`None`文件对象触发未处理异常；仍记录内存失败状态并返回未保存，CLI可明确告知未持久化。
- 状态/CLI定向22 passed，全量离线pytest654 passed/15项数据库集成跳过/13 subtests passed。未部署；P0-09外部验收缺口不变。

## 2026-11-11 P0-03/P0-09输入字节限额前置
- 在parser/discovery UTF-8编码前增加字符数上限判断，避免超大字符串先产生等量编码分配；保留UTF-8字节数门槛以拒绝限额内字符数但字节数超限的多字节内容。
- encode探针回归确认拒绝顺序；解析器/发现器206 passed，全量离线656 passed/15项数据库集成跳过/13 subtests passed。真实样本准确率与来源许可不变。

### P0-08规范化后根目录别名保护
- `BACKUP_ROOT`现检查物理规范化后的目录；像`/tmp/..`这样的别名指向文件系统根时，在副作用前失败。
- 危险路径假命令回归与stdlib全套37 passed，全量pytest656 passed/15项DB集成跳过/13 subtests passed。未在NAS实机验证。

### P0-08根目录规范化别名保护
- 对`cd -P`后的`BACKUP_ROOT`再次拒绝文件系统根，堵住`/tmp/..`等字面值不等于`/`的路径别名；保护发生在任何副作用之前。
- 假命令危险路径回归通过，stdlib37 passed；完整pytest656 passed/15项DB集成跳过/13 subtests passed。NAS实机复验待连接恢复。

### P0-08拒绝符号链接祖先路径
- 备份前检查最接近的已有目录祖先，逻辑/物理路径不一致则在任何副作用前拒绝，避免经中间符号链接重定向chmod或备份目标。
- 备份脚本专测8 passed，stdlib37 passed；完整pytest656 passed/15项DB集成跳过/13 subtests passed。NAS实机复验仍待连接恢复。

## 2026-11-11 P0-09排除菜单导航链接
- 发现器现在跳过`<menu>`子树内的详情链接，避免导航项混入候选；主列表链接继续保留。回归先失败后通过，发现器专项**13 passed**。
- 完整离线pytest **657 passed、15 skipped、13 subtests passed**，标准库测试**37 passed**；15项数据库集成因未设置`TEST_DATABASE_URL`跳过。
- 用户确认当前没有V0.1备份、获准真实页面/许可或人工标签，继续离线开发。没有访问网站、连接/写入NAS或部署。P0-09仍为todo，需获准真实分页样本和Worker自动分页验收。

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


## 2026-11-11 P0-08备份路径父目录遍历保护
- `backup.sh`拒绝`BACKUP_ROOT`中的`..`路径组件，封堵缺失中间目录加`..`解析到项目/父目录、从而触发错误`chmod`的路径。
- 临时路径回归、备份脚本专项9 passed、stdlib39 passed、完整离线pytest670 passed/16项数据库集成跳过/13 subtests passed。仅本机验证，NAS新版备份与隔离恢复未复验。


## 2026-11-11目标模式交接状态校准
- 更新`prompts/NEXT_ITERATION.md`，消除其P0状态、解析器版本和测试结果与GOAL_STATE的不一致；明确真实样本、许可和数据库环境缺失时可继续的离线工作与验收边界。
- 核验未改变目标状态/用户决策；无应用代码、数据库或NAS变更。


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

## 2026-11-11 P0-09连续缺失转人工核验（阈值已确认）
- 按用户确认的规则，同一采集目标连续2次完整分页遍历未见挂牌后转`pending_review`，不自动下架。失败、阻断、上限、分页回环或歧义的轮次不计数；重新观察清零缺失计数，但不自动清除已排队状态。
- 迁移007/008、Worker状态流、只读观察API和集成回归已写入；标准库测试42 passed，compileall/静态检查通过。当前环境无pytest，SQL及新增PostgreSQL集成未运行，故仅标记离线实现，数据库验证待补。
- 未访问来源网站、NAS或生产数据库，未部署。继续保持在线采集关闭；真实获准分页样本、隔离PG17及生产代码差异仍待验收。

## 2026-11-11 P0-09补齐完整扫描计数边界回归
- 新增数据库集成回归锁定页数上限、列表页失败、许可阻断均不计缺失扫描；只有恢复并完成当前分页遍历才递增一次。
- “两次完整缺失”用例现预置正式`available`挂牌，确认转`pending_review`后挂牌仍为`available`，无自动下架。
- 新用例经Python编译检查；标准库42 passed。pytest/项目依赖不可用，Docker socket permission denied，PostgreSQL集成未运行；未访问NAS/网站或部署。

## 2026-11-11 P0-09保持列表DOM顺序并通过PG16全量回归
- 发现器修复为按HTML DOM顺序返回详情链接；此前遍历栈反向入栈时同步追加锚点，导致返回顺序倒置，可能改变20条详情上限内先处理的房源。策略撤销Mock夹具依页面顺序重排。
- 数据库集成20 passed，全量pytest739 passed、0 skipped、15 subtests passed；发现器专项19 passed、采集服务+发现器47 passed、标准库42 passed。新增测试证明不完整遍历不计缺失且正式available挂牌在转人工核验后不自动下架。
- 使用本机临时PostgreSQL 16、tmpfs、临时Docker网络和127.0.0.1端口；资源已清理。不是NAS PG17或生产验收；未访问网站/NAS，未部署。


## 2026-11-11 P0-07 NAS隔离PostgreSQL 17集成验证
- 当前工作区源码只读挂载，在NAS内部Docker网络与tmpfs PostgreSQL 17测试库运行`tests/test_db_integration.py`：**22 passed**。测试schema残留0。
- 自动清理后确认临时容器、网络、归档和解压目录均已移除；不涉及生产库、持久卷或部署。生产迁移010与API版本差异仍待备份后单独评估。


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

## 当前目标模式交接（2026-11-12）
- P0-03继续做计数驱动的离线解析器审查；最近修复使已选候选文本只归一化一次。
- 真实准确率评估仍以每站20份获准HTML及人工标签为前置条件；现无材料，在线采集保持关闭。
- P0-01真实V0.1备份、P0-02许可/标签与P0-09来源及生产差异验收仍未完成。

## 当前目标模式交接（2026-11-12续）
- P0-03继续离线解析器审查；候选根评分窗口已与字段提取的35,000字符截断窗口一致，避免长前缀下选错根。
- 真实准确率评估仍依赖每站20份获准HTML和人工标签；材料未到前不启用在线采集。

## 当前目标模式交接（2026-11-12边界复核）
- P0-03评分/提取共用35,000字符窗口；精确边界回归锁定恰好到限与超限1字符两种结果。
- 下一轮复核截断点附近的字段证据和评估器场景；真实样本仍待授权页面及人工标注。

## 当前目标模式交接（2026-11-12证据边界复核）
- 字段证据偏移限制在解析器实际使用的35,000字符窗口内；截断后未扫描的冲突不会被计作已扫描，截断告警仍阻止审核就绪。
- 下一轮检查离线样本评估器对截断场景的判分边界。

## 当前目标模式交接（2026-11-12评估器审阅）
- 样本评估器已拒绝把截断导致的缺字段、价格歧义和候选证据遗漏记为通过；本轮确认现有保护和对应回归，无需重复实现。
- 下一轮检查候选根评分遇到混合/歧义字段时的选择边界，并维持人工复核策略。

## 当前目标模式交接（2026-11-12候选根歧义复核）
- 混合推荐卡与详情article的必需字段冲突时，解析器保留歧义并留空，未以缩小子树消除冲突。
- 下一轮对候选根信号评分开展离线精确率/覆盖率场景审查；不得替代真实获准样本评估。

## 当前目标模式交接（2026-11-12跨根组合诊断）
- 跨兄弟区域字段可拼成完整候选的风险已复现，策略选择等待用户；不得默默偏好召回或精确率一种方案。
- 重叠根重复归一化在约800 KB合成页上测为约1.6 MB输入扫描；该测量是性能线索，不代表真实站点表现。

## 当前目标模式交接（2026-11-12有界文本归一化）
- 重叠候选根只保留归一化后的35,000字符前缀，减少长候选的重复归一化分配；Unicode差分与精确边界测试通过。
- 合成基准仅作实现比较，不代表真实站点SLO。跨根字段合并策略继续等待用户确认。

## 当前目标模式交接（2026-11-12归一化多形状基准）
- 有界归一化在大量短节点、长空白、重复段落合成页上未见显著耗时回退；性能收益主要出现在长连续文本/重叠根。
- 保持选根/字段语义不变，继续验证截断前缀的字符级等价。

## 当前目标模式交接（2026-11-12归一化内存边界）
- 合成分段DOM中有界归一化峰值内存略高0.14–0.29 MiB；长连续文本中节省更多，暂不增加复杂实现。
- 性能数据需在获准真实页面到位后复核，不能推断生产SLO。

## 当前目标模式交接（2026-11-12 body回退边界）
- body回退使用同一有界归一化，窗口外冲突不会冒充已扫描证据；截断告警保持审核阻断。
- 解析器333 passed、全量846 passed/22 skipped/23 subtests；真实准确率仍待许可样本。

## 当前目标模式交接（2026-11-12 Unicode归一化差分）
- 1,000组固定种子Unicode输入确认有界归一化前缀及截断状态与完整`re.sub`一致。
- 解析器334 passed，全量847 passed/22 skipped/23 subtests；跨根字段策略仍待确认。

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
## 2026-11-12 P0-03锁定零样本价格场景的空通过率
- 评估器回归已锁定贝壳/安居客在`oral_prices`与`transaction_prices`场景无样本时报告`samples=0`、`passed=0`、`pass_rate_pct=null`；不把空分母渲染成成功率。
- 评估器92 passed，全量离线pytest 988 passed/26 skipped/25 subtests；26项PostgreSQL集成因未设置`TEST_DATABASE_URL`跳过。当前验证只用合成HTML和临时清单，不构成真实页面准确率验收。
- 下一步继续P0-03离线边界审查；每站20份获准真实页面和人工标签到位后，再验收字段精确率/覆盖率。在线采集保持关闭。

## 2026-11-12 P0-03候选根挂牌价语义回归
- 增加“合同总价不计候选根挂牌价信号”的兄弟根回归，锁定错误金额不能压过明确挂牌价根；全量离线pytest 1061 passed、26 skipped、27 subtests passed。
- 仅测试变更。下一步继续P0-03离线边界审查；真实准确率验收依赖每站20份获准页面及人工标签。不得改变待确认的跨语义根字段合并策略。

## 2026-11-12 P0-03评分后续已知类内容根
- 增加失败回归并修复首个类容器无挂牌字段时漏查后续已知类根；解析器升至`generic-labelled-v0.2.127`，不改变跨语义根合并策略。
- 解析器464 passed，全量离线pytest 1065 passed、26 skipped、27 subtests passed。下一步继续P0-03离线边界审查；真实准确率验收仍依赖每站20份获准页面及人工标签。

## 2026-11-12 P0-04官方协议与Robots时点复核
- 贝壳当前协议显示2026-11-12生效并要求书面许可；安居客消费者协议正文尚未从官方协议中心读取。两站当前实际目标Robots未取得，本轮NAS请求在主机DNS解析阶段未发出，旧快照不作为当前证据。
- 未获许可，在线采集继续OFF。下一步取得平台书面范围许可并确认安居客消费者协议；获准后再读取目标Robots，不请求房源页。

## 2026-11-12 P0-09详情队列级联回归
- 增加PG集成用例锁定失败元数据持久化和挂牌观察删除时详情队列级联清理；全量离线pytest1065 passed、27 skipped、27 subtests passed。
- 数据库用例尚未运行（无`TEST_DATABASE_URL`）；迁移014仍需在授权的隔离PostgreSQL 17验证，不得以离线Mock替代。

## 2026-11-12 P0-09本机PostgreSQL替代路径复核
- 尝试在临时目录初始化本机PostgreSQL 16，以便评估无需后台daemon的单用户数据库验证；`initdb`在bootstrap阶段即因System V `shmget`共享内存限制失败，未建立数据库。initdb清理了数据文件，本轮生成的临时目录也已删除；未执行任何迁移。
- 全量pytest **1065 passed、27 skipped、27 subtests passed**；27项均因未设置`TEST_DATABASE_URL`跳过，包含详情队列级联回归。保留1条Starlette/httpx弃用警告。
- 迁移014真实PostgreSQL执行仍待隔离PG17环境；NAS源码传输/临时容器授权尚未得到答复。本轮未访问来源网站、NAS或生产数据库，无部署。


## 2026-11-12 P0-09队列状态分支静态复核
- 核对普通详情失败后的队列保留与跨轮重试、403/429中止、详情/页数上限游标、分页循环的`sweep_incomplete`处理；现有回归有对应覆盖，未发现可确认的新缺陷。
- 本轮pytest无法启动：系统Python缺少pytest，uv离线缓存读取被沙箱拒绝。最近既有全量结果为1071 passed/27 skipped/27 subtests；本轮未复跑，数据库集成未运行。
- 跨平台面积差≤5%以较小面积作分母已确认，当前实现符合。无代码或部署变化；迁移014仍待获准隔离PG17验证。


## 2026-11-12 P0-09全量离线回归复验
- 完整pytest **1071 passed、27 skipped、27 subtests passed**（11.98秒）；27项PostgreSQL集成因未配置`TEST_DATABASE_URL`跳过。队列和扫轮离线回归随套件通过。
- 本机Docker daemon拒绝访问；未向NAS传输源码或创建临时测试资源。迁移014仍需授权隔离PG17数据库验证。


## 2026-11-12 P0-09隔离PG17测试环境只读盘点
- `nas-lan`超时，Tailscale CLI无法读取偏好且应用未安装；以此前允许的`notedock-nas`核对到`DXP4800/sheng`及Docker组权限。
- NAS现有`postgres:17-alpine`和`python:3.12-slim`镜像；未发现名称匹配`rehouse`/`p009`的测试容器。此次无远端写入。
- 需要传输源码并创建内部网络/临时PG17容器才可执行迁移014集成测试；此权限尚未获准。


## 2026-11-12 P0-04补充取得安居客消费者协议正文
- 取得安居客官方域名《安居客用户服务协议》PDF正文。条款明确涉及Robots遵守、书面许可及抓取/商业利用限制；协议中心当前目录列有消费者协议和历史版本。
- 项目先前核读记录该PDF标示2021年5月更新；本次提取未呈现日期，也无法验证其与当前消费者协议/历史版本的对应关系，故P0-04仍未完成。两站均无本项目许可，在线保持OFF；未访问房源页或执行采集。


## 2026-11-12 P0-09迁移014 PostgreSQL 17隔离验收
- 用户授权后，通过`notedock-nas`把本轮源码快照传到NAS `/tmp`，本地与远端SHA-256一致；测试运行器使用只读源码/pytest依赖挂载，接入专用Docker internal网络中的PostgreSQL 17.11。PG数据目录为512 MiB tmpfs，无宿主端口、无持久卷。
- 完整`tests/test_db_integration.py`：**28 passed**。覆盖迁移001–014按顺序初始化和重复执行、V0.1/V0.2合成数据保留、详情队列查询、观察记录删除时外键级联，以及Worker部分失败/策略撤销后的持久队列恢复。随机测试schema清理后仅`public`。
- 首次运行暴露测试文件缺少`json`导入，并发现恢复顺序断言未跟随持久队列契约；补上导入并将断言调整为“先处理队列待办，再读取列表页完成扫轮”。修正后28项全部通过；未改应用运行逻辑。
- 本机全量pytest **1073 passed、27 skipped、27 subtests passed**；默认运行的27项数据库集成跳过，现已由PG17运行覆盖。保留1条Starlette/httpx弃用警告；Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。
- 已清理精确命名的测试容器、internal网络、源码和依赖暂存。NAS复核生产API/Worker仍运行、生产DB healthy；生产schema/业务数据、卷、Compose和服务未改，未迁移/部署，未访问房源网站。P0-09继续`in_progress`，真实来源许可与获准分页/详情样本仍是外部验收缺口。


## 2026-11-12 P0-06 DTK/Worker离线边界续审
- 复核DTK envelope与异步任务页、类型/页数/cursor门禁、任务轮询截止、分享URL主机和持久文本边界，以及Worker补采断点与失败恢复；没有找到新的可复现缺陷，未改应用代码。
- `tests/test_dtk.py tests/test_worker.py tests/test_account_history_backfill.py`：**85 passed**。同一工作区全量离线pytest **1073 passed、27 skipped、27 subtests passed**；隔离PG17.11数据库集成另为28 passed。
- P0-06仍待核实真实DTK版本/权限，并用至少3个获准账号连续运行24小时；没有真实账号或接口联调证据，不把Mock结果当作线上验收。


## 2026-11-12 P0-03阻止“挂牌售价”后缀价绕过限定语
- 失败回归复现`折后挂牌售价`会绕过限定词，因解析器从内部“售价”子串重新匹配；现在“售价”不允许紧接在`挂牌`之后匹配，由完整“挂牌售价”标签处理。
- 将新别名纳入全部非挂牌前缀/分隔符组合回归；价签限定语组合 **82 passed**，解析器 **496 passed**，全量pytest **1097 passed、27 skipped、27 subtests passed**。
- 仅合成HTML离线验证，无来源网站、NAS、数据库、迁移或部署操作。

## 2026-11-12 P0-03支持“售价/挂牌售价”标签
- 两来源4个合法售价标签回归修复前未被解析；加入`售价`和`挂牌售价`后正确写入挂牌总价。另扩展回归确认`成交售价`、`合同售价`按现有非挂牌限定规则排除。
- 价签/限定词专项 **82 passed**，解析器专项 **496 passed**，全量pytest **1097 passed、27 skipped、27 subtests passed**。仅合成HTML验证，真实样本准确率未验证。
- 未访问来源网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-03识别“装修情况/装修状况”标签
- 两来源4个合成回归复现完整标签“装修情况：精装”和“装修状况：简装”无法提取；现在支持两种标签，并同步用于文本边界识别。解析器版本`generic-labelled-v0.2.135`。
- 解析器专项 **488 passed**；全量pytest **1089 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未连接；真实页面准确率仍未验证。
- 未访问来源网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-03排除“总楼层”对挂牌楼层的污染
- 两来源4个合成回归复现总楼层被错抽或触发楼层冲突；现排除“总楼层”独立字段，并将其作为“所在楼层”值的终止边界，解析器版本`generic-labelled-v0.2.134`。
- 解析器专项 **484 passed**；全量pytest **1085 passed、27 skipped、27 subtests passed**。真实样本和人工标签仍缺，准确率未验证。
- 未访问来源网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-03排除“实用面积”误报
- 两来源4个合成回归先复现“实用面积”被抽为建筑面积，以及与真实建筑面积并列时误触发冲突；现将“实用”加入现有非建筑面积限定词，解析器版本`generic-labelled-v0.2.133`。
- 解析器专项 **480 passed**；全量pytest **1081 passed、27 skipped、27 subtests passed**。仅合成HTML验证，27项PostgreSQL集成未配置数据库而跳过；真实页面准确率仍待每站20份获准样本与人工标签。
- 未访问来源网站、NAS或生产数据库，无迁移/部署。下一步继续离线复现边界问题，或在获准样本到位后完成样本评估。

## 2026-11-12 P0-03同页嵌套article/content报价冲突
- 用户确认同页外层`article`与内层`.content`出现不同挂牌价时留空待人工审核。两来源失败回归修复前均错误采用内层价格，修复后挂牌价留空、输出`multiple_price_mentions`、保留两条证据偏移且`ready_for_review=false`；相同重复价格不误报。只在同一嵌套article范围检查，不合并兄弟根字段。解析器版本`generic-labelled-v0.2.132`。
- 解析器专项 **476 passed**；全量离线pytest **1077 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成仍在默认离线运行中跳过；测试为合成HTML，不代表真实页面准确率。
- Python 3.12 compileall、GOAL_STATE JSON及`git diff --check`通过。无来源/NAS/生产数据库访问或部署。P0-03仍需每站20份获准样本及人工标注；材料未到前继续离线解析边界审查。

## 2026-11-12 P0-03人工改价证据回归复核
- 用户确认面积与挂牌价下限均为大于0；现有解析器、模型和样本校验边界一致，包含小于1万元的正价并拒绝零值，本轮无需重复改解析逻辑。
- 人工修正价格后，`field_evidence.asking_price_wan`置为`manual_review`且不遗留旧的`is_non_exact` mention，原`non_exact_asking_price`审计警告保留；未修改字段证据仍保留原来源。定向 **9 passed**。
- 全量离线pytest **1554 passed、27 skipped、27 subtests passed**；27项PostgreSQL集成未连接。仅mock/合成HTML验证，无来源网站、NAS或生产数据库访问，无迁移/部署。真实准确率仍待每站20份获准样本及人工标签。

## 2026-11-12 P0-03人工改价PATCH API证据回归
- 新增`PATCH /api/collection/candidates/{id}`回归，经真实FastAPI路由和mock数据库写入/返回验证：人工改价后的响应数值与证据一致，证据来源为`manual_review`、旧`is_non_exact`命中清空、`manually_corrected=true`；`non_exact_asking_price`仍作为解析审计警告保留。
- 定向API回归 **1 passed**；全量离线pytest **1555 passed、27 skipped、27 subtests passed**。27项PostgreSQL集成未连接，保留1条既有Starlette/httpx弃用警告。
- Python 3.12 `compileall`、目标状态JSON、文档空白检查和开发包完整性/清单校验通过。仅mock数据库与合成候选验证，无真实页面准确率结论；未访问来源网站、NAS或生产数据库，无迁移/部署。

## 2026-11-12 P0-03人工改正非精确挂牌价后审批闭环（隔离PG17）
- 新增PostgreSQL集成回归，覆盖近似挂牌价页面提交、候选待审、PATCH人工改价、manual_review证据与解析审计警告落库、审批进入正式挂牌及价格历史。审批后正式挂牌和历史价格均为人工确认值200万元，旧非精确mention清空，`non_exact_asking_price`警告仍在候选审计记录中。 修正后重放同一HTML仍返回同一候选及manual_review数值/证据，不被解析器覆盖。
- NAS隔离PostgreSQL 17完整`tests/test_db_integration.py` **29 passed**，源码SHA-256与本机开发包一致。测试仅用internal网络、PostgreSQL 512 MiB tmpfs，无宿主端口/持久卷；源码只读挂载。临时容器、网络、测试源码/依赖及上传ZIP均已清理。
- 本机全量pytest **1555 passed、28 skipped、27 subtests passed**；28项PostgreSQL集成未设置本机`TEST_DATABASE_URL`而跳过，隔离PG17运行覆盖完整数据库集成文件。保留1条既有Starlette/httpx弃用警告。
- Python 3.12 `compileall`、GOAL_STATE JSON、更新文档空白检查和开发包校验通过。未访问来源网站；生产API、Worker、DB容器保持运行，未修改生产数据库、Compose、卷或部署。真实准确率仍待获准页面及人工标签。
