import discord
from discord.ext import commands
import os
import io
import re
import gspread
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

# --- Replace these with your actual Discord IDs! ---
DRAFT_CHANNEL_ID = 1558478062558122106
ANNOUNCE_CHANNEL_ID = 1557950064679321721
NOTIFY_ROLE_ID = 1558034567766474762
WELCOME_CHANNEL_ID = 1557900784413188107 
ADMIN_ROLE_ID = 1557901221669642253 
RECORD_CHANNEL_ID = 1559322818116591666 
TICKET_CATEGORY_ID = 1559324491543351307 

# THE ID OF THE GOOGLE SHEET
GOOGLE_SHEET_ID = "1b3dngW8flOcbT7WASy7iQv_1TsWRFiVhLYY3LTNsNLI"

# --- Archiving & Google Sheets Function ---
async def archive_and_close_ticket(interaction, channel, user_cancelled=False):
    await interaction.response.send_message("Archiving, syncing to Google Sheets, and closing ticket... please wait.", ephemeral=True)
    
    messages = [m async for m in channel.history(limit=None, oldest_first=True)]
    
    transcript = ""
    
    # Defaults in case they don't fill out a specific line
    extracted_name = "N/A"
    extracted_email = "N/A"
    extracted_contact = "N/A"
    extracted_address = "N/A"
    extracted_courier = "N/A"
    extracted_payment = "N/A"
    extracted_item = "N/A"
    
    files_to_send = []
    
    for msg in messages:
        time_str = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        transcript += f"[{time_str}] {msg.author.name}: {msg.clean_content}\n"
        
        # Bot's message about selection (to figure out what they bought)
        if msg.author.bot and "You selected: **" in msg.clean_content:
            match = re.search(r'You selected: \*\*(.*?)\*\*', msg.clean_content)
            if match:
                extracted_item = match.group(1)
                
        # Parse the user's form submission
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
        
        # Download images/attachments to memory
        for attachment in msg.attachments:
            transcript += f" [Attachment logged: {attachment.filename}]\n"
            try:
                file_bytes = await attachment.read()
                files_to_send.append(discord.File(io.BytesIO(file_bytes), filename=f"{msg.author.name}_{attachment.filename}"))
            except Exception:
                pass

    buyer_discord_name = channel.name.replace("order-", "")
    
    if user_cancelled:
        thread_name = f"{buyer_discord_name} (Cancelled)"
    else:
        thread_name = f"{buyer_discord_name} ({extracted_name if extracted_name != 'N/A' else 'No Name'})"

        # --- GOOGLE SHEETS LIVE SYNC ---
        try:
            # Tell gspread to log in using the secret file we uploaded to Render
            gc = gspread.service_account(filename='google_credentials.json')
            sh = gc.open_by_key(GOOGLE_SHEET_ID)
            worksheet = sh.sheet1
            
            ph_time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
            
            # The data that gets pushed to your Google Sheet!
            row_data = [
                ph_time, 
                buyer_discord_name, 
                extracted_name, 
                extracted_email, 
                extracted_contact, 
                extracted_address, 
                extracted_courier, 
                extracted_payment, 
                extracted_item, 
                "Discord Order (Discord Member Discount Applied)"
            ]
            worksheet.append_row(row_data)
        except Exception as e:
            print(f"Error syncing to Google Sheets: {e}")

    # Send to Record Channel in Discord
    record_channel = interaction.guild.get_channel(RECORD_CHANNEL_ID)
    if record_channel:
        thread = await record_channel.create_thread(name=thread_name, type=discord.ChannelType.public_thread)
        transcript_file = discord.File(io.BytesIO(transcript.encode('utf-8')), filename="transcript.txt")
        await thread.send(content=f"**Ticket log for {buyer_discord_name}:**", file=transcript_file)
        
        chunk_size = 10
        for i in range(0, len(files_to_send), chunk_size):
            await thread.send(files=files_to_send[i:i+chunk_size])

    # Delete the ticket channel
    await channel.delete()


# --- Merch Ticketing System Classes ---
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket_button")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.guild_permissions.administrator:
            await archive_and_close_ticket(interaction, interaction.channel, user_cancelled=False)
        else:
            await interaction.response.send_message("Only admins can close this ticket.", ephemeral=True)


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
            "*Once you send this, an admin will be with you shortly to assist with payment!*"
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
        
        msg = f"You selected: **{product}**\nSince you are a Discord member, the price is **Php {price} + shipping fee**.\n\nWould you like to proceed?"
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
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
        }
        
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
        
        await ticket_channel.send(content=f"<@&{ADMIN_ROLE_ID}>", embed=embed, view=selection_view)
        await interaction.response.send_message(f"Your ticket has been created: {ticket_channel.mention}", ephemeral=True)


@bot.event
async def on_ready():
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    bot.add_view(ProductSelectionView())
    bot.add_view(ConfirmationView())

    activity = discord.CustomActivity(name="🎵 The Door Stoppers on Spotify")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f'Logged in successfully as {bot.user.name}!')


# --- Command to spawn the Merch Panel ---
@bot.command()
@commands.has_permissions(administrator=True)
async def merchpanel(ctx):
    view = TicketView()
    embed = discord.Embed(
        title="🎸 Grab Your Official The Door Stoppers Merch! 🚪",
        description="Our physical **Pillars EP CDs** and official band tees are now available!\n\nYou can reach out to us on Instagram or TikTok, or simply place your order right here on Discord.\n\nClick the **Order Now** button below to open a private ticket with the band and secure your merch!",
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

# --- Payment QR Commands ---
@bot.command()
async def gcash(ctx):
    embed = discord.Embed(title="GCash Payment", description="Please scan the QR code below to proceed with your GCash payment.", color=0x00529B)
    embed.set_image(url="https://i.imgur.com/YOUR_GCASH_LINK_HERE.png") # UPDATE THIS LINK
    await ctx.send(embed=embed)

@bot.command()
async def maya(ctx):
    embed = discord.Embed(title="Maya Payment", description="Please scan the QR code below to proceed with your Maya payment.", color=0x000000)
    embed.set_image(url="https://i.imgur.com/YOUR_MAYA_LINK_HERE.png") # UPDATE THIS LINK
    await ctx.send(embed=embed)

# Start the web server and bot
keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
