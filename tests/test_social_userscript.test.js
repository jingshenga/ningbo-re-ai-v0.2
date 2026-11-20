const assert = require("node:assert/strict");
const fs = require("node:fs");
const test = require("node:test");
const path = require("node:path");

const scriptPath = path.join(__dirname, "../tools/userscripts/ningbo_re_collector.user.js");
const { extractPostIdFromUrl } = require(scriptPath);
const scriptSource = fs.readFileSync(scriptPath, "utf8");

test("extracts numeric Douyin video IDs from known routes", () => {
  assert.equal(
    extractPostIdFromUrl("https://www.douyin.com/video/7234567890123456789"),
    "7234567890123456789",
  );
});

test("extracts hexadecimal Xiaohongshu IDs from known routes", () => {
  assert.equal(
    extractPostIdFromUrl("https://www.xiaohongshu.com/explore/65abc1234567890abcdef123"),
    "65abc1234567890abcdef123",
  );
});

test("extracts WeChat numeric article IDs from query parameters", () => {
  assert.equal(
    extractPostIdFromUrl("https://mp.weixin.qq.com/s?__biz=account&mid=7234567890123456789&idx=1"),
    "7234567890123456789",
  );
});

test("does not treat arbitrary numeric path segments as post IDs", () => {
  assert.equal(extractPostIdFromUrl("https://www.douyin.com/user/7234567890123456789"), "");
});

test("preview renders as text and only its confirmation handler sends", () => {
  assert.match(scriptSource, /previewJson\.textContent = JSON\.stringify\(payload, null, 2\)/);
  assert.match(scriptSource, /confirmButton\.addEventListener\("click"/);
  assert.match(scriptSource, /tokenField\.type = reveal \? "text" : "password"/);
  assert.doesNotMatch(scriptSource, /\.innerHTML\s*=/);
});
