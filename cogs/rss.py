import discord 
from discord.ext import tasks, commands
import feedparser
import time

class RSS(commands.Cog):
    def __init__(self,bot):
        self.bot = bot 
        if 'rss_feeds' not in self.bot.bot_config:
            self.bot.bot_config['rss_feeds'] = []
        saved_interval = self.bot.bot_config.get('rss_interval_minutes', self.bot.DEFAULT_RSS_INTERVAL)
        self.fetch_rss.change_interval(minutes = saved_interval)
        self.fetch_rss.start()

    def cog_unload(self):
        self.fetch_rss.cancel()
        
    async def perform_rss_check(self):
        await self.bot.wait_until_ready()
        for url in self.bot.bot_config.get('rss_feeds', []):
            feed = await self.bot.loop.run_in_executor(None, lambda: feedparser.parse(url))

            if feed.entries:
                latest = feed.entries[0]
                if latest.link not in self.bot.posted_articles:
                    print(f"New article found: {latest.title}")

                    self.bot.posted_articles[latest.link] = time.time()
                    
                    channel = self.bot.get_channel(self.bot.CHANNEL_ID)
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
                
                curr_time = time.time()
                three_hours = 3*60*60
                prune = {
                    link: timestamp
                    for link, timestamp in self.bot.posted_articles.items()
                    if (curr_time - timestamp) < three_hours
                }
                if len(prune) < len(self.bot.posted_articles):
                    self.bot.posted_articles = prune 
                self.bot.save_history()
    
    @tasks.loop(minutes=10)
    async def fetch_rss(self):
        await self.perform_rss_check()
    
    @commands.group(invoke_without_command=True, help="Manages RSS feeds and settings.")
    async def rss(self,prefix):
        curr_interval = self.fetch_rss.minutes
        feeds = self.bot.bot_config.get('rss_feeds', [])
        message = f"RSS Settings:\nInterval: **{curr_interval}** minutes.\nFeeds:\n"
        if not feeds:
            message += "No RSS feeds configured. Use `-rss add <url>` to add one."
        else:
            for i, url in enumerate(feeds):
                message += f"{i+1}. {url}\n"
        await prefix.send(message)
    
    @rss.command(name="add", help="Adds a new RSS feed. Usage: `-rss add <url>`")
    @commands.has_permissions(administrator=True)
    async def add_rss_feed(self, prefix, url: str):
        if 'rss_feeds' not in self.bot.bot_config:
            self.bot.bot_config['rss_feeds'] = []
        self.bot.bot_config['rss_feeds'].append(url)
        self.bot.save_configs()
        await prefix.send(f"✅ RSS feed added: {url}")

    @rss.command(name="remove", help="Removes an RSS feed by its index. Usage: `-rss remove <index>`")
    @commands.has_permissions(administrator=True)
    async def remove_rss_feed(self, prefix, index: int):
        if 'rss_feeds' in self.bot.bot_config and 1 <= index <= len(self.bot.bot_config['rss_feeds']):
            removed_url = self.bot.bot_config['rss_feeds'].pop(index - 1)
            self.bot.save_configs()
            await prefix.send(f"✅ RSS feed removed: {removed_url}")
        else:
            await prefix.send(f"❌ Invalid index. Use `-rss` to see the list of feeds.")

    @rss.command(name="interval", help="Sets the interval for checking for new RSS articles. Usage: `-rss interval <minutes>`")
    @commands.has_permissions(administrator=True)
    async def set_rss_interval(self, prefix, new_interval: int):
        if new_interval < self.bot.MIN_RSS_INTERVAL:
            await prefix.send(f"❌ Minimum RSS poll interval rate is **5 Minutes**.")
            return
        self.fetch_rss.change_interval(minutes=new_interval)
        self.bot.bot_config['rss_interval_minutes'] = new_interval
        self.bot.save_configs()
        await prefix.send(f"✅ RSS poll interval is now **{new_interval} minutes**.")

async def setup(bot):
    await bot.add_cog(RSS(bot))