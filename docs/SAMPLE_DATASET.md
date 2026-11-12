# 获准页面样本清单

P0-02/P0-03 的样本必须是有明确使用范围的真实保存页面，并由人工逐字段标注。仓库中的 fixtures/*_demo.html 只是虚构演示，不能用于样本数量、字段准确率或覆盖率验收。

## 文件与隐私

- 将允许用于离线解析的页面存入 data/raw-pages/；可使用 `.html` 或 `.html.gz`，解压后的HTML必须为严格有效的UTF-8。本版不会猜测或自动转换编码；校验器会在哈希校验后拒绝无效UTF-8，避免解析评估阶段才失败。SHA-256按存储文件字节计算。不要提交这些页面或 data/sample-manifest.csv 到版本库。
- 复制 docs/SAMPLE_MANIFEST_TEMPLATE.csv 到 data/sample-manifest.csv，逐页填写；sha256 是本地文件字节的 SHA-256。对于`.html.gz`，校验器另解压并在贝壳/安居客整个评估集范围内按HTML内容去重，避免同一份页面跨来源重复凑数，也不会因gzip时间头不同而重复计数；损坏的gzip文件会被拒绝。
- 清单中的`price_candidates_wan`用于`multiple_prices`；`source_listing_id_candidates`、`community_candidates`、`area_candidates_sqm`（也用于可选`area_ranges`和`non_exact_area_ranges`场景）、`bedroom_candidates`、`invalid_bedroom_candidates`、`district_candidates`、`floor_candidates`、`decoration_candidates`分别用于`source_id_conflict`、`multiple_communities`、`multiple_areas`/`area_ranges`、`multiple_bedrooms`、`invalid_bedrooms`、`multiple_districts`、`multiple_floors`、`multiple_decorations`歧义场景；`price_candidates_wan`也用于可选`price_ranges`和`non_exact_price_ranges`场景。候选值以`|`分隔，仅填写被对应场景标签标记的列；面积候选可用完整范围文本（如`120㎡-130㎡`）表示一个证据命中，价格候选同理可填`300万-320万`，不可把单个范围拆成两个端点；范围与单值共存时将它们分别列为候选。范围两端都须在对应字段合法范围内，格式和分隔符需与解析器支持形式一致。来源ID候选须匹配来源格式（贝壳8–220位数字、安居客7–220位数字），面积候选使用平方米且须在(0, 20000]范围内；title须与解析器最大500字符输出一致；标题缺失须由`missing_fields`标注。面积/报价数值及范围端点可带格式正确的千分位逗号，错误分组会被拒绝。
- 可选`non_exact_areas`用于建筑面积带近似或上下限限定的页面（如“建筑面积约100㎡”“建筑面积在100㎡左右”“大于100㎡”“100㎡以上”“100㎡封顶”“100㎡起步”）。该场景将`area_sqm`留空，并在`area_candidates_sqm`填写恰好一个正数面积候选；不接受范围候选，也不可与`multiple_areas`/`area_ranges`/`non_exact_area_ranges`并用。评估器要求预测面积为空、出现`non_exact_area_sqm`、每条面积证据均为`is_non_exact=true`、quote包含候选数值和限定词、证据未截断且候选与人工标注一致，且`ready_for_review`必须为false。它是可选覆盖，不替代每站必需场景。带限定词的范围应标为`non_exact_area_ranges`，而不是`area_ranges`。
- 可选`non_exact_prices`用于挂牌价数字带近似/上下限限定词的页面（如“挂牌价约200万”“挂牌价为约200万”“挂牌价在200万左右”“总价不超过200万”）。此场景将`asking_price_wan`留空，并在`price_candidates_wan`填写恰好一个正数数值候选；不可填写范围或与`multiple_prices`/`price_ranges`/`non_exact_price_ranges`并用。评估器要求预测价为空、出现`non_exact_asking_price`、每条挂牌价证据均标记`is_non_exact=true`、quote包含候选数值和限定词、证据未截断、候选值与人工标注一致且`ready_for_review`为false；页面同时包含精确价时判失败。它是可选覆盖，不替代每站必需场景。
- source_url 仅接受12–2000字符的贝壳 nb.ke.com、安居客 ningbo.anjuke.com HTTPS页面路径；删除查询参数、片段、用户名和其他访问令牌；URL中不得包含空白或控制字符。只记权限文件的引用编号/本地受控路径，不复制许可文件正文或个人信息。
- permission_reference、permission_scope 是运营者提供的来源依据摘要。自动校验器只检查字段存在，不判断许可真实、有效或足以覆盖用途；授权未明确时，不导入或运行在线采集。

## 人工标注规则

- 可选场景标签`oral_prices`和`transaction_prices`分别用于口播金额、交易/成交/网签/合同/签约金额。它们不新增CSV列；若页面没有明确挂牌价，可用相应标签解释`asking_price_wan`空值，若同时存在明确挂牌价则照常标注挂牌价。评估报告按来源分别统计这两类价格语境是否污染挂牌价；它们是可选覆盖项，不替代每站最低必需的`missing_fields`、`multiple_prices`、`unknown_id`场景。

- 每个平台至少 20 个不同内容的页面；两站都要覆盖source_status=active、withdrawn，以及`missing_fields`、`multiple_prices`、`unknown_id`。可选的字段冲突标签仅在页面实际含歧义时添加；标题来源冲突使用`title_source_conflict`，须保留非空人工标题真值，以核验解析器是否记录歧义并回退到正确的下一标题来源。
- 逐页人工标注`source_listing_id`、页面标题`title`、`community_name`、`district`、`area_sqm`、`bedrooms`、`floor_text`、`decoration`及无冲突的`asking_price_wan`。每个空标签必须由`missing_fields`或字段专属场景解释；来源URL/canonical ID冲突用`source_id_conflict`并填写各个冲突ID，来源URL中可识别ID必须在候选中；未知ID用`unknown_id`，冲突价格用`multiple_prices`，小区/面积/户型/区域/楼层/装修多值分别用`multiple_communities`、`multiple_areas`、`multiple_bedrooms`、`invalid_bedrooms`（单个越界户型值）和`multiple_districts`、`multiple_floors`、`multiple_decorations`。每个多值场景还须在对应`*_candidates`列填写至少两个不同的人工观察值；`invalid_bedrooms`须在`invalid_bedroom_candidates`填写一个大于20且不超过99的整数，且不得与`multiple_bedrooms`同时标记；候选值与页面解析证据不一致、或证据被截断时，场景评估不通过。未标注空值会被拒绝，避免从准确率分母静默省略。source_listing_id必须来自页面证据；仅当标记`unknown_id`或`source_id_conflict`时留空。若规范详情URL只暴露单一可识别ID且无冲突，清单ID必须一致。 即使来源URL本身不含可识别ID，非空`source_listing_id`仍须符合来源格式：贝壳8–220位、安居客7–220位ASCII数字；只有`unknown_id`或`source_id_conflict`时才留空。
- missing_fields 至少有一个人工真值字段留空，且不能只依赖`multiple_prices`导致的挂牌价空值（该字段由独立歧义场景评估）。multiple_prices 必须列出至少两个不同的 price_candidates_wan 证据命中，并将单值 asking_price_wan 留空，不替冲突报价选值；完整价格范围算一个命中，例如`300万-320万|310`。`multiple_areas`与`area_ranges`共用`area_candidates_sqm`；后者要求至少一个完整范围候选。`multiple_prices`与`price_ranges`共用`price_candidates_wan`；后者要求至少一个完整价格范围候选。范围可与普通单值同列标注，各候选场景均按对应标签检查完整证据。`non_exact_price_ranges`用于人工确认范围报价含近似/上下限限定词的页面：挂牌价留空，`price_candidates_wan`至少填写一个合法完整范围；评估器要求全部对应范围证据均为`is_non_exact=true`，存在`non_exact_asking_price`告警，且quote包含完整候选值和限定词，证据不能截断。它可与`multiple_prices`并用以标注其他报价；精确范围继续使用`price_ranges`，不要求非精确告警。 对应面积范围使用`non_exact_area_ranges`：将`area_sqm`留空并填写完整范围候选；评估器要求全部对应范围证据均有`is_non_exact=true`、`non_exact_area_sqm`告警及含候选值和限定词的quote。精确范围使用`area_ranges`。
- reviewed_by 使用不含个人身份信息的操作者代号；时间使用带时区的 ISO-8601。
- area_sqm 须为大于0且不超过20000的有限数；最终人工`bedrooms`须为0至20的整数（0表示无独立卧室）。`bedroom_candidates`记录页面原始户型提及，允许0至99的整数以保留越界冲突证据；越界候选不能作为最终`bedrooms`标签。asking_price_wan及冲突报价须大于0且不超过200000万元；multiple_prices中的报价必须至少有两个不同数值。千分位逗号必须按每组三位数字书写。

## 校验

在项目根目录执行：

    python scripts/validate_sample_set.py

校验器只接受以`.html`或`.html.gz`结尾的样本文件，并检查CSV清单本身使用有效UTF-8编码、采用严格引号语法、表头无重复/空列且不得包含模板之外的额外字段、每行字段数与表头一致、两来源数量、所需状态/场景覆盖、文件路径边界（路径控制字符拒绝）、SHA-256、域名与URL格式、许可依据字段及标签约束；`invalid_bedroom_candidates`要求单个21–99整数并与多户型场景互斥；来源ID冲突候选须符合来源ID格式并包含详情URL中可识别的ID；结构错误行不会计入样本数；普通/解压HTML还必须通过严格UTF-8解码。HTML解压后上限为1,000,000字节，gzip文件读取上限为2,000,000字节，超限样本会在解析前拒绝；样本根目录或文件路径含符号链接时拒绝清单。`submit_html_snapshot.py`同样会在本地API请求前限制UTF-8 HTML为1,000,000字节。它不访问网站、不读取页面内容作法律判断，也不把虚构测试样本当作真实验收样本。测试用临时虚构文件只验证校验器逻辑。

## 解析器准确率与覆盖率

通过清单校验后，在项目根目录执行：

    python scripts/evaluate_parser.py

清单校验器和评估器都只读取本地CSV及`.html`/`.html.gz`样本，不访问网站；CSV清单最大2,000,000字节，两个入口均在解析前执行有界读取，评估器另在评估后复核清单未变化。超限或评估期间清单增长都会拒绝。默认要求每站至少20份、哈希与人工标注完整且覆盖active/withdrawn及三个必需异常场景。评估器按来源和九项字段（含页面标题）输出严格匹配准确率、有效字段覆盖率及已输出字段精确率，文本字段在比较前折叠空白并做Unicode NFC规范化，数值仍按Decimal精确比较；并对清单中出现的字段歧义标签分别核验“字段留空且解析器发出对应警告”；当场景使来源ID、小区、面积或挂牌价任一核心必需字段无值时，还要求`ready_for_review=false`；可选`area_ranges`/`price_ranges`/`non_exact_area_ranges`/`non_exact_price_ranges`场景进一步核对完整范围证据；非精确范围标签还强制对应非精确标记、告警和限定词证据，范围作为Decimal端点对而非两个端点单值比较；`title_source_conflict`单独核验非空标题真值、歧义警告、所选来源避开歧义来源及标题准确性。准确率分母包括已标注字段、明确缺失字段、有标记的歧义字段，以及标记为`oral_prices`/`transaction_prices`且挂牌价为空的非挂牌价格场景；这类场景中的非挂牌金额误报计入准确率和精确率。未解析的`multiple_prices`不进入单值价格准确率，单独检查不误选。报告中的`sample_requirements`始终显示正式门槛（每站20份）、实际数量和是否达标；`sample_composition`显示每站各挂牌状态及场景标签的样本数；为测试而降低`--minimum-per-source`不会降低或隐藏正式门槛。 `multiple_prices`场景会对账解析证据中的全部报价候选与人工`price_candidates_wan`（单值按Decimal、范围按两个端点比较）；字段歧义场景会对账解析证据的完整候选集合与对应`*_candidates`列（按字段规范化比较，面积范围按两个端点比较）。候选缺失、不相等或超过证据上限导致截断时，场景判为未通过。

校验器不会判断授权效力，评估结果只有在页面确为获准真实样本且人工标签准确时才可用于P0-03验收。歧义场景按数值/规范化文本集合（文本先做NFC及空白折叠）与解析证据精确核对，且证据必须完整未截断。仓库fixture及临时虚构测试数据不能作为实际准确率结果。
