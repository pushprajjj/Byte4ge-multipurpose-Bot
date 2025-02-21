import discord
from discord import app_commands
from discord.ext import commands

class Slash(commands.Cog):
    """Slash Commands Cog"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Shows bot latency.")
    async def ping(self, interaction: discord.Interaction):
        """Slash command: Ping"""
        latency = round(self.bot.latency * 1000)  # Convert to ms
        embed = discord.Embed(title="🏓 Pong!", description=f"Latency: **{latency}ms**", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="help", description="Shows a list of available commands.")
    async def help(self, interaction: discord.Interaction):
        """Slash command: Help"""
        embed = discord.Embed(title="📜 Help Menu", description="List of available commands:", color=discord.Color.green())
        embed.add_field(name="/ping", value="🏓 Shows bot latency.", inline=False)
        embed.add_field(name="/play [url]", value="🎶 Plays music from a YouTube URL.", inline=False)
        embed.add_field(name="/stop", value="⏹️ Stops the music.", inline=False)
        embed.add_field(name="/leave", value="🔌 Disconnects the bot from the voice channel.", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="play", description="Plays a song from a YouTube URL.")
    async def play(self, interaction: discord.Interaction, url: str):
        """Slash command: Play"""
        if interaction.user.voice:
            if not interaction.guild.voice_client:
                await interaction.user.voice.channel.connect()

            embed = discord.Embed(title="🎶 Now Playing", description=f"**{url}**", color=discord.Color.green())
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ You must be in a voice channel!", ephemeral=True)

    @app_commands.command(name="stop", description="Stops the current song.")
    async def stop(self, interaction: discord.Interaction):
        """Slash command: Stop music"""
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            await interaction.guild.voice_client.stop()
            embed = discord.Embed(title="⏹️ Stopped", description="Music playback has been stopped.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ No music is currently playing.", ephemeral=True)

    @app_commands.command(name="leave", description="Disconnects the bot from the voice channel.")
    async def leave(self, interaction: discord.Interaction):
        """Slash command: Leave VC"""
        if interaction.guild.voice_client:
            if interaction.guild.voice_client.is_connected():
                await interaction.guild.voice_client.disconnect()
            embed = discord.Embed(title="🔌 Disconnected", description="Left the voice channel.", color=discord.Color.greyple())
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("❌ Bot is not in a voice channel.", ephemeral=True)

async def setup(bot):
    """Required function for loading the cog."""
    await bot.add_cog(Slash(bot))
