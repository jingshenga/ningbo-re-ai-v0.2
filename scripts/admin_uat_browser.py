#!/usr/bin/env python3
"""Real Chromium acceptance of the admin workflow against an isolated UAT stack."""
import json
import os
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get("ADMIN_UAT_BASE_URL", "http://127.0.0.1:18787").rstrip("/")
API_KEY = os.environ["ADMIN_UAT_API_KEY"]
REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "fixtures" / "beike_demo.html"
ARTIFACTS = Path(os.environ.get("ADMIN_UAT_ARTIFACT_DIR", "artifacts/admin-uat"))
ARTIFACTS.mkdir(parents=True, exist_ok=True)
steps = []
records = {}


def record(name, detail, screenshot=None):
    steps.append({"name": name, "result": "PASS", "detail": detail})
    if screenshot:
        page.screenshot(path=str(ARTIFACTS / screenshot), full_page=True)


def assert_no_api_key_in_browser():
    assert API_KEY not in page.content(), "APP_API_KEY appeared in rendered page"
    assert not page.evaluate("() => Object.values(localStorage).join(' ')").find(API_KEY) >= 0


def navigate(path, heading, empty_text=None, screenshot=None):
    page.goto(BASE_URL + path, wait_until="domcontentloaded")
    page.get_by_role("heading", name=heading).wait_for()
    if empty_text:
        assert empty_text in page.locator("body").inner_text()
    assert_no_api_key_in_browser()
    record("页面 " + heading, "HTTP页面可由 Chromium 实际访问；" + (empty_text or "页面内容已核对"), screenshot)


def import_candidate(html_text, label):
    page.goto(BASE_URL + "/admin/import", wait_until="domcontentloaded")
    form = page.locator("form[action='/admin/import']")
    form.locator("select[name='source']").select_option("beike")
    form.locator("input[name='source_url']").fill("https://nb.ke.com/ershoufang/109900001234.html")
    form.locator("input[name='note']").fill("自动化验收合成数据")
    form.locator("textarea[name='html']").fill(html_text)
    form.get_by_role("button", name="解析并创建待审核候选").click()
    try:
        page.get_by_role("heading", name="候选详情").wait_for()
    except Exception as exc:
        page.screenshot(path=str(ARTIFACTS / (label + "-import-error.png")), full_page=True)
        raise AssertionError(
            f"HTML import did not reach candidate detail: url={page.url!r}, "
            f"body={page.locator('body').inner_text()[:1000]!r}"
        ) from exc
    assert "样本已解析并进入待审核" in page.locator("body").inner_text()
    assert "pending" in page.locator("body").inner_text()
    candidate_id = urlparse(page.url).path.split("/")[-1]
    records[label + "_candidate_id"] = candidate_id
    assert_no_api_key_in_browser()
    record(label + " 导入待审", "候选ID=" + candidate_id, label + "-candidate.png")
    return candidate_id


def approve_candidate(candidate_id, correct_fields=False, label="candidate"):
    page.goto(BASE_URL + "/admin/candidates/" + candidate_id, wait_until="domcontentloaded")
    evidence_link = page.get_by_role("link", name="查看保存的原始HTML证据")
    evidence_link.click()
    page.get_by_role("heading", name="原始HTML证据").wait_for()
    assert "东湖花园" in page.locator("body").inner_text()
    record(label + " 原始证据核查", "浏览器打开经哈希校验并转义显示的合成HTML证据", label + "-evidence.png")
    page.get_by_role("link", name="返回候选详情").click()
    page.get_by_role("heading", name="候选详情").wait_for()

    if correct_fields:
        form = page.locator("form[action='/admin/candidates/" + candidate_id + "']")
        form.locator("input[name='correct_bedrooms']").check()
        form.locator("input[name='bedrooms']").fill("5")
        form.locator("input[name='review_note']").fill("确认合成户型字段")
        form.get_by_role("button", name="保存纠错").click()
        assert "纠错已保存" in page.locator("body").inner_text()
        assert page.locator("form[action='/admin/candidates/" + candidate_id + "'] input[name='bedrooms']").input_value() == "5"
        record(label + " 人工纠错表单", "勾选并保存卧室数字段，页面回显纠错结果", label + "-correction.png")

    review_form = page.locator("form[action='/admin/candidates/" + candidate_id + "/review']")
    review_form.locator("input[name='review_note']").fill("通过合成验收样本")
    review_form.locator("button[name='decision'][value='approve']").click()
    assert "审核已记录" in page.locator("body").inner_text()
    record(label + " 人工审批", "审核表单提交通过；正式挂牌由现有审批服务写入", label + "-approved.png")


def run():
    global page
    if not FIXTURE.is_file():
        raise FileNotFoundError(FIXTURE)
    original = FIXTURE.read_text(encoding="utf-8")
    if "365万" not in original:
        raise AssertionError("Synthetic fixture price anchor changed; update UAT fixture transform")
    reduced = original.replace("365万", "340万", 1).replace("4室2厅", "5室2厅", 1)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        page.set_default_timeout(10000)

        landing_response = page.goto(BASE_URL + "/admin/", wait_until="domcontentloaded")
        assert landing_response and landing_response.status == 401
        assert "Admin login required" in page.locator("body").inner_text()
        page.goto(BASE_URL + "/admin/login", wait_until="domcontentloaded")
        page.get_by_role("heading", name="宁波房产工作台").wait_for()
        page.get_by_label("APP_API_KEY").fill("invalid-uat-key")
        page.get_by_role("button", name="登录").click()
        assert "API Key 不匹配" in page.locator("body").inner_text()
        record("未登录保护与错误提示", "受保护首页未登录返回401；错误凭据被拒绝并显示提示", "login-error.png")

        page.get_by_role("link", name="返回登录").click()
        page.get_by_label("APP_API_KEY").fill(API_KEY)
        page.get_by_role("button", name="登录").click()
        page.get_by_role("heading", name="项目总览").wait_for()
        cookies = context.cookies()
        session_cookie = next((item for item in cookies if item.get("httpOnly")), None)
        assert session_cookie and session_cookie.get("sameSite") == "Strict"
        assert API_KEY not in page.content()
        record("登录与会话安全", "登录成功；会话Cookie为HttpOnly/SameSite=Strict；页面未泄露API Key", "dashboard-empty.png")

        nav_cases = [
            ("/admin/listings", "房源库", "尚无符合条件的正式挂牌。"),
            ("/admin/candidates", "候选审核", "该筛选条件下暂无候选。"),
            ("/admin/import", "HTML样本导入", None),
            ("/admin/searches", "条件找房", "尚无条件单。"),
            ("/admin/opportunities", "降价与挂牌机会", "所选时间窗内暂无同来源挂牌降价记录。"),
            ("/admin/monitoring", "视频账号监控", "尚未配置DTK服务"),
        ]
        for path, heading, empty_text in nav_cases:
            link = page.locator("nav a[href='" + path + "']")
            if link.count():
                link.first.click()
                page.get_by_role("heading", name=heading).wait_for()
            else:
                navigate(path, heading, empty_text)
            if empty_text:
                assert empty_text in page.locator("body").inner_text()
            assert_no_api_key_in_browser()
            record("导航与空状态 " + heading, empty_text or "导航链接可用", heading.replace("/", "-") + "-empty.png")

        csrf_status = page.evaluate("""async () => {
          const response = await fetch('/admin/searches', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: 'name=csrf-without-token'
          });
          return response.status;
        }""")
        assert csrf_status == 403, "CSRF-free write unexpectedly returned " + str(csrf_status)
        record("CSRF拒绝", "真实浏览器同源提交缺失CSRF token的写请求，服务端返回403")

        candidate1 = import_candidate(original, "first")
        approve_candidate(candidate1, correct_fields=True, label="first")

        candidate2 = import_candidate(reduced, "price-drop")
        approve_candidate(candidate2, correct_fields=False, label="price-drop")

        navigate("/admin/listings", "房源库")
        listing_link = page.locator("a[href^='/admin/listings/']").first
        listing_url = listing_link.get_attribute("href")
        assert listing_url
        page.goto(BASE_URL + listing_url, wait_until="domcontentloaded")
        page.get_by_role("heading", name="东湖花园").wait_for()
        assert "365.00" in page.locator("body").inner_text()
        assert "340.00" in page.locator("body").inner_text()
        assert "5室" in page.locator("body").inner_text()
        history_section = page.locator("section.panel").filter(has_text="价格历史")
        assert history_section.locator("tbody tr").count() >= 2
        listing_id = listing_url.rstrip("/").split("/")[-1]
        records["listing_id"] = listing_id
        record("挂牌入库与价格历史", "同来源合成挂牌已入库，详情含365万与340万两条证据记录；挂牌ID=" + listing_id, "listing-history.png")

        page.goto(BASE_URL + "/admin/searches", wait_until="domcontentloaded")
        form = page.locator("form[action='/admin/searches']")
        form.locator("input[name='name']").fill("UAT东湖花园改善房")
        form.locator("input[name='district']").fill("鄞州")
        form.locator("input[name='max_price_wan']").fill("400")
        form.locator("input[name='min_area_sqm']").fill("140")
        form.locator("input[name='min_bedrooms']").fill("5")
        form.get_by_role("button", name="保存条件").click()
        page.get_by_role("heading", name="匹配房源").wait_for()
        assert "东湖花园" in page.locator("body").inner_text()
        match_row = page.locator("tbody tr").filter(has_text="东湖花园").first
        assert match_row.locator("td").nth(3).inner_text().strip()
        search_id = urlparse(page.url).path.split("/")[-2]
        records["saved_search_id"] = search_id
        record("条件单匹配", "浏览器提交条件单并看到挂牌匹配与非空匹配理由；条件单ID=" + search_id, "saved-search-match.png")

        page.goto(BASE_URL + "/admin/opportunities?days=7", wait_until="domcontentloaded")
        body = page.locator("body").inner_text()
        assert "降" in body and "365.00" in body and "340.00" in body, "Seven-day drop opportunity is missing"
        record("降价机会", "7天窗口显示同挂牌365万→340万的历史降价机会及证据", "opportunities.png")

        response = page.goto(BASE_URL + "/admin/opportunities?days=13", wait_until="domcontentloaded")
        assert response and response.status == 422
        assert "days must be 7, 30, or 90" in page.locator("body").inner_text()
        record("异常提示", "无效机会窗口返回HTTP 422和明确错误原因", "invalid-window.png")

        navigate("/admin/monitoring", "视频账号监控")
        monitor = page.locator("body").inner_text()
        assert "尚未配置DTK服务" in monitor
        assert "尚未添加监控账号" in monitor
        assert "尚无导入视频" in monitor
        record("监控状态", "无DTK时明确标记未配置，账号和视频空状态如实显示", "monitoring.png")

        page.locator("form[action='/admin/logout'] input[name='csrf']").wait_for(state="attached")
        page.locator("form[action='/admin/logout'] button").click()
        assert urlparse(page.url).path == "/admin/login"
        response = page.goto(BASE_URL + "/admin/", wait_until="domcontentloaded")
        assert response and response.status == 401
        assert "Admin login required" in page.locator("body").inner_text()
        record("退出", "退出后会话失效；受保护首页返回401", "logout.png")
        browser.close()


try:
    run()
    outcome = "PASS"
except Exception as exc:
    outcome = "FAIL: " + type(exc).__name__ + ": " + str(exc)
    raise
finally:
    lines = [
        "# 管理后台真实浏览器验收",
        "",
        "- 状态：" + outcome,
        "- Commit：" + os.environ.get("UAT_COMMIT_SHA", "unknown"),
        "- 浏览器：Playwright Chromium（headless，真实浏览器进程）",
        "- 测试数据：fixtures/beike_demo.html 派生合成页面；ID 109900001234",
        "- 服务地址：" + BASE_URL,
        "- 生产数据库/NAS：未连接、未修改",
        "",
        "## 操作记录",
        "",
    ]
    for step in steps:
        lines.append("- [" + step["result"] + "] " + step["name"] + " — " + step["detail"])
    lines.extend(["", "## 合成记录ID", ""])
    for key, value in records.items():
        lines.append("- " + key + ": " + str(value))
    lines.extend(["", "截图位于本报告同目录。", ""])
    (ARTIFACTS / "ADMIN_UI_ACCEPTANCE.md").write_text(chr(10).join(lines), encoding="utf-8")
