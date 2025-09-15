import discord
from discord.ext import commands

class Help(commands.Cog):
    """Displays all usable commands using -help"""
    def __init__(self,bot):
        self.bot = bot

    @commands.command(name="help")
    async def help(self,prefix):
        embed = discord.Embed(
            title = "Bot Commands",
            description="Here are the usable commands: ",
            color = discord.Color.blue()
        )

        for cog_name, cog in self.bot.cogs.items():
            command_list = []
            for command in cog.get_commands():
                if not command.hidden:
                    command_list.append(f"-**{command.name}** - {command.help}")
                    if command_list:
                        embed.add_field(name=cog_name, value="\n".join(command_list),inline=False)
                    await prefix.send(embed=embed)
async def setup(bot):
    await bot.add_cog(Help(bot))
