import discord
from discord.ext import tasks, commands
import feedparser
import time

class RSS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.migrate_feeds()
        saved_interval = self.bot.bot_config.get('rss_interval_minutes', self.bot.DEFAULT_RSS_INTERVAL)
        self.fetch_rss.change_interval(minutes=saved_interval)
        self.fetch_rss.start()

    def migrate_feeds(self):
        """One-time migration of old string-based feed list to new object-based list."""
        if 'rss_feeds' in self.bot.bot_config and self.bot.bot_config['rss_feeds']:
            if isinstance(self.bot.bot_config['rss_feeds'][0], str):
                print("Migrating RSS feed structure...")
                self.bot.bot_config['rss_feeds'] = [
                    {'url': url, 'keywords': []} for url in self.bot.bot_config['rss_feeds']
                ]
                self.bot.save_configs()
                print("Migration complete.")

    def cog_unload(self):
        self.fetch_rss.cancel()

    async def perform_rss_check(self):
        await self.bot.wait_until_ready()
        for feed_obj in self.bot.bot_config.get('rss_feeds', []):
            url = feed_obj['url']
            keywords = feed_obj.get('keywords', [])
            feed = await self.bot.loop.run_in_executor(None, lambda: feedparser.parse(url))

            if feed.entries:
                latest = feed.entries[0]
                if latest.link not in self.bot.posted_articles:
                    # Check for keywords
                    content_to_check = (latest.title + ' ' + getattr(latest, 'summary', '')).lower()
                    if not keywords or any(k.lower() in content_to_check for k in keywords):
                        print(f"New article found: {latest.title}")
                        self.bot.posted_articles[latest.link] = time.time()
                        
                        channel = self.bot.get_channel(self.bot.CHANNEL_ID)
                        if channel:
                            embed = discord.Embed(
                                title=latest.title,
                                url=latest.link,
                                description=getattr(latest, 'summary', "A new article has been posted"),
                                color=discord.Color.blue()
                            )
                            embed.set_footer(text=feed.feed.title)
                            if hasattr(latest, 'media_content') and latest.media_content:
                                image_url = latest.media_content[0]['url']
                                embed.set_image(url=image_url)
                            await channel.send(embed=embed)
                
                curr_time = time.time()
                three_hours = 3 * 60 * 60
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
    async def rss(self, ctx):
        curr_interval = self.fetch_rss.minutes
        feeds = self.bot.bot_config.get('rss_feeds', [])
        message = f"RSS Settings:\nInterval: **{curr_interval}** minutes.\nFeeds:\n"
        if not feeds:
            message += "No RSS feeds configured. Use `-rss add <url>` to add one."
        else:
            for i, feed_obj in enumerate(feeds):
                keywords_str = ", ".join(feed_obj.get('keywords', []))
                message += f"**{i+1}.** {feed_obj['url']}\n"
                if keywords_str:
                    message += f"   *Keywords: `{keywords_str}`*\n"
        await ctx.send(message)

    @rss.command(name="add", help="Adds a new RSS feed. Usage: `-rss add <url>`")
    @commands.has_permissions(administrator=True)
    async def add_rss_feed(self, ctx, url: str):
        if 'rss_feeds' not in self.bot.bot_config:
            self.bot.bot_config['rss_feeds'] = []
        
        new_feed = {'url': url, 'keywords': []}
        self.bot.bot_config['rss_feeds'].append(new_feed)
        self.bot.save_configs()
        await ctx.send(f"✅ RSS feed added: {url}")

    @rss.command(name="remove", help="Removes an RSS feed by its index. Usage: `-rss remove <index>`")
    @commands.has_permissions(administrator=True)
    async def remove_rss_feed(self, ctx, index: int):
        feeds = self.bot.bot_config.get('rss_feeds', [])
        if 1 <= index <= len(feeds):
            removed_feed = feeds.pop(index - 1)
            self.bot.save_configs()
            await ctx.send(f"✅ RSS feed removed: {removed_feed['url']}")
        else:
            await ctx.send(f"❌ Invalid index. Use `-rss` to see the list of feeds.")

    @rss.command(name="interval", help="Sets the interval for checking for new RSS articles. Usage: `-rss interval <minutes>`")
    @commands.has_permissions(administrator=True)
    async def set_rss_interval(self, ctx, new_interval: int):
        if new_interval < self.bot.MIN_RSS_INTERVAL:
            await ctx.send(f"❌ Minimum RSS poll interval rate is **5 Minutes**.")
            return
        self.fetch_rss.change_interval(minutes=new_interval)
        self.bot.bot_config['rss_interval_minutes'] = new_interval
        self.bot.save_configs()
        await ctx.send(f"✅ RSS poll interval is now **{new_interval} minutes**.")

    @rss.group(name="keywords", help="Manage keywords for RSS feeds", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def keywords(self, ctx):
        await ctx.send("Manage keywords for a feed. Use `-rss keywords <add|remove|list> <feed_index> [keyword]`")

    @keywords.command(name="add", help="Add a keyword to a feed. Usage: `-rss keywords add <index> <keyword>`")
    @commands.has_permissions(administrator=True)
    async def add_keyword(self, ctx, index: int, keyword: str):
        feeds = self.bot.bot_config.get('rss_feeds', [])
        if 1 <= index <= len(feeds):
            feed_obj = feeds[index - 1]
            if keyword.lower() not in [k.lower() for k in feed_obj['keywords']]:
                feed_obj['keywords'].append(keyword)
                self.bot.save_configs()
                await ctx.send(f"✅ Keyword `{keyword}` added to feed #{index}.")
            else:
                await ctx.send(f"⚠️ Keyword `{keyword}` already exists for feed #{index}.")
        else:
            await ctx.send(f"❌ Invalid feed index.")

    @keywords.command(name="remove", help="Remove a keyword from a feed. Usage: `-rss keywords remove <index> <keyword>`")
    @commands.has_permissions(administrator=True)
    async def remove_keyword(self, ctx, index: int, keyword: str):
        feeds = self.bot.bot_config.get('rss_feeds', [])
        if 1 <= index <= len(feeds):
            feed_obj = feeds[index - 1]
            keyword_to_remove = next((k for k in feed_obj['keywords'] if k.lower() == keyword.lower()), None)
            if keyword_to_remove:
                feed_obj['keywords'].remove(keyword_to_remove)
                self.bot.save_configs()
                await ctx.send(f"✅ Keyword `{keyword}` removed from feed #{index}.")
            else:
                await ctx.send(f"❌ Keyword `{keyword}` not found for feed #{index}.")
        else:
            await ctx.send(f"❌ Invalid feed index.")

    @keywords.command(name="list", help="List all keywords for a feed. Usage: `-rss keywords list <index>`")
    @commands.has_permissions(administrator=True)
    async def list_keywords(self, ctx, index: int):
        feeds = self.bot.bot_config.get('rss_feeds', [])
        if 1 <= index <= len(feeds):
            feed_obj = feeds[index - 1]
            keywords = feed_obj.get('keywords', [])
            if keywords:
                await ctx.send(f"Keywords for feed #{index}: `{"`, `".join(keywords)}`")
            else:
                await ctx.send(f"Feed #{index} has no keywords.")
        else:
            await ctx.send(f"❌ Invalid feed index.")

async def setup(bot):
    await bot.add_cog(RSS(bot))