import discord
from discord.ext import commands

class General(commands.Cog):
    """General Commands Cog"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        """Shows bot latency."""
        latency = round(self.bot.latency * 1000)  # Convert to ms
        embed = discord.Embed(title="🏓 Pong!", description=f"Latency: **{latency}ms**", color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command(aliases=["helpme"])
    async def help(self, ctx):
        """Custom Help Command"""
        embed = discord.Embed(title="📜 Help Menu", description="List of available commands:", color=discord.Color.green())
        embed.add_field(name=".join", value="Makes the bot join your voice channel.", inline=False)
        embed.add_field(name=".leave", value="Makes the bot leave the voice channel.", inline=False)
        embed.add_field(name=".play <url> or Song Name", value="Plays music from a YouTube URL or search query.", inline=False)
        embed.add_field(name=".pause", value="Pauses the current song.", inline=False)
        embed.add_field(name=".resume", value="Resumes the paused song.", inline=False)
        embed.add_field(name=".stop", value="Stops the current song and clears the queue.", inline=False)
        embed.add_field(name=".skip", value="Skips the current song and plays the next one in the queue.", inline=False)
        embed.add_field(name=".queue", value="Displays the current queue.", inline=False)
        embed.add_field(name=".hello", value="Say hello to the bot.", inline=False)
        embed.add_field(name=".roll", value="Roll a dice.", inline=False)
        embed.add_field(name=".ping", value="Check the bot's latency.", inline=False)
        embed.add_field(name=".clear <amount>", value="Clear messages (requires Manage Messages permission).", inline=False)
        embed.add_field(name="mention bot to ask question and talk with.", value="Developer: Mr.MorningStar😎", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    """Required function for loading the cog."""
    await bot.add_cog(General(bot))
