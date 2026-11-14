/* 宁波房产工作台 · 视频素材页交互（同源脚本，无内联代码，无外部依赖） */
(function () {
  "use strict";

  function fmtBytes(size) {
    if (size >= 1024 * 1024 * 1024) return (size / 1024 / 1024 / 1024).toFixed(2) + " GB";
    if (size >= 1024 * 1024) return (size / 1024 / 1024).toFixed(1) + " MB";
    return Math.max(1, Math.round(size / 1024)) + " KB";
  }

  function setupDropzone(zone) {
    var input = document.getElementById(zone.dataset.input || "file");
    var feedback = document.getElementById(zone.dataset.feedback || "drop-feedback");
    var allowed = (zone.dataset.allowed || "").split(",").filter(Boolean);
    var maxSize = parseInt(zone.dataset.maxBytes || "0", 10);
    function accept(file) {
      if (!file) return;
      var name = file.name.toLowerCase();
      var ext = name.slice(name.lastIndexOf("."));
      if (allowed.indexOf(ext) === -1) {
        feedback.textContent = "不支持的文件类型 " + ext + "（允许：" + allowed.join(" / ") + "）";
        feedback.className = "drop-feedback bad";
        input.value = "";
        return;
      }
      if (maxSize && file.size > maxSize) {
        feedback.textContent = "文件 " + fmtBytes(file.size) + " 超过上限 " + fmtBytes(maxSize);
        feedback.className = "drop-feedback bad";
        input.value = "";
        return;
      }
      feedback.textContent = "已选择 " + file.name + "（" + fmtBytes(file.size) + "）";
      feedback.className = "drop-feedback ok";
    }
    zone.addEventListener("click", function () { input.click(); });
    zone.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") { event.preventDefault(); input.click(); }
    });
    ["dragenter", "dragover"].forEach(function (type) {
      zone.addEventListener(type, function (event) { event.preventDefault(); zone.classList.add("dragging"); });
    });
    ["dragleave", "drop"].forEach(function (type) {
      zone.addEventListener(type, function (event) { event.preventDefault(); zone.classList.remove("dragging"); });
    });
    zone.addEventListener("drop", function (event) {
      var file = event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files[0];
      if (file) { input.files = event.dataTransfer.files; accept(file); }
    });
    input.addEventListener("change", function () { accept(input.files && input.files[0]); });
  }

  function setupUploadForm(form) {
    var progress = document.getElementById("upload-progress");
    var bar = document.getElementById("upload-progress-bar");
    var statusText = document.getElementById("upload-status");
    var submit = form.querySelector("button[type='submit']");
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var fileInput = form.querySelector("input[type='file']");
      if (!fileInput.files || !fileInput.files[0]) return;
      submit.disabled = true;
      progress.hidden = false;
      statusText.textContent = "正在上传到服务器…";
      var data = new FormData(form);
      var request = new XMLHttpRequest();
      request.open("POST", form.action, true);
      request.setRequestHeader("Accept", "application/json");
      request.responseType = "text";
      request.upload.addEventListener("progress", function (event) {
        if (event.lengthComputable) {
          bar.style.width = Math.round((event.loaded / event.total) * 100) + "%";
        }
      });
      request.addEventListener("load", function () {
        if (request.status >= 200 && request.status < 300) {
          try {
            var payload = JSON.parse(request.responseText);
            if (payload && payload.detail_url) {
              statusText.textContent = "上传完成，进入识别队列…";
              window.location.assign(payload.detail_url);
              return;
            }
          } catch (parseError) { /* fall through to error handling */ }
        }
        submit.disabled = false;
        progress.hidden = true;
        var detail = "上传失败（HTTP " + request.status + "）";
        try {
          var payload = JSON.parse(request.responseText);
          if (payload && payload.error && payload.error.message) detail = payload.error.message;
        } catch (parseError) { /* keep default */ }
        statusText.textContent = detail;
        statusText.className = "upload-status bad";
      });
      request.addEventListener("error", function () {
        submit.disabled = false;
        progress.hidden = true;
        statusText.textContent = "网络错误，请重试";
        statusText.className = "upload-status bad";
      });
      request.send(data);
    });
  }

  function setupPolling(panel) {
    var intervalMs = parseInt(panel.dataset.pollMs || "3000", 10);
    var status = panel.dataset.status;
    if (status !== "queued" && status !== "processing") return;
    window.setTimeout(function () { window.location.reload(); }, intervalMs);
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-dropzone]").forEach(setupDropzone);
    var form = document.getElementById("video-upload-form");
    if (form) setupUploadForm(form);
    var panel = document.getElementById("video-detail");
    if (panel) setupPolling(panel);
  });
})();
