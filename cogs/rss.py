import discord
from discord.ext import tasks, commands
import feedparser
import time

# Custom check for RSS admin permissions
def is_rss_admin():
    async def predicate(prefix):
        if prefix.author.guild_permissions.administrator:
            return True
        guild_config = prefix.bot.bot_config.get(str(prefix.guild.id), {})
        admin_roles_ids = guild_config.get('admin_roles', [])
        return any(role.id in admin_roles_ids for role in prefix.author.roles)
    return commands.check(predicate)

class RSS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        saved_interval = self.bot.bot_config.get('rss_interval_minutes', self.bot.DEFAULT_RSS_INTERVAL)
        self.fetch_rss.change_interval(minutes=saved_interval)
        self.fetch_rss.start()

    def cog_unload(self):
        self.fetch_rss.cancel()

    async def perform_rss_check(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            guild_config = self.bot.bot_config.get(str(guild.id), {})
            feeds = guild_config.get('rss_feeds', [])
            default_channel_id = guild_config.get('channel_id')

            for feed_obj in feeds:
                url = feed_obj['url']
                keywords = feed_obj.get('keywords', [])
                feed = await self.bot.loop.run_in_executor(None, lambda: feedparser.parse(url))

                if not feed.entries:
                    continue

                latest = feed.entries[0]
                if latest.link not in self.bot.posted_articles:
                    content_to_check = (latest.title + ' ' + getattr(latest, 'summary', '')).lower()
                    if not keywords or any(k.lower() in content_to_check for k in keywords):
                        target_channel_id = feed_obj.get('channel_id') or default_channel_id
                        if not target_channel_id:
                            continue

                        channel = self.bot.get_channel(target_channel_id)
                        if channel:
                            print(f"New article found for guild {guild.id}: {latest.title}")
                            self.bot.posted_articles[latest.link] = time.time()
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

    @commands.group(invoke_without_command=True, help="Manages RSS feeds for this server.")
    async def rss(self, prefix):
        guild_config = self.bot.bot_config.get(str(prefix.guild.id), {})
        feeds = guild_config.get('rss_feeds', [])
        default_channel = self.bot.get_channel(guild_config.get('channel_id'))

        message = f"**RSS Settings for {prefix.guild.name}**\n"
        message += f"Interval: **{self.fetch_rss.minutes}** minutes.\n"
        message += f"Default Channel: {default_channel.mention if default_channel else 'Not Set'}\n\n**Feeds:**\n"

        if not feeds:
            message += "No RSS feeds configured. Use `-rss add <url> [#channel]` to add one."
        else:
            for i, feed_obj in enumerate(feeds):
                channel = self.bot.get_channel(feed_obj.get('channel_id'))
                keywords_str = ", ".join(feed_obj.get('keywords', []))
                message += f"**{i+1}.** {feed_obj['url']}\n"
                message += f"   *Channel:* {channel.mention if channel else 'Default'}\n"
                if keywords_str:
                    message += f"   *Keywords:* `{keywords_str}`\n"
        await prefix.send(message)

    @rss.command(name="add", help="Adds a new RSS feed. Usage: `-rss add <url> [channel]`")
    @is_rss_admin()
    async def add_rss_feed(self, prefix, url: str, channel: discord.TextChannel = None):
        guild_config = self.bot.bot_config.setdefault(str(prefix.guild.id), {})
        feeds = guild_config.setdefault('rss_feeds', [])
        channel_configs = guild_config.get('channel_configs', {})

        # Determine target channel
        target_channel = channel or self.bot.get_channel(guild_config.get('channel_id'))
        if not target_channel:
            await prefix.send("❌ No channel specified and no default channel is set for this server. Use `-setchannel` first.")
            return

        # --- Enforce All Limits ---
        # 1. Global server limit
        PROGRAM_MAX_FEEDS = 30
        guild_limit = guild_config.get('rss_feed_limit', PROGRAM_MAX_FEEDS)
        if len(feeds) >= guild_limit:
            await prefix.send(f"❌ This server has reached its limit of {guild_limit} RSS feeds.")
            return

        # 2. Channel-specific limits
        channel_settings = channel_configs.get(str(target_channel.id), {})
        channel_feed_count = sum(1 for feed in feeds if feed.get('channel_id') == target_channel.id)

        # 2a. Multiple feeds allowed?
        allow_multiple = channel_settings.get('allow_multiple', True) # Default to true
        if not allow_multiple and channel_feed_count > 0:
            await prefix.send(f"❌ {target_channel.mention} is configured to not allow more than one RSS feed.")
            return

        # 2b. Channel feed count limit
        channel_limit = channel_settings.get('limit')
        if channel_limit is not None and channel_feed_count >= channel_limit:
            await prefix.send(f"❌ {target_channel.mention} has reached its limit of {channel_limit} RSS feeds.")
            return

        new_feed = {'url': url, 'keywords': [], 'channel_id': target_channel.id}
        
        feeds.append(new_feed)
        self.bot.save_configs()
        await prefix.send(f"✅ RSS feed added for {target_channel.mention}.")

    @rss.command(name="limit", help="Sets the maximum number of RSS feeds for this server.")
    @commands.has_permissions(administrator=True) # Only full admins can set the limit
    async def set_rss_limit(self, prefix, limit: int):
        PROGRAM_MAX_FEEDS = 30
        if not (1 <= limit <= PROGRAM_MAX_FEEDS):
            await prefix.send(f"❌ Invalid limit. Please choose a number between 1 and {PROGRAM_MAX_FEEDS}.")
            return
        
        guild_config = self.bot.bot_config.setdefault(str(prefix.guild.id), {})
        guild_config['rss_feed_limit'] = limit
        self.bot.save_configs()
        await prefix.send(f"✅ The maximum number of RSS feeds for this server is now set to **{limit}**.")

    @rss.command(name="remove", help="Removes an RSS feed by its index. Usage: `-rss remove <index>`")
    @is_rss_admin()
    async def remove_rss_feed(self, prefix, index: int):
        guild_config = self.bot.bot_config.get(str(prefix.guild.id), {})
        feeds = guild_config.get('rss_feeds', [])
        if 1 <= index <= len(feeds):
            removed_feed = feeds.pop(index - 1)
            self.bot.save_configs()
            await prefix.send(f"✅ RSS feed removed: {removed_feed['url']}")
        else:
            await prefix.send(f"❌ Invalid index. Use `-rss` to see the list of feeds for this server.")

    @rss.command(name="interval", help="Sets the global interval for checking RSS articles.")
    @is_rss_admin()
    async def set_rss_interval(self, prefix, new_interval: int):
        if new_interval < self.bot.MIN_RSS_INTERVAL:
            await prefix.send(f"❌ Minimum RSS poll interval rate is **5 Minutes**.")
            return
        self.fetch_rss.change_interval(minutes=new_interval)
        self.bot.bot_config['rss_interval_minutes'] = new_interval
        self.bot.save_configs()
        await prefix.send(f"✅ Global RSS poll interval is now **{new_interval} minutes**.")

    @rss.group(name="keywords", help="Manage keywords for a specific RSS feed.", invoke_without_command=True)
    @is_rss_admin()
    async def keywords(self, prefix):
        await prefix.send("Use `-rss keywords <add|remove|list> <feed_index> [keyword]`")

    @keywords.command(name="add", help="Add a keyword to a feed. Usage: `-rss keywords add <index> <keyword>`")
    @is_rss_admin()
    async def add_keyword(self, prefix, index: int, keyword: str):
        guild_config = self.bot.bot_config.get(str(prefix.guild.id), {})
        feeds = guild_config.get('rss_feeds', [])
        if 1 <= index <= len(feeds):
            feed_obj = feeds[index - 1]
            if keyword.lower() not in [k.lower() for k in feed_obj['keywords']]:
                feed_obj.setdefault('keywords', []).append(keyword)
                self.bot.save_configs()
                await prefix.send(f"✅ Keyword `{keyword}` added to feed #{index}.")
            else:
                await prefix.send(f"⚠️ Keyword `{keyword}` already exists for feed #{index}.")
        else:
            await prefix.send(f"❌ Invalid feed index.")

    @keywords.command(name="remove", help="Remove a keyword from a feed. Usage: `-rss keywords remove <index> <keyword>`")
    @is_rss_admin()
    async def remove_keyword(self, prefix, index: int, keyword: str):
        guild_config = self.bot.bot_config.get(str(prefix.guild.id), {})
        feeds = guild_config.get('rss_feeds', [])
        if 1 <= index <= len(feeds):
            feed_obj = feeds[index - 1]
            keyword_to_remove = next((k for k in feed_obj.get('keywords', []) if k.lower() == keyword.lower()), None)
            if keyword_to_remove:
                feed_obj['keywords'].remove(keyword_to_remove)
                self.bot.save_configs()
                await prefix.send(f"✅ Keyword `{keyword}` removed from feed #{index}.")
            else:
                await prefix.send(f"❌ Keyword `{keyword}` not found for feed #{index}.")
        else:
            await prefix.send(f"❌ Invalid feed index.")

    @keywords.command(name="list", help="List all keywords for a feed. Usage: `-rss keywords list <index>`")
    @is_rss_admin()
    async def list_keywords(self, prefix, index: int):
        guild_config = self.bot.bot_config.get(str(prefix.guild.id), {})
        feeds = guild_config.get('rss_feeds', [])
        if 1 <= index <= len(feeds):
            feed_obj = feeds[index - 1]
            keywords = feed_obj.get('keywords', [])
            if keywords:
                await prefix.send(f"Keywords for feed #{index}: `{"`, `".join(keywords)}`")
            else:
                await prefix.send(f"Feed #{index} has no keywords.")
        else:
            await prefix.send(f"❌ Invalid feed index.")

async def setup(bot):
    await bot.add_cog(RSS(bot))