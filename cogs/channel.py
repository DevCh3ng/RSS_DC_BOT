import discord
from discord.ext import commands

# Custom check for RSS admin permissions
def is_rss_admin():
    async def predicate(prefix):
        if prefix.author.guild_permissions.administrator:
            return True
        guild_config = prefix.bot.bot_config.get(str(prefix.guild.id), {})
        admin_roles_ids = guild_config.get('admin_roles', [])
        return any(role.id in admin_roles_ids for role in prefix.author.roles)
    return commands.check(predicate)

class Channel(commands.Cog):
    """Inviter will decide the bot's dedicated posting channel"""
    def __init__(self,bot):
        self.bot = bot

    @commands.command(name = "setchannel", help="Sets the default channel for RSS updates. Usage: `-setchannel #channel-name`")
    @is_rss_admin()
    async def set_channel(self, prefix, channel: discord.TextChannel):
        guild_id = str(prefix.guild.id)
        if guild_id not in self.bot.bot_config:
            self.bot.bot_config[guild_id] = {}

        self.bot.bot_config[guild_id]["channel_id"] = channel.id
        self.bot.save_configs()
        await prefix.send(f"Default RSS channel set to {channel.mention}. Feeds without a specific channel will post here.")

    @set_channel.error
    async def set_channel_error(self, prefix, error):
        if isinstance(error, commands.CheckFailure):
            await prefix.send("❌ You do not have the required role or administrator permissions to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await prefix.send("Please specify a channel.")

async def setup(bot):
    await bot.add_cog(Channel(bot))