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
bot = commands.Bot(command_prefix="-", intents=intents, help_command=None) # new bot instance

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

async def log_action(bot, guild, message, author):
    """Sends a log message to the configured audit channel."""
    guild_config = bot.bot_config.get(str(guild.id), {})
    log_channel_id = guild_config.get('log_channel')

    if log_channel_id:
        log_channel = guild.get_channel(log_channel_id)
        if log_channel:
            embed = discord.Embed(description=message, color=discord.Color.blue())
            embed.set_author(name=author.display_name, icon_url=author.avatar.url if author.avatar else author.default_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            try:
                await log_channel.send(embed=embed)
            except discord.Forbidden:
                # Bot might not have permissions to send messages in the channel
                pass

bot.log_action = log_action

# event: on_ready
# runs once it got connected to discord
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord')

async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

@bot.event
async def guild_join(guild):
    inviter = None
    async for entry in guild.audit_logs(action=discord.AuditLogAction.bot_add):
        if entry.target == bot.user:
            inviter = entry.user
            break
    if inviter:
        message = await inviter.send(f"Hello! I've joined your server: **{guild.name}**. "
                                     f"Please specify a channel where I can post RSS updates. "
                                     f"You can do this by mentioning the channel (#your-channel-name). ")
        def check(m):
            return m.author == inviter and m.guild is None and m.channel_mentions
        try:
            response = await bot.wait_for('message', check=check, timeout=240)
            channel = response.channel_mentions[0]

            if str(guild.id) not in bot.bot_config:
                bot.bot_config[str(guild.id)] = {}
            bot.bot_config[str(guild.id)]["channel_id"] = channel.id
            bot.save_configs()

            await inviter.send(f"Great! I will now post RSS updates in {channel.mention}.")
        except asyncio.TimeoutError:
            await inviter.send("Please use the '-setchannel' command to set bot channel. ")
            

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