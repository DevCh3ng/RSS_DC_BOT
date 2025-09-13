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

def load_data(file_path):
    """Loads data from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(file_path, data):
    """Saves data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

bot.posted_articles = load_data(bot.HISTORY)
bot.active_alerts = load_data(bot.ALERTS)
bot.bot_config = load_data(bot.CONFIG)

bot.save_configs = lambda: save_data(bot.CONFIG, bot.bot_config)
bot.save_alerts = lambda: save_data(bot.ALERTS, bot.active_alerts)
bot.save_history = lambda: save_data(bot.HISTORY, bot.posted_articles)

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
        bot.load_configs()
        bot.load_history()
        bot.load_alerts
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    if TOKEN == None:
        print("Token ERROR")
    elif bot.CHANNEL_ID == None:
         print("Channel id error")
    else:
        asyncio.run(main())