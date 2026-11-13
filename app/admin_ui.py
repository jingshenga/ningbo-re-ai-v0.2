"""Server-rendered single-operator dashboard."""
import base64
import hashlib
import hmac
import html
import ipaddress
import secrets
import time
from urllib.parse import parse_qs

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app import collection_service, services
from app.db import session
from app.settings import APP_API_KEY, DTK_API_KEY, DTK_BASE_URL, ENABLE_ONLINE_COLLECTION


router = APIRouter()
COOKIE_NAME = "admin_session"
SESSION_SECONDS = 8 * 60 * 60


def _signed_cookie(now=None):
    expires = int(now if now is not None else time.time()) + SESSION_SECONDS
    payload = f"{expires}.{secrets.token_urlsafe(16)}".encode()
    signature = hmac.new(APP_API_KEY.encode(), payload, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(payload + b"." + signature.hex().encode()).decode().rstrip("=")


def _cookie_is_valid(value, now=None):
    if not APP_API_KEY or not value:
        return False
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        payload, encoded_signature = decoded.rsplit(b".", 1)
        signature = bytes.fromhex(encoded_signature.decode())
        expires = int(payload.split(b".", 1)[0])
    except (ValueError, TypeError):
        return False
    expected = hmac.new(APP_API_KEY.encode(), payload, hashlib.sha256).digest()
    return expires >= int(now if now is not None else time.time()) and hmac.compare_digest(signature, expected)


def _csrf_token(cookie):
    return hmac.new(APP_API_KEY.encode(), ("csrf:" + cookie).encode(), hashlib.sha256).hexdigest()


def _check_admin(request):
    if not APP_API_KEY:
        raise HTTPException(status_code=503, detail="APP_API_KEY is not configured")
    if not _cookie_is_valid(request.cookies.get(COOKIE_NAME)):
        raise HTTPException(status_code=401, detail="Admin login required")


def _html_page(title, body, status_code=200):
    page = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · 宁波房产工作台</title>
<style>
:root{{--ink:#172235;--muted:#64748b;--line:#e4e9f0;--paper:#f5f7fb;--blue:#2457d6;--green:#18794e;--amber:#9a5c00;--red:#b42318}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
header{{background:#fff;border-bottom:1px solid var(--line);padding:16px max(20px,calc((100vw - 1180px)/2));display:flex;align-items:center;justify-content:space-between;gap:16px}}
header strong{{font-size:18px}}main{{max-width:1180px;margin:28px auto;padding:0 20px}}h1{{font-size:26px;margin:0 0 6px}}h2{{font-size:18px;margin:0 0 14px}}h3{{font-size:15px;margin:0 0 10px}}p{{margin:4px 0;color:var(--muted)}}
.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:20px 0}}.card,.panel{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:0 2px 8px #19345c08}}
.metric{{font-size:30px;font-weight:700;margin-top:7px}}.label,.muted{{color:var(--muted);font-size:13px}}.cols{{display:grid;grid-template-columns:1.15fr .85fr;gap:14px;margin:14px 0}}
.row{{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;padding:11px 0;border-top:1px solid var(--line)}}.row:first-of-type{{border-top:0}}.row strong{{display:block}}.tag{{border-radius:999px;padding:3px 9px;background:#edf2ff;color:#284bb5;font-size:12px;white-space:nowrap}}.tag.ok{{background:#eaf7ef;color:var(--green)}}.tag.warn{{background:#fff5dd;color:var(--amber)}}.tag.bad{{background:#fff0ee;color:var(--red)}}
a{{color:var(--blue);text-decoration:none}}a:hover{{text-decoration:underline}}.nav{{display:flex;gap:18px;align-items:center}}button{{border:0;background:none;color:var(--blue);font:inherit;cursor:pointer;padding:4px}}
.empty{{padding:18px 0;color:var(--muted)}}.notice{{padding:12px 14px;background:#edf4ff;border-radius:10px;color:#294a78;margin:12px 0}}
.login{{max-width:420px;margin:8vh auto;background:white;border:1px solid var(--line);border-radius:16px;padding:28px}}label{{display:block;font-weight:600;margin:18px 0 7px}}input{{width:100%;padding:12px;border:1px solid #cbd5e1;border-radius:8px;font:inherit}}.primary{{width:100%;margin-top:20px;background:var(--blue);color:white;border:0;border-radius:8px;padding:12px;font:inherit;font-weight:650}}
@media(max-width:760px){{.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.cols{{grid-template-columns:1fr}}header{{padding:14px 18px}}main{{margin:20px auto;padding:0 14px}}.metric{{font-size:25px}}}}
</style></head><body>{body}</body></html>"""
    response = HTMLResponse(page, status_code=status_code)
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


def _form(request_body):
    return parse_qs(request_body.decode("utf-8", errors="replace"), keep_blank_values=True)


async def _request_form(request):
    chunks = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > 8192:
            raise HTTPException(status_code=413, detail="Form is too large")
        chunks.append(chunk)
    return _form(b"".join(chunks))


def _summary():
    with session() as conn:
        row = conn.execute("""SELECT
            (SELECT count(*) FROM source_listings WHERE status NOT IN ('withdrawn','sold')) AS listing_count,
            (SELECT count(*) FROM collection_candidates WHERE review_status='pending') AS pending_count,
            (SELECT count(*) FROM source_listings WHERE created_at >= now() - interval '7 days') AS new_count""").fetchone()
    return dict(row)


def _private_network_only(request):
    if any(name in request.headers for name in ("forwarded", "x-forwarded-for", "x-real-ip")):
        return False
    host = request.client.host if request.client else ""
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return address.is_private or address.is_loopback


@router.get("/admin/login", response_class=HTMLResponse)
def admin_login(request: Request, error: str = ""):
    if not _private_network_only(request):
        raise HTTPException(status_code=403, detail="Admin UI is available only from a private network")
    if _cookie_is_valid(request.cookies.get(COOKIE_NAME)):
        return RedirectResponse("/admin/", status_code=303)
    message = '<p class="notice">API Key 不匹配，请重试。</p>' if error else ""
    body = f"""<main class="login"><h1>宁波房产工作台</h1><p>单操作者登录</p>{message}
<form method="post" action="/admin/login"><label for="password">APP_API_KEY</label>
<input id="password" name="password" type="password" autocomplete="current-password" required>
<button class="primary" type="submit">登录</button></form></main>"""
    return _html_page("登录", body)


@router.post("/admin/login")
async def admin_login_submit(request: Request):
    if not _private_network_only(request):
        raise HTTPException(status_code=403, detail="Admin UI is available only from a private network")
    if not APP_API_KEY:
        raise HTTPException(status_code=503, detail="APP_API_KEY is not configured")
    values = await _request_form(request)
    supplied = values.get("password", [""])[0]
    if not secrets.compare_digest(supplied, APP_API_KEY):
        return _html_page("登录", '<main class="login"><h1>宁波房产工作台</h1><p class="notice">API Key 不匹配，请重试。</p><a href="/admin/login">返回登录</a></main>', 401)
    response = RedirectResponse("/admin/", status_code=303)
    response.set_cookie(COOKIE_NAME, _signed_cookie(), max_age=SESSION_SECONDS,
                        httponly=True, secure=request.url.scheme == "https",
                        samesite="strict", path="/admin")
    response.headers["Cache-Control"] = "no-store"
    return response


@router.post("/admin/logout")
async def admin_logout(request: Request):
    _check_admin(request)
    cookie = request.cookies.get(COOKIE_NAME, "")
    values = await _request_form(request)
    submitted = values.get("csrf", [""])[0]
    if not hmac.compare_digest(submitted, _csrf_token(cookie)):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    response = RedirectResponse("/admin/login", status_code=303)
    response.delete_cookie(COOKIE_NAME, path="/admin", httponly=True, samesite="strict")
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/admin", include_in_schema=False)
def admin_root(request: Request):
    if not APP_API_KEY:
        raise HTTPException(status_code=503, detail="APP_API_KEY is not configured")
    target = "/admin/" if _cookie_is_valid(request.cookies.get(COOKIE_NAME)) else "/admin/login"
    return RedirectResponse(target, status_code=303)


@router.get("/admin/", response_class=HTMLResponse, include_in_schema=False)
def admin_dashboard(request: Request):
    _check_admin(request)
    if not _private_network_only(request):
        raise HTTPException(status_code=403, detail="Admin UI is available only from a private network")

    summary = _summary()
    sources = collection_service.health_metrics()
    accounts = services.all_accounts()
    recent_listings = services.listings(limit=6)
    opportunities = services.opportunities(days=30, limit=1200)
    videos = services.list_videos(limit=4)
    cookie = request.cookies.get(COOKIE_NAME, "")
    esc = lambda value: html.escape(str(value if value is not None else "—"), quote=True)

    def metric(label, value, note):
        return f'<section class="card"><div class="label">{esc(label)}</div><div class="metric">{esc(value)}</div><div class="muted">{esc(note)}</div></section>'

    listing_rows = "".join(
        f'<div class="row"><div><strong>{esc(row.get("community_name") or row.get("title") or "未命名房源")}</strong>'
        f'<span class="muted">{esc(row.get("district"))} · {esc(row.get("area_sqm"))}㎡ · {esc(row.get("source"))} · 观察 {esc(row.get("last_observed_at"))}</span></div>'
        f'<span class="tag">{esc(row.get("asking_price_wan"))} 万</span></div>'
        for row in recent_listings
    ) or '<div class="empty">尚无入库房源。</div>'
    source_rows = "".join(
        f'<div class="row"><div><strong>{esc(row.get("source"))}</strong>'
        f'<span class="muted">最近尝试：{esc(row.get("last_attempt_at"))}<br>{esc(row.get("latest_note"))}</span></div>'
        f'<span class="tag {"ok" if row.get("latest_status") == "success" else "warn" if row.get("latest_status") in (None, "not_started") else "bad"}">{esc(row.get("latest_status") or "尚无运行")}</span></div>'
        for row in sources
    ) or '<div class="empty">尚无来源状态记录。</div>'
    account_rows = "".join(
        f'<div class="row"><div><strong>{esc(row.get("nickname") or row.get("account_ref"))}</strong>'
        f'<span class="muted">{esc(row.get("platform"))} · 最近成功 {esc(row.get("last_success_at"))}</span></div>'
        f'<span class="tag {"ok" if row.get("last_status") == "success" else "warn" if row.get("last_status") in (None, "not_started", "blocked_config") else "bad"}">{esc(row.get("last_status") or "尚无运行")}</span></div>'
        for row in accounts
    ) or '<div class="empty">尚未添加监控账号。</div>'
    video_rows = "".join(
        f'<div class="row"><div><strong>{esc(row.get("title") or row.get("author_name") or "未命名视频")}</strong>'
        f'<span class="muted">{esc(row.get("platform"))} · {esc(row.get("processing_status"))} · {esc(row.get("published_at"))}</span></div>'
        f'<span class="tag">{esc(len(row.get("extracted_fields") or {}))} 项提取</span></div>'
        for row in videos
    ) or '<div class="empty">尚无导入视频。</div>'
    dtk_note = "DTK 服务已配置" if DTK_BASE_URL and DTK_API_KEY else "尚未配置 DTK 服务；实时监控不可用。"
    online_note = "在线采集已启用" if ENABLE_ONLINE_COLLECTION else "在线采集关闭；可导入获准 HTML 样本。"
    body = f"""<header><strong>宁波房产工作台</strong><nav class="nav"><a href="/admin/">总览</a>
<form method="post" action="/admin/logout"><input type="hidden" name="csrf" value="{_csrf_token(cookie)}"><button type="submit">退出</button></form></nav></header>
<main><h1>项目总览</h1><p>仅显示系统实际记录；没有数据时不会生成演示房源。</p>
<div class="notice">{esc(online_note)}　{esc(dtk_note)}</div>
<div class="grid">{metric("在售房源", summary["listing_count"], "不含已撤牌或已售")}{metric("待审核候选", summary["pending_count"], "需要人工核验")}{metric("近 7 天新入库", summary["new_count"], "按正式挂牌创建时间")}{metric("近 30 天降价机会", len(opportunities), "沿用现有机会计算 API")}</div>
<div class="cols"><section class="panel"><h2>最近入库房源</h2>{listing_rows}</section><section class="panel"><h2>采集来源状态</h2>{source_rows}</section></div>
<div class="cols"><section class="panel"><h2>抖音账号监控</h2>{account_rows}</section><section class="panel"><h2>最近导入视频</h2>{video_rows}</section></div>
<p class="muted">访问范围：NAS 本机或可信内网。首次登录使用服务器环境中的 APP_API_KEY；页面不向浏览器脚本提供该密钥。</p></main>"""
    return _html_page("总览", body)
