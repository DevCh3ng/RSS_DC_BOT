import discord
from discord.ext import tasks,commands
import os 
from dotenv import load_dotenv
import feedparser
import json
import time

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
HISTORY = "history.json"
CHANNEL_ID = os.getenv("CHANNEL_ID")
posted_articles = {}


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
    except (FileNotFoundError, json.JSONDecodeError):
        print("History file not found. Created Automatically")
        posted_articles = {}

def save_history():
    with open(HISTORY, 'w') as f:
        json.dump(posted_articles, f, indent = 4)

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
    print("Init RSS checking")
    await perform_rss_check()

    if not fetch_rss.is_running():
        fetch_rss.start()

# Prefix command for :ping
@bot.command(name="ping")
async def prefix_ping(ctx):
    await ctx.send("Pong!")

@tasks.loop(minutes=10)
async def fetch_rss():
    await perform_rss_check()
if TOKEN is None:
    print("TOKEN ERROR")
else:
    bot.run(TOKEN)
