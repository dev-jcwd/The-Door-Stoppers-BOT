import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

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
intents.message_content = True  # Required so the bot can read the !announce command
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    # Use CustomActivity to display emojis exactly like a normal user's status
    activity = discord.CustomActivity(name="🎵 The Door Stoppers on Spotify")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f'Logged in successfully as {bot.user.name}!')

# --- Automated Announcement System ---

# Replace these with your actual Discord IDs!
DRAFT_CHANNEL_ID = 1558478062558122106      # The private channel where you type drafts
ANNOUNCE_CHANNEL_ID = 1557950064679321721   # The public channel where announcements go
NOTIFY_ROLE_ID = 1558034567766474762        # Your @NOTIFY role ID

class ConfirmView(discord.ui.View):
    def __init__(self, draft_message, announce_channel):
        super().__init__(timeout=None) 
        self.draft_message = draft_message
        self.announce_channel = announce_channel

    @discord.ui.button(label="Yes, send it!", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Prevent non-admins from clicking the buttons
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Only admins can confirm announcements.", ephemeral=True)
            return

        # Build the yellow embed
        embed = discord.Embed(color=0xFFFF00)
        embed.set_author(name="The Door Stoppers", icon_url=bot.user.display_avatar.url)
        
        if self.draft_message.content:
            embed.description = self.draft_message.content
            
        if self.draft_message.attachments:
            embed.set_image(url=self.draft_message.attachments[0].url)
            
        notify_text = f"<@&{NOTIFY_ROLE_ID}>\n**ANNOUNCEMENT!**"
        
        # Send to the public announcement channel
        await self.announce_channel.send(content=notify_text, embed=embed)
        
        # Disable buttons and update the prompt message
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="✅ **Announcement sent!**", view=self)

    @discord.ui.button(label="No, cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Only admins can cancel announcements.", ephemeral=True)
            return
        
        # Disable buttons and update the prompt message
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content="❌ **Announcement cancelled.**", view=self)


@bot.event
async def on_message(message):
    # Ignore the bot's own messages to prevent endless loops
    if message.author.bot:
        return

    # Trigger only if the message is in the designated draft channel and sent by an admin
    if message.channel.id == DRAFT_CHANNEL_ID:
        if message.author.guild_permissions.administrator:
            announce_channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)
            
            # Send the confirmation prompt with the buttons
            view = ConfirmView(message, announce_channel)
            await message.channel.send("Do you want to send this as an official announcement?", view=view)

    # Ensure other commands still work
    await bot.process_commands(message)

# Start the web server and bot
keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
