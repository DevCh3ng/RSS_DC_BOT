import discord
from discord.ext import commands
import aiohttp

class Price(commands.Cog):
    """A cog for checking cryptocurrency prices."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="price", help="Get the current price of a cryptocurrency. Usage: `-price <crypto>`")
    async def price(self, ctx, crypto: str):
        crypto_id = crypto.lower()
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 404:
                        await ctx.send(f"❌ **Error:** Could not find a cryptocurrency named `{crypto}`.")
                        return
                    response.raise_for_status()
                    data = await response.json()

            if crypto_id not in data:
                await ctx.send(f"❌ **Error:** Could not find price data for `{crypto}`.")
                return

            price_data = data[crypto_id]
            current_price = price_data.get('usd', 0)
            market_cap = price_data.get('usd_market_cap', 0)
            volume = price_data.get('usd_24h_vol', 0)
            change = price_data.get('usd_24h_change', 0)

            embed = discord.Embed(
                title=f"Price Information for {crypto.capitalize()}",
                color=discord.Color.blue()
            )
            embed.add_field(name="Current Price", value=f"${current_price:,.2f}", inline=True)
            embed.add_field(name="24h Change", value=f"{change:.2f}%", inline=True)
            embed.add_field(name="Market Cap", value=f"${market_cap:,.0f}", inline=False)
            embed.add_field(name="24h Volume", value=f"${volume:,.0f}", inline=False)
            
            await ctx.send(embed=embed)

        except aiohttp.ClientError as e:
            print(f"Price Command Error: {e}")
            await ctx.send("⚠️ Could not fetch cryptocurrency data. Please try again later.")

async def setup(bot):
    await bot.add_cog(Price(bot))
