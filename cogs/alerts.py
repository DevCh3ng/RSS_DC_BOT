import discord 
from discord.ext import tasks, commands
import aiohttp

class Alerts(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.check_prices.start()

    def cog_unload(self):
        self.check_prices.cancel()

    @tasks.loop(seconds=60)
    async def check_prices(self):
        await self.bot.wait_until_ready()
        if not self.bot.active_alerts:
            return

        crypto_ids = {alert['crypto'] for alert in self.bot.active_alerts}
        if not crypto_ids:
            return

        id_str = ",".join(crypto_ids)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={id_str}&vs_currencies=usd"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()  # Raise an exception for bad status codes
                    prices = await response.json()
                    print(f"Fetched prices: {prices}")

        except aiohttp.ClientError as e:
            print(f"Error fetching prices: {e}")
            return

        triggered_alerts = []
        for alert in self.bot.active_alerts:
            crypto = alert['crypto']
            if crypto not in prices or 'usd' not in prices[crypto]:
                continue

            curr_price = prices[crypto]['usd']
            condition = alert['condition']
            target_price = alert['price']

            if (condition == '>' and curr_price > target_price) or \
               (condition == '<' and curr_price < target_price):
                
                print(f"ALERT TRIGGERED: User {alert['user_id']} for {crypto} {condition} {target_price}")
                try:
                    user = await self.bot.fetch_user(alert['user_id'])
                    message = (
                        f"🔔 **Price Alert!** 🔔\n\n"
                        f"Your alert for **{crypto.capitalize()}** was triggered.\n"
                        f"Target: {condition} ${target_price:,.2f}\n"
                        f"Current Price: ${curr_price:,.2f}"
                    )
                    await user.send(message)
                    triggered_alerts.append(alert)
                except discord.NotFound:
                    print(f"User {alert['user_id']} not found.")
                except discord.Forbidden:
                    print(f"Cannot send DM to user {alert['user_id']}.")

        if triggered_alerts:
            self.bot.active_alerts[:] = [alert for alert in self.bot.active_alerts if alert not in triggered_alerts]
            self.bot.save_alerts()

    @commands.group(invoke_without_command=True, help="Manages price alerts for cryptocurrencies.")
    async def alert(self,prefix):
        await prefix.send("Alert command. Use `-alert add <crypto> <condition> <price>`")

    @alert.command (name="add", help="Adds a new price alert. Usage: `-alert add <crypto> <condition> <price>`")
    async def add_alert(self,prefix, crypto: str, condition: str, price: float):
        crypto_id = crypto.lower()
        valid_url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(valid_url) as response:
                    if response.status == 404:
                        await prefix.send(f"❌ **Error:** Could not find a cryptocurrency named `{crypto}`.")
                        return
                    response.raise_for_status()
        except aiohttp.ClientError as e:
            print(f"Crypto Validation Error: {e}")
            await prefix.send("⚠️ Could not fetch cryptocurrency data. Please try again later.")
            return

        if condition not in ['>', '<']:
            await prefix.send("Invalid condition. Please use `<` or `>`.")
            return
        
        new_alert={
            'user_id' : prefix.author.id,
            'crypto' : crypto.lower(),
            'condition' : condition,
            'price' : price
        }
        self.bot.active_alerts.append(new_alert)
        self.bot.save_alerts()
        await prefix.send(f"✅ Alert set: I will notify you when **{crypto}** is **{condition} ${price:,.2f}**.")
    
    @alert.command(name="list", help="Lists your active price alerts.")
    async def list_alerts(self,prefix):
        user_alerts = []
        for i, alert in enumerate(self.bot.active_alerts):
            if alert['user_id'] == prefix.author.id:
                user_alerts.append((i,alert))

        if not user_alerts:
            await prefix.send("You have no active alerts. Set one with `-alert add <crypto> <condition> <price>`.")
            return

        message = "Your active alerts:\n```\n"
        for alert_id, alert in user_alerts:
            crypto = alert['crypto'].capitalize()
            condition = alert['condition']
            price = f"${alert['price']:,.2f}"
            message += f"ID: {alert_id} | {crypto} {condition} {price}\n"
        message += "```\nUse the ID to remove an alert."
        await prefix.send(message)

    @alert.command(name="remove", help="Removes a price alert by its ID. Usage: `-alert remove <ID>`")
    async def remove_alert(self,prefix, alert_id: int):
        if not(0 <= alert_id < len(self.bot.active_alerts)):
            await prefix.send(f"Error: Invalid ID. There is no alert with ID {alert_id}. Use `-alert list` to see valid IDs")
            return 
        
        if self.bot.active_alerts[alert_id]['user_id'] != prefix.author.id:
            await prefix.send("Error: You can only remove your own alerts.")
            return
            
        removed = self.bot.active_alerts.pop(alert_id)
        self.bot.save_alerts()
        crypto = removed['crypto'].capitalize()
        condition = removed['condition']
        price = f"${removed['price']:,.2f}"
        await prefix.send(f"✅ Alert removed: Your alert for **{crypto} {condition} {price}** has been deleted")

async def setup(bot):
    await bot.add_cog(Alerts(bot))