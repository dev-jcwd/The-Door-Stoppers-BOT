import discord
from discord.ext import commands
import os
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
intents.members = True  # Required for the welcome message
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Replace these with your actual Discord IDs! ---
DRAFT_CHANNEL_ID = 1558478062558122106
ANNOUNCE_CHANNEL_ID = 1557950064679321721
NOTIFY_ROLE_ID = 1558034567766474762
WELCOME_CHANNEL_ID = 1557900784413188107 # Replace this with your Welcome channel ID

@bot.event
async def on_ready():
    # Custom status with the music note
    activity = discord.CustomActivity(name="🎵 The Door Stoppers on Spotify")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f'Logged in successfully as {bot.user.name}!')

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
        embed.set_author(name="The Door Stoppers", icon_url=bot.user.display_avatar.url)
        
        if self.draft_message.content:
            embed.description = self.draft_message.content
            
        if self.draft_message.attachments:
            embed.set_image(url=self.draft_message.attachments[0].url)
            
        notify_text = f"<@&{NOTIFY_ROLE_ID}>\n**ANNOUNCEMENT!**"
        
        await self.announce_channel.send(content=notify_text, embed=embed)
        
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

# Start the web server and bot
keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
