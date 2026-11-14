"""Shared layout shell and static assets for the admin workbench (UI scope only).

Owns the design-system wiring: sidebar navigation, topbar, page shell with
security headers, and the whitelisted same-origin static endpoints. Route
handlers, SQL, auth and CSRF semantics stay in app/admin_ui.py.
"""
from __future__ import annotations

import html
from pathlib import Path

from fastapi.responses import HTMLResponse, Response

STATIC_DIR = Path(__file__).resolve().parent / "static"

# Allowed static assets: fixed names only, so user input can never select a path.
STATIC_FILES = {
    "admin.css": ("text/css; charset=utf-8", "public, max-age=300"),
}

NAV_ITEMS = (
    ("dashboard", "/admin/", "总览"),
    ("listings", "/admin/listings", "房源库"),
    ("candidates", "/admin/candidates", "候选审核"),
    ("import", "/admin/import", "HTML样本导入"),
    ("searches", "/admin/searches", "条件找房"),
    ("opportunities", "/admin/opportunities", "降价机会"),
    ("monitoring", "/admin/monitoring", "视频监控"),
)

_SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'none'; style-src 'self'; "
        "img-src 'self' data:; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


def static_response(name: str) -> Response:
    """Serve a whitelisted static asset with immutable-ish caching."""
    if name not in STATIC_FILES:
        return Response("Not found", status_code=404, media_type="text/plain")
    content_type, cache = STATIC_FILES[name]
    payload = (STATIC_DIR / name).read_bytes()
    return Response(payload, media_type=content_type, headers={"Cache-Control": cache})


def _nav_html(active: str | None) -> str:
    items = "".join(
        f'<a href="{href}"{" class=\"active\"" if key == active else ""}'
        f'{" aria-current=\"page\"" if key == active else ""}>{html.escape(label)}</a>'
        for key, href, label in NAV_ITEMS
    )
    return f'<nav class="nav" aria-label="主导航">{items}</nav>'


def _sidebar(active: str | None) -> str:
    return f"""<aside class="sidebar"><div class="brand"><div class="brand-mark">甬</div>
<div><div class="brand-name">宁波房产工作台</div><div class="brand-sub">数据驾驶舱 · 单操作者</div></div></div>
{_nav_html(active)}
<div class="sidebar-foot">仅限 NAS 本机或可信内网访问。<br>页面不向浏览器提供 APP_API_KEY。</div></aside>"""


def _topbar(title: str, side: str) -> str:
    return f"""<header class="topbar"><h1>{html.escape(title)}</h1>
<div class="topbar-side">{side}</div></header>"""


def logout_button(csrf: str) -> str:
    return (f'<form method="post" action="/admin/logout">'
            f'<input type="hidden" name="csrf" value="{html.escape(csrf, quote=True)}">'
            f'<button class="ghost" type="submit">退出</button></form>')


def page_shell(title: str, inner: str, csrf: str, active: str | None,
               status_code: int = 200) -> HTMLResponse:
    """Standard workbench shell: sidebar + topbar + content.

    `csrf` is computed by the caller (app.admin_ui owns the auth primitives)
    so this module stays free of auth logic and import cycles.
    """
    side = logout_button(csrf)
    body = (f'<div class="app">{_sidebar(active)}<div class="main">'
            f'{_topbar(title, side)}<main class="content">{inner}</main></div></div>')
    return _html_response(title, body, status_code)


def login_shell(title: str, inner: str, status_code: int = 200) -> HTMLResponse:
    body = f'<div class="login-wrap"><main class="login">{inner}</main></div>'
    return _html_response(title, body, status_code)


def _html_response(title: str, body: str, status_code: int) -> HTMLResponse:
    page = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · 宁波房产工作台</title>
<link rel="stylesheet" href="/admin/static/admin.css">
</head><body>{body}</body></html>"""
    response = HTMLResponse(page, status_code=status_code)
    for name, value in _SECURITY_HEADERS.items():
        response.headers[name] = value
    return response
