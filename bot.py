import discord
from discord.ext import tasks,commands
import os 
from dotenv import load_dotenv
import asyncio
import json
import aiohttp

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CID = os.getenv('CHANNEL_ID')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="-", intents=intents) # new bot instance

bot.HISTORY = "history.json"
bot.ALERTS = "alerts.json"
bot.CONFIG = "configs.json"

bot.posted_articles = {}
bot.active_alerts = []
bot.bot_config = {}
bot.MIN_RSS_INTERVAL = 5
bot.DEFAULT_RSS_INTERVAL = 10

bot.CHANNEL_ID = int(CID)

def load_history(bot):
    """Loads the history of posted article links from file."""
    try: 
        with open(bot.HISTORY, 'r') as f:    
            bot.posted_articles = json.load(f)
        print(f"Loaded {len(bot.posted_articles)} articles from history.")
    except(FileNotFoundError, json.JSONDecodeError):
        print("History file not found. Creating")
        bot.posted_articles = {}

def load_alerts(bot):
    """Load alert.json"""
    try:
        with open(bot.ALERTS, 'r') as f:
            bot.active_alerts = json.load(f)
        print(f"Loaded {len(bot.active_alerts)} alerts from history.")
            
    except (FileNotFoundError, json.JSONDecodeError):
            print("Alert file not found. Creating")
            bot.active_alerts = []

def load_configs(bot):
    """Load bot configs to configs.json"""
    try:
        with open(bot.CONFIG, 'r') as f:
            bot.bot_config = json.load(f)
        print(f"Loaded {len(bot.bot_config)} configs from history.")
    except (FileNotFoundError, json.JSONDecodeError):
        print("Config file not found. Creating")
        bot.bot_config = {}

def save_history(bot):
    with open(bot.HISTORY, 'w') as f:
        json.dump(bot.posted_articles, f, indent = 4)

def save_alerts(bot):
    with open(bot.ALERTS, 'w') as f:
        json.dump(bot.active_alerts, f, indent=4)

def save_configs(bot):
    with open(bot.CONFIG, 'w') as f:
        json.dump(bot.bot_config, f, indent=4)

bot.load_configs = lambda: load_configs(bot)
bot.save_configs = lambda: save_configs(bot)
bot.load_alerts = lambda: load_alerts(bot)
bot.save_alerts = lambda: save_alerts(bot)
bot.load_history = lambda: load_history(bot)
bot.save_history = lambda: save_history(bot)

# event: on_ready
# runs once it got connected to discord
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord')
    bot.load_history()
    bot.load_alerts()
    bot.load_configs()

async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

# Prefix command for :ping
@bot.command(name="ping")
async def prefix_ping(prefix):
    await prefix.send("Pong!")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    if TOKEN == None:
        print("Token ERROR")
    elif bot.CHANNEL_ID == None:
         print("Channel id error")
    else:
        asyncio.run(main())