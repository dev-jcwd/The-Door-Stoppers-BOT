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
    # Render assigns a port dynamically. We must listen on it.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

# --- Discord Bot Setup ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    band_link = "your_link_here" 
    activity = discord.Activity(type=discord.ActivityType.listening, name=band_link)
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f'Logged in successfully as {bot.user.name}!')

# Start the web server on a separate thread
keep_alive()

# Start the bot using the environment variable token
# DO NOT put your actual token directly in the code here anymore!
bot.run(os.getenv('DISCORD_TOKEN'))