# DTK v5 指定账号增量监控：契约验证与实测状态报告

更新：2026-11-13（ZCode，Issue #3）。**离线契约验证与真实联调状态严格分列；未完成的实测一律标记"待外部条件"，不宣称通过。**

## 一、适配器版本与请求契约（已固定，离线验证）

- 适配器：`app/dtk.py`，DTK v5 作者作品 REST 接口 `/api/v1/douyin/user/posts`，异步任务轮询 `/api/v1/tasks/{task_id}`。
- 请求：`count=20`（`PAGE_SIZE`，响应超过 20 条即报错，见 `test_page_exceeds` 族）、`wait=15`；`account_ref` 为合法 HTTPS 主页时传 `url`（去除 query/fragment，拒绝 userinfo/非 443 端口），否则传 `sec_user_id`；游标仅传非空白字符串。
- 响应：`success:true` 信封 + `data` 对象；完成态 `data.items` 或任务态 `data.data.items`；`meta`/`result_meta` 双位置游标与 `guest_fallback` 兼容读取；`has_more` 缺省时按游标存在性推断，显式 `false` 优先。
- 任务轮询：52.5 秒单调时钟截止、剩余时间约束 HTTP 超时、`task_id` 单路径段编码、未知 `state` 拒绝推断。

## 二、`account_sync_runs` 状态语义（已在 `worker.run_account` 文档化并有回归）

| status | 语义 | 关键回归 |
|---|---|---|
| `success` | 全部请求页读完且无降级信号；基线模式（`history_mode='none'`）刻意只读一页，上游 `has_more` 属预期 | `test_first_baseline_sync_reads_single_page_and_completes` |
| `partial` | 有数据但置信度下降：`guest_fallback`、无稳定 ID 被跳过、补采期未知发布时间、`has_more` 无游标、页限未读完。**`new_count=0` 且 partial 必须读作"未知/可能遗漏"，不得读作"无更新"** | `test_guest_fallback_page_reports_partial_even_without_new_works`、`test_missing_cursor_with_more_pages_is_reported_as_partial` |
| `failed` | 异常中断；`pages/observed_count/new_count` 保留中断前计数；错误经 `safe_error_summary` 脱敏；账号保持启用，按下一常规轮询自动重试（认领时已提前推进 `next_poll_at`，`finish_run` 不触碰 `enabled/next_poll_at`） | `test_failed_run_keeps_partial_counts_and_leaves_account_enabled`、`test_history_backfill_resumes_after_request_failure` |
| `blocked_config` | `DTK_BASE_URL`/`DTK_API_KEY` 未配置；**不发起任何网络请求** | `test_unconfigured_dtk_records_blocked_config_without_network` |

指标输出仅使用既有 `account_sync_runs` 字段：`status`、`pages`、`observed_count`、`new_count`、`error_text`（partial 时承载降级原因清单）。**未新增表。**

## 三、去重与基线

- 以 `source_post_id`（`aweme_id|post_id|id|video_id` 首个有效值）在 `account_seen_posts` 内 `ON CONFLICT` 去重；`baseline_only` 语义：首次基线/补采范围外的旧内容先标记不入库，之后显式补采可升级入库。
- 首次基线（`history_mode='none'`）：单页、全部标记基线、`initial_synced` 置位。
- 增量同步：遇到已见内容即停止翻页（`already>0` break），不重复请求历史页。

## 四、历史补采：范围限制与断点恢复

- 范围限制：`history_mode` ∈ `30d|90d` → `cutoff = now - 30/90 天`；发布时间缺失或早于 cutoff 的条目只记基线，不补采（`unknown_date` 计数并判 partial）。
- 断点恢复：`history_backfill_cursor`/`history_backfill_cutoff` 每页持久化；请求失败后从断点续跑（`test_history_backfill_resumes_after_request_failure`）；页限（5 页/轮）后下轮续跑（`test_history_backfill_resumes_after_page_limit_with_fixed_cutoff`）；翻完置空游标并完成 `initial_synced`。
- 重新补采：改 `history_mode` 或显式 `queue_account_poll` 会重置进度（`test_changing_history_mode_resets_backfill_progress`、`test_explicit_backfill_request_resets_old_progress`）。

## 五、离线验证汇总（2026-11-13）

- `tests/test_worker.py` **8 passed**（原 4 项 + 本轮新增 4 项契约：blocked_config / guest_fallback-partial / failed-重试语义 / 首次基线单页）。
- `tests/test_dtk.py` 39 项（信封/游标/URL 安全/时间规范化/任务轮询截止等）与 `tests/test_account_history_backfill.py` 2 项继续通过。
- 全量离线 pytest 见 PR 描述（本轮基于 main `d372a94`）。
- 以上全部使用合成/脱敏 fixture 与 mock 客户端，**不代表真实 DTK 行为**。

## 六、真实联调状态：**待外部条件，未开始，未通过**

| 前置条件 | 状态 |
|---|---|
| NAS 上已部署并可访问的 DTK v5 服务（`DTK_BASE_URL`/`DTK_API_KEY`） | 缺失 |
| 至少 3 个获准使用的测试账号 | 未提供 |
| 平台权限与请求频率核对（不规避验证码/反爬/限流） | 未执行 |

实测验收口径（条件具备后执行）：连续 24 小时轮询 ≥3 账号，逐轮记录请求延迟、`success/partial/failed/blocked_config` 分布、新作品发现数、去重命中数、遗漏（事后人工比对账号页）与页级部分失败；guest_fallback 出现率单独统计。结果追加至本文件，任何未达标项保持阻塞状态。

## 七、已知限制

- DTK 真实版本/接口字段与本文契约的偏差只能在联调中发现；出现未知 schema 时适配器按 `DtkError` 失败而非猜测。
- 不实现任何验证码/风控规避；**403/429/限流类信号当前并未被单独识别**：`app/dtk.py`→`app/worker.py` 对 DTK 请求异常统一捕获，`account_sync_runs` 记为普通 `failed`（`error_text` 经 `safe_error_summary` 脱敏），没有独立的 `blocked_*` 状态或退避策略。collection 域的 robots/阻断策略只作用于网页采集路径，与账号同步路径无关。本域只如实记录失败，不猜测阻断原因。

## 八、后续安全改造任务（待办，未开始）

- 目标：在 `app/dtk.py`→`app/worker.py` 增加 403/429/限流的专用识别，使 `account_sync_runs` 能区分限流阻断与普通 `failed`，并记录连续阻断次数与下次安全轮询时间；实现不得绕过验证码/反爬/限流。
- 验收要求：
  1. 离线回归覆盖 403/429/超时/畸形响应各自的分类、退避与重试行为（失败先行）；
  2. 若需要新增状态值或数据列（SQL 迁移），必须单独 PR 审查，不在本 PR 内附带；
  3. 在未满足 §六 前置条件（NAS 已部署 DTK 服务、≥3 个获准账号、平台权限与频率核对）前，不得发起真实平台压测；403/429 真实频次统计并入 §六 实测口径。
