# 管理后台隔离浏览器验收

本验收使用独立临时 checkout、唯一 Compose 项目、全新 PostgreSQL 17 卷、内部 Docker 网络和真实 Chromium 浏览器进程。只启动 `db` 与 `api`，不启动 worker；在线采集关闭、DTK 未配置。不会连接 NAS 或生产数据库。

## 执行

使用干净的 Git checkout（不要在含 ZIP 或其他未提交文件的工作目录执行）：

```sh
python3 -m pip install -r requirements-dev.txt
bash scripts/admin_uat.sh
```

脚本从当前 Git commit 创建临时源码树，随机生成仅用于本次验收的 PostgreSQL 密码和 APP_API_KEY，并以 Compose 项目 `ningbo-admin-uat-<timestamp>-<pid>` 启动全新 PostgreSQL 17 与 API，并构建固定 Playwright 版本的浏览器验收镜像。Chromium 容器加入仅供该项目使用的 internal 网络，通过 `http://api:8000` 访问服务；API 健康探针也在 API 容器内执行。端口变量留作本机调试配置。可用 `ADMIN_UAT_PORT` 改端口；默认将截图/报告写入系统临时目录，也可用 `ADMIN_UAT_ARTIFACT_DIR` 指定目录；默认不会在源码checkout内留下产物。完成或失败后仅清理该唯一 Compose 项目的容器、网络和命名卷、此次构建的唯一浏览器镜像，以及本次临时源码目录。

不要把主 Compose 项目名、已有环境变量文件、NAS卷或生产数据库 URL 传给脚本。脚本在源码树脏时拒绝运行，并且不会启动 worker。隔离网络为 Docker internal 网络，浏览器也在容器内实际运行；测试样本来自仓库合成 fixture，流程不访问外部网站。

## 浏览器流程与证据

`scripts/admin_uat_browser.py` 以 Playwright Chromium 实际启动浏览器并提交 HTML 表单，覆盖登录拒绝/成功、会话 Cookie、安全Key不回显、导航、空状态、缺少CSRF时写请求被拒绝、合成HTML导入、原始证据核验、人工纠错与审批、再次导入同一来源挂牌的降价版本、价格历史、条件单匹配理由、7天降价机会、无效窗口提示、DTK缺失状态与退出。浏览器截图和 `ADMIN_UI_ACCEPTANCE.md` 写入验收产物目录。CI workflow 上传为保留14天的 Actions artifact。

CI与TestClient检查不能替代这项浏览器验收。Issue #5 只有在浏览器workflow成功且人工检查截图/报告之后才可关闭。
