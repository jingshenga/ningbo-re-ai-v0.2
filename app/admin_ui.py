"""Server-rendered single-operator dashboard."""
import base64
import gzip
import hashlib
import hmac
import html
import ipaddress
import re
import json
import secrets
import time
import zlib
from decimal import Decimal
from pathlib import Path
from uuid import UUID
from urllib.parse import parse_qs, urlsplit

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError

from app import collection_service, services
from app.db import session
from app.collection_models import CandidateCorrection, HTMLPageIn
from app.collectors.parser import CollectionError
from app.settings import APP_API_KEY, DTK_API_KEY, DTK_BASE_URL, ENABLE_ONLINE_COLLECTION, RAW_HTML_DIR


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
    if not _private_network_only(request):
        raise HTTPException(status_code=403, detail="Admin UI is available only from a private network")
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
.login{{max-width:420px;margin:8vh auto;background:white;border:1px solid var(--line);border-radius:16px;padding:28px}}label{{display:block;font-weight:600;margin:18px 0 7px}}input,select,textarea{{width:100%;padding:10px;border:1px solid #cbd5e1;border-radius:8px;font:inherit;background:#fff}}textarea{{min-height:180px;font-family:ui-monospace,monospace}}.filters{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:16px 0}}.filters label{{margin:0}}.table-wrap{{overflow:auto}}table{{width:100%;border-collapse:collapse;min-width:680px}}th,td{{text-align:left;padding:11px;border-bottom:1px solid var(--line);vertical-align:top}}th{{color:var(--muted);font-size:13px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#f6f8fb;padding:12px;border-radius:8px}}.actions{{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0}}.actions button,.button{{background:var(--blue);color:#fff;border:0;border-radius:8px;padding:9px 13px;font:inherit;cursor:pointer}}.primary{{width:100%;margin-top:20px;background:var(--blue);color:white;border:0;border-radius:8px;padding:12px;font:inherit;font-weight:650}}
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


async def _request_form(request, max_bytes=8192):
    chunks = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > max_bytes:
            raise HTTPException(status_code=413, detail="Form is too large")
        chunks.append(chunk)
    return _form(b"".join(chunks))


def _summary():
    with session() as conn:
        row = conn.execute("""SELECT
            (SELECT count(*) FROM source_listings WHERE status NOT IN ('withdrawn','sold')) AS listing_count,
            (SELECT count(*) FROM collection_candidates WHERE review_status='pending') AS pending_count,
            (SELECT count(*) FROM source_listings WHERE created_at >= now() - interval '7 days') AS new_count,
            (SELECT count(*) FROM (
                SELECT listing_id, array_agg(price_wan ORDER BY observed_at) AS prices
                FROM price_history
                WHERE quote_type='platform_listed'
                  AND observed_at >= now() - interval '30 days'
                  AND observed_at <= now()
                GROUP BY listing_id
                HAVING count(*) >= 2
            ) drops JOIN source_listings l ON l.id=drops.listing_id
             WHERE (drops.prices)[1] > (drops.prices)[array_length(drops.prices, 1)]
               AND l.source <> 'agent'
               AND l.status NOT IN ('withdrawn','sold')
               AND l.last_observed_at >= now() - interval '90 days'
               AND l.last_observed_at <= now()) AS recent_price_drop_count""").fetchone()
    return dict(row)


def _recently_created_listings():
    with session() as conn:
        return conn.execute("""SELECT l.*,p.area_sqm,c.name AS community_name,c.district
          FROM source_listings l JOIN properties p ON p.id=l.property_id
          JOIN communities c ON c.id=p.community_id
          ORDER BY l.created_at DESC LIMIT 6""").fetchall()


def _private_network_only(request):
    if any(name in request.headers for name in ("forwarded", "x-forwarded-for", "x-real-ip")):
        return False
    host = request.client.host if request.client else ""
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return address.is_private or address.is_loopback


@router.get("/admin/login", response_class=HTMLResponse, include_in_schema=False)
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


@router.post("/admin/login", include_in_schema=False)
async def admin_login_submit(request: Request):
    if not _private_network_only(request):
        raise HTTPException(status_code=403, detail="Admin UI is available only from a private network")
    if not APP_API_KEY:
        raise HTTPException(status_code=503, detail="APP_API_KEY is not configured")
    values = await _request_form(request)
    supplied = values.get("password", [""])[0]
    if not secrets.compare_digest(supplied.encode("utf-8"), APP_API_KEY.encode("utf-8")):
        return _html_page("登录", '<main class="login"><h1>宁波房产工作台</h1><p class="notice">API Key 不匹配，请重试。</p><a href="/admin/login">返回登录</a></main>', 401)
    response = RedirectResponse("/admin/", status_code=303)
    response.set_cookie(COOKIE_NAME, _signed_cookie(), max_age=SESSION_SECONDS,
                        httponly=True, secure=request.url.scheme == "https",
                        samesite="strict", path="/admin")
    response.headers["Cache-Control"] = "no-store"
    return response


@router.post("/admin/logout", include_in_schema=False)
async def admin_logout(request: Request):
    _check_admin(request)
    cookie = request.cookies.get(COOKIE_NAME, "")
    values = await _request_form(request)
    submitted = values.get("csrf", [""])[0]
    if not hmac.compare_digest(submitted.encode("utf-8"), _csrf_token(cookie).encode("ascii")):
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
    accounts = [row for row in services.all_accounts() if row.get("platform") == "douyin"]
    recent_listings = _recently_created_listings()
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
    online_note = ("全局在线采集开关已开启；来源授权和来源开关仍会分别校验。"
                   if ENABLE_ONLINE_COLLECTION else "在线采集全局开关关闭；可导入获准 HTML 样本。")
    body = f"""<header><strong>宁波房产工作台</strong><nav class="nav"><a href="/admin/">总览</a>
<form method="post" action="/admin/logout"><input type="hidden" name="csrf" value="{_csrf_token(cookie)}"><button type="submit">退出</button></form></nav></header>
<main><h1>项目总览</h1><p>仅显示系统实际记录；没有数据时不会生成演示房源。</p>
<div class="notice">{esc(online_note)}　{esc(dtk_note)}</div>
<div class="grid">{metric("在售房源", summary["listing_count"], "不含已撤牌或已售")}{metric("待审核候选", summary["pending_count"], "需要人工核验")}{metric("近 7 天新入库", summary["new_count"], "按正式挂牌创建时间")}{metric("近 30 天挂牌降价", summary["recent_price_drop_count"], "只统计同一来源挂牌历史价格确有下降；完整机会线索在机会页按需扫描")}</div>
<div class="cols"><section class="panel"><h2>最近入库房源</h2>{listing_rows}</section><section class="panel"><h2>采集来源状态</h2>{source_rows}</section></div>
<div class="cols"><section class="panel"><h2>抖音账号监控</h2>{account_rows}<p class="muted">微信视频号使用手工导入，不显示为实时监控。</p></section><section class="panel"><h2>最近导入视频</h2>{video_rows}</section></div>
<p class="muted">访问范围：NAS 本机或可信内网。首次登录使用服务器环境中的 APP_API_KEY；页面不向浏览器脚本提供该密钥。</p></main>"""
    return _html_page("总览", body)


def _verify_csrf(request, values):
    cookie = request.cookies.get(COOKIE_NAME, "")
    submitted = values.get("csrf", [""])[0]
    if not hmac.compare_digest(submitted.encode("utf-8"), _csrf_token(cookie).encode("ascii")):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")


def _admin_page(title, inner, cookie, status_code=200):
    header = f"""<header><strong>宁波房产工作台</strong><nav class="nav">
<a href="/admin/">总览</a><a href="/admin/listings">房源管理</a>
<a href="/admin/candidates">候选审核</a><a href="/admin/import">HTML样本导入</a>
<form method="post" action="/admin/logout"><input type="hidden" name="csrf" value="{_csrf_token(cookie)}"><button type="submit">退出</button></form>
</nav></header><main>{inner}</main>"""
    return _html_page(title, header, status_code)


def _safe_link(value):
    value = str(value or "")
    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return html.escape(value, quote=True)
    escaped = html.escape(value, quote=True)
    return f'<a href="{escaped}" rel="noopener noreferrer">{escaped}</a>'


def _search_listings(district=None, community_name=None, min_area_sqm=None,
                     max_area_sqm=None, min_price_wan=None, max_price_wan=None,
                     min_bedrooms=None):
    conditions = ["l.status NOT IN ('withdrawn','sold')"]
    values = []

    def add(condition, value):
        if value is not None:
            conditions.append(condition)
            values.append(value)

    add("c.district=%s", district)
    add("c.name=%s", community_name)
    add("p.area_sqm >= %s", min_area_sqm)
    add("p.area_sqm <= %s", max_area_sqm)
    add("l.asking_price_wan >= %s", min_price_wan)
    add("l.asking_price_wan <= %s", max_price_wan)
    add("p.bedrooms >= %s", min_bedrooms)
    sql = """SELECT l.id,l.source,l.source_listing_id,l.title,l.listing_url,l.asking_price_wan,
                    l.last_observed_at,l.created_at,p.area_sqm,p.bedrooms,c.name AS community_name,c.district
             FROM source_listings l JOIN properties p ON p.id=l.property_id
             JOIN communities c ON c.id=p.community_id
             WHERE """ + " AND ".join(conditions) + " ORDER BY l.last_observed_at DESC LIMIT 200"
    with session() as conn:
        return conn.execute(sql, values).fetchall()


def _listing_detail(listing_id):
    with session() as conn:
        return conn.execute("""SELECT l.*,p.area_sqm,p.bedrooms,p.floor_text,p.decoration,
                    c.name AS community_name,c.district
             FROM source_listings l JOIN properties p ON p.id=l.property_id
             JOIN communities c ON c.id=p.community_id WHERE l.id=%s""",
            (listing_id,)).fetchone()


def _candidate_detail(candidate_id):
    with session() as conn:
        return conn.execute("SELECT * FROM collection_candidates WHERE id=%s",
                            (candidate_id,)).fetchone()


def _candidate_html_evidence(row):
    sha = str(row.get("raw_sha256") or "")
    if not re.fullmatch(r"[0-9a-f]{64}", sha):
        return None
    folder = Path(RAW_HTML_DIR)
    path = folder / f"{sha}.html.gz"
    if folder.is_symlink() or path.is_symlink() or not path.is_file():
        return None
    try:
        with gzip.open(path, "rb") as source:
            content = source.read(1_000_001)
        if len(content) > 1_000_000:
            return None
        return content.decode("utf-8")
    except (OSError, EOFError, UnicodeDecodeError, zlib.error):
        return None


def _layout_fields(row, keys):
    esc = lambda value: html.escape(str(value if value is not None else ""), quote=True)
    return "".join(
        f'<label>{esc(key)}<input name="{esc(key)}" value="{esc(row.get(key))}"></label>'
        for key in keys
    )


@router.get("/admin/listings", response_class=HTMLResponse, include_in_schema=False)
def admin_listings(request: Request, district: str | None = None,
                   community_name: str | None = None,
                   min_area_sqm: Decimal | None = Query(default=None, gt=0),
                   max_area_sqm: Decimal | None = Query(default=None, gt=0),
                   min_price_wan: Decimal | None = Query(default=None, gt=0),
                   max_price_wan: Decimal | None = Query(default=None, gt=0),
                   min_bedrooms: int | None = Query(default=None, ge=0, le=20)):
    _check_admin(request)
    if min_area_sqm and max_area_sqm and min_area_sqm > max_area_sqm:
        raise HTTPException(status_code=422, detail="面积下限不能大于上限")
    if min_price_wan and max_price_wan and min_price_wan > max_price_wan:
        raise HTTPException(status_code=422, detail="价格下限不能大于上限")
    rows = _search_listings(district, community_name, min_area_sqm, max_area_sqm,
                            min_price_wan, max_price_wan, min_bedrooms)
    esc = lambda value: html.escape(str(value if value is not None else "—"), quote=True)
    row_html = "".join(
        f'<tr><td><a href="/admin/listings/{esc(row["id"])}">{esc(row.get("community_name"))}</a>'
        f'<br><span class="muted">{esc(row.get("district"))} · {esc(row.get("source"))}</span></td>'
        f'<td>{esc(row.get("area_sqm"))}㎡ · {esc(row.get("bedrooms"))}室</td>'
        f'<td>{esc(row.get("asking_price_wan"))} 万</td>'
        f'<td>{esc(row.get("last_observed_at"))}</td><td>{_safe_link(row.get("listing_url"))}</td></tr>'
        for row in rows
    ) or '<tr><td colspan="5" class="empty">尚无符合条件的正式挂牌。</td></tr>'
    inner = f"""<h1>房源管理</h1><p>仅显示已审核正式挂牌。列表最多展示200条，按最近观察排序。</p>
<form class="panel filters" method="get">
<label>区域<input name="district" value="{esc(district)}"></label>
<label>小区<input name="community_name" value="{esc(community_name)}"></label>
<label>面积下限㎡<input name="min_area_sqm" type="number" min="0" step="0.01" value="{esc(min_area_sqm)}"></label>
<label>面积上限㎡<input name="max_area_sqm" type="number" min="0" step="0.01" value="{esc(max_area_sqm)}"></label>
<label>价格下限万<input name="min_price_wan" type="number" min="0" step="0.01" value="{esc(min_price_wan)}"></label>
<label>价格上限万<input name="max_price_wan" type="number" min="0" step="0.01" value="{esc(max_price_wan)}"></label>
<label>最少卧室<input name="min_bedrooms" type="number" min="0" max="20" value="{esc(min_bedrooms)}"></label>
<div class="actions"><button type="submit">筛选</button><a href="/admin/listings">清除条件</a></div>
</form><section class="panel table-wrap"><table><thead><tr><th>小区 / 区域 / 来源</th><th>面积 / 户型</th><th>挂牌价</th><th>观察时间</th><th>来源链接</th></tr></thead><tbody>{row_html}</tbody></table></section>"""
    return _admin_page("房源管理", inner, request.cookies.get(COOKIE_NAME, ""))


@router.get("/admin/listings/{listing_id}", response_class=HTMLResponse, include_in_schema=False)
def admin_listing_detail(request: Request, listing_id: UUID):
    _check_admin(request)
    row = _listing_detail(listing_id)
    if not row:
        raise HTTPException(status_code=404, detail="Listing not found")
    prices = services.listing_prices(listing_id)
    esc = lambda value: html.escape(str(value if value is not None else "—"), quote=True)
    history = "".join(
        f'<tr><td>{esc(item.get("observed_at"))}</td><td>{esc(item.get("price_wan"))} 万</td>'
        f'<td>{esc(item.get("quote_type"))}</td><td>{_safe_link(item.get("evidence_url"))}</td></tr>'
        for item in prices
    ) or '<tr><td colspan="4">暂无价格历史记录。</td></tr>'
    inner = f"""<h1>{esc(row.get("community_name"))}</h1><p>{esc(row.get("district"))} · {esc(row.get("source"))} · 挂牌ID {esc(row.get("source_listing_id"))}</p>
<section class="panel"><h2>当前挂牌</h2><p>{esc(row.get("asking_price_wan"))} 万 · {esc(row.get("area_sqm"))}㎡ · {esc(row.get("bedrooms"))}室</p>
<p>挂牌状态：{esc(row.get("status"))} · 最近观察：{esc(row.get("last_observed_at"))}</p><p>来源：{_safe_link(row.get("listing_url"))}</p></section>
<section class="panel"><h2>价格历史</h2><div class="table-wrap"><table><thead><tr><th>观察时间</th><th>价格</th><th>报价类型</th><th>价格证据来源</th></tr></thead><tbody>{history}</tbody></table></div></section>
<p><a href="/admin/listings">返回房源列表</a></p>"""
    return _admin_page("房源详情", inner, request.cookies.get(COOKIE_NAME, ""))


@router.get("/admin/candidates", response_class=HTMLResponse, include_in_schema=False)
def admin_candidates(request: Request, status: str = "pending", source: str | None = None):
    _check_admin(request)
    if status not in ("pending", "approved", "rejected"):
        raise HTTPException(status_code=422, detail="Invalid review status")
    if source not in (None, "beike", "anjuke"):
        raise HTTPException(status_code=422, detail="Invalid source")
    rows = collection_service.candidates(status=status, source=source, limit=200)
    esc = lambda value: html.escape(str(value if value is not None else "—"), quote=True)
    row_html = "".join(
        f'<tr><td><a href="/admin/candidates/{esc(row["id"])}">{esc(row.get("source"))} · {esc(row.get("source_listing_id"))}</a></td>'
        f'<td>{esc((row.get("extracted_fields") or {}).get("community_name"))}<br>{esc((row.get("extracted_fields") or {}).get("asking_price_wan"))}万 / {esc((row.get("extracted_fields") or {}).get("area_sqm"))}㎡</td>'
        f'<td>{esc(row.get("parser_version"))}<br>{esc(row.get("captured_at"))}</td>'
        f'<td>{esc(row.get("review_status"))}</td><td>{_safe_link(row.get("source_url"))}</td></tr>'
        for row in rows
    ) or '<tr><td colspan="5" class="empty">该筛选条件下暂无候选。</td></tr>'
    inner = f"""<h1>采集候选审核</h1><p>审批会调用现有审核服务，并在同一事务中写入正式挂牌及价格历史。</p>
<form class="panel filters" method="get"><label>状态<select name="status"><option value="pending">待审核</option><option value="approved">已通过</option><option value="rejected">已拒绝</option></select></label>
<label>来源<select name="source"><option value="">全部</option><option value="beike">贝壳</option><option value="anjuke">安居客</option></select></label><div class="actions"><button type="submit">筛选</button></div></form>
<section class="panel table-wrap"><table><thead><tr><th>来源 / 挂牌ID</th><th>解析房源信息</th><th>解析器 / 捕获时间</th><th>审核状态</th><th>来源链接</th></tr></thead><tbody>{row_html}</tbody></table></section>"""
    return _admin_page("候选审核", inner, request.cookies.get(COOKIE_NAME, ""))


@router.get("/admin/candidates/{candidate_id}", response_class=HTMLResponse, include_in_schema=False)
def admin_candidate_detail(request: Request, candidate_id: UUID, message: str = ""):
    _check_admin(request)
    row = _candidate_detail(candidate_id)
    if not row:
        raise HTTPException(status_code=404, detail="Candidate not found")
    fields = row.get("extracted_fields") or {}
    esc = lambda value: html.escape(str(value if value is not None else ""), quote=True)
    evidence = html.escape(json.dumps(fields, ensure_ascii=False, indent=2, default=str))
    warnings = html.escape(json.dumps(row.get("warnings") or [], ensure_ascii=False, indent=2, default=str))
    names = ("source_listing_id", "title", "community_name", "district", "area_sqm",
             "bedrooms", "floor_text", "decoration", "asking_price_wan")
    current = {**fields, "source_listing_id": row.get("source_listing_id") or fields.get("source_listing_id")}
    inputs = _layout_fields(current, names)
    csrf = _csrf_token(request.cookies.get(COOKIE_NAME, ""))
    status_note = f'<p class="notice">{esc(message)}</p>' if message else ""
    correct_form = f"""<form method="post" action="/admin/candidates/{esc(candidate_id)}">
<input type="hidden" name="csrf" value="{esc(csrf)}"><input type="hidden" name="action" value="correct">
<section class="panel"><h2>人工纠错字段</h2><div class="filters">{inputs}</div>
<label>审核备注（至少5字）<input name="review_note" minlength="5" maxlength="1000" required></label>
<div class="actions"><button type="submit">保存纠错</button></div></section></form>"""
    review_form = f"""<form method="post" action="/admin/candidates/{esc(candidate_id)}/review">
<input type="hidden" name="csrf" value="{esc(csrf)}"><label>审核备注（至少5字）<input name="review_note" minlength="5" maxlength="1000" required></label>
<div class="actions"><button name="decision" value="approve">通过并入库</button><button name="decision" value="reject">拒绝候选</button></div></form>"""
    inner = f"""<h1>候选详情</h1>{status_note}<p>{esc(row.get("source"))} · {esc(row.get("review_status"))} · {esc(row.get("captured_at"))}</p>
<section class="panel"><h2>来源与证据</h2><p>来源页面：{_safe_link(row.get("source_url"))}</p>
<p>采集方式：{esc(row.get("capture_method"))} · 解析器：{esc(row.get("parser_version"))}</p>
<p>原始HTML SHA-256：<code>{esc(row.get("raw_sha256"))}</code> · <a href="/admin/candidates/{esc(candidate_id)}/evidence">查看保存的原始HTML证据</a></p>
<details><summary>解析字段与字段证据</summary><pre>{evidence}</pre></details>
<details><summary>解析警告</summary><pre>{warnings}</pre></details></section>
{correct_form}
{review_form}<p><a href="/admin/candidates">返回候选列表</a></p>"""
    return _admin_page("候选详情", inner, request.cookies.get(COOKIE_NAME, ""))


@router.post("/admin/candidates/{candidate_id}", include_in_schema=False)
async def admin_correct_candidate(request: Request, candidate_id: UUID):
    _check_admin(request)
    values = await _request_form(request)
    _verify_csrf(request, values)
    names = ("source_listing_id", "title", "community_name", "district", "area_sqm",
             "bedrooms", "floor_text", "decoration", "asking_price_wan")
    payload = {name: values[name][0] for name in names if values.get(name, [""])[0].strip()}
    payload["review_note"] = values.get("review_note", [""])[0]
    try:
        collection_service.correct_candidate(candidate_id, CandidateCorrection(**payload))
    except (ValidationError, HTTPException) as exc:
        message = getattr(exc, "detail", None) or "请检查纠错字段和审核备注。"
        return RedirectResponse(f"/admin/candidates/{candidate_id}?message={html.escape(str(message), quote=True)}", status_code=303)
    return RedirectResponse(f"/admin/candidates/{candidate_id}?message=纠错已保存", status_code=303)


@router.post("/admin/candidates/{candidate_id}/review", include_in_schema=False)
async def admin_review_candidate(request: Request, candidate_id: UUID):
    _check_admin(request)
    values = await _request_form(request)
    _verify_csrf(request, values)
    decision = values.get("decision", [""])[0]
    note = values.get("review_note", [""])[0]
    try:
        collection_service.review_candidate(candidate_id, decision, note)
    except HTTPException as exc:
        message = getattr(exc, "detail", None) or "审核失败。"
        return RedirectResponse(f"/admin/candidates/{candidate_id}?message={html.escape(str(message), quote=True)}", status_code=303)
    return RedirectResponse(f"/admin/candidates/{candidate_id}?message=审核已记录", status_code=303)


@router.get("/admin/import", response_class=HTMLResponse, include_in_schema=False)
def admin_import_page(request: Request):
    _check_admin(request)
    cookie = request.cookies.get(COOKIE_NAME, "")
    csrf = _csrf_token(cookie)
    inner = f"""<h1>导入获准HTML样本</h1><p>仅导入你有权保存和处理的页面快照。导入只创建待审核候选，不会直接创建正式挂牌。</p>
<form method="post" action="/admin/import" class="panel">
<input type="hidden" name="csrf" value="{html.escape(csrf, quote=True)}">
<label>来源<select name="source" required><option value="beike">贝壳</option><option value="anjuke">安居客</option></select></label>
<label>来源页面URL<input name="source_url" type="url" maxlength="2000" required></label>
<label>说明（可选）<input name="note" maxlength="500"></label>
<label>HTML快照（最大1MB）<textarea name="html" required></textarea></label>
<div class="actions"><button type="submit">解析并创建待审核候选</button></div></form>"""
    return _admin_page("HTML样本导入", inner, cookie)


@router.post("/admin/import", include_in_schema=False)
async def admin_import_page_submit(request: Request):
    _check_admin(request)
    values = await _request_form(request, max_bytes=3_100_000)
    _verify_csrf(request, values)
    data = {key: values.get(key, [""])[0] for key in ("source", "source_url", "html", "note")}
    try:
        result = collection_service.stage_manual_page(HTMLPageIn(**data))
    except (ValidationError, CollectionError, HTTPException) as exc:
        message = getattr(exc, "detail", None) or str(exc)
        inner = f'<h1>样本未能导入</h1><p class="notice">{html.escape(str(message))}</p><a href="/admin/import">返回表单</a>'
        return _admin_page("导入失败", inner, request.cookies.get(COOKIE_NAME, ""), 422)
    candidate_id = result["candidate"]["id"]
    return RedirectResponse(f"/admin/candidates/{candidate_id}?message=样本已解析并进入待审核", status_code=303)


@router.get("/admin/candidates/{candidate_id}/evidence", response_class=HTMLResponse, include_in_schema=False)
def admin_candidate_evidence(request: Request, candidate_id: UUID):
    _check_admin(request)
    row = _candidate_detail(candidate_id)
    if not row:
        raise HTTPException(status_code=404, detail="Candidate not found")
    content = _candidate_html_evidence(row)
    if content is None:
        raise HTTPException(status_code=404, detail="Stored HTML evidence is unavailable")
    inner = f"<h1>原始HTML证据</h1><p>内容已作为文本转义显示，不会执行页面脚本。</p><pre>{html.escape(content)}</pre><p><a href=\"/admin/candidates/{candidate_id}\">返回候选详情</a></p>"
    return _admin_page("原始证据", inner, request.cookies.get(COOKIE_NAME, ""))
