// ==UserScript==
// @name         宁波房产线索一键采集助手 (Ningbo RE Collector)
// @namespace    https://github.com/jingshenga/ningbo-re-ai
// @version      1.0.0
// @description  在小红书/抖音/微信视频号页面上人工一键采集当前帖子为宁波房产线索，推送到自有 NAS 后端（单条、人工触发、仅内部留存）
// @author       ningbo-re-ai operator
// @match        https://*.xiaohongshu.com/*
// @match        https://*.douyin.com/*
// @match        https://*.weixin.qq.com/*
// @grant        GM_xmlhttpRequest
// @grant        GM_notification
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_registerMenuCommand
// @connect      localhost
// @connect      127.0.0.1
// ==/UserScript==

/*
 * 合规边界（务必遵守）：
 * - 仅在操作者本人正在浏览的页面上，经人工点击采集“当前这一条”内容；
 *   本脚本不做后台轮询、不批量抓取、不绕过验证码/登录/风控/频率限制。
 * - 各平台服务条款仍然有效；请仅采集你有权保存与处理的内容，
 *   并在NAS端记录来源与授权说明。
 * - 采集结果只是“待核实线索”（not_calibrated），不会成为正式挂牌或成交价。
 */

(function () {
  "use strict";

  // ---------- 配置（GM 存储，浏览器内不涉及 NAS 真实密钥之外的任何信息） ----------
  var DEFAULT_API_BASE = "http://127.0.0.1:8000";
  var INGEST_PATH = "/api/v1/ingest/social";
  var KEY_API_BASE = "nbre_api_base";
  var KEY_TOKEN = "nbre_api_token";
  var KEY_PANEL_OPEN = "nbre_panel_open";

  function isPrivateHost(host) {
    host = host.toLowerCase().replace(/^\[|\]$/g, "");
    if (host === "localhost" || host.endsWith(".localhost") || host.endsWith(".local")) return true;
    if (host === "::1" || /^f[cd][0-9a-f:]*$/i.test(host) || /^fe[89ab][0-9a-f:]*$/i.test(host)) return true;
    var parts = host.split(".");
    if (parts.length !== 4 || !parts.every(function (part) { return /^\d{1,3}$/.test(part) && Number(part) <= 255; })) return false;
    var a = Number(parts[0]), b = Number(parts[1]);
    return a === 10 || a === 127 || a === 192 && b === 168 || a === 172 && b >= 16 && b <= 31;
  }

  function normalizeApiBase(value) {
    try {
      var parsed = new URL(value);
      if ((parsed.protocol !== "http:" && parsed.protocol !== "https:") ||
          parsed.username || parsed.password || !["", "/"].includes(parsed.pathname) ||
          parsed.search || parsed.hash || !isPrivateHost(parsed.hostname)) return "";
      return parsed.origin;
    } catch (err) {
      return "";
    }
  }

  function getApiBase() {
    return normalizeApiBase(GM_getValue(KEY_API_BASE, DEFAULT_API_BASE) || DEFAULT_API_BASE) || DEFAULT_API_BASE;
  }
  function getToken() { return GM_getValue(KEY_TOKEN, "") || ""; }

  // ---------- 平台识别 ----------
  function detectPlatform() {
    var host = location.hostname.toLowerCase();
    if (host.indexOf("xiaohongshu.com") !== -1) return "xiaohongshu";
    if (host.indexOf("douyin.com") !== -1) return "douyin";
    if (host.indexOf("weixin.qq.com") !== -1) return "channels";
    return "other";
  }

  // ---------- 宁波地域关键词（与后端 app/social_service.py 保持一致） ----------
  var NINGBO_KEYWORDS = [
    "宁波", "海曙", "鄞州", "江北", "镇海", "北仑", "奉化",
    "高新区", "东部新城", "前湾新区", "余姚", "慈溪", "宁海", "象山"
  ];
  function matchNingbo(text) {
    var hits = [];
    NINGBO_KEYWORDS.forEach(function (kw) {
      if (text && text.indexOf(kw) !== -1 && hits.indexOf(kw) === -1) hits.push(kw);
    });
    return hits;
  }

  // ---------- 内容提取（优先 meta/og 与页面 JSON，划选文本作降级） ----------
  function metaContent(selector) {
    var el = document.querySelector(selector);
    return el ? (el.getAttribute("content") || "").trim() : "";
  }

  function safeParse(jsonText) {
    try { return JSON.parse(jsonText); } catch (err) { return null; }
  }

  // 在任意对象树中深度查找第一个包含目标键的字符串值（抖音 RENDER_DATA 等）。
  function deepFind(root, keys, depth) {
    if (!root || typeof root !== "object" || depth > 8) return "";
    for (var i = 0; i < keys.length; i++) {
      var value = root[keys[i]];
      if (typeof value === "string" && value.trim()) return value.trim();
    }
    for (var prop in root) {
      if (!Object.prototype.hasOwnProperty.call(root, prop)) continue;
      var found = deepFind(root[prop], keys, depth + 1);
      if (found) return found;
    }
    return "";
  }

  function extractFromState() {
    // 小红书：window.__INITIAL_STATE__；抖音：script#__UNIVERSAL_DATA_FOR_REHYDRATION__。
    var state = window.__INITIAL_STATE__;
    if (state) {
      var text = deepFind(state.noteDetailMap || state.note || state, ["desc", "title", "content"], 0);
      if (text) return text;
    }
    var hydration = document.querySelector("script#__UNIVERSAL_DATA_FOR_REHYDRATION__");
    if (hydration) {
      var data = safeParse(hydration.textContent);
      if (data) {
        var found = deepFind(data, ["desc", "title", "content"], 0);
        if (found) return found;
      }
    }
    return "";
  }

  function extractContent() {
    var candidates = [
      metaContent('meta[name="description"]'),
      metaContent('meta[property="og:description"]'),
      extractFromState()
    ];
    for (var i = 0; i < candidates.length; i++) {
      if (candidates[i]) return candidates[i];
    }
    // 降级：操作者划选的高亮文本（人工确认的内容）。
    var selection = "";
    try { selection = String(window.getSelection().toString() || "").trim(); } catch (err) { /* ignore */ }
    if (selection) return selection;
    return "";
  }

  function extractTitle() {
    var candidates = [
      metaContent('meta[property="og:title"]'),
      metaContent('meta[name="description"]').slice(0, 60),
      (document.querySelector("#detail-title") || {}).textContent || "",
      (document.querySelector("#activity-name") || {}).textContent || "",
      document.title.replace(/[_\-|（(].*$/, "").trim()
    ];
    for (var i = 0; i < candidates.length; i++) {
      if (candidates[i] && candidates[i].trim()) return candidates[i].trim().slice(0, 300);
    }
    return "";
  }

  function extractAuthor() {
    var named = document.querySelector('a[name], .author, [class*="author"], [class*="nickname"]');
    // 类名易混淆，仅作最后回退；优先 og:site_name / 作者 meta。
    var candidates = [
      metaContent('meta[name="author"]'),
      named ? named.textContent.trim() : "",
      metaContent('meta[property="og:site_name"]')
    ];
    for (var i = 0; i < candidates.length; i++) {
      if (candidates[i] && candidates[i].trim()) return candidates[i].trim().slice(0, 120);
    }
    return "";
  }

  function extractPublishTime() {
    var candidates = [
      metaContent('meta[property="article:published_time"]'),
      (document.querySelector("time[datetime]") || {}).getAttribute ?
        document.querySelector("time[datetime]").getAttribute("datetime") : ""
    ];
    for (var i = 0; i < candidates.length; i++) {
      if (candidates[i] && candidates[i].trim()) return candidates[i].trim().slice(0, 64);
    }
    return "";
  }

  function extractMediaUrls() {
    var urls = [];
    var images = document.querySelectorAll('meta[property="og:image"]');
    for (var i = 0; i < images.length && urls.length < 20; i++) {
      var url = (images[i].getAttribute("content") || "").trim();
      if (url && urls.indexOf(url) === -1) urls.push(url);
    }
    return urls;
  }

  function extractPostId() {
    var match = location.pathname.match(/([0-9a-f]{16,64})/i);
    return match ? match[1] : "";
  }

  function collectPayload(edits) {
    var content = (edits && edits.content) ? edits.content : extractContent();
    return {
      platform: detectPlatform(),
      source_url: location.href.split("#")[0],
      post_id: extractPostId(),
      title: ((edits && edits.title) ? edits.title : extractTitle()) || null,
      content: content,
      author_name: ((edits && edits.author) ? edits.author : extractAuthor()) || null,
      publish_time: extractPublishTime() || null,
      media_urls: extractMediaUrls(),
      tags: [],
      raw_html_snippet: null
    };
  }

  // ---------- UI：右下角悬浮按钮 + 抽屉面板（textContent 构建，防 XSS） ----------
  var panelOpen = GM_getValue(KEY_PANEL_OPEN, false);

  function el(tag, className, textContent) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (textContent !== undefined && textContent !== null) node.textContent = textContent;
    return node;
  }

  function buildPanel() {
    var wrap = el("div", "nbre-panel");
    wrap.id = "nbre-panel";
    wrap.style.cssText = "position:fixed;right:16px;bottom:76px;width:320px;max-height:70vh;overflow:auto;" +
      "background:#14263A;color:#E8EEF4;border-radius:12px;padding:14px;font:13px/1.6 system-ui,sans-serif;" +
      "box-shadow:0 8px 24px rgba(0,0,0,.35);z-index:2147483647;display:none;";

    var title = el("div", "nbre-title", "宁波房产线索采集");
    title.style.cssText = "font-weight:700;font-size:14px;margin-bottom:8px;";
    wrap.appendChild(title);

    var compliance = el("div", null, "仅采集你有权保存的内容；单条人工触发；结果为待核实线索。");
    compliance.style.cssText = "font-size:11px;color:#9FB0C0;margin-bottom:8px;";
    wrap.appendChild(compliance);

    function fieldRow(labelText, value, isTextarea) {
      var label = el("label", null, labelText);
      label.style.cssText = "display:block;font-size:11px;color:#9FB0C0;margin:6px 0 2px;";
      var field = isTextarea ?
        document.createElement("textarea") : document.createElement("input");
      field.className = "nbre-field-" + labelText;
      field.value = value || "";
      field.style.cssText = "width:100%;box-sizing:border-box;padding:6px;border-radius:6px;" +
        "border:1px solid #33475C;background:#0F1B2B;color:#E8EEF4;font:12px system-ui;" +
        (isTextarea ? "min-height:72px;resize:vertical;" : "");
      wrap.appendChild(label);
      wrap.appendChild(field);
      return field;
    }

    var platformRow = el("div");
    platformRow.appendChild(el("span", null, "平台："));
    var platformValue = el("strong", null, detectPlatform());
    platformRow.appendChild(platformValue);
    platformRow.style.cssText = "margin-bottom:4px;";
    wrap.appendChild(platformRow);

    var indicatorRow = el("div");
    indicatorRow.appendChild(el("span", null, "宁波关联："));
    var indicator = el("strong", null, "—");
    indicator.id = "nbre-indicator";
    indicatorRow.appendChild(indicator);
    indicatorRow.style.cssText = "margin-bottom:8px;";
    wrap.appendChild(indicatorRow);

    var titleField = fieldRow("标题", "", false);
    var authorField = fieldRow("作者", "", false);
    var contentField = fieldRow("正文（可人工微调）", "", true);

    var statusLine = el("div");
    statusLine.id = "nbre-status";
    statusLine.style.cssText = "font-size:12px;margin:8px 0;min-height:16px;";
    wrap.appendChild(statusLine);

    var buttonRow = el("div");
    buttonRow.style.cssText = "display:flex;gap:8px;";
    var pushButton = el("button", null, "一键推送");
    pushButton.style.cssText = "flex:1;padding:8px;border:0;border-radius:8px;background:#147D79;color:#fff;" +
      "font-weight:600;cursor:pointer;";
    var refreshButton = el("button", null, "重新提取");
    refreshButton.style.cssText = "padding:8px 10px;border:0;border-radius:8px;background:#33475C;color:#fff;cursor:pointer;";
    var settingsButton = el("button", null, "设置");
    settingsButton.style.cssText = "padding:8px 10px;border:0;border-radius:8px;background:#33475C;color:#fff;cursor:pointer;";
    buttonRow.appendChild(pushButton);
    buttonRow.appendChild(refreshButton);
    buttonRow.appendChild(settingsButton);
    wrap.appendChild(buttonRow);

    var settingsBox = el("div");
    settingsBox.style.cssText = "display:none;margin-top:10px;";
    var apiField = fieldRowIn(settingsBox, "后端 API 地址", getApiBase(), false);
    var tokenField = fieldRowIn(settingsBox, "X-API-Key（本机开发可留空）", getToken(), false);
    var saveButton = el("button", null, "保存设置");
    saveButton.style.cssText = "margin-top:8px;padding:6px 12px;border:0;border-radius:8px;background:#C48A36;color:#14263A;cursor:pointer;";
    saveButton.addEventListener("click", function () {
      var apiBase = normalizeApiBase(apiField.value.trim() || DEFAULT_API_BASE);
      if (!apiBase) {
        showStatus("后端地址仅支持本机或内网 HTTP(S) 地址，且不能带账号、路径或查询参数。", true);
        return;
      }
      GM_setValue(KEY_API_BASE, apiBase);
      GM_setValue(KEY_TOKEN, tokenField.value.trim());
      showStatus("设置已保存", false);
    });
    settingsBox.appendChild(saveButton);
    wrap.appendChild(settingsBox);

    settingsButton.addEventListener("click", function () {
      settingsBox.style.display = settingsBox.style.display === "none" ? "block" : "none";
    });

    function fieldRowIn(container, labelText, value, isTextarea) {
      var label = el("label", null, labelText);
      label.style.cssText = "display:block;font-size:11px;color:#9FB0C0;margin:6px 0 2px;";
      var field = isTextarea ? document.createElement("textarea") : document.createElement("input");
      field.value = value || "";
      field.style.cssText = "width:100%;box-sizing:border-box;padding:6px;border-radius:6px;" +
        "border:1px solid #33475C;background:#0F1B2B;color:#E8EEF4;font:12px system-ui;";
      container.appendChild(label);
      container.appendChild(field);
      return field;
    }

    function showStatus(message, isBad) {
      statusLine.textContent = message;
      statusLine.style.color = isBad ? "#F6C1B8" : "#9FD9C7";
    }
    wrap._showStatus = showStatus;

    function updateIndicator() {
      var hits = matchNingbo((titleField.value || "") + " " + (contentField.value || ""));
      indicator.textContent = hits.length ? "相关（" + hits.join("、") + "）" : "未识别";
      indicator.style.color = hits.length ? "#7FD6A4" : "#F0C36D";
    }

    function fillFromPage() {
      var payload = collectPayload(null);
      titleField.value = payload.title || "";
      authorField.value = payload.author_name || "";
      contentField.value = payload.content || "";
      updateIndicator();
      if (!contentField.value) {
        showStatus("未能自动提取正文：请划选页面文字后点击“重新提取”，或手动粘贴。", true);
      } else {
        showStatus("已提取，请核对后推送。", false);
      }
    }

    refreshButton.addEventListener("click", function () {
      var selection = String(window.getSelection().toString() || "").trim();
      if (selection) { contentField.value = selection; updateIndicator(); showStatus("已使用划选文本。", false); }
      else { fillFromPage(); }
    });

    pushButton.addEventListener("click", function () {
      var content = contentField.value.trim();
      if (!content) { showStatus("正文为空，无法推送。", true); return; }
      var hits = matchNingbo((titleField.value || "") + " " + content);
      if (!hits.length) { showStatus("未识别到宁波关键词；后端会拒绝该条。", true); return; }
      pushButton.disabled = true;
      showStatus("正在推送…", false);
      var payload = collectPayload({
        title: titleField.value.trim(),
        author: authorField.value.trim(),
        content: content
      });
      pushPayload(payload, function (ok, message) {
        pushButton.disabled = false;
        showStatus(message, !ok);
        if (ok) GM_notification({ title: "宁波线索采集", text: message });
      });
    });

    panelRefreshers.push(updateIndicator);
    return wrap;
  }

  var panelRefreshers = [];

  // ---------- 推送（GM_xmlhttpRequest 跨域直推本地 NAS 后端） ----------
  function pushPayload(payload, onDone) {
    GM_xmlhttpRequest({
      method: "POST",
      url: getApiBase() + INGEST_PATH,
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": getToken()
      },
      data: JSON.stringify(payload),
      timeout: 15000,
      onload: function (response) {
        var body = safeParse(response.responseText) || {};
        if (response.status === 200 || response.status === 201) {
          var label = body.status === "duplicate" ? "已存在（去重生效）" : "入库成功";
          onDone(true, label + "；SHA " + String(body.sha256 || "").slice(0, 12) + "…");
        } else if (body.error && body.error.code === "not_ningbo_related") {
          onDone(false, "未识别到宁波关键词，后端拒绝。");
        } else if (body.error && body.error.code === "storage_pending") {
          onDone(false, "后端存储层尚未部署（storage_pending）。");
        } else if (response.status === 401) {
          onDone(false, "鉴权失败：请在设置里核对 X-API-Key。");
        } else {
          onDone(false, "推送失败（HTTP " + response.status + "）");
        }
      },
      onerror: function () {
        onDone(false, "无法连接后端：请确认 API 地址与 NAS 服务。");
      },
      ontimeout: function () {
        onDone(false, "推送超时。");
      }
    });
  }

  // ---------- 挂载 ----------
  function mount() {
    var fab = document.createElement("button");
    fab.id = "nbre-fab";
    fab.type = "button";
    fab.textContent = "🏠 采";
    fab.title = "宁波房产线索采集";
    fab.style.cssText = "position:fixed;right:16px;bottom:16px;width:44px;height:44px;border-radius:999px;" +
      "border:0;background:#147D79;color:#fff;font:700 13px system-ui;cursor:pointer;" +
      "box-shadow:0 4px 12px rgba(0,0,0,.35);z-index:2147483647;opacity:.85;";
    fab.addEventListener("click", function () {
      var panel = document.getElementById("nbre-panel");
      var visible = panel && panel.style.display !== "none";
      if (!panel) { panel = buildPanel(); document.body.appendChild(panel); }
      panel.style.display = visible ? "none" : "block";
      GM_setValue(KEY_PANEL_OPEN, !visible);
      if (!visible) {
        // 打开时刷新提取结果；划选文本优先由“重新提取”按钮显式采用。
        var event = new Event("nbre-refresh");
        panel.dispatchEvent(event);
      }
    });
    document.body.appendChild(fab);

    var panel = buildPanel();
    document.body.appendChild(panel);
    if (panelOpen) { panel.style.display = "block"; }
    panel.addEventListener("nbre-refresh", function () { /* refresh handled per-button */ });

    GM_registerMenuCommand("采集当前页面线索", function () {
      document.getElementById("nbre-fab").click();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else {
    mount();
  }
})();
