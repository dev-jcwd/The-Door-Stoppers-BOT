"""Admin dashboard for The Door Stoppers bot.

Discord login + allowlist. Lives inside the same Render service as the bot.
Loaded by bot.py:  dashboard.register(app, <bot module>)

Environment variables (Render -> Environment):
  DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET   Discord Developer Portal -> OAuth2
  SESSION_SECRET                             any long random string
  ALLOWED_USER_IDS                           comma-separated Discord user IDs allowed in
  SITE_URL                                   optional (defaults to Render's URL)
  GEMINI_API_KEY                             optional, enables the AI writing helper
  GEMINI_MODEL                               optional (default: gemini-flash-latest)
  ASSET_CHANNEL_ID                           optional, private channel that hosts images uploaded here
"""
import asyncio
import base64
import functools
import hashlib
import hmac
import io
import json
import math
import os
import re
import secrets
import uuid
from datetime import timedelta
from urllib.parse import urlencode

import discord
import requests
from flask import Blueprint, Response, abort, jsonify, redirect, render_template, request, session
from jinja2 import ChoiceLoader, DictLoader

import dashboard_ui

bp = Blueprint("dash", __name__)
B = None  # the bot module (set in register)

DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET", "")
SESSION_SECRET = os.getenv("SESSION_SECRET", "")
ALLOWED_USER_IDS = {x for x in re.split(r"[,\s;]+", os.getenv("ALLOWED_USER_IDS", "")) if x.isdigit()}
WEB_ENABLED = bool(DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET and SESSION_SECRET)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
MAX_UPLOAD_MB = 60
API = "https://discord.com/api/v10"

NAV = [
    ("overview", "/admin", "Home", "home"),
    ("merch", "/admin/merch", "Merch panel", "merch"),
    ("stickies", "/admin/stickies", "Sticky messages", "pin"),
    ("send", "/admin/send", "Send a message", "send"),
    ("members", "/admin/members", "Members & roles", "people"),
    ("notifications", "/admin/notifications", "Notifications", "bell"),
    ("bot", "/admin/bot", "Bot profile", "bot"),
]
ASSET_V = hashlib.md5((dashboard_ui.CSS + dashboard_ui.JS).encode("utf-8")).hexdigest()[:8]


# ---------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------
def register(app, bot_module):
    global B
    B = bot_module
    app.secret_key = SESSION_SECRET or secrets.token_hex(32)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=bool(os.getenv("RENDER")),
        PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
        MAX_CONTENT_LENGTH=MAX_UPLOAD_MB * 1024 * 1024,
    )
    app.jinja_env.loader = ChoiceLoader([DictLoader(dashboard_ui.TEMPLATES), app.jinja_env.loader])
    app.register_blueprint(bp)


@bp.after_app_request
def _headers(resp):
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Robots-Tag"] = "noindex, nofollow"
    resp.headers["Referrer-Policy"] = "same-origin"
    if request.path.startswith(("/admin", "/login", "/callback", "/logout")) and "/assets/" not in request.path:
        resp.headers["Cache-Control"] = "no-store"
    return resp


@bp.app_errorhandler(413)
def _too_big(_e):
    return f"That upload is too large (limit {MAX_UPLOAD_MB} MB). Go back and choose a smaller file.", 413


# ---------------------------------------------------------------------
# Bridges to the bot's event loop
# ---------------------------------------------------------------------
def run_on_bot(coro, timeout=120):
    try:
        loop = B.bot.loop
    except Exception:
        coro.close()
        raise RuntimeError("The bot is still starting up. Try again in a moment.")
    return asyncio.run_coroutine_threadsafe(coro, loop).result(timeout=timeout)

def bot_call(coro):
    """Run an action coroutine that returns (ok, message[, url]); never raises."""
    try:
        return run_on_bot(coro)
    except Exception as e:
        return (False, f"Something went wrong: {e}")

def primary_guild():
    ch = B.bot.get_channel(B.RECORD_CHANNEL_ID)
    if ch is not None and getattr(ch, "guild", None):
        return ch.guild
    return B.bot.guilds[0] if B.bot.guilds else None

def channel_options(guild):
    out = []
    if not guild:
        return out
    chans = sorted(guild.text_channels, key=lambda c: ((c.category.position if c.category else -1), c.position))
    for c in chans:
        out.append({"id": str(c.id), "label": f"#{c.name}", "group": c.category.name if c.category else "No category"})
    return out

def role_options(guild, assignable_only=False):
    if not guild:
        return []
    top = guild.me.top_role.position if guild.me else 0
    out = []
    for r in sorted(guild.roles, key=lambda r: -r.position):
        if r.is_default():
            continue
        ok = (not r.managed) and r.position < top and not r.permissions.administrator
        if assignable_only and not ok:
            continue
        out.append({"id": str(r.id), "name": r.name, "color": f"#{r.color.value:06x}" if r.color.value else "#99aab5",
                    "assignable": ok})
    return out


# ---------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------
def _site_url():
    base = os.getenv("SITE_URL") or os.getenv("RENDER_EXTERNAL_URL") or ""
    if not base:
        base = request.host_url
        if "localhost" not in base and "127.0.0.1" not in base:
            base = base.replace("http://", "https://", 1)
    return base.rstrip("/")

def _allowed():
    return bool(WEB_ENABLED and session.get("uid") in ALLOWED_USER_IDS)

def _gate():
    """Returns None when the visitor may use the dashboard, otherwise the response to show."""
    if not WEB_ENABLED:
        return render_template("login.html", disabled=True, v=ASSET_V), 503
    uid = session.get("uid")
    if not uid:
        return render_template("login.html", disabled=False, v=ASSET_V)
    if uid not in ALLOWED_USER_IDS:
        return render_template("denied.html", name=session.get("name", ""), uid=uid,
                               csrf=session.get("csrf", ""), v=ASSET_V), 403
    return None

def guard(f):
    @functools.wraps(f)
    def wrapper(*a, **k):
        if _gate() is not None:
            return redirect("/admin")
        if request.method == "POST" and not hmac.compare_digest(request.form.get("csrf", ""), session.get("csrf", "")):
            abort(400)
        return f(*a, **k)
    return wrapper

def guard_json(f):
    @functools.wraps(f)
    def wrapper(*a, **k):
        if not _allowed():
            return jsonify(ok=False, error="Please log in again."), 403
        if not hmac.compare_digest(request.headers.get("X-CSRF", ""), session.get("csrf", "")):
            return jsonify(ok=False, error="Your session expired. Refresh the page."), 400
        return f(*a, **k)
    return wrapper

@bp.route("/login")
def login():
    if not WEB_ENABLED:
        return redirect("/admin")
    state = secrets.token_urlsafe(24)
    session["oauth_state"] = state
    params = {"client_id": DISCORD_CLIENT_ID, "redirect_uri": f"{_site_url()}/callback", "response_type": "code",
              "scope": "identify", "state": state, "prompt": "none"}
    return redirect("https://discord.com/oauth2/authorize?" + urlencode(params))

@bp.route("/callback")
def callback():
    if not WEB_ENABLED or request.args.get("error"):
        return redirect("/admin")
    expected = session.pop("oauth_state", None)
    if not expected or not hmac.compare_digest(request.args.get("state", ""), expected):
        return "Login expired. Please go back and try again.", 400
    try:
        tok = requests.post(f"{API}/oauth2/token",
                            data={"grant_type": "authorization_code", "code": request.args.get("code", ""),
                                  "redirect_uri": f"{_site_url()}/callback"},
                            auth=(DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET), timeout=15)
        tok.raise_for_status()
        me = requests.get(f"{API}/users/@me", headers={"Authorization": f"Bearer {tok.json()['access_token']}"}, timeout=15)
        me.raise_for_status()
        u = me.json()
    except Exception as e:
        print(f"Dashboard login error: {e}")
        return "Discord login failed. Check the redirect URL and client secret, then try again.", 502
    session.clear()
    session.permanent = True
    session.update(uid=str(u["id"]), name=u.get("global_name") or u.get("username") or "Unknown",
                   avatar=u.get("avatar") or "", csrf=secrets.token_hex(16))
    return redirect("/admin")

@bp.route("/logout", methods=["POST"])
def logout():
    if session.get("csrf") and hmac.compare_digest(request.form.get("csrf", ""), session["csrf"]):
        session.clear()
    return redirect("/admin")


# ---------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------
def page(template, **ctx):
    avatar = session.get("avatar")
    uid = session.get("uid", "0")
    user_avatar = (f"https://cdn.discordapp.com/avatars/{uid}/{avatar}.png?size=64" if avatar
                   else "https://cdn.discordapp.com/embed/avatars/0.png")
    try:
        bot_avatar = str(B.bot.user.display_avatar.url)
        bot_name = B.bot.user.name
    except Exception:
        bot_avatar, bot_name = "", "Bot"
    boot = {"bot_avatar": bot_avatar, "bot_name": bot_name, "csrf": session.get("csrf", "")}
    m = ctx.get("m")
    if m:
        boot["products"] = [{"label": p.get("label", ""), "style": p.get("style", "primary")} for p in m.get("products", [])]
        boot["reply"] = m.get("reply", {})
        first = (m.get("products") or [{}])[0]
        boot["sample"] = {k: first.get(k, "") for k in ("name", "price", "note", "image", "thumbnail")}
    if ctx.get("img_map"):
        boot["assets"] = dict(ctx["img_map"])
        if m and boot.get("sample"):
            for k in ("image", "thumbnail"):
                boot["sample"][k] = boot["assets"].get(boot["sample"][k], boot["sample"][k])
    if ctx.get("roles"):
        boot["roles"] = {str(r["id"]): r["name"] for r in ctx["roles"]}
    base = dict(nav=NAV, user_name=session.get("name", ""), user_avatar=user_avatar, csrf=session.get("csrf", ""),
                flash=session.pop("flash", None), bot_avatar=bot_avatar, bot_name=bot_name, v=ASSET_V,
                ai_ready=bool(GEMINI_API_KEY), boot=boot)
    base.update(ctx)
    return render_template(template, **base)

def back(result, to):
    """Flash an (ok, message[, url]) result and redirect."""
    session["flash"] = [bool(result[0]), str(result[1])[:500], result[2] if len(result) > 2 else ""]
    return redirect(to)

def _text(name, n, required=False, label=None):
    v = (request.form.get(name, "") or "").replace("\r\n", "\n").strip()
    if required and not v:
        raise ValueError(f"{label or name} can't be empty.")
    if len(v) > n:
        raise ValueError(f"{label or name} is too long (max {n} characters).")
    return v

def _color(name="color", default="#FFFF00"):
    v = (request.form.get(name, "") or default).strip()
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", v):
        raise ValueError("Pick a valid color.")
    return v.upper()

def _img(name, label="Image"):
    v = (request.form.get(name, "") or "").strip()
    if not v:
        return ""
    if len(v) > 700 or not (re.match(r"^https?://\S+$", v) or re.fullmatch(r"asset:\d+:\d+:\d+", v)):
        raise ValueError(f"{label} must be a link starting with http(s):// or an uploaded image.")
    return v

def _int(name):
    try:
        return int(request.form.get(name) or 0)
    except ValueError:
        return 0

async def _img_map(refs):
    out = {}
    for r in refs:
        if r and r.startswith("asset:"):
            out[r] = await B.resolve_image(r)
    return out

def _snapshot(obj):
    return json.loads(json.dumps(obj))


# ---------------------------------------------------------------------
# Static assets
# ---------------------------------------------------------------------
@bp.route("/admin/assets/app.css")
def asset_css():
    return Response(dashboard_ui.CSS, mimetype="text/css", headers={"Cache-Control": "public, max-age=3600"})

@bp.route("/admin/assets/app.js")
def asset_js():
    return Response(dashboard_ui.JS, mimetype="application/javascript", headers={"Cache-Control": "public, max-age=3600"})


# ---------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------
async def _overview_data():
    cfg = await B.get_config()
    state = await B.get_notifier_state()
    g = primary_guild()
    lat = B.bot.latency
    asset_ok = False
    if B.ASSET_CHANNEL_ID:
        asset_ok = (await B._resolve_channel(B.ASSET_CHANNEL_ID)) is not None
    pm = cfg["merch"].get("panel_message") or {}
    default_chan = state.get("channel_id") or B.NOTIFIER_CHANNEL_ID
    return {
        "guild_name": g.name if g else "—", "members": g.member_count if g else 0,
        "latency": None if (lat is None or math.isnan(lat) or math.isinf(lat)) else round(lat * 1000),
        "feeds": len(state["feeds"]), "products": len(cfg["merch"]["products"]),
        "stickies": len([s for s in cfg["stickies"] if s.get("enabled", True)]),
        "checks": [
            {"ok": bool(pm.get("message_id")), "label": "Merch panel is linked",
             "hint": "Publish or link your panel so edits can update it in Discord.", "href": "/admin/merch?tab=panel"},
            {"ok": bool(GEMINI_API_KEY), "label": "Gemini writing helper",
             "hint": "Add GEMINI_API_KEY in Render to enable “Write with AI”.", "href": "/admin/bot"},
            {"ok": asset_ok, "label": "Image uploads",
             "hint": "Add ASSET_CHANNEL_ID (a private channel) in Render to upload images here.", "href": "/admin/merch?tab=products"},
            {"ok": bool(await B._resolve_channel(default_chan)), "label": "Notification channel",
             "hint": "Pick where feed alerts are posted.", "href": "/admin/notifications"},
        ],
    }

@bp.route("/admin")
def overview():
    gate = _gate()
    if gate is not None:
        return gate
    try:
        data = run_on_bot(_overview_data())
    except Exception as e:
        return f"The bot isn't ready yet ({e}). Refresh in a few seconds.", 503
    return page("overview.html", active="overview", **data)


# ---------------------------------------------------------------------
# Merch panel
# ---------------------------------------------------------------------
async def _merch_data():
    cfg = await B.get_config()
    m = _snapshot(cfg["merch"])
    g = primary_guild()
    refs = [m["panel"].get("image"), m["panel"].get("thumbnail"), m["ticket"].get("image"), m["ticket"].get("thumbnail")]
    for p in m["products"]:
        refs += [p.get("image"), p.get("thumbnail")]
    pm = m.get("panel_message") or {}
    jump = f"https://discord.com/channels/{g.id}/{pm['channel_id']}/{pm['message_id']}" if (g and pm.get("message_id")) else ""
    return {"m": m, "channels": channel_options(g), "img_map": await _img_map(refs),
            "can_upload": bool(B.ASSET_CHANNEL_ID), "panel_url": jump}

@bp.route("/admin/merch")
@guard
def merch_page():
    data = run_on_bot(_merch_data())
    return page("merch.html", active="merch", tab=request.args.get("tab", "panel"), **data)

def _merch_back(tab):
    return f"/admin/merch?tab={tab}"

@bp.route("/admin/merch/panel", methods=["POST"])
@guard
def merch_panel_save():
    try:
        vals = dict(title=_text("title", 256, label="Title"), description=_text("description", 4000, label="Description"),
                    color=_color(), image=_img("image"), thumbnail=_img("thumbnail", "Thumbnail"),
                    footer=_text("footer", 200, label="Footer"), button_label=_text("button_label", 80, True, "Button label"),
                    button_style=request.form.get("button_style", "primary"))
    except ValueError as e:
        return back((False, str(e)), _merch_back("panel"))
    if vals["button_style"] not in B.STYLE_MAP:
        vals["button_style"] = "primary"
    push = bool(request.form.get("push"))

    async def act():
        cfg = await B.get_config()
        cfg["merch"]["panel"].update(vals)
        await B.save_config()
        if push:
            ok, msg = await B.update_panel_message()
            return (ok, "Saved. " + msg)
        return (True, "Saved. Use “Update posted panel” to push it to Discord.")
    return back(bot_call(act()), _merch_back("panel"))

@bp.route("/admin/merch/panel/publish", methods=["POST"])
@guard
def merch_panel_publish():
    cid = _int("channel")

    async def act():
        ch = await B._resolve_channel(cid)
        if not ch or ch.guild != primary_guild():
            return (False, "Pick a channel from the list.")
        msg = await B.post_panel(ch)
        return (True, f"Published in #{ch.name}. The bot now tracks this panel.", msg.jump_url)
    return back(bot_call(act()), _merch_back("panel"))

@bp.route("/admin/merch/panel/update", methods=["POST"])
@guard
def merch_panel_update():
    return back(bot_call(B.update_panel_message()), _merch_back("panel"))

@bp.route("/admin/merch/panel/track", methods=["POST"])
@guard
def merch_panel_track():
    m = re.search(r"channels/(\d+)/(\d+)/(\d+)", request.form.get("link", ""))
    if not m:
        return back((False, "Paste the message link (right-click the panel → Copy Message Link)."), _merch_back("panel"))
    gid, cid, mid = (int(x) for x in m.groups())

    async def act():
        g = primary_guild()
        if not g or g.id != gid:
            return (False, "That message is from a different server.")
        ch = await B._resolve_channel(cid)
        if not ch:
            return (False, "Couldn't open that channel.")
        try:
            msg = await ch.fetch_message(mid)
        except Exception:
            return (False, "Couldn't find that message.")
        if msg.author.id != B.bot.user.id:
            return (False, "That message wasn't posted by this bot, so it can't be edited.")
        cfg = await B.get_config()
        cfg["merch"]["panel_message"] = {"channel_id": cid, "message_id": mid}
        await B.save_config()
        return (True, "Linked. Edits will now update that panel.", msg.jump_url)
    return back(bot_call(act()), _merch_back("panel"))

@bp.route("/admin/merch/ticket", methods=["POST"])
@guard
def merch_ticket_save():
    try:
        vals = dict(title=_text("title", 256, label="Title"), description=_text("description", 4000, True, "Message"),
                    color=_color(), image=_img("image"), thumbnail=_img("thumbnail", "Thumbnail"))
    except ValueError as e:
        return back((False, str(e)), _merch_back("ticket"))

    async def act():
        cfg = await B.get_config()
        cfg["merch"]["ticket"].update(vals)
        await B.save_config()
        return (True, "Saved. New tickets will use this welcome message.")
    return back(bot_call(act()), _merch_back("ticket"))

@bp.route("/admin/merch/product", methods=["POST"])
@guard
def merch_product_save():
    pid = request.form.get("id", "")
    try:
        vals = dict(label=_text("label", 80, True, "Button label"), name=_text("name", 100, True, "Item name"),
                    price=_text("price", 30, True, "Price"), note=_text("note", 500, label="Note"),
                    image=_img("image"), thumbnail=_img("thumbnail", "Thumbnail"),
                    style=request.form.get("style", "primary"))
    except ValueError as e:
        return back((False, str(e)), _merch_back("products"))
    if vals["style"] not in B.STYLE_MAP:
        vals["style"] = "primary"

    async def act():
        cfg = await B.get_config()
        products = cfg["merch"]["products"]
        if pid == "new":
            if len(products) >= 25:
                return (False, "Discord allows up to 25 buttons on one message.")
            products.append({"id": uuid.uuid4().hex[:8], **vals})
            msg = f"Added “{vals['label']}”."
        else:
            p = B.find_product(cfg, pid)
            if not p:
                return (False, "That item no longer exists.")
            p.update(vals)
            msg = f"Saved “{vals['label']}”."
        await B.save_config()
        return (True, msg + " It's live for new and existing tickets.")
    return back(bot_call(act()), _merch_back("products"))

@bp.route("/admin/merch/product/delete", methods=["POST"])
@guard
def merch_product_delete():
    pid = request.form.get("id", "")

    async def act():
        cfg = await B.get_config()
        p = B.find_product(cfg, pid)
        if not p:
            return (False, "That item no longer exists.")
        cfg["merch"]["products"].remove(p)
        await B.save_config()
        return (True, f"Deleted “{p['label']}”.")
    return back(bot_call(act()), _merch_back("products"))

@bp.route("/admin/merch/product/move", methods=["POST"])
@guard
def merch_product_move():
    pid, d = request.form.get("id", ""), request.form.get("dir", "up")

    async def act():
        cfg = await B.get_config()
        ps = cfg["merch"]["products"]
        i = next((k for k, p in enumerate(ps) if p["id"] == pid), None)
        if i is None:
            return (False, "That item no longer exists.")
        j = i - 1 if d == "up" else i + 1
        if 0 <= j < len(ps):
            ps[i], ps[j] = ps[j], ps[i]
            await B.save_config()
        return (True, "Order updated. New tickets will show the buttons in this order.")
    return back(bot_call(act()), _merch_back("products"))

@bp.route("/admin/merch/reply", methods=["POST"])
@guard
def merch_reply_save():
    try:
        r = dict(message=_text("message", 2000, True, "Chat message"), embed_title=_text("embed_title", 256, label="Card title"),
                 embed_description=_text("embed_description", 4000, label="Card text"), color=_color(),
                 yes_label=_text("yes_label", 80, True, "Yes button"), no_label=_text("no_label", 80, True, "No button"))
        form_text = _text("form_text", 2000, True, "Order form")
    except ValueError as e:
        return back((False, str(e)), _merch_back("replies"))

    async def act():
        cfg = await B.get_config()
        cfg["merch"]["reply"].update(r)
        cfg["merch"]["form"]["text"] = form_text
        await B.save_config()
        return (True, "Saved. The next item a buyer picks will use these replies.")
    return back(bot_call(act()), _merch_back("replies"))

@bp.route("/admin/merch/close", methods=["POST"])
@guard
def merch_close_save():
    when = request.form.get("when", "after_proceed")
    if when not in ("ticket_open", "after_select", "after_proceed", "after_receipt"):
        when = "after_proceed"
    try:
        label = _text("label", 80, True, "Button label")
        message = _text("message", 500, label="Message above the button")
    except ValueError as e:
        return back((False, str(e)), _merch_back("close"))

    async def act():
        cfg = await B.get_config()
        cfg["merch"]["close"].update(when=when, label=label, message=message)
        await B.save_config()
        return (True, "Saved. The close button will appear at the new moment in new tickets.")
    return back(bot_call(act()), _merch_back("close"))


# ---------------------------------------------------------------------
# Image upload (hosted in the private asset channel)
# ---------------------------------------------------------------------
def _sniff_image(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:4] == b"GIF8":
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None

@bp.route("/admin/upload-image", methods=["POST"])
@guard_json
def upload_image():
    f = request.files.get("file")
    if not f:
        return jsonify(ok=False, error="Choose an image first."), 400
    data = f.read()
    ext = _sniff_image(data)
    if not ext:
        return jsonify(ok=False, error="That file isn't a PNG, JPG, GIF or WEBP image."), 400
    if len(data) > 8 * 1024 * 1024:
        return jsonify(ok=False, error="Images must be 8 MB or smaller."), 400
    if not B.ASSET_CHANNEL_ID:
        return jsonify(ok=False, error="Uploads aren't set up. Add ASSET_CHANNEL_ID in Render."), 400

    async def act():
        ch = await B._resolve_channel(B.ASSET_CHANNEL_ID)
        if not ch:
            raise RuntimeError("The asset channel isn't visible to the bot.")
        msg = await ch.send(file=discord.File(io.BytesIO(data), filename=f"upload-{uuid.uuid4().hex[:8]}.{ext}"))
        return {"ref": f"asset:{ch.id}:{msg.id}:0", "url": msg.attachments[0].url}
    try:
        out = run_on_bot(act())
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500
    return jsonify(ok=True, **out)


# ---------------------------------------------------------------------
# Sticky messages
# ---------------------------------------------------------------------
async def _stickies_data():
    cfg = await B.get_config()
    g = primary_guild()
    names = {str(c.id): c.name for c in (g.text_channels if g else [])}
    items = _snapshot(cfg["stickies"])
    for s in items:
        s["channel_name"] = names.get(str(s["channel_id"]), "unknown channel")
    return {"stickies": items, "channels": channel_options(g), "img_map": await _img_map([s.get("image") for s in items]),
            "can_upload": bool(B.ASSET_CHANNEL_ID), "ai_ready": bool(GEMINI_API_KEY)}

@bp.route("/admin/stickies")
@guard
def stickies_page():
    return page("stickies.html", active="stickies", edit=request.args.get("edit", ""), **run_on_bot(_stickies_data()))

@bp.route("/admin/stickies/save", methods=["POST"])
@guard
def stickies_save():
    sid = request.form.get("id", "")
    cid = _int("channel")
    mode = request.form.get("mode", "text")
    mode = mode if mode in ("text", "embed") else "text"
    try:
        content = _text("content", 1900 if mode == "text" else 3900, True, "Message")
        title = _text("title", 256, label="Title")
        color = _color()
        image = _img("image")
    except ValueError as e:
        return back((False, str(e)), "/admin/stickies" + (f"?edit={sid}" if sid else ""))
    enabled = bool(request.form.get("enabled"))

    async def act():
        cfg = await B.get_config()
        g = primary_guild()
        ch = await B._resolve_channel(cid)
        if not ch or ch.guild != g:
            return (False, "Pick a channel from the list.")
        existing = next((s for s in cfg["stickies"] if s["id"] == sid), None) if sid else None
        clash = next((s for s in cfg["stickies"] if int(s["channel_id"]) == cid and s is not existing), None)
        if clash:
            return (False, f"#{ch.name} already has a sticky message. Edit or delete that one first.")
        old_channel = int(existing["channel_id"]) if existing else None
        data = {"channel_id": cid, "mode": mode, "content": content, "title": title, "color": color,
                "image": image, "enabled": enabled}
        if existing:
            existing.update(data)
        else:
            cfg["stickies"].append({"id": uuid.uuid4().hex[:8], **data})
        await B.save_config()
        B.rebuild_sticky_index(cfg)
        if old_channel and old_channel != cid:
            await B.remove_sticky_messages(old_channel)
        if enabled:
            await B.refresh_sticky(cid, force=True)
            return (True, f"Sticky message is live in #{ch.name}. It posts silently and stays at the bottom.")
        await B.remove_sticky_messages(cid)
        return (True, f"Saved, but paused. Nothing is posted in #{ch.name} until you turn it on.")
    return back(bot_call(act()), "/admin/stickies")

@bp.route("/admin/stickies/delete", methods=["POST"])
@guard
def stickies_delete():
    sid = request.form.get("id", "")

    async def act():
        cfg = await B.get_config()
        s = next((x for x in cfg["stickies"] if x["id"] == sid), None)
        if not s:
            return (False, "That sticky message no longer exists.")
        cfg["stickies"].remove(s)
        await B.save_config()
        B.rebuild_sticky_index(cfg)
        await B.remove_sticky_messages(int(s["channel_id"]))
        return (True, "Sticky message deleted and removed from the channel.")
    return back(bot_call(act()), "/admin/stickies")

@bp.route("/admin/stickies/repost", methods=["POST"])
@guard
def stickies_repost():
    sid = request.form.get("id", "")

    async def act():
        cfg = await B.get_config()
        s = next((x for x in cfg["stickies"] if x["id"] == sid), None)
        if not s:
            return (False, "That sticky message no longer exists.")
        await B.refresh_sticky(int(s["channel_id"]), force=True)
        return (True, "Reposted at the bottom of the channel.")
    return back(bot_call(act()), "/admin/stickies")


# ---------------------------------------------------------------------
# Send a message
# ---------------------------------------------------------------------
async def _send_data():
    g = primary_guild()
    return {"channels": channel_options(g), "roles": role_options(g), "ai_ready": bool(GEMINI_API_KEY),
            "limit_mb": round((g.filesize_limit if g else 8 * 1024 * 1024) / (1024 * 1024))}

@bp.route("/admin/send")
@guard
def send_page():
    return page("send.html", active="send", **run_on_bot(_send_data()))

@bp.route("/admin/send", methods=["POST"])
@guard
def send_post():
    cid = _int("channel")
    ping = _int("ping_role")
    silent = bool(request.form.get("silent"))
    mode = request.form.get("mode", "plain")
    try:
        content = _text("content", 4000 if mode == "embed" else 2000, label="Message")
        title = _text("title", 256, label="Title")
        color = _color()
        image = _img("image")
    except ValueError as e:
        return back((False, str(e)), "/admin/send")
    files = []
    for f in request.files.getlist("files"):
        if f and f.filename:
            files.append((re.sub(r"[^\w.\- ]", "_", f.filename)[:100] or "file", f.read()))
    if not content and not files and not (mode == "embed" and (title or image)):
        return back((False, "Write a message or attach a file first."), "/admin/send")
    who = session.get("name", "admin")

    async def act():
        g = primary_guild()
        ch = await B._resolve_channel(cid)
        if not ch or ch.guild != g:
            return (False, "Pick a channel from the list.")
        if not ch.permissions_for(g.me).send_messages:
            return (False, f"The bot can't send messages in #{ch.name}. Check the channel permissions.")
        limit = g.filesize_limit
        for name, data in files:
            if len(data) > limit:
                return (False, f"“{name}” is {len(data) // (1024 * 1024)} MB. This server allows {limit // (1024 * 1024)} MB per file.")
        if len(files) > 10:
            return (False, "Discord allows up to 10 files per message.")
        dfiles = [discord.File(io.BytesIO(data), filename=name) for name, data in files]
        role = g.get_role(ping) if ping else None
        allowed = discord.AllowedMentions(everyone=False, users=False, roles=[role] if role else False)
        lead = f"{role.mention}" if role else ""
        kwargs = dict(allowed_mentions=allowed, silent=silent)
        if mode == "embed":
            embed = await B.build_embed(title, content, color, image)
            first_img = next((f.filename for f in dfiles if re.search(r"\.(png|jpe?g|gif|webp)$", f.filename, re.I)), None)
            if first_img and not image:
                embed.set_image(url=f"attachment://{first_img}")
            msg = await ch.send(content=lead or None, embed=embed, files=dfiles or None, **kwargs)
        else:
            text = (f"{lead} {content}".strip() if lead else content)[:2000]
            msg = await ch.send(content=text or None, files=dfiles or None, **kwargs)
        if ch.id in B.STICKY_CHANNELS:
            B.schedule_sticky(ch.id)
        print(f"Dashboard: {who} sent a message to #{ch.name}")
        return (True, f"Sent to #{ch.name}.", msg.jump_url)
    return back(bot_call(act()), "/admin/send")


# ---------------------------------------------------------------------
# Gemini writing helper
# ---------------------------------------------------------------------
KIND_HELP = {
    "announcement": ("a server announcement that gets people excited and tells them exactly what's happening", 1800),
    "post": ("a regular message to post in a channel", 1800),
    "sticky": ("a short sticky note that stays at the bottom of a channel (rules, links or a reminder)", 600),
    "merch": ("a short, friendly merch message for buyers", 900),
}
_gemini_model_cache = {}

def _gemini_error(r):
    try:
        return r.json().get("error", {}).get("message") or r.text[:200]
    except Exception:
        return r.text[:200]

def _gemini_pick_model():
    r = requests.get("https://generativelanguage.googleapis.com/v1beta/models", params={"pageSize": 200},
                     headers={"x-goog-api-key": GEMINI_API_KEY}, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"Gemini: {_gemini_error(r)}")
    best, best_v = None, (-1, -1)
    for m in r.json().get("models", []):
        name = m.get("name", "").replace("models/", "")
        mm = re.fullmatch(r"gemini-(\d+)(?:\.(\d+))?-flash", name)
        if mm and "generateContent" in m.get("supportedGenerationMethods", []):
            v = (int(mm.group(1)), int(mm.group(2) or 0))
            if v > best_v:
                best, best_v = name, v
    if not best:
        raise RuntimeError("Gemini: couldn't find a usable model. Set GEMINI_MODEL in Render.")
    return best

def gemini_generate(system, user_text):
    if not GEMINI_API_KEY:
        raise RuntimeError("Gemini isn't connected yet. Add GEMINI_API_KEY in Render → Environment.")
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user_text}]}],
            "generationConfig": {"temperature": 0.8, "maxOutputTokens": 2048}}
    headers = {"x-goog-api-key": GEMINI_API_KEY, "Content-Type": "application/json"}
    for attempt in range(2):
        model = _gemini_model_cache.get("m") or GEMINI_MODEL
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                          headers=headers, json=body, timeout=45)
        if r.status_code == 404 and attempt == 0:
            _gemini_model_cache["m"] = _gemini_pick_model()
            continue
        break
    if r.status_code != 200:
        raise RuntimeError(f"Gemini: {_gemini_error(r)}")
    data = r.json()
    cands = data.get("candidates") or []
    if not cands:
        reason = (data.get("promptFeedback") or {}).get("blockReason", "no answer")
        raise RuntimeError(f"Gemini didn't return a message ({reason}). Try rephrasing.")
    parts = (cands[0].get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
    if not text:
        raise RuntimeError("Gemini returned an empty message. Try again.")
    return text

def _fit(text, limit):
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for sep in ("\n", ". ", " "):
        i = cut.rfind(sep)
        if i > limit * 0.6:
            return cut[:i + (1 if sep != " " else 0)].rstrip()
    return cut

async def _ai_context():
    cfg = await B.get_config()
    return (cfg.get("ai") or {}).get("context", "")

@bp.route("/admin/ai", methods=["POST"])
@guard_json
def ai_generate():
    p = request.get_json(silent=True) or {}
    kind = p.get("kind") if p.get("kind") in KIND_HELP else "post"
    tone = str(p.get("tone") or "friendly and upbeat")[:60]
    language = "Taglish (natural Filipino-English mix)" if p.get("language") == "taglish" else "English"
    prompt = str(p.get("prompt") or "").strip()[:1500]
    current = str(p.get("current") or "").strip()[:3500]
    if not prompt and not current:
        return jsonify(ok=False, error="Tell Gemini what the message is about."), 400
    desc, limit = KIND_HELP[kind]
    if p.get("limit"):
        try:
            limit = max(100, min(int(p["limit"]), 3900))
        except (TypeError, ValueError):
            pass
    try:
        context = run_on_bot(_ai_context())
    except Exception:
        context = ""
    system = (
        "You write Discord messages for The Door Stoppers, an independent band, posted by the band's admins in their Discord server.\n"
        f"About the band and server: {context or 'No extra details provided.'}\n"
        "Rules: reply with only the finished message text, with no preamble, quotation marks or explanations. "
        "Use Discord markdown sparingly (**bold**, *italics*, > quotes, -# small text, bullet lists) and a few fitting emojis. "
        "Never invent dates, prices, links or names. If a detail is missing, leave a [bracketed placeholder]. "
        f"Keep it under {limit} characters. Tone: {tone}. Language: {language}. The message is {desc}."
    )
    user_text = (f"Improve this draft. Instruction: {prompt or 'make it clearer and more engaging'}\n\nDraft:\n{current}"
                 if current else prompt)
    try:
        text = gemini_generate(system, user_text)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 502
    return jsonify(ok=True, text=_fit(text, limit))


# ---------------------------------------------------------------------
# Bot profile
# ---------------------------------------------------------------------
def _api(method, path, **kw):
    return requests.request(method, f"{API}{path}", headers={"Authorization": f"Bot {B.DISCORD_TOKEN}"}, timeout=20, **kw)

def _api_error(r):
    try:
        j = r.json()
        detail = "; ".join(f"{k}: {x.get('message', '')}" for k, x in (j.get("errors") or {}).items()
                           if isinstance(x, dict))
        return (j.get("message") or "Discord refused the change") + (f" ({detail})" if detail else "")
    except Exception:
        return f"Discord returned {r.status_code}"

@bp.route("/admin/bot")
@guard
def bot_page():
    prof = {"name": "", "bio": "", "avatar": "", "banner": ""}
    problem = ""
    try:
        me = _api("GET", "/users/@me")
        app_info = _api("GET", "/applications/@me")
        if me.status_code == 200:
            u = me.json()
            prof["name"] = u.get("global_name") or u.get("username", "")
            if u.get("avatar"):
                prof["avatar"] = f"https://cdn.discordapp.com/avatars/{u['id']}/{u['avatar']}.png?size=256"
            if u.get("banner"):
                prof["banner"] = f"https://cdn.discordapp.com/banners/{u['id']}/{u['banner']}.png?size=600"
        if app_info.status_code == 200:
            prof["bio"] = app_info.json().get("description", "")
        else:
            problem = "Couldn't read the bot's current bio."
    except Exception as e:
        problem = f"Couldn't reach Discord: {e}"
    return page("bot.html", active="bot", prof=prof, problem=problem, ai_context=run_on_bot(_ai_context()),
                ai_ready=bool(GEMINI_API_KEY), model=_gemini_model_cache.get("m") or GEMINI_MODEL)

@bp.route("/admin/bot/bio", methods=["POST"])
@guard
def bot_bio():
    try:
        bio = _text("bio", 400, label="Bio")
    except ValueError as e:
        return back((False, str(e)), "/admin/bot")
    try:
        r = _api("PATCH", "/applications/@me", json={"description": bio})
    except Exception as e:
        return back((False, f"Couldn't reach Discord: {e}"), "/admin/bot")
    if r.status_code == 200:
        return back((True, "Bio updated. Discord can take a moment to show it on the profile."), "/admin/bot")
    return back((False, _api_error(r)), "/admin/bot")

def _profile_image(field, label):
    f = request.files.get("file")
    if not f:
        return back((False, f"Choose an image for the {label} first."), "/admin/bot")
    data = f.read()
    ext = _sniff_image(data)
    if not ext:
        return back((False, "Use a PNG, JPG, GIF or WEBP image."), "/admin/bot")
    if len(data) > 8 * 1024 * 1024:
        return back((False, "Images must be 8 MB or smaller."), "/admin/bot")
    mime = {"png": "image/png", "jpg": "image/jpeg", "gif": "image/gif", "webp": "image/webp"}[ext]
    uri = f"data:{mime};base64,{base64.b64encode(data).decode()}"
    try:
        r = _api("PATCH", "/users/@me", json={field: uri})
    except Exception as e:
        return back((False, f"Couldn't reach Discord: {e}"), "/admin/bot")
    if r.status_code == 200:
        return back((True, f"The bot's {label} was updated."), "/admin/bot")
    return back((False, _api_error(r)), "/admin/bot")

@bp.route("/admin/bot/avatar", methods=["POST"])
@guard
def bot_avatar():
    return _profile_image("avatar", "profile picture")

@bp.route("/admin/bot/banner", methods=["POST"])
@guard
def bot_banner():
    return _profile_image("banner", "banner")

@bp.route("/admin/bot/banner/remove", methods=["POST"])
@guard
def bot_banner_remove():
    try:
        r = _api("PATCH", "/users/@me", json={"banner": None})
    except Exception as e:
        return back((False, f"Couldn't reach Discord: {e}"), "/admin/bot")
    return back((True, "Banner removed.") if r.status_code == 200 else (False, _api_error(r)), "/admin/bot")

@bp.route("/admin/bot/ai", methods=["POST"])
@guard
def bot_ai_context():
    try:
        ctx = _text("context", 1500, label="Band details")
    except ValueError as e:
        return back((False, str(e)), "/admin/bot")

    async def act():
        cfg = await B.get_config()
        cfg.setdefault("ai", {})["context"] = ctx
        await B.save_config()
        return (True, "Saved. Gemini will use these details in every message it writes.")
    return back(bot_call(act()), "/admin/bot")


# ---------------------------------------------------------------------
# Members & roles
# ---------------------------------------------------------------------
async def _members_data(q, role_id):
    g = primary_guild()
    roles = role_options(g)
    assignable = {r["id"] for r in roles if r["assignable"]}
    ql = q.lower()
    found = []
    for m in (g.members if g else []):
        if m.bot and not ql:
            continue
        hay = f"{m.name} {m.display_name} {m.global_name or ''} {m.id}".lower()
        if ql and ql not in hay:
            continue
        if role_id and not any(r.id == role_id for r in m.roles):
            continue
        found.append(m)
    found.sort(key=lambda m: m.display_name.lower())
    total = len(found)
    members = []
    for m in found[:40]:
        members.append({
            "id": str(m.id), "name": m.name, "display": m.display_name, "bot": m.bot,
            "avatar": str(m.display_avatar.replace(size=64).url),
            "roles": [{"id": str(r.id), "name": r.name, "color": f"#{r.color.value:06x}" if r.color.value else "#99aab5",
                       "removable": str(r.id) in assignable}
                      for r in sorted(m.roles, key=lambda r: -r.position) if not r.is_default()],
        })
    return {"members": members, "total": total, "roles": roles, "assignable": [r for r in roles if r["assignable"]]}

@bp.route("/admin/members")
@guard
def members_page():
    q = (request.args.get("q") or "").strip()[:60]
    try:
        role_id = int(request.args.get("role") or 0)
    except ValueError:
        role_id = 0
    return page("members.html", active="members", q=q, role_filter=str(role_id or ""),
                **run_on_bot(_members_data(q, role_id)))

@bp.route("/admin/members/role", methods=["POST"])
@guard
def members_role():
    uid, rid, action = _int("user_id"), _int("role_id"), request.form.get("action", "add")
    q, rf = request.form.get("q", ""), request.form.get("rf", "")
    who = session.get("name", "admin")
    to = "/admin/members?" + urlencode({"q": q, "role": rf})

    async def act():
        g = primary_guild()
        member = g.get_member(uid)
        if not member:
            try:
                member = await g.fetch_member(uid)
            except Exception:
                return (False, "Couldn't find that member.")
        role = g.get_role(rid)
        if not role:
            return (False, "Pick a role.")
        if role.is_default() or role.managed or role.permissions.administrator or role.position >= g.me.top_role.position:
            return (False, f"The bot isn't allowed to manage “{role.name}”. Roles with admin permission, integration roles and roles above the bot are protected.")
        try:
            if action == "remove":
                await member.remove_roles(role, reason=f"Dashboard: {who}")
                return (True, f"Removed {role.name} from {member.display_name}.")
            await member.add_roles(role, reason=f"Dashboard: {who}")
            return (True, f"Gave {role.name} to {member.display_name}.")
        except discord.Forbidden:
            return (False, "Discord refused. Move the bot's role above this role in Server Settings → Roles.")
    return back(bot_call(act()), to)


# ---------------------------------------------------------------------
# Notifications (social + music feeds)
# ---------------------------------------------------------------------
async def _notif_data():
    state = await B.get_notifier_state()
    snap = _snapshot(state)
    g = primary_guild()
    feeds = []
    for f in snap["feeds"]:
        meta = B.PLATFORMS.get(f["platform"], B.PLATFORMS["rss"])
        feeds.append({"name": f["name"], "label": meta["label"], "emoji": meta["emoji"], "platform": f["platform"],
                      "target": f["target"][:80], "channel_id": str(f.get("channel_id") or "")})
    return {"feeds": feeds, "channels": channel_options(g),
            "default_id": str(snap.get("channel_id") or B.NOTIFIER_CHANNEL_ID),
            "platforms": [(k, v["label"]) for k, v in B.PLATFORMS.items()],
            "interval": B.NOTIFIER_INTERVAL_SECONDS // 60}

@bp.route("/admin/notifications")
@guard
def notifications_page():
    return page("notifications.html", active="notifications", **run_on_bot(_notif_data()))

async def _valid_channel(cid):
    ch = await B._resolve_channel(cid) if cid else None
    return ch if (ch and ch.guild == primary_guild()) else None

@bp.route("/admin/notifications/add", methods=["POST"])
@guard
def notif_add():
    platform = request.form.get("platform", "").lower()
    name, target, cid = request.form.get("name", "").strip(), request.form.get("target", "").strip(), _int("channel")

    async def act():
        if platform not in B.PLATFORMS:
            return (False, "Unknown platform.")
        if not re.fullmatch(r"[\w.\-]{1,32}", name):
            return (False, "Name must be 1-32 characters: letters, numbers, dash, underscore or dot (no spaces).")
        if name.lower() in ("default", "all"):
            return (False, "That name is reserved. Pick another.")
        if not target or len(target) > 300:
            return (False, "Enter a handle, ID or link (max 300 characters).")
        state = await B.get_notifier_state()
        if any(f["name"].lower() == name.lower() for f in state["feeds"]):
            return (False, f"A feed named “{name}” already exists.")
        feed = {"name": name, "platform": platform, "target": target}
        if cid:
            if not await _valid_channel(cid):
                return (False, "That channel isn't visible to the bot.")
            feed["channel_id"] = cid
        try:
            if platform == "youtube":
                feed["target"] = await asyncio.to_thread(B.resolve_youtube_channel_id, target)
            items = await asyncio.to_thread(B.fetch_items, feed)
        except Exception as e:
            return (False, f"Couldn't read that feed: {e}")
        state["feeds"].append(feed)
        state["seen"][name] = [i["id"] for i in items][:B.MAX_SEEN_PER_FEED]
        await B.save_notifier_state()
        if items:
            return (True, f"Added {name}. Latest item right now: {items[0]['title'][:100]}. Only new posts will be announced.")
        return (True, f"Added {name}, but the feed has no items yet. For Facebook, Instagram or TikTok, use an rss.app feed link.")
    return back(bot_call(act()), "/admin/notifications")

@bp.route("/admin/notifications/remove", methods=["POST"])
@guard
def notif_remove():
    name = request.form.get("name", "")

    async def act():
        state = await B.get_notifier_state()
        match = next((f for f in state["feeds"] if f["name"] == name), None)
        if not match:
            return (False, "Feed not found.")
        state["feeds"].remove(match)
        state["seen"].pop(name, None)
        await B.save_notifier_state()
        return (True, f"Removed {name}.")
    return back(bot_call(act()), "/admin/notifications")

@bp.route("/admin/notifications/test", methods=["POST"])
@guard
def notif_test():
    name = request.form.get("name", "")

    async def act():
        state = await B.get_notifier_state()
        match = next((f for f in state["feeds"] if f["name"] == name), None)
        if not match:
            return (False, "Feed not found.")
        try:
            items = await asyncio.to_thread(B.fetch_items, match)
        except Exception as e:
            return (False, f"Fetch failed: {e}")
        if not items:
            return (False, "The feed returned no items.")
        if await B.send_notification(match, items[0], test=True):
            return (True, f"Test notification for {name} sent.")
        return (False, "Couldn't send. Check the channel and the bot's permissions.")
    return back(bot_call(act()), "/admin/notifications")

@bp.route("/admin/notifications/channel", methods=["POST"])
@guard
def notif_channel():
    scope, cid = request.form.get("scope", ""), _int("channel")

    async def act():
        state = await B.get_notifier_state()
        if scope in ("default", "all"):
            if not await _valid_channel(cid):
                return (False, "Pick a valid channel.")
            state["channel_id"] = cid
            if scope == "all":
                for f in state["feeds"]:
                    f.pop("channel_id", None)
            await B.save_notifier_state()
            return (True, "Default channel updated" + (" and every feed moved to it." if scope == "all" else "."))
        match = next((f for f in state["feeds"] if f["name"] == scope), None)
        if not match:
            return (False, "Feed not found.")
        if cid:
            if not await _valid_channel(cid):
                return (False, "That channel isn't visible to the bot.")
            match["channel_id"] = cid
        else:
            match.pop("channel_id", None)
        await B.save_notifier_state()
        return (True, f"Channel updated for {scope}.")
    return back(bot_call(act()), "/admin/notifications")

@bp.route("/admin/notifications/check", methods=["POST"])
@guard
def notif_check():
    async def act():
        sent = await B.check_all_feeds()
        return (True, f"Checked every feed. {sent} new notification(s) sent.")
    return back(bot_call(act()), "/admin/notifications")
