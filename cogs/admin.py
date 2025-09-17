import discord
from discord.ext import commands

class Admin(commands.Cog):
    """Cog for server administration commands related to the bot."""
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="rssadmin", help="Manage which roles can administer RSS feeds.", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def rssadmin(self, prefix):
        await prefix.send("Use `-rssadmin <add|remove|list> <role>` to manage RSS admin roles.")

    @rssadmin.command(name="add", help="Allow a role to manage RSS feeds. Usage: `-rssadmin add @role`")
    @commands.has_permissions(administrator=True)
    async def add_admin_role(self, prefix, role: discord.Role):
        guild_config = self.bot.bot_config.setdefault(str(prefix.guild.id), {})
        admin_roles = guild_config.setdefault('admin_roles', [])
        
        if role.id in admin_roles:
            await prefix.send(f"⚠️ The role {role.mention} is already an RSS admin.")
            return

        admin_roles.append(role.id)
        self.bot.save_configs()
        await prefix.send(f"✅ The role {role.mention} can now manage RSS feeds.")
        await self.bot.log_action(self.bot, prefix.guild, f"Role {role.mention} was given RSS admin permissions.", prefix.author)

    @rssadmin.command(name="remove", help="Remove a role's ability to manage RSS feeds. Usage: `-rssadmin remove @role`")
    @commands.has_permissions(administrator=True)
    async def remove_admin_role(self, prefix, role: discord.Role):
        if prefix.guild.owner == prefix.author and role in prefix.guild.owner.roles:
             await prefix.send("❌ You cannot remove a role from the server owner.")
             return

        guild_config = self.bot.bot_config.get(str(prefix.guild.id), {})
        admin_roles = guild_config.get('admin_roles', [])

        if role.id not in admin_roles:
            await prefix.send(f"⚠️ The role {role.mention} is not an RSS admin.")
            return

        admin_roles.remove(role.id)
        self.bot.save_configs()
        await prefix.send(f"✅ The role {role.mention} can no longer manage RSS feeds.")
        await self.bot.log_action(self.bot, prefix.guild, f"Role {role.mention} was removed from RSS admin permissions.", prefix.author)

    @rssadmin.command(name="list", help="List roles that can manage RSS feeds.")
    @commands.has_permissions(administrator=True)
    async def list_admin_roles(self, prefix):
        guild_config = self.bot.bot_config.get(str(prefix.guild.id), {})
        admin_roles_ids = guild_config.get('admin_roles', [])

        if not admin_roles_ids:
            await prefix.send("No specific roles are set for RSS administration. Only server admins can manage feeds.")
            return

        message = "**Authorized RSS Admin Roles:**\n"
        for role_id in admin_roles_ids:
            role = prefix.guild.get_role(role_id)
            if role:
                message += f"- {role.mention}\n"
        
        await prefix.send(message)

    @commands.group(name="channelconfig", help="Configure channel-specific settings for the bot.", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def channelconfig(self, prefix):
        await prefix.send("Use `-channelconfig <limit|allow_multiple> <#channel> <value>` to configure a channel.")

    @channelconfig.command(name="limit", help="Set the max number of RSS feeds for a channel. Usage: `-channelconfig limit #channel <count>`")
    @commands.has_permissions(administrator=True)
    async def set_channel_limit(self, prefix, channel: discord.TextChannel, limit: int):
        if limit < 0:
            await prefix.send("❌ Limit cannot be negative.")
            return
        
        guild_config = self.bot.bot_config.setdefault(str(prefix.guild.id), {})
        channel_configs = guild_config.setdefault('channel_configs', {})
        channel_settings = channel_configs.setdefault(str(channel.id), {})
        channel_settings['limit'] = limit
        self.bot.save_configs()
        await prefix.send(f"✅ The RSS feed limit for {channel.mention} is now **{limit}**.")
        await self.bot.log_action(self.bot, prefix.guild, f"RSS feed limit for {channel.mention} was set to **{limit}**.", prefix.author)

    @channelconfig.command(name="allow_multiple", help="Allow/disallow multiple feeds in a channel. Usage: `-channelconfig allow_multiple #channel <true|false>`")
    @commands.has_permissions(administrator=True)
    async def set_channel_multiple(self, prefix, channel: discord.TextChannel, value: bool):
        guild_config = self.bot.bot_config.setdefault(str(prefix.guild.id), {})
        channel_configs = guild_config.setdefault('channel_configs', {})
        channel_settings = channel_configs.setdefault(str(channel.id), {})
        channel_settings['allow_multiple'] = value
        self.bot.save_configs()
        status = "now allows" if value else "no longer allows"
        await prefix.send(f"✅ {channel.mention} {status} multiple RSS feeds.")
        await self.bot.log_action(self.bot, prefix.guild, f"Channel {channel.mention} {status} multiple RSS feeds.", prefix.author)

    @commands.group(name="adminlog", help="Configure the audit log for bot actions.", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def adminlog(self, prefix):
        await prefix.send("Use `-adminlog <set|disable> <#channel>` to configure the audit log.")

    @adminlog.command(name="set", help="Set the channel for audit logs. Usage: `-adminlog set #channel`")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, prefix, channel: discord.TextChannel):
        guild_config = self.bot.bot_config.setdefault(str(prefix.guild.id), {})
        guild_config['log_channel'] = channel.id
        self.bot.save_configs()
        await prefix.send(f"✅ Bot actions will now be logged in {channel.mention}.")
        await self.bot.log_action(self.bot, prefix.guild, f"Audit log channel was set to {channel.mention}.", prefix.author)

    @adminlog.command(name="disable", help="Disable the audit log.")
    @commands.has_permissions(administrator=True)
    async def disable_log_channel(self, prefix):
        guild_config = self.bot.bot_config.setdefault(str(prefix.guild.id), {})
        if 'log_channel' in guild_config:
            del guild_config['log_channel']
            self.bot.save_configs()
            await prefix.send("✅ Audit log disabled.")
            await self.bot.log_action(self.bot, prefix.guild, "Audit log was disabled.", prefix.author)
        else:
            await prefix.send("⚠️ Audit log is not currently enabled.")

async def setup(bot):
    await bot.add_cog(Admin(bot))
