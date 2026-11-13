# 本地视频媒体流水线（Issue #12）

将运营人员**有权处理的本地视频文件**转换为逐字稿、画面文字与结构化房产线索，并可选提交到现有 `PATCH /api/videos/{video_id}/enrichment`。不访问抖音/微信页面，不爬取，不涉及验证码或授权绕过。

## 1. 链路

```
本地 MP4/mov/mkv/... 
  → 校验（扩展名/大小）→ 复制到隔离工作目录（input.media，同时计算原始 SHA-256）
  → ffprobe（时长/分辨率/音轨存在性；时长超限拒绝）
  → ffmpeg 提取 16kHz 单声道 WAV（无音轨 → transcript 标记 no_audio）
  → ffmpeg 按固定间隔抽取关键帧（默认 2s 一帧，上限 12 帧）
  → ASR（FunASR / mock 人工逐字稿）→ transcript
  → OCR（RapidOCR / mock）→ 每帧文字 + 帧出处（帧号/路径/时间戳/置信度）
  → extract_hints(ocr_text, transcript)（复用 app/extractor.py）
  → dry-run 结构化 JSON；或 --submit 走现有 enrichment 接口
```

提交路径复用现有服务端逻辑：`services.enrich_video` 用 COALESCE 合并 transcript/ocr_text，并用数据库内小区名单重算 hints 写入 `extracted_fields`。**口播/画面价格只作为线索，绝不写成平台挂牌价**（extractor 自带警告，服务端不写 source_listings 价格）。

## 2. 用法

```bash
# 离线闭环（无需数据库/API Key）：真实 FFmpeg + mock 引擎 + 人工逐字稿
python scripts/enrich_local_video.py listing.mp4 \
  --asr mock --asr-script transcript.txt \
  --ocr mock --ocr-text "小区：东湖花园 总价：365万 建筑面积：160㎡"

# 提交到现有视频行（NAS 本机 API，默认 http://127.0.0.1:8788）
APP_API_KEY=... python scripts/enrich_local_video.py listing.mp4 \
  --video-id <uuid> --submit

# LAN/私有地址 API 需要显式 opt-in
... --submit --api-url http://192.168.1.10:8788 --allow-private-network
```

- API Key **只**从 `APP_API_KEY` 环境变量读取，绝不写入命令行历史、日志或 JSON 输出。
- `--keep-work DIR` 保留音频/关键帧供人工复核；DIR 必须不存在，脚本以 0700 创建，避免覆盖已有文件/符号链接；默认临时目录处理完即清理。
- 退出码：0 成功；2 非法输入/超限；3 处理失败（ffmpeg 等）；4 提交失败。

## 3. 引擎与状态语义

| 引擎 | 说明 |
|---|---|
| ASR `funasr` | 只加载本地已安装模型目录（`FUNASR_MODEL`）；未安装依赖/本地模型 → `unavailable`，不会自动下载模型 |
| ASR `mock` | 测试与**人工逐字稿**路径；输出永远带 `engine='mock'` 并在 warnings 中声明"非真实转写" |
| OCR `rapidocr` | 优先真实引擎（rapidocr-onnxruntime）；失败 → `unavailable` |
| OCR `mock` | 测试与人工标注路径；同上有 mock 标记 |

`auto`：真实引擎可用则用真实引擎；ASR 无可供脚本时显式 `unavailable`（不产出空内容）；OCR 回落 mock 并标记。

## 4. 资源限制（绿联 DXP4800 N100 / 16GB，默认单任务）

| 参数 | 默认 | 环境变量覆盖 |
|---|---|---|
| 输入文件上限 | 1 GiB | `NBRE_MEDIA_MAX_BYTES` |
| 时长上限 | 1800 s（30 分钟） | `NBRE_MEDIA_MAX_DURATION_SECONDS` |
| 关键帧间隔 | 2 s（仅允许 1/2/3/5/10） | `NBRE_MEDIA_KEYFRAME_INTERVAL_SECONDS` |
| 关键帧上限 | 12 帧/视频（固定） | — |
| 单次 ffmpeg 超时 | 120 s | — |
| 并发 | 单任务（CLI 一次一个文件） | — |

## 5. NAS 部署说明

- ffmpeg/ffprobe 需在 PATH（容器内 `apk add ffmpeg` 或基础镜像自带）。
- 真实模型（可选，分容器或按需安装，不要常驻大模型）：
  ```bash
  pip install funasr                      # ASR 运行时；模型另行预下载到本地目录
  pip install rapidocr-onnxruntime        # OCR（onnxruntime CPU）
  ```
  通过 `FUNASR_MODEL=/path/to/local/model` 指向预先下载的模型目录；运行时不自动联网下载。可用环境变量记录模型版本：`FUNASR_MODEL_VERSION`、`RAPIDOCR_MODEL_VERSION`。
- **许可证**：FFmpeg 为 LGPL/GPL（按编译选项）；FunASR 与 RapidOCR 为开源模型/运行时，各自许可证（MIT/Apache-2.0 等）随版本变化，商用分发前须单独核对；本文档不构成许可结论。
- 磁盘：每视频临时占用 ≈ 输入副本 + WAV（约 32KB/s×时长）+ 12 张 1280px JPG；`--keep-work` 会保留，需运营定期清理。
- CPU/内存：默认单任务；ffmpeg 不做额外并发设置；如 NAS 同时跑采集 Worker，建议错峰运行。

## 6. 安全边界

- ffmpeg argv 为纯字面量（无 shell、`shell=False`）；媒体文件复制为固定名 `input.media`，输入拒绝符号链接，拷贝时再次以 no-follow 打开并限量；私有空工作目录以 `cwd` 运行，命令限制为 `file,pipe` 协议，不能访问网络。
- 输入先校验（扩展名白名单、大小、`resolve` 后仅接受普通文件），工作目录隔离，异常/失败统一 `MediaPipelineError` 稳定 kind，日志只含脱敏摘要（退出码 + stderr 首行截断），不泄漏文件路径与密钥。
- enrichment 提交只允许 http/https、拒绝 URL 内凭据/路径/query/fragment；只接受 IP 字面地址，回环地址默认允许，私有/LAN IP 需 `--allow-private-network` 显式 opt-in；主机名和公网 IP 拒绝，避免 API Key 发往外部服务。
- 不绕过任何验证码/风控/限流；媒体内容须为运营有权处理。

## 7. 已验证与未验证（2026-11-13）

**已验证（本机 macOS）**
- 真实 FFmpeg 9.0.2 链路 + mock 引擎：合成 MP4（testsrc2+sine，6 秒带音轨）→ 真实 ffprobe/音频/3 帧 → extract_hints 输出 365万/160㎡、证据 quote 与帧出处。
- **真实 RapidOCR 推理（rapidocr-onnxruntime CPU）**：合成房源视频（8 秒、4 行中文文字：小区/总价/面积/户型装修）→ 真实抽 4 帧 → 每帧 4 行全部识别（置信度 0.94–0.9998；`㎡` 被识别为 `m²`，extractor 的面积正则同时覆盖两种写法）→ hints 输出 `price_mentions_wan=[365.0]`、`area_mentions_sqm=[160.0]`、证据来源 `ocr_text`。端到端 0.86–1.14 s，峰值内存 ≈481–504 MB（`/usr/bin/time -l`）。首跑暴露新版 RapidOCR `(rows, elapse)` 元组返回契约：已修复为防御性解包（整行 repr 与 elapse 不得进入 OCR 文本，含失败先行回归）。
- **enrichment 测试库闭环（Docker 隔离 PostgreSQL 16，sql 001–014 全量迁移）**：`POST /api/ingest/videos` 建行 → CLI `--ocr rapidocr --submit` → 服务端真实写入 `videos.transcript/ocr_text/extracted_fields`，`processing_status='enriched'`，服务端按库内小区名单重算 hints；**`source_listings` 与 `price_history` 均为 0 行**——口播价/画面价未进入正式挂牌与价格历史。
- 单元测试（媒体流水线 47+ 项）：无音频、空 OCR、重复运行确定性、超长/超大/非法扩展名、ffmpeg 失败、ASR/OCR unavailable、多价格并存仅作线索、CLI dry-run/退出码/密钥不泄漏/私网 opt-in、RapidOCR 元组契约。

**未验证（明确标记，不视为完成）**
- FunASR 真实模型推理（未安装；mock/人工逐字稿路径已验证并被强制标记非真实转写）。
- NAS（DXP4800）容器内 ffmpeg/RapidOCR 端到端与资源占用。
- 真实房产视频（非合成）的识别准确率。
- 抖音/视频号平台采集相关能力（本流水线只处理运营本地文件）。

## 8. 文件清单

- `app/media_pipeline/`：errors / limits / models / ffmpeg_tools / asr / ocr / pipeline / enrich_api
- `scripts/enrich_local_video.py`：CLI
- `tests/test_media_pipeline_ffmpeg.py`、`tests/test_media_pipeline_engines.py`、`tests/test_media_pipeline_pipeline.py`、`tests/test_enrich_local_video.py`
