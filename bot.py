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

@bot.group(invoke_without_command=True)
async def alert(prefix):
    await prefix.send("Alert command. Use `:alert add <crypto> <condition> <price>`")

@alert.command (name="add")
async def add_alert(prefix, crypto: str, condition: str, price: float):
    crypto_id = crypto.lower()
    valid_url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(valid_url) as response:
                if response.status == 404: # wrong crypto name or doesn't exist
                    await prefix.send(f"❌ **Error:** Could not find a cryptocurrency named {crypto}.")
                    return
                if response.status != 200:
                    await prefix.send("⚠️ Could not fetch Cryptocurrency price. Please try again later.")
                    return
    except Exception as e:
        print(f"Crypyo Validation Error")
        await prefix.send("⚠️ Could not fetch Cryptocurrency price. Please try again later.")
        return

    if condition not in ['>', '<']:
        await prefix.send("Invalid Condition. Please use `<` or `>`.")
        return
    new_alert={
        'user_id' : prefix.author.id,
        'crypto' : crypto.lower(),
        'condition' : condition,
        'price' : price
    }
    active_alerts.append(new_alert)
    save_alerts()
    await prefix.send(f"✅ Alert set: I will notify you when **{crypto}** is **{condition} ${price:,.2f}**.")

@alert.command(name="list")
async def list_alerts(prefix):
    user_alerts = []
    for i, alert in enumerate(active_alerts):
        if alert['user_id'] == prefix.author.id:
            user_alerts.append((i,alert))
    if not user_alerts:
        await prefix.send("You have no active alerts. Set one with -alert add <crypto> <condition> <price>.")
        return
    message = "Your active alerts:\n```\n"
    for alert_id, alert in user_alerts:
        crypto = alert['crypto'].capitalize()
        condition = alert['condition']
        price = f"${alert['price']:,.2f}"
        message += f"ID: {alert_id} | {crypto} {condition} {price}\n"
    message += "```\nUse the ID to edit or remove an alert."
    await prefix.send(message)

@alert.command(name="remove")
async def remove_alert(prefix, alert_id: int):
    if not(0<=alert_id < len(active_alerts)):
        await prefix.send(f"Error: Invalid ID. There is no alert with ID {alert_id}. Use -alert list to see valid IDs")
        return 
    if active_alerts[alert_id]['user_id'] != prefix.author.id:
        await prefix.send("Error: You can only remove your own alerts.")
        return
    removed = active_alerts.pop(alert_id)
    save_alerts()
    crypto = removed['crypto'].capitalize()
    condition = removed['condition']
    price = f"${removed['price']:,.2f}"
    await prefix.send(f"✅ Alert removed: Your alert for **{crypto} {condition} {price}** has been deleted")

@tasks.loop(seconds=60)
async def check_prices():
    await bot.wait_until_ready()
    if not active_alerts: # empty
        return
    # get unique set of crypto ID from alerts
    crypto_id = {alert['crypto'] for alert in active_alerts}
    
    # format id for CG API
    id_str = ".".join(crypto_id)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={id_str}&vs_currencies=usd"

    # api call here
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:

            # these nested if would be revisited someday
            if response.status == 200:
                prices = await response.json()
                print(f"Fetched prices: {prices}")
                triggered_alerts = []
                for alert in active_alerts:
                    crypto = alert['crypto']
                    if crypto in prices and 'usd' in prices[crypto]:
                        curr_price = prices[crypto]['usd']
                        condition = alert['condition']
                        target_price = alert['price']

                        alert_triggered = (condition == '>' and curr_price > target_price) or (condition == '<' and curr_price < target_price)
                        if alert_triggered:
                            print(f"ALERT TRIGGERED: User {alert['user_id']} for {crypto} {condition} {target_price}")
                            user = await bot.fetch_user(alert['user_id'])
                            if user:
                                message = (
                                    f"🔔 **Price Alert!** 🔔\n\n"
                                    f"Your alert for **{crypto.capitalize()}** was triggered.\n"
                                    f"Target: {condition} $ {target_price:,.2f}\n"
                                    f"Current Price: ${curr_price:,.2f}"
                                )
                                await user.send(message)
                                triggered_alerts.append(alert)
                if triggered_alerts:
                    active_alerts[:] = [alert for alert in active_alerts if alert not in triggered_alerts]
                    save_alerts()


            else:
                print(f"Error fetching prices, status: {response.status}")

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