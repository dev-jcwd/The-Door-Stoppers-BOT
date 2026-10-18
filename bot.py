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

# Optional: Paste the "TDS - Members" Role ID here, or leave as 0 and the bot will auto-detect it by name!
TDS_MEMBERS_ROLE_ID = 0

# --- Google Sheets & Google Drive IDs ---
GOOGLE_SHEET_ID = "1b3dngW8flOcbT7WASy7iQv_1TsWRFiVhLYY3LTNsNLI"
DRIVE_MAIN_FOLDER_ID = "1FdR9bUPW-uHkgLrCn0zvf-V-0jfhDKEp"
# Optional: Paste your Google Apps Script Web App URL here, OR put it in Cell B3 of your "Settings" sheet!
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
    step = 15  # Updates every 15 seconds to stay safe from Discord rate limits

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


# --- Helper: Fallback Direct Multipart Upload (Used only if Apps Script URL is not set) ---
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


# --- Helper: Sync Order to Google Drive & Google Sheets (Runs in Background Thread) ---
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

    # Clean text so slashes don't break folder names
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

    # Check if the user added the Google Apps Script Web App URL in Settings!B3
    script_url = DRIVE_APPS_SCRIPT_URL.strip()
    if not script_url:
        try:
            settings_sheet = sh.worksheet("Settings")
            cell_b3 = settings_sheet.acell("B3").value
            if cell_b3 and cell_b3.strip().startswith("https://script.google.com"):
                script_url = cell_b3.strip()
        except Exception:
            pass

    # Prepare files to save in the buyer's Google Drive folder
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

    # 1A. UPLOAD VIA GOOGLE APPS SCRIPT BRIDGE (Bypasses Service Account 0-byte quota!)
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

    # 1B. FALLBACK: Direct Drive API (If Apps Script URL is not set yet)
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

            # If the very last message in the channel is already the sticky note, leave it alone
            if recent_msgs and recent_msgs[0].author == bot.user and recent_msgs[0].content.startswith("# RECORDS BACK-UP"):
                return

            # Delete old sticky notes so there are never duplicates
            for msg in recent_msgs:
                if msg.author == bot.user and msg.content.startswith("# RECORDS BACK-UP"):
                    try:
                        await msg.delete()
                    except Exception:
                        pass

            # Send the new sticky note at the bottom silently (no notifications)
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

    # Refresh the sticky note in #ticket-records so it stays below the new thread
    if record_channel:
        await update_sticky_message(record_channel)

    # 4. DELETE THE TICKET CHANNEL
    await channel.delete()


# --- Merch Ticketing System Classes ---
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close & Archive Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket_button")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        tds_role = get_tds_members_role(interaction.guild)
        is_tds_member = tds_role in interaction.user.roles if tds_role else False

        if interaction.user.guild_permissions.administrator or is_tds_member:
            await archive_and_close_ticket(interaction, interaction.channel, user_cancelled=False)
        else:
            await interaction.response.send_message("Only admins or TDS - Members can close this ticket.", ephemeral=True)


class ConfirmationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Yes, Proceed", style=discord.ButtonStyle.green, custom_id="proceed_yes")
    async def proceed(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)

        form_text = (
            "**Awesome! Please fill out the form below by copying and pasting it into your chat:**\n\n"
            "Name:\n"
            "Email:\n"
            "Contact Number:\n"
            "Complete Delivery Address:\n"
            "Preferred courier: Lalamove/J&T/LBC\n"
            "Mode of Payment: GCash/Maya\n\n"
            "📸 *Once an admin sends the payment QR, please upload a **screenshot of your payment receipt** directly in this chat so we can verify and archive your order!*"
        )

        close_view = CloseTicketView()
        await interaction.channel.send(form_text, view=close_view)

    @discord.ui.button(label="No, Cancel", style=discord.ButtonStyle.red, custom_id="proceed_no")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await archive_and_close_ticket(interaction, interaction.channel, user_cancelled=True)


class ProductSelectionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def handle_selection(self, interaction, product, price):
        for child in self.children:
            child.disabled = True

        msg = (
            f"You selected: **{product}**\n"
            f"Since you are a Discord member, the price is **Php {price} + shipping fee**.\n\n"
            f"Would you like to proceed?"
        )
        confirm_view = ConfirmationView()
        await interaction.response.edit_message(content=msg, view=confirm_view)

    @discord.ui.button(label="T-Shirt Only", style=discord.ButtonStyle.primary, custom_id="sel_tshirt")
    async def select_tshirt(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_selection(interaction, "T-Shirt Only", 500)

    @discord.ui.button(label="Pillars EP CD Only", style=discord.ButtonStyle.primary, custom_id="sel_cd")
    async def select_cd(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_selection(interaction, "Pillars EP CD Only", 300)

    @discord.ui.button(label="Pillars EP CD & T-Shirt", style=discord.ButtonStyle.primary, custom_id="sel_both")
    async def select_both(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_selection(interaction, "Pillars EP CD & T-Shirt", 800)


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🛒 Order Now", style=discord.ButtonStyle.blurple, custom_id="open_ticket_button")
    async def order(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        tds_members_role = get_tds_members_role(guild)
        admin_role = guild.get_role(ADMIN_ROLE_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
        }

        # Give both Admin Role and "TDS - Members" Role access to see and chat in the ticket!
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
        if tds_members_role:
            overwrites[tds_members_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)

        ticket_channel = await guild.create_text_channel(
            name=f"order-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        selection_view = ProductSelectionView()
        embed = discord.Embed(
            title="Merch Order Ticket",
            description=f"Welcome {interaction.user.mention}!\n\nWhat would you like to buy? Please select an option below:",
            color=0xFFFF00
        )

        # Build the role notification ping for both Admin and TDS - Members
        ping_list = [f"<@&{ADMIN_ROLE_ID}>"]
        if tds_members_role and tds_members_role.id != ADMIN_ROLE_ID:
            ping_list.append(tds_members_role.mention)

        ping_text = f"🔔 {' '.join(ping_list)} — **New Merch Order Ticket opened by {interaction.user.mention}!**"

        await ticket_channel.send(
            content=ping_text,
            embed=embed,
            view=selection_view,
            allowed_mentions=discord.AllowedMentions(roles=True, users=True)
        )
        await interaction.response.send_message(f"Your ticket has been created: {ticket_channel.mention}", ephemeral=True)


@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    bot.add_view(ProductSelectionView())
    bot.add_view(ConfirmationView())

    if not hasattr(bot, "spotify_loop_started"):
        bot.spotify_loop_started = True
        bot.loop.create_task(spotify_activity_loop())

    # Ensure the sticky note is posted in #ticket-records on startup
    record_channel = bot.get_channel(RECORD_CHANNEL_ID)
    if record_channel:
        await update_sticky_message(record_channel)

    print(f'Logged in successfully as {bot.user.name}!')


# --- Command to spawn the Merch Panel ---
@bot.command()
@commands.has_permissions(administrator=True)
async def merchpanel(ctx):
    view = TicketView()
    embed = discord.Embed(
        title="🎸 Grab Your Official The Door Stoppers Merch! 🚪",
        description=(
            "Our physical **Pillars EP CDs** and official band tees are now available!\n\n"
            "You can reach out to us on Instagram or TikTok, or simply place your order right here on Discord.\n\n"
            "Click the **Order Now** button below to open a private ticket with the band and secure your merch!"
        ),
        color=0xFFFF00
    )

    await ctx.send(embed=embed, view=view)
    await ctx.message.delete()


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

        embed = discord.Embed(color=0xFFFF00)
        embed.set_author(name=self.draft_message.author.display_name, icon_url=self.draft_message.author.display_avatar.url)

        url_match = None
        if self.draft_message.content:
            url_match = re.search(r'(https?://\S+)', self.draft_message.content)
            embed.description = self.draft_message.content

        file_to_send = None
        attachment_url = None

        if self.draft_message.attachments:
            attachment = self.draft_message.attachments[0]
            attachment_url = attachment.url

            if attachment.content_type and attachment.content_type.startswith('image/'):
                embed.set_image(url=attachment.url)
            else:
                try:
                    file_bytes = await attachment.read()
                    file_to_send = discord.File(io.BytesIO(file_bytes), filename=attachment.filename)
                except Exception:
                    pass

        notify_text = f"<@&{NOTIFY_ROLE_ID}>\n**ANNOUNCEMENT!**"

        link_view = discord.ui.View()
        has_buttons = False

        if url_match:
            extracted_url = url_match.group(1)
            link_view.add_item(discord.ui.Button(label="View Post", style=discord.ButtonStyle.link, url=extracted_url))
            has_buttons = True

        if attachment_url:
            link_view.add_item(discord.ui.Button(label="Open File", style=discord.ButtonStyle.link, url=attachment_url))
            has_buttons = True

        view_to_pass = link_view if has_buttons else None

        if file_to_send:
            await self.announce_channel.send(content=notify_text, embed=embed, view=view_to_pass, file=file_to_send)
        else:
            await self.announce_channel.send(content=notify_text, embed=embed, view=view_to_pass)

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="✅ **Announcement sent!**", view=self)

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
    if message.author.bot:
        return

    if message.channel.id == DRAFT_CHANNEL_ID:
        if message.author.guild_permissions.administrator:
            announce_channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)
            view = ConfirmView(message, announce_channel)
            await message.channel.send("Do you want to send this as an official announcement?", view=view)

    # Keep the sticky note at the very bottom if someone chats in #ticket-records
    if message.channel.id == RECORD_CHANNEL_ID:
        await update_sticky_message(message.channel)

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


# Start the web server and bot
keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
