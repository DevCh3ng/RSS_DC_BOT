import discord 
from discord.ext import tasks, commands
import feedparser
import time
class RSS(commands.cog):
    def __init__(self,bot):
        self.bot = bot 
        saved_interval = self.bot.bot_config.get('rss_interval_minutes', self.bot.DEFAULT_RSS_INTERVAL)
        self.fetch_rss.change_interval(minutes = saved_interval)
        self.fetch_rss.start()

    def cog_unload(self):
        self.fetch_rss.cancel()
        
    async def perform_rss_check(self):
        await self.bot.wait_until_ready()
        crypto_url = "https://cointelegraph.com/rss"
        feed = await self.bot.loop.run_in_executor(None, lambda: feedparser.parse(crypto_url))

        if feed.entries:
            latest = feed.entries[0]
            # check if article link is not on HISTORY
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
    
    @commands.group(invoke_without_command=True)
    async def rss(self,prefix):
        curr_interval = self.fetch_rss_minutes
        await prefix.send(f"RSS Settings. The curent check interval is **{curr_interval}** minutes. Use -rss interval <minutes> to change")
    
    @rss.command(name="interval")
    @commands.has_permissions(administrator=True)
    async def set_rss_interval(self, prefix, new_interval: int):
        if new_interval < self.bot.MIN_RSS_INTERVAL:
            await prefix.send(f"❌ Minimum RSS poll interval rate is **5 Minutes**.")
            return
        self.fetch_rss.change_interval(minutes=new_interval)
        self.bot.bot_config['rss_interval_minutes'] = new_interval
        self.bot.save_configs()
        await prefix.send(f"✅ RSS poll interval is now ** {new_interval} minutes**.")

    async def setup(bot):
        await bot.add_cog(RSS(bot))


