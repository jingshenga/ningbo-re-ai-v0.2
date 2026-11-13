# NAS 媒体流水线隔离验收

## 隔离范围

该流程从 GitHub main 精确源码副本启动独立 Compose 项目 `rehouse-ai-uat-20261113`，只创建 PostgreSQL 17 的 `rehouse-ai-uat-20261113-pgdata` 卷和 `rehouse-ai-uat-20261113_private` 网络。

- API 仅绑定 NAS 本机 `127.0.0.1:18788`；数据库不发布宿主机端口。
- 采集全局开关固定为 false，DTK 地址与密钥为空。
- 不引用 `ningbo-re-ai` 生产 Compose 文件以外的配置、数据库或卷；基础服务挂载相对当前隔离源码目录的 `./data`。
- 命令中的 `stop` 只停止该测试项目，不删除数据卷；生产项目及卷不在命令目标内。
- 合成视频和随机测试凭据均只进入隔离目录/卷。

不要把生产 `/volume3/docker/ningbo-re-ai` 目录当成本流程源码。应将同一 Git commit 的源码检出或解包到新的隔离目录。

## 媒体依赖设计

基础 `Dockerfile` 只安装 API Python 依赖；NAS 当前生产 API 镜像未发现 FFmpeg 或 `rapidocr_onnxruntime`。隔离镜像仅增加 FFmpeg 与固定版本 `rapidocr_onnxruntime==1.4.4`，不改变生产依赖或部署镜像。

当前 `RapidOcrEngine` 以 `RapidOCR()` 默认参数初始化，不接收外部模型根路径。因此 UAT 将 RapidOCR 与其默认模型资产一并固定在镜像中，不挂载一个应用实际不会读取的“模型卷”。若后续要独立持久化模型，须先由采集/媒体负责人提供经验证的显式模型路径契约；建议主机路径为 `/volume3/docker/ningbo-re-ai-models/rapidocr/<模型版本>`，容器只读挂载到 `/models/rapidocr`，同时校验模型文件 SHA-256。该目录在当前 UAT 不创建、不挂载。

UAT 用 `--ocr mock --ocr-text` 检验“媒体文件 → FFmpeg 抽帧 → 结果写入既有 enrichment API”协作链路。真实中文 OCR 质量仍由已提供媒体样本的质量验收确认，本脚本不把 mock 结果当作真实 OCR 通过。

## 启动和验收

在具备 Docker 权限的 NAS 隔离目录内执行：

```bash
chmod +x scripts/nas_media_uat.sh
scripts/nas_media_uat.sh accept
```

首次启动时脚本创建权限为 0600 的 `.env.uat`，随机生成独立数据库密码与 API key，不会打印凭据。Compose 会：

1. 仅构建并启动隔离项目的 PG17、API、worker。
2. 等待 PG17 就绪并用失败即退出的 PostgreSQL DO 断言逐个检查 001–014 的关键表、列、索引与触发器签名。
3. 检查 FFmpeg、RapidOCR 包/模型初始化和现有管理后台登录页。
4. 用 FFmpeg 生成合成 MP4，创建合成视频行，以手工 OCR 文本写入既有 enrichment API。
5. 核实视频处于 `enriched` 且保留提取字段；脚本另输出挂牌及历史价格表记录数，视频步骤不调用挂牌写入接口。
6. 对一个无效媒体文件触发预期处理错误，再检查 API 与 PG17 可用。

检查运行状态与停止测试容器：

```bash
scripts/nas_media_uat.sh status
scripts/nas_media_uat.sh stop
```

卷会保留，供复核日志和合成记录。不要使用 `down -v` 或任何全局 prune 命令。本地验收结束后如需销毁此测试卷，请单独确认卷名并只删除明确的隔离卷；不得碰生产卷。

## 成功证据与边界

要求终端输出完整脚本结束标记、Compose 状态包含 PG17/API/worker、API health 与 Admin login GET 成功、视频 enrichment 返回成功、媒体故障后 API/PG17 仍健康。记录 main SHA、UAT 开始/结束时间、独立卷名称及生成的合成视频 ID。

`accept` 的脚本实际执行结果才是 NAS Docker 验收证据。GitHub Actions 或静态 Compose 校验不等于 NAS 实际运行验收；真实 OCR 准确率也不是该脚本的验收目标。


## NAS 实际隔离验收记录（2026-11-13）

DXP4800（Docker 29.6.2 / Compose v5.1.3）已在 `main 47e72124dd7fe4f2ed1577d54ff384ed1cfbc35d` 运行时源码上执行 `scripts/nas_media_uat.sh accept`。UAT Compose 项目 `rehouse-ai-uat-20261113`、PG17 卷 `rehouse-ai-uat-20261113-pgdata` 与 API `127.0.0.1:18788` 独立；PG 数据卷只挂在 UAT DB，API/worker 只绑定 UAT 源码的 `./data`，未引用生产项目或 `ningbo-re-ai_pgdata`。

验收结果：PG17 healthy；迁移 006/012/013/014 签名校验通过；FFmpeg 7.1.5 和 `rapidocr_onnxruntime==1.4.4` 模型初始化成功；管理后台登录 GET 与 API health 均通过；合成 2 秒 MP4 成功写入既有 video enrichment API（记录 ID `04d54230-57bd-47cc-b810-58274207c5ac`，`processing_status=enriched`）；脚本在 enrichment 后验证 `source_listings=0`、`price_history=0`；畸形媒体按预期返回输入错误，随后 API 和 PG17 仍健康。项目状态显示 3/3 运行，连续两次有效运行留下 2 条合成视频记录（`04d54230-57bd-47cc-b810-58274207c5ac` 与 `e751f7ac-15d8-4acb-a5ad-1e7b58cea296`），二者均为 `enriched`。

第一次脚本运行暴露了启动就绪等待和宿主机 bind 目录权限问题；修正后已在最终脚本上重新通过。UAT 数据卷和项目保留以便复核。此验收的 OCR 文本使用 mock 输入；仅证明媒体/FFmpeg/enrichment 协作与故障隔离，不构成真实 OCR 质量证明，也不是生产迁移或生产数据库验收。
