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

# --- Announcement Command ---
@bot.command()
@commands.has_permissions(administrator=True)
async def announce(ctx, channel: discord.TextChannel, *, message: str = None):
    # Creates the embed box with a yellow line (0xFFFF00)
    embed = discord.Embed(color=0xFFFF00)
    
    # Add the text if you typed a message
    if message:
        embed.description = message
        
    # Check if you uploaded an image and add it inside the embed
    if ctx.message.attachments:
        embed.set_image(url=ctx.message.attachments[0].url)
        
    # Prevent empty announcements
    if not message and not ctx.message.attachments:
        await ctx.send("Please provide some text or attach an image!")
        return
        
    await channel.send(embed=embed)
    await ctx.send(f"Success! Announcement sent to {channel.mention}.")

@announce.error
async def announce_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing information! Usage: `!announce #channel The message here` (or attach an image)")

# Start the web server and bot
keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
