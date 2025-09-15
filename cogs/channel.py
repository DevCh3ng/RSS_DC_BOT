import discord
from discord.ext import commands
class Channel(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    @commands.command(name = "setchannel")
    @commands.has_permissions(manage_channel = True)
    async def set_channel(self, prefix, channel: discord.TextChannel):
        guild_id = str(prefix.guild.id)
        if guild_id not in self.bot.bot_config:
            self.bot.bot_config[guild_id] = {}

        self.bot.bot_config[guild_id]["channel_id"] = channel.id
        self.bot.save_configs()
        await prefix.send(f"RSS updates will now be sent to {channel.mention}. ")

    @set_channel.error
    async def set_channel_error(self, prefix, error):
        if isinstance(error,commands.MissingPermissions):
            await prefix.send("You don't have permission. ")
        elif isinstance(error, commands.MissingRequiredArgument):
            await prefix.send("Please specify a channel. ")
async def setup(bot):
    await bot.add_cog(Channel(bot))
    

