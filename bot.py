import discord
from discord.ext import tasks,commands
import os 
from dotenv import load_dotenv
import feedparser
import json
import time
import aiohttp

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
HISTORY = "history.json"
ALERTS = "alerts.json"
CONFIG = "configs.json"
CID = os.getenv('CHANNEL_ID')
CHANNEL_ID = int(CID)
posted_articles = {}
active_alerts = []
bot_config = {}
MIN_RSS_INTERVAL = 5
DEFAULT_RSS_INTERVAL = 10


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="-", intents=intents) # new bot instance

def load_history():
    """Loads the history of posted article links from file."""
    global posted_articles
    try: 
        with open(HISTORY, 'r') as f:    
            posted_articles = json.load(f)
        print(f"Loaded {len(posted_articles)} articles from history.")
    except(FileNotFoundError, json.JSONDecodeError):
        print("History file not found. Creating")
        posted_articles = {}

def load_alerts():
    """Load alert.json"""
    global active_alerts
    try:
        with open(ALERTS, 'r') as f:
            active_alerts = json.load(f)
        print(f"Loaded {len(active_alerts)} alerts from history.")
            
    except (FileNotFoundError, json.JSONDecodeError):
            print("Alert file not found. Creating")
            active_alerts = []

def load_configs():
    """Load bot configs to configs.json"""
    global bot_config 
    try:
        with open(CONFIG, 'r') as f:
            bot_config = json.load(f)
        print(f"Loaded {len(bot_config)} configs from history.")
    except (FileNotFoundError, json.JSONDecodeError):
        print("Config file not found. Creating")
        bot_config = {}

def save_history():
    with open(HISTORY, 'w') as f:
        json.dump(posted_articles, f, indent = 4)

def save_alerts():
    with open(ALERTS, 'w') as f:
        json.dump(active_alerts, f, indent=4)

def save_configs():
    with open(CONFIG, 'w') as f:
        json.dump(bot_config, f, indent=4)
async def perform_rss_check():
    """Main logic for fetching, parsing, and checking RSS feed"""
    global posted_articles
    await bot.wait_until_ready()
    crypto_url = "https://cointelegraph.com/rss"
    feed = await bot.loop.run_in_executor(None, lambda: feedparser.parse(crypto_url))
    if feed.entries:
        latest = feed.entries[0]

        # check if article link is not on HISTORY
        if latest.link not in posted_articles:
            print(f"New article found: {latest.title}")

            posted_articles[latest.link] = time.time()
            
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title = latest.title,
                    url = latest.link,
                    description="A new article has been posted",
                    color = discord.Color.blue()
                )
                embed.set_footer(text=feed.feed.title)
                if hasattr(latest, 'media_content') and latest.media_content:
                    image_url = latest.media_content[0]['url']
                    embed.set_image(url=image_url)
                await channel.send(embed=embed)
            else:
                print(f"Error: Channel with ID {CHANNEL_ID} not found.")
        
        curr_time = time.time()
        three_hours = 3*60*60

        prune = {
            link: timestamp
            for link, timestamp in posted_articles.items()
            if (curr_time - timestamp) < three_hours
        }
        if len(prune) < len(posted_articles):
            print(f"Pruned {len(posted_articles) - len(prune)} articles from history.")
            posted_articles = prune 
        save_history()

    else:
        print(f"Could not find any articles in the feed: {crypto_url}")


# event: on_ready
# runs once it got connected to discord
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord')
    load_history()
    load_alerts()
    load_configs()

    interval = bot_config.get('rss_interval_minutes', DEFAULT_RSS_INTERVAL)
    fetch_rss.change_interval(minutes = interval)

    print("Init RSS checking")
    await perform_rss_check()

    if not fetch_rss.is_running():
        fetch_rss.start()
    if not check_prices.is_running():
        check_prices.start()

# Prefix command for :ping
@bot.command(name="ping")
async def prefix_ping(prefix):
    await prefix.send("Pong!")

@bot.group(invoke_without_command=True)
async def alert(prefix):
    await prefix.send("Alert command. Use `:alert add <crypto> <condition> <price>`")

@bot.group(invoke_without_command=True)
async def rss(prefix):
    curr_interval = fetch_rss.minutes
    await prefix.send(f"RSS Settings. The curent check interval is **{curr_interval}** minutes. Use -rss interval <minutes> to change")
    
@rss.command(name="interval")
@commands.has_permissions(administrator=True)
async def set_rss_interval(prefix, new_interval: int):
    if new_interval < MIN_RSS_INTERVAL:
        await prefix.send(f"❌ Minimum RSS poll interval rate is **5 Minutes**.")
        return
    fetch_rss.change_interval(minutes=new_interval)
    bot_config['rss_interval_minutes'] = new_interval
    save_configs()
    await fetch_rss.send(f"✅ RSS poll interval is now ** {new_interval} minutes**.")

@set_rss_interval.error
async def interval_error(prefix,error):
    if isinstance(error, commands.MissingPermissions):
        await prefix.send(f"❌ **Error:** You don't have any previledge to use this command")
    elif isinstance(error, commands.BadArgument):
        await prefix.send(f"❌ **Error:** Please provide a valid number")
    else:
        print(f"RSS command error: {error}")
        await prefix.send("An unexpected error occured")

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

@tasks.loop(minutes=10)
async def fetch_rss():
    await perform_rss_check()
if TOKEN is None:
    print("TOKEN ERROR")
else:
    bot.run(TOKEN)
