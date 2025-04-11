import discord
from discord.ext import commands
import wavelink


class MusicControlView(discord.ui.View):
    def __init__(self, vc: wavelink.Player):
        super().__init__(timeout=300)
        self.vc = vc

    @discord.ui.button(label="⏯️ Pause/Resume", style=discord.ButtonStyle.primary)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.playing:
            if self.vc.paused:
                await self.vc.pause(False)
                await interaction.response.send_message("▶️ Resumed", ephemeral=True)
            else:
                await self.vc.pause(True)
                await interaction.response.send_message("⏸️ Paused", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing is playing!", ephemeral=True)

    @discord.ui.button(label="⏭️ Skip", style=discord.ButtonStyle.success)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.playing:
            await self.vc.stop()
            await interaction.response.send_message("⏭️ Skipped", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing to skip!", ephemeral=True)

    @discord.ui.button(label="⏹️ Stop", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.vc.playing:
            await self.vc.stop()
            await self.vc.disconnect()
            await interaction.response.send_message("⏹️ Stopped and disconnected.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing to stop!", ephemeral=True)


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='join')
    async def join(self, ctx: commands.Context):
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            return await ctx.send("⚠️ Join a voice channel first!")

        channel = ctx.author.voice.channel

        if ctx.voice_client is not None:
            return await ctx.send("🔊 I'm already connected!")

        await channel.connect(cls=wavelink.Player)
        await ctx.send(f"✅ Joined `{channel.name}`")

    @commands.command(name='play')
    async def play(self, ctx: commands.Context, *, search: str):
        if ctx.voice_client is None:
            await ctx.invoke(self.join)

        vc: wavelink.Player = ctx.voice_client

        # Search for the track
        results = await wavelink.Playable.search(search)
        if not results:
            return await ctx.send("❌ No results found.")

        track = results[0]
        await vc.play(track)

        # Create embed
        embed = discord.Embed(
            title="🎶 Now Playing",
            description=f"[{track.title}]({track.uri})",
            color=discord.Color.blurple()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.set_footer(text=f"Requested in #{ctx.channel.name}")

        # Create view with control buttons
        view = MusicControlView(vc)
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
