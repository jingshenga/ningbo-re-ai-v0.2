# 数据结构与可信度设计

## 1. 重要表关系

- `monitored_accounts` → `account_sync_runs` → `videos`：指定作者监控、新视频元数据。
- `source_registry`：贝壳/安居客的当前采集方式、线上权限审批及状态。默认 online OFF。
- `collection_targets` → `collection_runs`：可追踪的网页目标检查和阻断日志。
- `collection_parse_attempts`：每次页面解析的追加记录，保存来源、采集方式、解析器版本、成功/失败和四个关键字段是否齐全；触发器同步累计至`collection_health_metrics`。该表记录解析器输出，不等同于候选审批或真实页面准确率。
- `collection_health_metrics`：按来源维护运行、解析、字段完整、候选审核及挂牌累计计数；API比率由这些累计计数派生，分母为0时返回null。
- `collection_candidates`：网页抓取/保存后抽取的候选，原始HTML文件路径、SHA256、解析器版本、字段与审核结论。`extracted_fields.field_evidence`为文本和来源ID命中保留最多20条原文/URL片段、来源及字符偏移和总数/截断状态；canonical URL证据删除查询参数、片段和路径前缀。歧义字段保留命中但字段值为空。人工修正标记为`manual_review`；`confidence_status=not_calibrated`。
- `communities` + `community_aliases`：宁波小区标准名及别名。
- `properties`：内部房源身份，不自动表示跨平台已经确认相同房屋。
- `source_listings`：来源网站的独立挂牌记录；源站+源ID唯一；V0.2有 `acquisition_method`、`latest_candidate_id`、`last_evidence_sha256`。
- `collection_listing_observations`：按采集目标追踪列表页出现/连续完整遍历缺失与人工核验队列状态；`collection_listing_reviews`追加保存人工核验结论和备注，不写入或改变正式挂牌状态。
- `price_history`：来源挂牌价格历史；视频中的“急售365万”不能直接写入贝壳挂牌价格历史。
- `property_matches`：视频→来源挂牌候选关联，默认为 `candidate`。
- `saved_searches` + `notification_logs`：用户条件单与待处理提醒事件（不等于已发送）。

## 2. 标准字段字典（以后各采集器必须输出）

| 字段 | 类型与单位 | 说明 |
|---|---|---|
| `source` | enum | `beike/anjuke/agent/other` |
| `source_listing_id` | string | 只有可验证的源站ID，绝不从描述拼凑 |
| `listing_url` | HTTPS URL | 可追踪证据链接 |
| `community_name` | string | 原始展示名，须经小区标准化核对 |
| `area_sqm` | numeric(9,2) | 建筑面积，单位平方米，注意套内面积差异 |
| `asking_price_wan` | numeric(12,2) | 人民币总价，单位万元 |
| `bedrooms` | integer/null | 室数，与厅/卫独立 |
| `district` | string/null | 必须来自实际房屋区域字段，不能由IP属地推定 |
| `observed_at` | timezone datetime | 采集/观察时间；与发布/调价时间区分 |
| `source_published_at` | datetime/null（未来） | 平台所称发布时间，不等于抓取时间 |
| `acquisition_method` | string | `manual_import/manual_html_snapshot/public_page_collection`；将来增加licensed_api |
| `last_evidence_sha256` | sha256/null | 供原始证据核对 |
| `review_status` | enum | `pending/approved/rejected`（候选） |

## 3. 价格逻辑
- 只有同一来源、同一来源ID并经审核的挂牌快照可以计算同源降幅。
- `first_observed_at` ≠ 房源首次挂牌日期；除非来源可靠提供，否则只能说“首次观察到”。
- 如果同一来源ID对应小区或面积发生明显变化，直接拒绝自动更新。
- 历史录入的 `observed_at` 不能覆盖最新价。价格变化与通知基于最新快照。
- 多平台报价冲突只是候选信息，不得推断卖家最低接受价或已经成交。

## 4. 估值和机会分数（规划）
参考池必须按小区/分期、面积偏差、户型、楼层、楼龄、装修、时间进行清洗，并明确样本数量与置信区间。低于样本中位价不是成交价折扣，只是挂牌价格相对位置。默认把估值看作供人工核实的提示，不是保证收益或成交承诺。

## 5. 数据状态与保留
- `pending`：AI/规则抽取但未经核实；默认不公开显示确定性报价结论。
- `approved`：人工确认字段读取正确；仍不保证房屋在售/产权/成交状况。
- `stale`（未来）：超过更新时效，必须显著标记；不能自动改成已售。
- 原始HTML及视频文件设定留存策略，处理个人敏感信息前进行最小化、删除请求和权限检查。
