import discord
from discord.ext import commands

class Help(commands.Cog):
    """Displays all usable commands using -help"""
    def __init__(self,bot):
        self.bot = bot

    @commands.command(name="help")
    async def help(self, prefix):
        embed = discord.Embed(
            title="Bot Commands",
            description="Here are the usable commands:",
            color=discord.Color.blue()
        )

        for cog_name, cog in self.bot.cogs.items():
            if cog_name == 'Help':
                continue
            
            command_list = []
            for command in cog.get_commands():
                if command.hidden:
                    continue
                
                entry = f"-**{command.name}** - {command.help}"
                if isinstance(command, commands.Group):
                    sub_commands = []
                    for subcommand in command.commands:
                        if not subcommand.hidden:
                            sub_commands.append(f"  - `{subcommand.name}`: {subcommand.help}")
                    if sub_commands:
                        entry += "\n" + "\n".join(sub_commands)

                command_list.append(entry)

            if command_list:
                embed.add_field(name=cog_name, value="\n".join(command_list), inline=False)

        await prefix.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))