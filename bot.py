import discord
from discord.ext import commands
import os
import io
import re
import json
import base64
import asyncio
import itertools
import requests
import gspread
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import AuthorizedSession
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta, timezone

# --- Web Server Setup ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is awake and running!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

# --- Discord Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Discord Channel & Role IDs ---
DRAFT_CHANNEL_ID = 1558478062558122106
ANNOUNCE_CHANNEL_ID = 1557950064679321721
NOTIFY_ROLE_ID = 1558034567766474762
WELCOME_CHANNEL_ID = 1557900784413188107
GENERAL_CHANNEL_ID = 1557900784413188111
ADMIN_ROLE_ID = 1557901221669642253
RECORD_CHANNEL_ID = 1559322818116591666
TICKET_CATEGORY_ID = 1559324491543351307
CLOSE_ADMIN_ROLE_ID = 1558077964477014116

# Optional: Paste the "TDS - Members" Role ID here, or leave as 0 to auto-detect by name
TDS_MEMBERS_ROLE_ID = 1557901221669642253

# --- Merch Product Image URLs ---
CHASING_SUNSET_IMG = "https://drive.google.com/u/0/drive-viewer/AKGpihZcpA7KlE787PdD6nWf9kPkC_3LIQNmZb0aYyy5CcXClBlKoHKJCBBMfJWyRqCPpU6HA7pB_cBKVYvzHrPM8LBvkzRr8VWBIvY=s1600-rw-v1?auditContext=forDisplay"
# Paste a direct image URL for the Chasing Sunsets CD below (e.g., from Postimages or Imgur):
CHASING_SUNSETS_CD_IMG = "https://drive.google.com/u/0/drive-viewer/AKGpihamW56qYpFmyJqKwJx9ZwZS_Z0xE_i2GAksbMsephoLAAgwn98MJNAo3vIVeLG_Fhk9jWCC-9V66zV37RskZzyCWxiSawQ-_A=s1600-rw-v1?auditContext=forDisplay"
PILLARS_CD_IMG = "https://i.scdn.co/image/ab67616d00001e02824b1eee789e616fa731334a"
TDS_TSHIRT_IMG = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQNzZW-GBBsyhfLJcagd8js2KlHj3C2CNU09f-tBICb4XWIvC9TC1DbjfZ3&s=10"

# --- Google Sheets & Google Drive IDs ---
GOOGLE_SHEET_ID = "1b3dngW8flOcbT7WASy7iQv_1TsWRFiVhLYY3LTNsNLI"
DRIVE_MAIN_FOLDER_ID = "1FdR9bUPW-uHkgLrCn0zvf-V-0jfhDKEp"
# Optional: Paste your Google Apps Script Web App URL here, OR put it in Cell B3 of your "Settings" sheet
DRIVE_APPS_SCRIPT_URL = ""

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# --- The Door Stoppers Spotify Playlist Loop (With Live Imitation Timer) ---
TDS_PLAYLIST = itertools.cycle([
    ("Light Me Up", 210),
    ("I'll Be Around", 205),
    ("Whatever", 195),
    ("Pillars", 220),
    ("Circles", 215),
    ("I Don't Need You", 190),
    ("Fight for My Way", 200),
    ("All the Things, All the Crazy Things", 210)
])

def format_mm_ss(seconds):
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins:02d}:{secs:02d}"

def build_progress_bar(elapsed, total, length=9):
    progress = min(1.0, elapsed / total)
    filled = int(round(length * progress))
    empty = length - filled
    return ("━" * filled) + ("─" * empty)

async def spotify_activity_loop():
    await bot.wait_until_ready()
    step = 15  # Updates every 15 seconds to stay within Discord rate limits

    while not bot.is_closed():
        song_title, duration = next(TDS_PLAYLIST)

        for elapsed in range(0, duration + 1, step):
            if bot.is_closed():
                return

            current_str = format_mm_ss(elapsed)
            total_str = format_mm_ss(duration)
            bar = build_progress_bar(elapsed, duration, length=9)

            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name="Spotify",
                state=f"{song_title} • {current_str} {bar} {total_str}"
            )
            await bot.change_presence(status=discord.Status.online, activity=activity)
            await asyncio.sleep(step)


# --- Helper: Fallback Direct Multipart Upload ---
def upload_file_to_drive_direct(authed_session, folder_id, filename, file_bytes, content_type):
    boundary = "===TDS_DRIVE_UPLOAD_BOUNDARY==="
    metadata_bytes = json.dumps({"name": filename, "parents": [folder_id]}).encode("utf-8")
    body = (
        f"--{boundary}\r\n"
        f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
    ).encode("utf-8") + metadata_bytes + (
        f"\r\n--{boundary}\r\n"
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    headers = {"Content-Type": f"multipart/related; boundary={boundary}"}
    res = authed_session.post(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&supportsAllDrives=true",
        data=body,
        headers=headers
    )
    if res.status_code not in (200, 201):
        print(f"Direct Drive File Upload Error ({filename}): {res.text}")


# --- Helper: Sync Order to Google Drive & Google Sheets ---
def sync_order_to_google(
    ph_time,
    ph_date_short,
    buyer_discord_name,
    extracted_name,
    extracted_email,
    extracted_contact,
    extracted_address,
    extracted_courier,
    extracted_payment,
    extracted_item,
    thread_url,
    transcript_text,
    raw_attachments
):
    drive_folder_url = ""

    safe_user = re.sub(r'[\\/*?:"<>|]', '-', buyer_discord_name).strip()
    safe_name = re.sub(r'[\\/*?:"<>|]', '-', extracted_name if extracted_name != "N/A" else "No Name").strip()
    safe_item = re.sub(r'[\\/*?:"<>|]', '-', extracted_item).strip()
    safe_payment = re.sub(r'[\\/*?:"<>|]', '-', extracted_payment).strip()

    subfolder_name = f"{safe_user} - {safe_name} | {safe_item} | {safe_payment} ({ph_date_short})"
    folder_description = (
        f"Buyer: {extracted_name} ({buyer_discord_name})\n"
        f"Item: {extracted_item}\n"
        f"Payment: {extracted_payment}\n"
        f"Discord Thread: {thread_url}"
    )

    creds = Credentials.from_service_account_file("google_credentials.json", scopes=GOOGLE_SCOPES)
    authed_session = AuthorizedSession(creds)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(GOOGLE_SHEET_ID)

    script_url = DRIVE_APPS_SCRIPT_URL.strip()
    if not script_url:
        try:
            settings_sheet = sh.worksheet("Settings")
            cell_b3 = settings_sheet.acell("B3").value
            if cell_b3 and cell_b3.strip().startswith("https://script.google.com"):
                script_url = cell_b3.strip()
        except Exception:
            pass

    html_shortcut = (
        f"<!DOCTYPE html><html><head>"
        f"<meta http-equiv='refresh' content='0; url={thread_url}' />"
        f"</head><body style='font-family:sans-serif;text-align:center;padding-top:50px;'>"
        f"<h2>Redirecting to Discord Record Thread...</h2>"
        f"<p><a href='{thread_url}'>Click here if you are not redirected automatically</a></p>"
        f"</body></html>"
    ).encode("utf-8")

    files_payload = [
        {
            "name": "🔗 Open_Discord_Thread.html",
            "mimeType": "text/html",
            "base64Data": base64.b64encode(html_shortcut).decode("utf-8"),
            "rawBytes": html_shortcut
        },
        {
            "name": "transcript.txt",
            "mimeType": "text/plain",
            "base64Data": base64.b64encode(transcript_text.encode("utf-8")).decode("utf-8"),
            "rawBytes": transcript_text.encode("utf-8")
        }
    ]

    for idx, (att_name, att_bytes, att_type) in enumerate(raw_attachments, start=1):
        files_payload.append({
            "name": f"Receipt_{idx}_{att_name}",
            "mimeType": att_type or "image/png",
            "base64Data": base64.b64encode(att_bytes).decode("utf-8"),
            "rawBytes": att_bytes
        })

    # 1A. UPLOAD VIA GOOGLE APPS SCRIPT BRIDGE
    if script_url:
        try:
            bridge_data = {
                "parentFolderId": DRIVE_MAIN_FOLDER_ID,
                "folderName": subfolder_name,
                "description": folder_description,
                "files": [
                    {
                        "name": f["name"],
                        "mimeType": f["mimeType"],
                        "base64Data": f["base64Data"]
                    }
                    for f in files_payload
                ]
            }
            res = requests.post(
                script_url,
                data=json.dumps(bridge_data),
                headers={"Content-Type": "text/plain;charset=utf-8"},
                timeout=60
            )
            if res.status_code == 200:
                res_json = res.json()
                if res_json.get("status") == "success":
                    drive_folder_url = res_json.get("folderUrl", "")
                else:
                    print(f"Apps Script Error: {res_json.get('message')}")
            else:
                print(f"Apps Script HTTP Error {res.status_code}: {res.text}")
        except Exception as e:
            print(f"Error calling Google Apps Script bridge: {e}")

    # 1B. FALLBACK: Direct Drive API
    if not drive_folder_url and DRIVE_MAIN_FOLDER_ID:
        try:
            folder_metadata = {
                "name": subfolder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [DRIVE_MAIN_FOLDER_ID],
                "description": folder_description
            }
            folder_res = authed_session.post(
                "https://www.googleapis.com/drive/v3/files?fields=id,webViewLink&supportsAllDrives=true",
                json=folder_metadata
            )
            if folder_res.status_code in (200, 201):
                folder_data = folder_res.json()
                subfolder_id = folder_data.get("id")
                drive_folder_url = folder_data.get(
                    "webViewLink",
                    f"https://drive.google.com/drive/folders/{subfolder_id}"
                )
                for f in files_payload:
                    upload_file_to_drive_direct(
                        authed_session,
                        subfolder_id,
                        f["name"],
                        f["rawBytes"],
                        f["mimeType"]
                    )
            else:
                print(f"Drive Folder Creation Error: {folder_res.text}")
        except Exception as e:
            print(f"Error uploading to Google Drive: {e}")

    # 2. APPEND ORDER & CLICKABLE LINKS TO GOOGLE SHEETS
    try:
        worksheet = sh.sheet1

        thread_hyperlink = f'=HYPERLINK("{thread_url}", "💬 Open Thread")' if thread_url else "N/A"
        drive_hyperlink = f'=HYPERLINK("{drive_folder_url}", "📁 View Receipts")' if drive_folder_url else "Drive Error"

        row_data = [
            ph_time,                                            # Column A: Date
            buyer_discord_name,                                 # Column B: Discord User
            extracted_name,                                     # Column C: Full Name
            extracted_email,                                    # Column D: Email
            extracted_contact,                                  # Column E: Contact Number
            extracted_address,                                  # Column F: Address
            extracted_courier,                                  # Column G: Courier
            extracted_payment,                                  # Column H: Payment Mode
            extracted_item,                                     # Column I: Item Ordered
            "Discord Order (Discord Member Discount Applied)",  # Column J: Source/Notes
            thread_hyperlink,                                   # Column K: Discord Thread Link
            drive_hyperlink                                     # Column L: Google Drive Folder Link
        ]

        worksheet.append_row(row_data, value_input_option="USER_ENTERED")
        worksheet.format("A:L", {"horizontalAlignment": "CENTER"})
    except Exception as e:
        print(f"Error syncing to Google Sheets: {e}")

    return drive_folder_url


# --- Helper: Find the "TDS - Members" Role ---
def get_tds_members_role(guild):
    if TDS_MEMBERS_ROLE_ID:
        role = guild.get_role(TDS_MEMBERS_ROLE_ID)
        if role:
            return role
    return discord.utils.find(
        lambda r: r.name.lower().strip() in ("tds - members", "tds members", "tds - member"),
        guild.roles
    )


# --- Sticky Message Helper for #ticket-records ---
sticky_lock = asyncio.Lock()

async def update_sticky_message(channel):
    if not channel:
        return
    async with sticky_lock:
        sticky_text = (
            "# RECORDS BACK-UP\n"
            f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/edit?usp=sharing"
        )
        try:
            recent_msgs = [m async for m in channel.history(limit=15)]

            if recent_msgs and recent_msgs[0].author == bot.user and recent_msgs[0].content.startswith("# RECORDS BACK-UP"):
                return

            for msg in recent_msgs:
                if msg.author == bot.user and msg.content.startswith("# RECORDS BACK-UP"):
                    try:
                        await msg.delete()
                    except Exception:
                        pass

            await channel.send(content=sticky_text, silent=True)
        except Exception as e:
            print(f"Sticky Message Error: {e}")


# --- Archiving, Google Drive & Google Sheets Function ---
async def archive_and_close_ticket(interaction, channel, user_cancelled=False):
    await interaction.response.send_message(
        "Archiving receipts to Google Drive, syncing to Google Sheets, and closing ticket... please wait.",
        ephemeral=True
    )

    messages = [m async for m in channel.history(limit=None, oldest_first=True)]

    transcript = ""

    extracted_name = "N/A"
    extracted_email = "N/A"
    extracted_contact = "N/A"
    extracted_address = "N/A"
    extracted_courier = "N/A"
    extracted_payment = "N/A"
    extracted_item = "N/A"

    raw_attachments = []

    for msg in messages:
        time_str = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        transcript += f"[{time_str}] {msg.author.name}: {msg.clean_content}\n"

        if msg.author.bot and "You selected: **" in msg.clean_content:
            match = re.search(r'You selected: \*\*(.*?)\*\*', msg.clean_content)
            if match:
                extracted_item = match.group(1)

        if msg.author.bot:
            for emb in msg.embeds:
                if emb.footer and emb.footer.text and emb.footer.text.startswith(ORDER_MARKER):
                    extracted_item = emb.footer.text[len(ORDER_MARKER):].strip() or extracted_item

        if not msg.author.bot:
            for line in msg.clean_content.split('\n'):
                line_lower = line.strip().lower()
                if line_lower.startswith("name:"):
                    extracted_name = line.split(":", 1)[1].strip() or "N/A"
                elif line_lower.startswith("email:"):
                    extracted_email = line.split(":", 1)[1].strip() or "N/A"
                elif line_lower.startswith("contact number:"):
                    extracted_contact = line.split(":", 1)[1].strip() or "N/A"
                elif line_lower.startswith("complete delivery address:"):
                    extracted_address = line.split(":", 1)[1].strip() or "N/A"
                elif line_lower.startswith("preferred courier:"):
                    extracted_courier = line.split(":", 1)[1].strip() or "N/A"
                elif line_lower.startswith("mode of payment:"):
                    extracted_payment = line.split(":", 1)[1].strip() or "N/A"

        for attachment in msg.attachments:
            transcript += f" [Attachment logged: {attachment.filename}]\n"
            try:
                file_bytes = await attachment.read()
                clean_fname = f"{msg.author.name}_{attachment.filename}"
                raw_attachments.append((clean_fname, file_bytes, attachment.content_type))
            except Exception:
                pass

    buyer_discord_name = channel.name.replace("order-", "")
    now_ph = datetime.now(timezone(timedelta(hours=8)))
    ph_time = now_ph.strftime("%Y-%m-%d %H:%M:%S")
    ph_date_short = now_ph.strftime("%Y-%m-%d")

    if user_cancelled:
        thread_name = f"{buyer_discord_name} (Cancelled)"
    else:
        display_buyer = extracted_name if extracted_name != "N/A" else "No Name"
        thread_name = f"{buyer_discord_name} - {display_buyer} ({extracted_item})"

    # 1. CREATE DISCORD RECORD THREAD FIRST
    record_channel = interaction.guild.get_channel(RECORD_CHANNEL_ID)
    thread = None
    thread_url = ""

    if record_channel:
        thread = await record_channel.create_thread(
            name=thread_name[:100],
            type=discord.ChannelType.public_thread
        )
        thread_url = f"https://discord.com/channels/{interaction.guild.id}/{thread.id}"

    full_transcript = (
        f"=== THE DOOR STOPPERS MERCH ORDER LOG ===\n"
        f"Date: {ph_time}\n"
        f"Discord User: {buyer_discord_name}\n"
        f"Buyer Name: {extracted_name}\n"
        f"Item Ordered: {extracted_item}\n"
        f"Payment Mode: {extracted_payment}\n"
        f"Discord Thread Link: {thread_url}\n"
        f"=========================================\n\n"
        + transcript
    )

    # 2. SYNC TO GOOGLE DRIVE & GOOGLE SHEETS
    drive_folder_url = ""
    if not user_cancelled:
        drive_folder_url = await asyncio.to_thread(
            sync_order_to_google,
            ph_time,
            ph_date_short,
            buyer_discord_name,
            extracted_name,
            extracted_email,
            extracted_contact,
            extracted_address,
            extracted_courier,
            extracted_payment,
            extracted_item,
            thread_url,
            full_transcript,
            raw_attachments
        )

    # 3. SEND FILES & GOOGLE DRIVE BUTTON TO DISCORD RECORD THREAD
    if thread:
        transcript_file = discord.File(io.BytesIO(full_transcript.encode('utf-8')), filename="transcript.txt")
        log_summary = (
            f"**Ticket log for {buyer_discord_name}** (`{extracted_name}`)\n"
            f"• **Item:** {extracted_item}\n"
            f"• **Payment:** {extracted_payment}\n"
            f"• **Receipts Saved:** {len(raw_attachments)} file(s)"
        )

        drive_view = None
        if drive_folder_url:
            drive_view = discord.ui.View()
            drive_view.add_item(
                discord.ui.Button(
                    label="📁 Open Google Drive Receipt Folder",
                    style=discord.ButtonStyle.link,
                    url=drive_folder_url
                )
            )

        await thread.send(content=log_summary, file=transcript_file, view=drive_view)

        discord_files = [
            discord.File(io.BytesIO(f_bytes), filename=f_name)
            for f_name, f_bytes, _ in raw_attachments
        ]
        chunk_size = 10
        for i in range(0, len(discord_files), chunk_size):
            await thread.send(files=discord_files[i:i+chunk_size])

    if record_channel:
        await update_sticky_message(record_channel)

    # 4. DELETE THE TICKET CHANNEL
    await channel.delete()


# =====================================================================
# --- Config store (Google Sheet tab "BotConfig") ---
# Everything edited on the web dashboard (merch panel, auto replies,
# stickies) is saved here so it survives restarts and redeploys.
# =====================================================================
import copy
import sys
import time

CONFIG_TAB = "BotConfig"
CONFIG_LOCAL_FILE = "bot_config.json"
CONFIG_CHUNK = 45000          # Google Sheets cells hold max 50,000 characters
CONFIG_MAX_CHUNKS = 12
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ORDER_MARKER = "Order item: "  # hidden-in-plain-sight footer used to detect the chosen item when archiving
STICKY_MARK_TEXT = "-# 📌 Sticky"
STICKY_MARK_EMBED = "📌 Sticky"
STICKY_DELAY_SECONDS = 2.5

try:
    ASSET_CHANNEL_ID = int(os.getenv("ASSET_CHANNEL_ID", "0") or 0)  # private channel used to host images uploaded on the dashboard
except ValueError:
    ASSET_CHANNEL_ID = 0

DEFAULT_CONFIG = {
    "merch": {
        "panel": {
            "title": "🎸 Grab Your Official The Door Stoppers Merch! 🚪",
            "description": (
                "🌅 **NEW PRE-ORDERS (Discord Exclusive Discounts):**\n"
                "• **Chasing Sunset Tee** — **Php 100 OFF** exclusively on Discord!\n"
                "• **Chasing Sunsets Album CD** — **Php 350** *(~~Php 400~~ regular — Php 50 OFF)*!\n\n"
                "Our physical **Pillars EP CDs** and official band tees are also available.\n\n"
                "Click the **Order Now** button below to open a private ticket with the band and secure your merch!"
            ),
            "color": "#FFFF00", "image": "", "thumbnail": "", "footer": "",
            "button_label": "🛒 Order Now", "button_style": "primary",
        },
        "panel_message": {"channel_id": 0, "message_id": 0},
        "ticket": {
            "title": "Merch Order Ticket",
            "description": (
                "Welcome {user}!\n\n"
                "🌅 **PRE-ORDERS OPEN (Discord Exclusive Discounts):**\n"
                "• **Chasing Sunset Tee** — **Php 100 OFF**\n"
                "• **Chasing Sunsets CD** — **Php 350** *(~~Php 400~~ — Php 50 OFF)*\n\n"
                "What would you like to buy? Please select an option below:"
            ),
            "color": "#FFFF00", "image": "", "thumbnail": "",
        },
        "products": [
            {"id": "chasing_sunset", "legacy_id": "sel_chasing_sunset", "label": "🌅 Chasing Sunset Tee (Pre-Order)", "style": "success",
             "name": "Chasing Sunset Tee (Pre-Order)", "price": "500", "image": CHASING_SUNSET_IMG, "thumbnail": "",
             "note": "🔥 *Includes your **Php 100 OFF** Discord exclusive pre-order discount!*"},
            {"id": "chasing_sunsets_cd", "legacy_id": "sel_chasing_sunsets_cd", "label": "💿 Chasing Sunsets CD (Pre-Order)", "style": "success",
             "name": "Chasing Sunsets CD (Pre-Order)", "price": "350", "image": CHASING_SUNSETS_CD_IMG, "thumbnail": "",
             "note": "🔥 *Regular price: ~~Php 400~~ — Includes your **Php 50 OFF** Discord exclusive pre-order discount!*"},
            {"id": "tshirt", "legacy_id": "sel_tshirt", "label": "T-Shirt Only", "style": "primary",
             "name": "T-Shirt Only", "price": "500", "image": TDS_TSHIRT_IMG, "thumbnail": "", "note": ""},
            {"id": "pillars_cd", "legacy_id": "sel_cd", "label": "Pillars EP CD Only", "style": "primary",
             "name": "Pillars EP CD Only", "price": "300", "image": PILLARS_CD_IMG, "thumbnail": "", "note": ""},
            {"id": "both", "legacy_id": "sel_both", "label": "Pillars EP CD & T-Shirt", "style": "primary",
             "name": "Pillars EP CD & T-Shirt", "price": "800", "image": TDS_TSHIRT_IMG, "thumbnail": PILLARS_CD_IMG, "note": ""},
        ],
        "reply": {
            "message": ("You selected: **{product}**\n"
                        "Since you are a Discord member, the price is **Php {price} + shipping fee**.{note}\n\n"
                        "Would you like to proceed?"),
            "embed_title": "🛒 {product}",
            "embed_description": "**Discord Member Price:** Php {price} + shipping fee{note}",
            "color": "#FFFF00",
            "yes_label": "Yes, Proceed", "no_label": "No, Cancel",
        },
        "form": {
            "text": (
                "**Awesome! Please fill out the form below by copying and pasting it into your chat:**\n\n"
                "Name:\nEmail:\nContact Number:\nComplete Delivery Address:\n"
                "Preferred courier: Lalamove/J&T/LBC\nMode of Payment: GCash/Maya\n\n"
                "📸 *Once an admin sends the payment QR, please upload a **screenshot of your payment receipt** "
                "directly in this chat so we can verify and archive your order!*"
            ),
        },
        # when: ticket_open | after_select | after_proceed | after_receipt
        "close": {"when": "after_proceed", "label": "🔒 Close & Archive Ticket",
                  "message": "Staff: press the button below once this order is complete."},
    },
    "stickies": [],
}

BOT_CONFIG = None


def _merge_defaults(base, loaded):
    for k, v in loaded.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge_defaults(base[k], v)
        else:
            base[k] = v
    return base

def _config_ws():
    gc = gspread.service_account(filename="google_credentials.json")
    sh = gc.open_by_key(GOOGLE_SHEET_ID)
    try:
        return sh.worksheet(CONFIG_TAB)
    except gspread.WorksheetNotFound:
        return sh.add_worksheet(title=CONFIG_TAB, rows=5, cols=CONFIG_MAX_CHUNKS + 1)

def load_config_sync():
    try:
        row = _config_ws().row_values(1)
        if row and row[0] == "config":
            raw = "".join(row[1:])
            if raw:
                return json.loads(raw)
    except Exception as e:
        print(f"Config: could not read from Google Sheets ({e}); trying local file")
    try:
        with open(CONFIG_LOCAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_config_sync(raw):
    try:
        with open(CONFIG_LOCAL_FILE, "w", encoding="utf-8") as f:
            f.write(raw)
    except Exception as e:
        print(f"Config: local save failed: {e}")
    chunks = [raw[i:i + CONFIG_CHUNK] for i in range(0, len(raw), CONFIG_CHUNK)]
    if len(chunks) > CONFIG_MAX_CHUNKS:
        raise ValueError("Config is too large to store in Google Sheets.")
    row = ["config"] + chunks + [""] * (CONFIG_MAX_CHUNKS - len(chunks))
    _config_ws().update(range_name="A1", values=[row])

async def get_config():
    global BOT_CONFIG
    if BOT_CONFIG is None:
        loaded = await asyncio.to_thread(load_config_sync)
        BOT_CONFIG = _merge_defaults(copy.deepcopy(DEFAULT_CONFIG), loaded or {})
    return BOT_CONFIG

async def save_config():
    raw = json.dumps(BOT_CONFIG)
    await asyncio.to_thread(save_config_sync, raw)


# =====================================================================
# --- Merch panel & ticket flow (fully driven by the config above) ---
# Buttons are handled in on_interaction, so edits apply instantly and
# older panel messages keep working (legacy button IDs are mapped).
# =====================================================================
STYLE_MAP = {
    "primary": discord.ButtonStyle.primary,
    "success": discord.ButtonStyle.success,
    "danger": discord.ButtonStyle.danger,
    "secondary": discord.ButtonStyle.secondary,
}
LEGACY_BUTTON_IDS = {
    "open_ticket_button": "tds:order",
    "proceed_yes": "tds:yes",
    "proceed_no": "tds:no",
    "close_ticket_button": "tds:close",
}
CLOSE_POSTED = set()
_asset_cache = {}


def parse_color(value, default=0xFFFF00):
    if isinstance(value, int):
        return value
    m = re.fullmatch(r"#?([0-9a-fA-F]{6})", str(value or "").strip())
    return int(m.group(1), 16) if m else default

def render_tpl(text, **kw):
    out = text or ""
    for k, v in kw.items():
        out = out.replace("{" + k + "}", str(v))
    return out

async def resolve_image(ref):
    """Image fields hold either a normal URL or an 'asset:<channel>:<message>:<n>' reference to an uploaded file."""
    ref = (ref or "").strip()
    if not ref.startswith("asset:"):
        return ref if ref.startswith("http") else ""
    cached = _asset_cache.get(ref)
    if cached and time.time() - cached[1] < 1200:
        return cached[0]
    try:
        _, cid, mid, idx = ref.split(":")
        ch = await _resolve_channel(int(cid))
        msg = await ch.fetch_message(int(mid))
        url = msg.attachments[int(idx)].url
        _asset_cache[ref] = (url, time.time())
        return url
    except Exception as e:
        print(f"Asset resolve failed for {ref}: {e}")
        return ""

async def build_embed(title, description, color, image="", thumbnail="", footer=""):
    title = (title or "").strip()[:256]
    description = (description or "").strip()[:4000]
    img = await resolve_image(image)
    thumb = await resolve_image(thumbnail)
    if not title and not description and not img:
        description = "​"
    e = discord.Embed(title=title or None, description=description or None, color=parse_color(color))
    if img:
        e.set_image(url=img)
    if thumb:
        e.set_thumbnail(url=thumb)
    if footer:
        e.set_footer(text=footer[:2000])
    return e

def _button(label, custom_id, style="primary", disabled=False):
    return discord.ui.Button(label=(label or "Button")[:80], custom_id=custom_id,
                             style=STYLE_MAP.get(style, discord.ButtonStyle.primary), disabled=disabled)

def _view(*buttons):
    v = discord.ui.View(timeout=None)
    for b in buttons:
        v.add_item(b)
    return v

def build_panel_view(cfg):
    p = cfg["merch"]["panel"]
    return _view(_button(p.get("button_label"), "tds:order", p.get("button_style", "primary")))

def build_product_view(cfg):
    return _view(*[_button(p.get("label") or p.get("name"), f"tds:sel:{p['id']}", p.get("style", "primary"))
                   for p in cfg["merch"]["products"][:25]])

def build_confirm_view(cfg, disabled=False):
    r = cfg["merch"]["reply"]
    return _view(_button(r.get("yes_label", "Yes, Proceed"), "tds:yes", "success", disabled),
                 _button(r.get("no_label", "No, Cancel"), "tds:no", "danger", disabled))

def build_close_view(cfg):
    return _view(_button(cfg["merch"]["close"].get("label", "🔒 Close & Archive Ticket"), "tds:close", "danger"))

async def build_panel_embed(cfg):
    p = cfg["merch"]["panel"]
    return await build_embed(p["title"], p["description"], p["color"], p.get("image"), p.get("thumbnail"), p.get("footer"))

async def post_panel(channel):
    cfg = await get_config()
    msg = await channel.send(embed=await build_panel_embed(cfg), view=build_panel_view(cfg))
    cfg["merch"]["panel_message"] = {"channel_id": channel.id, "message_id": msg.id}
    await save_config()
    return msg

async def update_panel_message():
    cfg = await get_config()
    pm = cfg["merch"].get("panel_message") or {}
    if not pm.get("message_id"):
        return False, "No panel is being tracked yet. Publish a new one or link an existing panel message."
    ch = await _resolve_channel(int(pm["channel_id"]))
    if not ch:
        return False, "Couldn't find the channel of the tracked panel."
    try:
        msg = await ch.fetch_message(int(pm["message_id"]))
        await msg.edit(embed=await build_panel_embed(cfg), view=build_panel_view(cfg))
    except Exception as e:
        return False, f"Couldn't update the panel message: {e}"
    return True, "Panel updated in Discord."

def find_product(cfg, pid):
    return next((p for p in cfg["merch"]["products"] if p["id"] == pid), None)

async def _reply_ephemeral(interaction, text):
    try:
        if interaction.response.is_done():
            await interaction.followup.send(text, ephemeral=True)
        else:
            await interaction.response.send_message(text, ephemeral=True)
    except Exception as e:
        print(f"Interaction reply failed: {e}")

async def _has_close_button(channel):
    async for m in channel.history(limit=40):
        if m.author.id == bot.user.id:
            for row in m.components:
                for child in getattr(row, "children", []):
                    if getattr(child, "custom_id", None) in ("tds:close", "close_ticket_button"):
                        return True
    return False

async def post_close_button(channel, cfg):
    if channel.id in CLOSE_POSTED:
        return
    CLOSE_POSTED.add(channel.id)
    try:
        if await _has_close_button(channel):
            return
        await channel.send(cfg["merch"]["close"].get("message") or "​", view=build_close_view(cfg))
    except Exception as e:
        CLOSE_POSTED.discard(channel.id)
        print(f"Close button post failed: {e}")


async def handle_order(interaction):
    cfg = await get_config()
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    category = guild.get_channel(TICKET_CATEGORY_ID)
    tds_members_role = get_tds_members_role(guild)
    admin_role = guild.get_role(ADMIN_ROLE_ID)
    close_admin_role = guild.get_role(CLOSE_ADMIN_ROLE_ID)

    perms = dict(read_messages=True, send_messages=True, attach_files=True)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(**perms),
        guild.me: discord.PermissionOverwrite(**perms),
    }
    for role in (admin_role, close_admin_role, tds_members_role):
        if role:
            overwrites[role] = discord.PermissionOverwrite(**perms)

    ticket_channel = await guild.create_text_channel(
        name=f"order-{interaction.user.name}", category=category, overwrites=overwrites)

    t = cfg["merch"]["ticket"]
    embed = await build_embed(t["title"], render_tpl(t["description"], user=interaction.user.mention),
                              t["color"], t.get("image"), t.get("thumbnail"))
    ping_list = [f"<@&{ADMIN_ROLE_ID}>"]
    if tds_members_role and tds_members_role.id != ADMIN_ROLE_ID:
        ping_list.append(tds_members_role.mention)
    ping_text = f"🔔 {' '.join(ping_list)} — **New Merch Order Ticket opened by {interaction.user.mention}!**"

    await ticket_channel.send(content=ping_text, embed=embed, view=build_product_view(cfg),
                              allowed_mentions=discord.AllowedMentions(roles=True, users=True))
    await interaction.followup.send(f"Your ticket has been created: {ticket_channel.mention}", ephemeral=True)
    if cfg["merch"]["close"].get("when") == "ticket_open":
        await post_close_button(ticket_channel, cfg)

async def handle_select(interaction, pid):
    cfg = await get_config()
    p = find_product(cfg, pid)
    if not p:
        await _reply_ephemeral(interaction, "That item isn't available anymore. Please pick another one.")
        return
    r = cfg["merch"]["reply"]
    note = f"\n{p['note']}" if p.get("note") else ""
    v = dict(product=p["name"], price=p["price"], note=note, user=interaction.user.mention)
    embed = await build_embed(render_tpl(r["embed_title"], **v), render_tpl(r["embed_description"], **v),
                              r["color"], p.get("image"), p.get("thumbnail"), footer=f"{ORDER_MARKER}{p['name']}")
    await interaction.response.edit_message(content=render_tpl(r["message"], **v)[:2000], embed=embed,
                                            view=build_confirm_view(cfg))
    if cfg["merch"]["close"].get("when") == "after_select":
        await post_close_button(interaction.channel, cfg)

async def handle_yes(interaction):
    cfg = await get_config()
    await interaction.response.edit_message(view=build_confirm_view(cfg, disabled=True))
    close = cfg["merch"]["close"]
    view = build_close_view(cfg) if close.get("when", "after_proceed") == "after_proceed" else None
    if view:
        CLOSE_POSTED.add(interaction.channel.id)
    await interaction.channel.send(cfg["merch"]["form"]["text"][:2000], view=view)

async def handle_close(interaction):
    tds_role = get_tds_members_role(interaction.guild)
    user_role_ids = [role.id for role in interaction.user.roles]
    allowed = (
        CLOSE_ADMIN_ROLE_ID in user_role_ids or ADMIN_ROLE_ID in user_role_ids
        or (tds_role and tds_role.id in user_role_ids)
        or interaction.user.guild_permissions.administrator
    )
    if allowed:
        await archive_and_close_ticket(interaction, interaction.channel, user_cancelled=False)
    else:
        await _reply_ephemeral(interaction, "Only admins or TDS - Members can close this ticket.")

@bot.event
async def on_interaction(interaction):
    if interaction.type != discord.InteractionType.component:
        return
    original = (interaction.data or {}).get("custom_id", "")
    cid = LEGACY_BUTTON_IDS.get(original, original)
    try:
        cfg = await get_config()
        if original.startswith("sel_"):  # buttons from panels posted before the dashboard existed
            match = next((p for p in cfg["merch"]["products"] if p.get("legacy_id") == original), None)
            cid = f"tds:sel:{match['id']}" if match else ""
        if not cid.startswith("tds:"):
            return
        if cid == "tds:order":
            await handle_order(interaction)
        elif cid.startswith("tds:sel:"):
            await handle_select(interaction, cid[len("tds:sel:"):])
        elif cid == "tds:yes":
            await handle_yes(interaction)
        elif cid == "tds:no":
            await archive_and_close_ticket(interaction, interaction.channel, user_cancelled=True)
        elif cid == "tds:close":
            await handle_close(interaction)
    except Exception as e:
        print(f"Interaction error ({original}): {e}")
        await _reply_ephemeral(interaction, "Something went wrong. Please try again or ping an admin.")


# =====================================================================
# --- Sticky messages (silent, per channel) ---
# After anyone posts in a sticky channel, the bot re-posts its sticky
# at the bottom without notifications and deletes the old copy.
# =====================================================================
STICKY_CHANNELS = set()
_sticky_state = {}
_sticky_locks = {}

def rebuild_sticky_index(cfg):
    STICKY_CHANNELS.clear()
    for s in cfg.get("stickies", []):
        if s.get("enabled", True) and str(s.get("channel_id", "")).isdigit():
            STICKY_CHANNELS.add(int(s["channel_id"]))

def _is_sticky_message(m):
    if m.author.id != bot.user.id:
        return False
    if (m.content or "").rstrip().endswith(STICKY_MARK_TEXT):
        return True
    return any(e.footer and e.footer.text == STICKY_MARK_EMBED for e in m.embeds)

async def refresh_sticky(channel_id, force=False):
    cfg = await get_config()
    s = next((x for x in cfg["stickies"] if x.get("enabled", True) and int(x["channel_id"]) == channel_id), None)
    if not s:
        return
    channel = await _resolve_channel(channel_id)
    if not channel:
        return
    lock = _sticky_locks.setdefault(channel_id, asyncio.Lock())
    async with lock:
        recent = [m async for m in channel.history(limit=25)]
        if not force and recent and _is_sticky_message(recent[0]):
            return
        for m in recent:
            if _is_sticky_message(m):
                try:
                    await m.delete()
                except Exception:
                    pass
        if s.get("mode") == "embed":
            embed = await build_embed(s.get("title"), s.get("content"), s.get("color", "#FFFF00"),
                                      s.get("image"), "", footer=STICKY_MARK_EMBED)
            await channel.send(embed=embed, silent=True)
        else:
            await channel.send(content=f"{(s.get('content') or '')[:1900]}\n{STICKY_MARK_TEXT}", silent=True)

async def remove_sticky_messages(channel_id):
    channel = await _resolve_channel(channel_id)
    if not channel:
        return
    async for m in channel.history(limit=50):
        if _is_sticky_message(m):
            try:
                await m.delete()
            except Exception:
                pass

async def _sticky_worker(channel_id, st):
    try:
        while st["dirty"]:
            st["dirty"] = False
            await asyncio.sleep(STICKY_DELAY_SECONDS)
            if st["dirty"]:
                continue  # more messages arrived while waiting; wait again
            await refresh_sticky(channel_id)
    except Exception as e:
        print(f"Sticky error in {channel_id}: {e}")
    finally:
        st["running"] = False

def schedule_sticky(channel_id):
    st = _sticky_state.setdefault(channel_id, {"running": False, "dirty": False})
    st["dirty"] = True
    if not st["running"]:
        st["running"] = True
        asyncio.create_task(_sticky_worker(channel_id, st))


@bot.event
async def on_ready():
    cfg = await get_config()
    rebuild_sticky_index(cfg)
    for sticky in cfg["stickies"]:
        if sticky.get("enabled", True):
            schedule_sticky(int(sticky["channel_id"]))

    if not hasattr(bot, "spotify_loop_started"):
        bot.spotify_loop_started = True
        bot.loop.create_task(spotify_activity_loop())

    if not hasattr(bot, "notifier_loop_started"):
        bot.notifier_loop_started = True
        bot.loop.create_task(notifier_loop())

    record_channel = bot.get_channel(RECORD_CHANNEL_ID)
    if record_channel:
        await update_sticky_message(record_channel)

    print(f'Logged in successfully as {bot.user.name}!')


# --- Command to spawn the Merch Panel (content is edited on the web dashboard) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def merchpanel(ctx):
    await post_panel(ctx.channel)
    try:
        await ctx.message.delete()
    except Exception:
        pass


# --- Automated Announcement System ---
class ConfirmView(discord.ui.View):
    def __init__(self, draft_message, announce_channel):
        super().__init__(timeout=None)
        self.draft_message = draft_message
        self.announce_channel = announce_channel

    @discord.ui.button(label="Yes, send it!", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Only admins can confirm announcements.", ephemeral=True)
            return

        await interaction.response.defer()

        embed = discord.Embed(color=0xFFFF00)
        embed.set_author(
            name=self.draft_message.author.display_name,
            icon_url=self.draft_message.author.display_avatar.url
        )

        url_match = None
        if self.draft_message.content:
            url_match = re.search(r'(https?://\S+)', self.draft_message.content)
            embed.description = self.draft_message.content

        files_to_send = []
        image_filenames = []

        for idx, attachment in enumerate(self.draft_message.attachments):
            try:
                file_bytes = await attachment.read()
                safe_fname = re.sub(r'[^a-zA-Z0-9._-]', '_', attachment.filename)
                unique_fname = f"{idx + 1}_{safe_fname}"

                files_to_send.append(discord.File(io.BytesIO(file_bytes), filename=unique_fname))
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    image_filenames.append(unique_fname)
            except Exception as e:
                print(f"Error reading announcement attachment {attachment.filename}: {e}")

        # Single image goes inside the embed; multiple images display as Discord's native photo grid below the embed
        if len(files_to_send) == 1 and len(image_filenames) == 1:
            embed.set_image(url=f"attachment://{image_filenames[0]}")

        notify_text = f"<@&{NOTIFY_ROLE_ID}>\n**ANNOUNCEMENT!**"

        link_view = discord.ui.View()
        has_buttons = False

        if url_match:
            extracted_url = url_match.group(1)
            link_view.add_item(discord.ui.Button(label="View Post", style=discord.ButtonStyle.link, url=extracted_url))
            has_buttons = True

        view_to_pass = link_view if has_buttons else None

        if files_to_send:
            await self.announce_channel.send(
                content=notify_text,
                embed=embed,
                view=view_to_pass,
                files=files_to_send[:10]
            )
        else:
            await self.announce_channel.send(
                content=notify_text,
                embed=embed,
                view=view_to_pass
            )

        for child in self.children:
            child.disabled = True
        await interaction.edit_original_response(content="✅ **Announcement sent!**", view=self)

    @discord.ui.button(label="No, cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Only admins can cancel announcements.", ephemeral=True)
            return

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="❌ **Announcement cancelled.**", view=self)


@bot.event
async def on_message(message):
    if message.guild and message.author.id != bot.user.id and message.channel.id in STICKY_CHANNELS:
        schedule_sticky(message.channel.id)

    if message.author.bot:
        return

    if message.channel.id == DRAFT_CHANNEL_ID:
        if message.author.guild_permissions.administrator:
            announce_channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)
            view = ConfirmView(message, announce_channel)
            await message.channel.send("Do you want to send this as an official announcement?", view=view)

    if message.channel.id == RECORD_CHANNEL_ID:
        await update_sticky_message(message.channel)

    if message.attachments and getattr(message.channel, "category_id", None) == TICKET_CATEGORY_ID:
        cfg = await get_config()
        if cfg["merch"]["close"].get("when") == "after_receipt":
            await post_close_button(message.channel, cfg)

    await bot.process_commands(message)


# --- Welcome Message System ---
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if not channel:
        return

    def get_ordinal(n):
        if 11 <= (n % 100) <= 13:
            return f"{n}th"
        return f"{n}" + {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')

    member_count = get_ordinal(member.guild.member_count)
    ph_time = datetime.now(timezone(timedelta(hours=8))).strftime("%m/%d/%Y %I:%M %p")

    embed = discord.Embed(
        description="**Welcome to the world of doors!**\nPlease follow our [socials](https://www.submithub.com/link/thedoorstoppers)! Enjoy your stay.",
        color=0xFFFFFF
    )

    embed.set_author(name=member.name, icon_url=member.display_avatar.url)
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text=f"You are our {member_count} doorling! | {ph_time}")

    await channel.send(embed=embed)


# --- Server Boost Tracker ---
@bot.event
async def on_member_update(before, after):
    if before.premium_since is None and after.premium_since is not None:
        gen_chat = bot.get_channel(GENERAL_CHANNEL_ID)
        if gen_chat:
            embed = discord.Embed(
                title="🚀 NEW SERVER BOOST! 🚀",
                description=(
                    f"Huge thanks to {after.mention} for boosting the server!\n\n"
                    f"Your support helps us keep the music playing and the doors open. We appreciate you! 🎵🚪"
                ),
                color=0xF47FFF
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            await gen_chat.send(embed=embed)


# --- Payment QR Command (Linked to Google Sheets Settings Tab) ---
@bot.command()
async def payment(ctx, option: str = "1"):
    try:
        gc = gspread.service_account(filename='google_credentials.json')
        sh = gc.open_by_key(GOOGLE_SHEET_ID)
        settings_sheet = sh.worksheet("Settings")

        primary_link = settings_sheet.acell('B1').value
        backup_link = settings_sheet.acell('B2').value
    except Exception as e:
        await ctx.send("Error connecting to the Settings tab in Google Sheets. Please make sure the 'Settings' tab exists.")
        print(f"Sheets Error: {e}")
        return

    if option == "2":
        embed = discord.Embed(
            title="Backup Payment Method",
            description="Please use this backup QR code to proceed with your payment. Once paid, please send a screenshot of your receipt here!",
            color=0x000000
        )
        embed.set_image(url=backup_link)
    else:
        embed = discord.Embed(
            title="QRph Payment",
            description="Please scan the QRph code below to proceed with your payment (works for GCash, Maya, and banking apps). Once paid, please send a screenshot of your receipt here!",
            color=0x00529B
        )
        embed.set_image(url=primary_link)

    await ctx.send(embed=embed)


# =====================================================================
# --- Social & Music Release Notifier ---
# Replaces MonitoRSS (Facebook/Instagram) and NotifyMe (TikTok/YouTube),
# and adds Spotify + Apple Music release alerts.
#
# Manage feeds with (admins only):
#   !feed list
#   !feed add youtube   TDS-YT   @thedoorstoppers [#channel]
#   !feed add tiktok    TDS-TT   thedoorstoppers  [#channel]
#   !feed add facebook  TDS-FB   <page-id or full RSS url>
#   !feed add instagram TDS-IG   <username or full RSS url>
#   !feed add rss       Anything <full RSS/Atom url>
#   !feed add spotify   TDS-SP   <artist id or open.spotify.com/artist/... url>
#   !feed add apple     TDS-AM   <artist id or music.apple.com/.../artist/... url>
#   !feed notify <#channel> [name|all]   |   !feed force <name> <#channel>
#   !feed remove <name>   |   !feed test <name>   |   !feed check
# =====================================================================
import hashlib
import html as html_lib
import xml.etree.ElementTree as ET

NOTIFIER_CHANNEL_ID = ANNOUNCE_CHANNEL_ID      # default channel for alerts (per-feed override: add #channel)
NOTIFIER_PING_ROLE_ID = NOTIFY_ROLE_ID         # set to 0 to disable pings
NOTIFIER_INTERVAL_SECONDS = 300                # how often feeds are checked
NOTIFIER_SHEET_TAB = "Notifier"                # tab in your Google Sheet that stores feeds + "already seen" posts
NOTIFIER_LOCAL_FILE = "notifier_state.json"    # local fallback if Sheets is unreachable
MAX_SEEN_PER_FEED = 40
MAX_POSTS_PER_CHECK = 5                        # safety cap so a glitchy feed can't flood the channel

# Facebook / Instagram / TikTok have no official RSS. These are built through RSSHub.
# The public rsshub.app is rate-limited and often blocked for those sites, so for reliability either
# self-host RSSHub (set RSSHUB_BASE) or paste a full feed URL from rss.app / FetchRSS / PolitePol.
RSSHUB_BASE = os.getenv("RSSHUB_BASE", "https://rsshub.app").rstrip("/")

# Spotify needs a free API app: https://developer.spotify.com/dashboard -> set these two env vars
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")

HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; TheDoorStoppersBot/1.0)"}

PLATFORMS = {
    "youtube":   {"label": "YouTube",     "emoji": "▶️", "color": 0xFF0000},
    "tiktok":    {"label": "TikTok",      "emoji": "🎵", "color": 0x25F4EE},
    "facebook":  {"label": "Facebook",    "emoji": "📘", "color": 0x1877F2},
    "instagram": {"label": "Instagram",   "emoji": "📸", "color": 0xE1306C},
    "spotify":   {"label": "Spotify",     "emoji": "🟢", "color": 0x1DB954},
    "apple":     {"label": "Apple Music", "emoji": "🍎", "color": 0xFA243C},
    "rss":       {"label": "Website",     "emoji": "📰", "color": 0x808080},
}

# Seeded on the very first run (only if no saved state exists yet). Existing releases are NOT announced.
DEFAULT_FEEDS = [
    {"name": "TDS-Spotify", "platform": "spotify", "target": "3X4BLDDmGQ8bdiJbbBPMaJ"},
    {"name": "TDS-Apple",   "platform": "apple",   "target": "1591640721"},
]

NOTIFIER_STATE = None  # {"feeds": [...], "seen": {feed_name: [ids]}, "channel_id": optional int}


# ---------- Parsing helpers ----------
def _norm_id(raw):
    raw = (raw or "").strip()
    return raw if len(raw) <= 60 else hashlib.md5(raw.encode("utf-8")).hexdigest()

def _lname(el):
    return el.tag.rsplit("}", 1)[-1]

def _clean_html(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", html_lib.unescape(text)).strip()

def parse_feed(xml_bytes):
    """Parses RSS 2.0 and Atom (incl. YouTube) into a list of dicts, newest first."""
    root = ET.fromstring(xml_bytes)
    items = []
    for e in root.iter():
        if _lname(e) not in ("item", "entry"):
            continue
        title = link = guid = desc = img = ""
        for c in e.iter():
            if c is e:
                continue
            n = _lname(c)
            if n == "title" and not title:
                title = (c.text or "").strip()
            elif n == "link" and not link:
                link = c.get("href") or (c.text or "").strip()
            elif n in ("id", "guid", "videoId") and not guid:
                guid = (c.text or "").strip()
            elif n in ("description", "summary", "content", "encoded") and not desc:
                desc = c.text or ""
            elif n == "thumbnail" and not img:
                img = c.get("url", "")
            elif n == "enclosure" and not img and c.get("type", "").startswith("image"):
                img = c.get("url", "")
        if not img:
            m = re.search(r'<img[^>]+src=["\']([^"\']+)', html_lib.unescape(desc))
            if m:
                img = m.group(1)
        text = _clean_html(desc)
        items.append({
            "id": _norm_id(guid or link or title),
            "title": title or text[:80] or "New post",
            "url": link,
            "desc": text[:300],
            "image": img,
        })
    return items

def fetch_rss(url):
    r = requests.get(url, headers=HTTP_HEADERS, timeout=20)
    r.raise_for_status()
    return parse_feed(r.content)


# ---------- Per-platform fetchers ----------
_spotify_token = {"value": None, "expires": 0.0}

def _get_spotify_token():
    now = datetime.now().timestamp()
    if _spotify_token["value"] and now < _spotify_token["expires"] - 30:
        return _spotify_token["value"]
    if not (SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET):
        raise RuntimeError("SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET env vars are not set")
    r = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        timeout=20,
    )
    r.raise_for_status()
    j = r.json()
    _spotify_token["value"] = j["access_token"]
    _spotify_token["expires"] = now + int(j.get("expires_in", 3600))
    return _spotify_token["value"]

def fetch_spotify(artist_id):
    token = _get_spotify_token()
    r = requests.get(
        f"https://api.spotify.com/v1/artists/{artist_id}/albums",
        params={"include_groups": "album,single", "market": "PH", "limit": 10},
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    if r.status_code != 200:
        # Show Spotify's own explanation (e.g. "Active premium subscription required for the owner of the app")
        raise RuntimeError(f"Spotify HTTP {r.status_code}: {r.text[:300]}")
    albums = sorted(r.json().get("items", []), key=lambda a: a.get("release_date", ""), reverse=True)
    return [{
        "id": a["id"],
        "title": f'{a["name"]} ({a.get("album_type", "release").title()})',
        "url": a.get("external_urls", {}).get("spotify", ""),
        "desc": f'Released {a.get("release_date", "")}',
        "image": a["images"][0]["url"] if a.get("images") else "",
    } for a in albums]

def fetch_apple(artist_id):
    r = requests.get(
        "https://itunes.apple.com/lookup",
        params={"id": artist_id, "entity": "album", "country": "ph", "limit": 25, "sort": "recent"},
        headers=HTTP_HEADERS,
        timeout=20,
    )
    r.raise_for_status()
    albums = [x for x in r.json().get("results", []) if x.get("wrapperType") == "collection"]
    albums.sort(key=lambda a: a.get("releaseDate", ""), reverse=True)
    return [{
        "id": str(a["collectionId"]),
        "title": a.get("collectionName", "New release"),
        "url": a.get("collectionViewUrl", ""),
        "desc": f'Released {a.get("releaseDate", "")[:10]}',
        "image": a.get("artworkUrl100", "").replace("100x100", "600x600"),
    } for a in albums]

def resolve_youtube_channel_id(text):
    t = text.strip()
    if re.fullmatch(r"UC[\w-]{22}", t):
        return t
    m = re.search(r"channel/(UC[\w-]{22})", t) or re.search(r"channel_id=(UC[\w-]{22})", t)
    if m:
        return m.group(1)
    url = t if t.startswith("http") else f"https://www.youtube.com/{t if t.startswith('@') else '@' + t}"
    r = requests.get(url, headers={**HTTP_HEADERS, "Accept-Language": "en-US,en;q=0.9"},
                     cookies={"CONSENT": "YES+1"}, timeout=20)
    m = (re.search(r'rel="canonical" href="https://www\.youtube\.com/channel/(UC[\w-]{22})', r.text)
         or re.search(r'<meta itemprop="channelId" content="(UC[\w-]{22})"', r.text)
         or re.search(r'"channelId":"(UC[\w-]{22})"', r.text)
         or re.search(r'channel_id=(UC[\w-]{22})', r.text))
    if not m:
        raise ValueError("Could not find a YouTube channel ID. Paste the channel ID (starts with UC) instead.")
    return m.group(1)

def _extract_id(text, pattern):
    m = re.search(pattern, text)
    return m.group(1) if m else text.strip()

def build_feed_url(platform, target):
    t = target.strip()
    if t.startswith("http"):
        return t
    if platform == "tiktok":
        return f"{RSSHUB_BASE}/tiktok/user/@{t.lstrip('@')}"
    if platform == "instagram":
        return f"{RSSHUB_BASE}/instagram/user/{t.lstrip('@')}"
    if platform == "facebook":
        return f"{RSSHUB_BASE}/facebook/page/{t}"
    return t

def fetch_tiktok(target):
    """TikTok has no RSS. Accepts a username/profile link (read directly) or an RSS generator URL."""
    t = target.strip()
    if t.startswith("http") and "tiktok.com" not in t:
        return fetch_rss(t)  # feed URL from rss.app etc.
    m = re.search(r"@([\w.]+)", t)
    username = m.group(1) if m else t.lstrip("@")

    errors = []
    # Method 1: public TikTok profile lookup (tikwm.com, unofficial, free, ~1 request/second)
    try:
        import time
        data = None
        for attempt in range(2):
            r = requests.get("https://www.tikwm.com/api/user/posts",
                             params={"unique_id": username, "count": 10},
                             headers=HTTP_HEADERS, timeout=25)
            r.raise_for_status()
            data = r.json()
            if data.get("code") == 0:
                break
            if "limit" in str(data.get("msg", "")).lower() and attempt == 0:
                time.sleep(2)
                continue
            raise RuntimeError(data.get("msg") or "unknown error")
        videos = sorted(data.get("data", {}).get("videos", []), key=lambda v: v.get("create_time", 0), reverse=True)
        return [{
            "id": str(v["video_id"]),
            "title": (v.get("title") or "New TikTok video")[:256],
            "url": f"https://www.tiktok.com/@{username}/video/{v['video_id']}",
            "desc": "",
            "image": v.get("origin_cover") or v.get("cover") or "",
        } for v in videos]
    except Exception as e:
        errors.append(f"tikwm: {e}")

    # Method 2: RSSHub fallback
    try:
        return fetch_rss(f"{RSSHUB_BASE}/tiktok/user/@{username}")
    except Exception as e:
        errors.append(f"rsshub: {e}")
    raise RuntimeError("; ".join(errors))

def fetch_items(feed):
    p, t = feed["platform"], feed["target"]
    if p == "spotify":
        return fetch_spotify(_extract_id(t, r"artist/([A-Za-z0-9]+)"))
    if p == "apple":
        return fetch_apple(_extract_id(t, r"/artist/(?:[^/]+/)?(\d+)"))
    if p == "tiktok":
        return fetch_tiktok(t)
    if p == "youtube":
        return fetch_rss(f"https://www.youtube.com/feeds/videos.xml?channel_id={t}")
    return fetch_rss(build_feed_url(p, t))


# ---------- State storage (Google Sheet tab, with local file fallback) ----------
def _notifier_worksheet():
    gc = gspread.service_account(filename="google_credentials.json")
    sh = gc.open_by_key(GOOGLE_SHEET_ID)
    try:
        return sh.worksheet(NOTIFIER_SHEET_TAB)
    except gspread.WorksheetNotFound:
        return sh.add_worksheet(title=NOTIFIER_SHEET_TAB, rows=10, cols=2)

def load_notifier_state():
    try:
        raw = _notifier_worksheet().acell("A1").value
        if raw:
            return json.loads(raw)
    except Exception as e:
        print(f"Notifier: could not read state from Google Sheets ({e}); trying local file")
    try:
        with open(NOTIFIER_LOCAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        pass
    return {"feeds": [dict(f) for f in DEFAULT_FEEDS], "seen": {}}

def save_notifier_state_raw(raw):
    try:
        with open(NOTIFIER_LOCAL_FILE, "w", encoding="utf-8") as f:
            f.write(raw)
    except Exception as e:
        print(f"Notifier: local save failed: {e}")
    try:
        _notifier_worksheet().update_acell("A1", raw)
    except Exception as e:
        print(f"Notifier: Google Sheets save failed: {e}")

async def get_notifier_state():
    global NOTIFIER_STATE
    if NOTIFIER_STATE is None:
        NOTIFIER_STATE = await asyncio.to_thread(load_notifier_state)
        NOTIFIER_STATE.setdefault("feeds", [])
        NOTIFIER_STATE.setdefault("seen", {})
    return NOTIFIER_STATE

async def save_notifier_state():
    raw = json.dumps(NOTIFIER_STATE)
    await asyncio.to_thread(save_notifier_state_raw, raw)


# ---------- Sending alerts ----------
async def _resolve_channel(channel_id):
    channel = bot.get_channel(channel_id)
    if channel is None and channel_id:
        try:
            channel = await bot.fetch_channel(channel_id)
        except Exception:
            channel = None
    return channel

async def send_notification(feed, item, test=False, channel_override=None):
    if channel_override is not None:
        channel = channel_override
    else:
        state = await get_notifier_state()
        default_channel_id = state.get("channel_id") or NOTIFIER_CHANNEL_ID
        channel = await _resolve_channel(feed.get("channel_id") or default_channel_id)
    if not channel:
        print(f"Notifier: channel for feed '{feed['name']}' not found")
        return False

    meta = PLATFORMS.get(feed["platform"], PLATFORMS["rss"])
    verb = "released something new" if feed["platform"] in ("spotify", "apple") else "just posted"
    ping = f"<@&{NOTIFIER_PING_ROLE_ID}> " if NOTIFIER_PING_ROLE_ID else ""
    headline = f"{ping}{meta['emoji']} **{feed['name']}** {verb} on **{meta['label']}**!"
    if test:
        headline = "🧪 *Test notification*\n" + headline
    allowed = discord.AllowedMentions(roles=True)

    # YouTube: plain link so Discord shows its native playable video preview (like NotifyMe)
    if feed["platform"] == "youtube" and item["url"]:
        await channel.send(content=f"{headline}\n{item['url']}", allowed_mentions=allowed)
        return True

    embed = discord.Embed(
        title=item["title"][:256],
        description=item["desc"][:300] or None,
        color=meta["color"],
        timestamp=datetime.now(timezone.utc),
    )
    if item["url"].startswith("http"):
        embed.url = item["url"]
    if item["image"].startswith("http"):
        embed.set_image(url=item["image"])
    embed.set_footer(text=meta["label"])

    view = None
    if item["url"].startswith("http"):
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label=f"Open on {meta['label']}", style=discord.ButtonStyle.link, url=item["url"]))

    await channel.send(content=headline, embed=embed, view=view, allowed_mentions=allowed)
    return True


# ---------- Polling ----------
async def check_all_feeds():
    state = await get_notifier_state()
    sent, changed = 0, False

    for feed in list(state["feeds"]):
        name = feed["name"]
        try:
            items = await asyncio.to_thread(fetch_items, feed)
        except Exception as e:
            print(f"Notifier: '{name}' fetch failed: {e}")
            continue

        ids = [i["id"] for i in items]
        seen = state["seen"].get(name)

        if seen is None:  # first time we see this feed: remember what exists, announce nothing
            state["seen"][name] = ids[:MAX_SEEN_PER_FEED]
            changed = True
            continue

        new_items = [i for i in items if i["id"] not in seen]
        if not new_items:
            continue

        for item in reversed(new_items[:MAX_POSTS_PER_CHECK]):  # oldest first
            try:
                if await send_notification(feed, item):
                    sent += 1
            except Exception as e:
                print(f"Notifier: send failed for '{name}': {e}")

        state["seen"][name] = (ids + [s for s in seen if s not in ids])[:MAX_SEEN_PER_FEED]
        changed = True

    if changed:
        await save_notifier_state()
    return sent

async def notifier_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            await check_all_feeds()
        except Exception as e:
            print(f"Notifier loop error: {e}")
        await asyncio.sleep(NOTIFIER_INTERVAL_SECONDS)


# ---------- Admin commands ----------
@bot.group(name="feed", invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def feed_group(ctx):
    await ctx.send(
        "**Notifier commands**\n"
        "`!feed list`\n"
        "`!feed add <youtube|tiktok|facebook|instagram|spotify|apple|rss> <name> <handle/id/url> [#channel]`\n"
        "`!feed notify <#channel> [name|all]` — change where notifications are sent\n"
        "`!feed force <name> <#channel>` — force-send a test notification to another channel\n"
        "`!feed remove <name>` • `!feed test <name>` • `!feed check`"
    )

@feed_group.command(name="list")
@commands.has_permissions(administrator=True)
async def feed_list(ctx):
    state = await get_notifier_state()
    default_channel_id = state.get("channel_id") or NOTIFIER_CHANNEL_ID
    header = f"**Default notification channel:** <#{default_channel_id}>"
    if not state["feeds"]:
        await ctx.send(f"{header}\nNo feeds yet. Add one with `!feed add`.")
        return
    lines = [header]
    for f in state["feeds"]:
        meta = PLATFORMS.get(f["platform"], PLATFORMS["rss"])
        dest = f"<#{f['channel_id']}>" if f.get("channel_id") else f"<#{default_channel_id}>"
        lines.append(f"{meta['emoji']} **{f['name']}** — {meta['label']} → {dest}\n`{f['target'][:80]}`")
    await ctx.send("\n".join(lines))

@feed_group.command(name="add")
@commands.has_permissions(administrator=True)
async def feed_add(ctx, platform: str, name: str, target: str, channel: discord.TextChannel = None):
    platform = {"applemusic": "apple", "yt": "youtube"}.get(platform.lower(), platform.lower())
    if platform not in PLATFORMS:
        await ctx.send(f"Platform must be one of: {', '.join(PLATFORMS)}")
        return

    state = await get_notifier_state()
    if any(f["name"].lower() == name.lower() for f in state["feeds"]):
        await ctx.send(f"A feed named `{name}` already exists.")
        return

    feed = {"name": name, "platform": platform, "target": target.strip()}
    if channel:
        feed["channel_id"] = channel.id

    async with ctx.typing():
        try:
            if platform == "youtube":
                feed["target"] = await asyncio.to_thread(resolve_youtube_channel_id, target)
            items = await asyncio.to_thread(fetch_items, feed)
        except Exception as e:
            await ctx.send(f"❌ Couldn't read that feed: `{e}`")
            return

    state["feeds"].append(feed)
    state["seen"][feed["name"]] = [i["id"] for i in items][:MAX_SEEN_PER_FEED]
    await save_notifier_state()

    if items:
        await ctx.send(f"✅ Added **{name}** ({PLATFORMS[platform]['label']}). Latest item right now: *{items[0]['title'][:100]}*. "
                       f"Only posts made from now on will be announced.")
    else:
        await ctx.send(f"⚠️ Added **{name}**, but the feed returned no items yet. If this is Facebook/Instagram/TikTok, "
                       f"the RSS source may be blocked — try a feed URL from rss.app or your own RSSHub.")

@feed_group.command(name="remove")
@commands.has_permissions(administrator=True)
async def feed_remove(ctx, name: str):
    state = await get_notifier_state()
    match = next((f for f in state["feeds"] if f["name"].lower() == name.lower()), None)
    if not match:
        await ctx.send(f"No feed named `{name}`.")
        return
    state["feeds"].remove(match)
    state["seen"].pop(match["name"], None)
    await save_notifier_state()
    await ctx.send(f"🗑️ Removed **{match['name']}**.")

@feed_group.command(name="test")
@commands.has_permissions(administrator=True)
async def feed_test(ctx, name: str):
    state = await get_notifier_state()
    match = next((f for f in state["feeds"] if f["name"].lower() == name.lower()), None)
    if not match:
        await ctx.send(f"No feed named `{name}`.")
        return
    try:
        items = await asyncio.to_thread(fetch_items, match)
    except Exception as e:
        await ctx.send(f"❌ Fetch failed: `{e}`")
        return
    if not items:
        await ctx.send("The feed returned no items.")
        return
    await send_notification(match, items[0], test=True)
    await ctx.send("✅ Test sent.", delete_after=5)

@feed_group.command(name="notify")
@commands.has_permissions(administrator=True)
async def feed_notify(ctx, channel: discord.TextChannel = None, name: str = None):
    state = await get_notifier_state()

    if channel is None:
        current_id = state.get("channel_id") or NOTIFIER_CHANNEL_ID
        await ctx.send(
            f"Current default notification channel: <#{current_id}>\n"
            f"Usage: `!feed notify <#channel>` (or `!feed notify <#channel> <feed_name>` / `!feed notify <#channel> all`)"
        )
        return

    if name and name.lower() != "all":
        match = next((f for f in state["feeds"] if f["name"].lower() == name.lower()), None)
        if not match:
            await ctx.send(f"No feed named `{name}`.")
            return
        match["channel_id"] = channel.id
        await save_notifier_state()
        await ctx.send(f"✅ Notifications for **{match['name']}** will now be sent to {channel.mention}.")
        return

    state["channel_id"] = channel.id
    if name and name.lower() == "all":
        for f in state["feeds"]:
            f.pop("channel_id", None)
        await save_notifier_state()
        await ctx.send(f"✅ Moved **all** feed notifications (and the default channel) to {channel.mention}.")
        return

    await save_notifier_state()
    custom_feeds = [f["name"] for f in state["feeds"] if f.get("channel_id")]
    msg = f"✅ Default notification channel changed to {channel.mention}."
    if custom_feeds:
        msg += (
            f"\nℹ️ Note: these feeds still have custom channels set: {', '.join(f'`{n}`' for n in custom_feeds)}. "
            f"Run `!feed notify {channel.mention} all` to move them too."
        )
    await ctx.send(msg)

@feed_notify.error
async def feed_notify_error(ctx, error):
    if isinstance(error, commands.ChannelNotFound):
        await ctx.send("❌ Channel not found. Please mention a valid text channel (e.g., `!feed notify #announcements`).")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Only administrators can change the notification channel.")
    else:
        await ctx.send(f"❌ Error: `{error}`")

@feed_group.command(name="force")
@commands.has_permissions(administrator=True)
async def feed_force(ctx, name: str, channel: discord.TextChannel, mode: str = "test"):
    state = await get_notifier_state()
    match = next((f for f in state["feeds"] if f["name"].lower() == name.lower()), None)
    if not match:
        await ctx.send(f"No feed named `{name}`.")
        return

    async with ctx.typing():
        try:
            items = await asyncio.to_thread(fetch_items, match)
        except Exception as e:
            await ctx.send(f"❌ Fetch failed: `{e}`")
            return

    if not items:
        await ctx.send("The feed returned no items.")
        return

    is_test = mode.lower() != "live"
    sent = await send_notification(match, items[0], test=is_test, channel_override=channel)
    if sent:
        label = "test notification" if is_test else "live notification"
        await ctx.send(f"✅ Forced {label} for **{match['name']}** sent to {channel.mention}.", delete_after=5)
    else:
        await ctx.send(f"❌ Failed to send notification to {channel.mention}.")

@feed_force.error
async def feed_force_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Usage: `!feed force <name> <#channel>` (add `live` at the end to hide the test label).")
    elif isinstance(error, commands.ChannelNotFound):
        await ctx.send("❌ Channel not found. Please mention a valid text channel (e.g., `!feed force TDS-Spotify #bot-test`).")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Only administrators can force-send feed notifications.")
    else:
        await ctx.send(f"❌ Error: `{error}`")

@feed_group.command(name="check")
@commands.has_permissions(administrator=True)
async def feed_check(ctx):
    sent = await check_all_feeds()
    await ctx.send(f"Checked all feeds. {sent} new notification(s) sent.")


# --- Admin web dashboard (Discord login). Needs dashboard.py and dashboard_ui.py next to this file ---
try:
    import dashboard
    dashboard.register(app, sys.modules[__name__])
except Exception as e:
    print(f"Dashboard not loaded: {e}")

# Start the web server and bot
keep_alive()
bot.run(DISCORD_TOKEN)