import discord
from discord.ext import commands

class Admin(commands.Cog):
    """Admin Commands Cog"""

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        """Clears a specified number of messages."""
        await ctx.channel.purge(limit=amount)
        embed = discord.Embed(title="🧹 Cleared!", description=f"Cleared {amount} messages.", color=discord.Color.green())
        await ctx.send(embed=embed, delete_after=5)

async def setup(bot):
    """Required function for loading the cog."""
    await bot.add_cog(Admin(bot))
