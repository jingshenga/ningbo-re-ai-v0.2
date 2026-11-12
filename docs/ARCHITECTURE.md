# 技术架构 / 组件边界

## 1. 当前物理架构

```text
[绿联 DXP4800 / Docker]
 ├─ api (FastAPI :8000 内部 / 8787 只绑定本机)
 │   ├─ /api/accounts /api/videos       抖音、视频号输入与追踪
 │   ├─ /api/collection/*                贝壳/安居客来源策略、网页样本、审核
 │   ├─ /api/listings /api/communities    标准房源与小区
 │   └─ /api/saved-searches /opportunities /notifications
 ├─ worker (单进程、串行轮询)
 │   ├─ DTK 指定作者作品轮询（第三方DTK需另行部署）
 │   └─ 网页采集目标检查（默认策略阻断，权限批准后才执行）
 ├─ db (PostgreSQL 17；内部网络)
 └─ data/raw-pages/ (gzip 原始HTML证据；主机挂载卷)

[外部独立部署]
 ├─ DTK v5 (按实际适配器配置；未联机验收)
 └─ 微信客户端导出JSON → import_channels_export.py → api
```

## 2. 核心数据流

```text
(网页样本 / 获批准的在线目标)
       ↓
  URL/来源策略 → 原始HTML文件SHA256 → beike.py / anjuke.py解析入口
                                                 ↓
                                       通用保守解析基线（未用真实样本校准）
       ↓
 collection_candidates(pending)
       ↓  人工纠错/审核
 source_listings(同来源唯一ID)
       ↓
 price_history(可追溯历史挂牌价)
       ↓
 购房条件筛选 / 机会线索 / outbox提醒

(抖音/视频号)
       ↓
 videos → 逐字稿/OCR(当前需要外部输入) → 地名字段提取
       ↓
 property_matches(candidate) → 人工复核 → 房源关联
```

## 3. 采集适配器接口与当前解析状态

当前`app.collectors.parse_listing_html(source, url, html)`按source分发到`beike.py`或`anjuke.py`；两个入口暂时委托`parser.py`中的通用保守基线。测试fixture均为合成样本，尚无获准真实页面，因此这只是代码路由拆分，不代表贝壳/安居客布局校准或准确率验收。取得合规样本后，站点模块再加入经标注验证的字段规则与布局版本处理。

后续列表发现需要独立的 `discover(source, area_or_community, cursor) -> [detail_url]`，并保持严格的来源权限检查。现有V0.2只支持已知详情页URL，不具备按宁波区域全自动发现所有挂牌房源的能力。

`collect(source, url_or_id) -> List[RawObservation]`：只处理能够访问且允许获取的数据；运行记录明确记录失败原因。`parse(raw) -> CandidateListing`：网页抽取只形成候选。`normalize(candidate) -> ListingObservation`：统一单位（万元、平方米）和来源时间。`approve(candidate)`：人工核对后写入正式库。

后续上线 `licensed_api` 时，仅替换 collect+parse 环节，保持 `community_id`、`source_listing_id`、`price_history` 和条件单不变。**不同来源同名同面积不自动合并。**

## 4. 资源与扩展
- N100优先控制采集并发/HTML大小；运行ASR/OCR时保持每次最多一个转写任务。
- HTML 1MB 上限，原始样本 gzip 保存；未来设置保留期限与容量告警。
- Worker串行巡检以防止对上游产生突发请求；未来如规模增长，增加独立队列、每来源并发限制及失败退避。
- 数据库先以单机PostgreSQL为主，不引入过度复杂的微服务、向量数据库或大型本地模型；必要时再引入。

## 5. 安全界面
- 当前 `/api/*` 需要 `X-API-Key`。没有用户管理、细粒度权限和审计前，不能公开互联网访问。
- 所有外部目标URL必须限定来源域名及HTTPS；不跟随跳转；robots错误、403/429一律停止。
- 来源政策和域名白名单不等于法律保证。即使开发环境开启线上任务，也须运营者先核实许可范围。
- 原始网页、视频文件、账号权限、用户购房需求均应按照最小化、留存期限和访问控制要求处理。
