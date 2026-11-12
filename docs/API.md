# API 清单（V0.2，单操作者后端）

基础地址：`http://127.0.0.1:8787`；所有 `/api/*` 需 `X-API-Key`。默认不是公网服务。JSON日期字段要明确时区，人民币价格单位为 **万元**，面积单位为 **㎡**。 写入挂牌、条件单及候选纠错的面积/价格/降幅最多两位小数；若超出两位会改变数值，API会返回422。仅多余尾随零（如`120.2300`）会接受并规范为两位。
网页解析的建筑面积识别`㎡`、`m²`、`平米`、`平方米`、`平方`和`平`单位；证据片段包含完整单位。近似/上下限面积（如“建筑面积约100㎡”“大于100㎡”“100㎡以上”“100㎡封顶”“100㎡起步”）留空并追加`non_exact_area_sqm`，候选值和带`is_non_exact`标记的原文证据供人工审核。范围表达保留完整范围并待审核，不选取端点。
贝壳和安居客来源挂牌ID必须是平台格式的数字（贝壳8–220位，安居客7–220位）；此校验同时适用于挂牌写入及候选审批。`agent`/`other`来源可使用其自有ID格式。挂牌写入会裁剪来源ID与小区名的首尾空白并拒绝纯空白值；新建小区名也执行相同规范化。挂牌可选文本（标题、挂牌URL、区域、楼层、装修、备注）会裁剪首尾空白，纯空白视为未提供，因此更新时不会清空已有值。
账户标识、视频作品ID和条件单名称会在检查长度前裁剪首尾空白，并拒绝纯空白或规范化后不符合最小长度的值。条件单的可选区域/小区文本也会裁剪；纯空白按未设置处理。
挂牌、条件单和候选纠错中的户型字段，以及条件单的最大挂牌时效，均要求整数；JSON布尔值`true`/`false`会拒绝，不会转换为1/0。API中的开关、通知偏好和小区`verified`标记只接受JSON布尔值，不会把数字`1`/`0`隐式转换为`true`/`false`。

## 已有V0.1接口（仍在V0.2）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/healthz` | 数据库健康探针 |
| POST/GET | `/api/accounts` | 指定抖音/视频号账号登记及列表 |
| PATCH | `/api/accounts/{id}` | 启停、周期、历史策略 |
| POST | `/api/accounts/{id}/poll` | 排入抖音账号检查队列（依赖DTK） |
| POST | `/api/accounts/{id}/backfill?history_mode=30d` | 请求抖音历史补采 |
| GET | `/api/accounts/{id}/runs` | 查看账号同步健康 |
| POST | `/api/ingest/videos` | 单条视频元数据入库 |
| POST | `/api/ingest/videos/batch` | 批量视频元数据 |
| GET | `/api/videos` | 视频列表 |
| PATCH | `/api/videos/{id}/enrichment` | 提交外部转写/OCR并提取候选 |
| POST | `/api/videos/{id}/match-candidates` | 同小区候选关联，不自动确定同套 |
| POST | `/api/property-matches/{id}/review` | 人工确认或拒绝关联 |
| POST/GET | `/api/communities` | 小区和别名 |
| POST/GET | `/api/listings` | 人工/程序导入来源挂牌与条件查询 |
| GET | `/api/listings/{id}/prices` | 同来源ID历史价格 |
| POST/GET | `/api/saved-searches` | 条件单；支持单/多区域、硬性筛选、偏好/排除小区和挂牌时效 |
| GET | `/api/saved-searches/{id}/matches?limit=100` | 执行条件单；硬条件过滤正式挂牌，偏好小区优先排序并标注，每条结果返回命中理由与总匹配数 |
| GET | `/api/opportunities?days=30` | 7/30/90日挂牌机会；同一挂牌平台历史降价包含金额、幅度、前后时间和证据链接；可比折价信号返回挂牌单价、可比单价中位数、独立房屋样本数、挂牌更新时间与理由（非成交预测） |
| GET | `/api/notifications` | 内部提醒outbox；不会自动发送微信/邮件 |
| POST | `/api/notifications/{id}/read` | 标记提醒已读 |

抖音`account_ref`仅接受HTTPS `douyin.com`主机链接；凭据和非标准端口拒绝，query/fragment会清除（包括空`?`/`#`分隔符）。

## 新增V0.2网页采集/审核接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/collection/sources` | 两站来源方式/线上权限/全局开关状态 |
| GET | `/api/collection/health` | 按来源返回采集/解析/字段完整/审核计数与比率、挂牌数、最近成功/观察时间和最近运行原因 |
| GET | `/api/collection/discovery-observations?source=beike&target_id=...&review_status=pending_review&limit=100&offset=0` | 按最近观察时间列出目标级挂牌记录、首次/最近列表观察时间、观察次数、缺失完整扫描数及人工核验状态；附首末列表页证据和最近人工核验结论 |
| POST | `/api/collection/targets/{target_id}/discovery-observations/{source_listing_id}/reviews` | 对`pending_review`记录追加人工核验结论：`still_listed`、`confirmed_withdrawn`或`inconclusive`；备注可选。记录后观察状态变为`reviewed`，不修改正式挂牌状态 |
| GET | `/api/collection/targets/{target_id}/discovery-observations/{source_listing_id}/reviews?limit=50&offset=0` | 分页读取该挂牌的追加式人工核验历史 |
| POST | `/api/collection/sources/{source}/policy-review` | 记录来源审核和权限依据；不代表系统自动判断合同有效 |
| POST | `/api/collection/pages` | 上传HTML正文作为人工/本地采集样本，不访问远端网站 |
| GET | `/api/collection/candidates?status=pending` | 待审核网页候选 |
| PATCH | `/api/collection/candidates/{id}` | 人工改正候选字段，需说明原因 |
| POST | `/api/collection/candidates/{id}/review?decision=approve&note=...` | 事务中审批入正式来源挂牌和价格历史 |
| POST | `/api/collection/targets` | 登记采集目标，默认enabled=false |
| GET | `/api/collection/targets` | 查看采集目标和最新检查状态 |
| PATCH | `/api/collection/targets/{id}` | 启停/更改周期 |
| GET | `/api/collection/targets/{id}/discovery-state` | 读取数据库分页游标、已访问页、已发现ID、当前完整扫描轮次/已见ID、累计完成轮次、错误类别及待抓详情URL；待抓详情URL列表最多返回100条，另报告总数和截断标记 |
| PUT | `/api/collection/targets/{id}/discovery-state` | 以revision校验并保存分页状态；传入的已暂存ID并入目标级去重账本，数据库不再把完整ID集累积在游标JSON内；来源/URL/ID均需符合目标来源，等价URL写法也不能形成分页回环（scheme/主机大小写、DNS尾点、默认443端口、空路径，以及未保留字符百分号编码及原始Unicode的UTF-8百分号形式按同一页比较；路径大小写敏感，`%2F`保留为编码字符） |
| POST | `/api/collection/targets/{id}/check` | 下次Worker检查（若禁用仍不会运行） |
| GET | `/api/collection/runs` | 网页采集执行/阻断日志 |

健康比率是累计值（无时间窗口）：`collection_success_rate_pct=success_count/(success_count+failure_count)`，blocked不入分母；`parse_success_rate_pct=parse_success_count/parse_attempt_count`；`field_complete_rate_pct=complete_field_count/parse_success_count`；`approval_rate_pct=approved_count/(approved_count+rejected_count)`，pending不入分母。百分比保留两位小数；分母为0时返回`null`。解析记录覆盖手动HTML提交和在线采集进入解析器的页面；解析函数返回结果即计解析成功，警告/字段缺失不算解析失败。字段完整要求来源挂牌ID、小区、总价和面积均有非空解析值。解析成功率与字段完整率仅统计迁移010启用后的解析记录；旧运行记录无法可靠区分网络失败和解析失败，因此不回填迁移前历史。迁移011将解析尝试明细作为追加式记录，拒绝更新、删除和清空，以保持其与累计汇总一致。

## 示例1：手工保存页面样本

```json
{
  "source": "beike",
  "source_url": "https://nb.ke.com/ershoufang/109900001234.html",
  "html": "<html><body><main><p>小区：东湖花园</p><p>建筑面积：158㎡</p><p>总价：365万</p></main></body></html>",
  "note": "仅用于虚构测试，非真实房源"
}
```

提交至 `POST /api/collection/pages` 后应得到 `candidate.review_status=pending`、可能的缺失字段警告。候选导入不改变正式挂牌；审批时必须实际核对原始证据，测试数据不能用于对外产品。
HTML正文上限为1,000,000 UTF-8字节；请求JSON正文最大6,100,000字节，超过时直接返回413。API在字段校验前限制请求体，避免未受限地缓冲超大提交。`scripts/submit_html_snapshot.py`只读取本地UTF-8文件，并在发送前拒绝超过1,000,000字节的样本；它不会请求来源网站。
`source_url`长度须为12–2000字符，只允许贝壳`nb.ke.com`或安居客`ningbo.anjuke.com`的HTTPS URL，且不得包含空白/控制字符、userinfo、查询参数或片段；主机名最多接受一个DNS根尾点。请在提交前移除凭据、跟踪参数和临时令牌。
页面声明的canonical URL或`og:url`若暴露与提交链接不一致的挂牌ID，候选的`source_listing_id`会留空并追加`canonical_source_id_mismatch`，需人工核对。
候选`extracted_fields`为挂牌属性附带`field_evidence[field]`，包含解析值和最多20条命中（候选原文值、来源、片段、字符偏移），并给出总数及截断标志；可见文本偏移相对完整归一化文本（最长35,000字符），而`evidence_excerpt`仅返回该文本的前1,000字符，因此较后命中的偏移可能超出摘录，但每条命中仍附有独立原文`quote`。URL偏移相对相应URL/path quote。房源ID注明来自提交URL或canonical/og:url；canonical证据去掉查询参数、片段及路径前缀。字段冲突/越界仍保留命中证据但解析值为空。`confidence_status`为`not_calibrated`，不代表真实页面准确率。人工修正字段标记为`manual_review`并清除旧解析命中；PATCH提交的来源ID、标题、小区、区域、楼层、装修和审核备注会先去除首尾空格，纯空白值被拒绝；来源ID仅接受数字，贝壳为8–220位、安居客为7–220位。标题限1–500字符，其他字段按各自长度/类型校验。可空字段用`null`显式清空。
同一`article`内若外层报价与嵌套的`.content`候选报价数值不同，解析器以该`article`的可见文本保留两条挂牌价证据，将`asking_price_wan`置为`null`并追加`multiple_price_mentions`，候选保持待审核；数值相同的重复报价不会触发冲突。该规则只处理同一嵌套`article`中的价格冲突，不拼接兄弟内容根的字段。

面积或挂牌价以区间表达（如`120㎡-130㎡`、`300万-320万`）时，不从区间中挑选端点；区间以完整原文范围作为`field_evidence[field]`命中保留，并追加`multiple_area_mentions`或`multiple_price_mentions`。若同时出现单值，该字段也留空；若没有其他单值，还会追加对应`missing_area_sqm`或`missing_asking_price_wan`。范围符后为解析器暂不支持的中文数字端点时，也不会把前面的阿拉伯数字单独提升为挂牌值。区间命中与其他字段证据一样，最多返回20条并给出总数及截断标志；原文同样保留于关联的原始HTML证据。
“口播:总价”“口播的总价”“合同中的挂牌价”“交易中的总价”“签约里的出售总价”“成交:总价”“交易总价”“合同总价”“签约总价”“折后:挂牌价”及“口播 挂牌总价”等修饰价格不计为挂牌报价；限定词与价格标签间存在常见连接词（包括HTML节点分割后折叠为空格的文本）、使用冒号，或复合标签含“总价”后缀，都不会绕过该排除规则。被排除的口播/合同/交易金额不会作为挂牌价命中写入`field_evidence.asking_price_wan`；原始页面仍按哈希压缩保存，金额若位于前1,000字符的可见文本摘录内，也会出现在`evidence_excerpt`中。
“挂牌价：2万/㎡”及同类ASCII/全角斜杠、“/m²”“/平米”“/平方米”“/平”“每平方米”“每平”金额写作“万”或“万元”后的单位面积报价均不作为挂牌总价；括号包裹的“（元/㎡）”“（每平方米）”等写法也会排除；单位价格区间同样不会被提升为总价或造成多个挂牌价冲突。若同时有明确挂牌总价，保留总价并排除单位价。
挂牌价标签后的金额前（如“挂牌价：约200万”“总价：不超过200万”），或挂牌价金额后（如“200万左右”“200万以上”）出现近似/上下限修饰时，解析器不会把数字当作精确`asking_price_wan`，而是追加`non_exact_asking_price`、保留数值证据并使候选保持待审。支持“挂牌价为约200万”“挂牌价约为200万”“挂牌价在200万左右”；精确连接词“挂牌价为200万”仍按精确值解析。“在”作为限定词时视为非精确。证据`quote`包含该报价的完整前置/后置限定词；每条`asking_price_wan.field_evidence.mentions`都带`is_non_exact`布尔值，用于标明该条报价证据本身是否带近似/上下限修饰。建筑面积近似或上下限修饰同样留空、追加`non_exact_area_sqm`并保留每条`area_sqm.field_evidence.mentions`的`is_non_exact`标记。价格/面积范围继续作为完整范围证据留空待审；范围价格若有限定词，也会追加`non_exact_asking_price`。“起始价”也按非精确报价处理；单独出现在折叠摘要等页面文本中的“起始”不构成报价限定词。
解析器最多扫描35,000字符的归一化可见正文。超过上限时，候选警告含`visible_text_truncated`，且`ready_for_review=false`，表示截断部分的字段冲突尚未核验；候选仍保持pending并需人工检查原始证据。
若内联`display`、`opacity`、`visibility`或`content-visibility`的最终值依赖未解析的CSS `var()`，或内联样式声明`clip`/`clip-path`/`mask`/`mask-image`/`-webkit-mask`/`-webkit-mask-image`，可见性无法由离线HTML确定；候选保留文本及字段证据，追加`unresolved_inline_visibility`并返回`ready_for_review=false`，需人工检查原始页面样式。
静态解析器不计算CSS样式表的层叠结果。若当前文档（`<template>`与`<noscript>`惰性内容除外）包含带`display`、`opacity`、`visibility`、`content-visibility`、`clip`、`clip-path`、`mask`、`mask-image`、`-webkit-mask`或`-webkit-mask-image`声明的`<style>`规则、`<style>`中的`@import`，或引用任一`rel="stylesheet"`外部样式表，候选追加`unresolved_stylesheet_visibility`并返回`ready_for_review=false`；文本及字段证据仍保留，需人工核对页面渲染结果。扫描时忽略CSS注释、引号字符串及非声明位置中的相同文本。外部样式表不会被解析器联网获取。
解析出的面积/挂牌价若超过数据库`NUMERIC(...,2)`可保存精度，命中原始文本保留在`field_evidence`，并追加`numeric_precision_requires_correction:{field}`警告、使`ready_for_review=false`。审批时返回409并要求先人工纠正；历史候选即使没有该警告，也会在字段校验失败时返回409，不会静默舍入或返回未处理的500。

## 示例2：登记一个**禁用状态**的目标

```json
{
  "source": "beike",
  "url": "https://nb.ke.com/ershoufang/109900001234.html",
  "enabled": false,
  "poll_interval_minutes": 1440
}
```

该URL也是演示用，不是已确认真实房源。V0.2在线采集总开关和来源审批默认都关闭。即使记录目标也不会自动访问网站。

## 示例3：来源权限审查记录

```json
{
  "online_policy_status": "not_authorized",
  "online_enabled": false,
  "policy_reference": null,
  "note": "尚未核实允许自动采集，禁止在线运行"
}
```

只有取得对应的真实权限依据、核实使用条款/robots/使用范围且程序全局开关也显式打开后，才可能尝试获取。**切忌将 `approved` 当作一种绕过平台限制的操作。**

## 重要限制
- 通用HTML解析器尚未在真实贝壳/安居客宁波页面做字段准确率验收。
- 条件单兼容旧字段 `district`、`community_name`；新字段 `districts` 是硬性区域范围，`preferred_communities` 只作为提醒偏好标记，`excluded_communities` 为硬性排除，`max_listing_age_days` 按挂牌最近观察时间过滤。
- 条件单匹配结果的`match_reasons`逐条解释实际满足的区域、小区、总价、面积、户型、挂牌时效和偏好小区条件；未设置这些过滤时只返回通用命中说明，不推断未存储的购房理由。
- 正式成交价不由挂牌价或视频口播推断。
- `/api/opportunities` 的 `days` 仅接受 7、30、90；降价基于窗口内首末两条有效平台挂牌快照，窗口外/未来时间及 `agent_claim` 不参与。输出中的降价金额/幅度、首末价格、观察时间和末次证据链接均来自同一挂牌的有效窗口快照；仍是挂牌线索，不是成交价、估值或已核实低价。
- 机会可比池仅比较已知且相同的卧室数，且候选面积相对目标挂牌面积差不超过10%（以目标挂牌面积为分母）；按不同`property_id`计数。同一房屋的多条挂牌先合并为该房屋单价中位数，至少有5套不同可比房屋才显示挂牌中位数折价信号。
- 机会信号附`signal_reasons`；`unit_price_wan_per_sqm`与`last_observed_at`解释目标挂牌，`comparable_median_wan_per_sqm`和`comparable_sample_count`解释达到5套门槛后的可比折价。它们来自挂牌报价，不代表成交或估值。
- 跨平台价差只在贝壳与安居客不同来源、同小区、同户型且面积差不超过5%的挂牌间比较；面积差定义为`abs(a-b)/min(a,b)`，即以较小面积为分母。挂牌最近观察时间仅接受过去90天至请求当前时刻，未来时间戳不参与机会计算。单价差达到10%时返回`cross_platform_price_gaps`候选详情。差异率为`(高单价-低单价)/低单价`，恰好10%计入。响应标记`verification_status=candidate`并说明待核实，不自动合并房源或确认同套；该信号尚未在NAS验收。
- V0.1来源房源人工导入API仍可用，录入时必须携带来源与许可备注，默认 `acquisition_method=manual_import`。
- 当前只有前端Swagger `/docs`，暂无正式审核管理界面。
