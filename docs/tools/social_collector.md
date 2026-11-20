# 社交线索采集助手（Tampermonkey 油猴脚本）使用说明

`tools/userscripts/ningbo_re_collector.user.js` 在小红书 / 抖音 / 微信（视频号·公众号）网页上注入一个右下角悬浮按钮（`🏠 采`），把**你正在看的这一条帖子**采集为宁波房产线索，推送到你自己的 NAS 后端。

## 合规边界（先读这段）

- **单条、人工触发**：每点一次只采集当前页面这一条；脚本不做后台轮询、不批量抓取、不绕过验证码/登录/风控/频率限制。
- **平台条款仍有效**：你有权浏览不等于可以批量复制或商用；请自行确认各平台服务条款与内容权利，仅采集你有权保存与处理的内容。
- **数据只进你自己的 NAS**：脚本只把当前页面内容推送到你配置的后端地址；不经任何第三方中转。
- **结果只是线索**：入库内容带 `not_calibrated` 置信状态，只是待核实线索，**不会**写入正式挂牌（source_listings）或价格历史（price_history）。

## 安装

1. 浏览器安装 [Tampermonkey](https://www.tampermonkey.net/) 扩展。
2. Tampermonkey 控制台 → 新建脚本 → 粘贴 `tools/userscripts/ningbo_re_collector.user.js` 全部内容并保存（或拖入 .user.js 文件安装）。
3. 确认脚本已启用；目标平台页面右下角出现 `🏠 采` 圆形按钮。

## 配置后端地址

1. 点击 `🏠 采` 展开面板 → 「设置」；
2. **后端 API 地址**：默认 `http://127.0.0.1:8000`。若后端跑在 NAS 其他端口（如 UAT 的 18788），改为 `http://<NAS内网IP或回环>:<端口>`；仅允许本机/私网 HTTP(S) 地址，不能经过公网代理或填写带路径、账号、查询参数的地址；
3. **X-API-Key**：后端配置了 `APP_API_KEY` 时必填且需与其一致；后端未配置密钥时只允许本机回环访问，此栏留空即可；
4. 「保存设置」（GM_setValue 本地持久化，不会同步到任何云端）。

## 三平台操作要点

| 平台 | 打开页面 | 提取效果 | 避坑 |
|---|---|---|---|
| 小红书 | 帖子详情页（弹窗或独立页均可） | `meta description` / `og:title` / `__INITIAL_STATE__`；正文通常可完整提取 | 站内弹窗若提取为空：手动划选正文文字后点「重新提取」（自动采用划选文本） |
| 抖音 | 视频/图文详情页 | `__UNIVERSAL_DATA_FOR_REHYDRATION__` JSON 与 meta | 视频口播内容不在页面文字里：请把标题/简介粘贴进正文框，或人工摘录关键信息 |
| 视频号·公众号 | 公众号文章页效果最好（`#activity-name`/`js_content`）；视频号页面信息少 | og/meta + 标题元素 | 视频号以人工摘录为主；公众号全文一般可直接提取 |

通用规则：

- **宁波关联指示灯**：面板根据标题+正文匹配 `宁波/海曙/鄞州/江北/镇海/北仑/奉化/高新区/东部新城/前湾新区/余姚/慈溪/宁海/象山`；指示"未识别"时推送会被后端 422 拒绝——可在正文里人工补写地名后再推（仅在内容确实与宁波相关时）。
- **人工微调**：标题/作者/正文均可编辑后再推送；正文为空或无宁波关键词时按钮会明确报错，不静默成功。
- **去重**：后端按 `platform + source_url + content` 规范化后的 SHA-256 幂等去重；重复推送返回 `duplicate`，不会产生重复记录。

## 后端接口（供核对）

`POST /api/v1/ingest/social`，JSON 字段：`platform(xiaohongshu|douyin|channels|other)`、`source_url`(https)、`post_id?`、`title?`、`content`(必填)、`author_name?`、`publish_time?`、`media_urls?`(≤20)、`tags?`(≤20)、`raw_html_snippet?`。

响应：`{status: stored|duplicate, id, sha256, is_ningbo_related, matched_keywords, hints}`。错误码：`not_ningbo_related`(422)、`storage_pending`(503，后端存储层未部署)、401/403（鉴权）。

入库表：`social_posts`（`sql/015_social_posts.sql`）。已有 NAS 环境需按项目迁移流程单独应用该迁移；全新 Compose 初始化会自动挂载迁移文件。请勿为应用迁移删除或重建现有数据库卷。

## 常见问题

- **推送报"无法连接后端"**：核对 API 地址端口、NAS 防火墙；脚本只允许 `localhost`/`127.0.0.1` 的 @connect 声明，NAS 内网 IP 直连需在 Tampermonkey 设置中把该地址加入脚本的网络白名单（或改用 SSH 隧道到本机端口）。
- **面板没出现**：确认 URL 匹配（脚本只在三个平台域名注入）、Tampermonkey 已启用该脚本；页面为 SPA 时可能需刷新一次。
- **为什么不做自动监控**：项目合规基线明确——线上自动化采集默认关闭、视频号仅手工导入；本脚本定位是"人工浏览 + 单条采集"的手动辅助，与自动化监控是两回事。
