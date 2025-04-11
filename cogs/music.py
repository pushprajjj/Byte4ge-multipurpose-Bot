import discord
from discord.ext import commands
import wavelink
from discord.ui import Button

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queue = {}

    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice is None:
                await ctx.send("You're not connected to a voice channel.")
                return False
            await ctx.author.voice.channel.connect(cls=wavelink.Player)
        return True

    def get_queue(self, guild_id):
        return self.queue.setdefault(guild_id, [])

    class MusicControlView(discord.ui.View):
        def __init__(self, vc, music_cog):
            super().__init__(timeout=300)
            self.vc = vc
            self.music_cog = music_cog

        @discord.ui.button(label="⏯️ Pause/Resume", style=discord.ButtonStyle.primary)
        async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.vc.paused:
                await self.vc.pause(False)
                await interaction.response.send_message("▶️ Resumed", ephemeral=True)
            else:
                await self.vc.pause(True)
                await interaction.response.send_message("⏸️ Paused", ephemeral=True)

        @discord.ui.button(label="⏭️ Skip", style=discord.ButtonStyle.success)
        async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.vc.stop()
            await interaction.response.send_message("⏭️ Skipped", ephemeral=True)
            
        
   

        @discord.ui.button(label="⏹️ Stop", style=discord.ButtonStyle.danger)
        async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.vc.disconnect()
            await interaction.response.send_message("⏹️ Stopped and disconnected", ephemeral=True)

    @commands.command(name='play')
    async def play(self, ctx: commands.Context, *, search: str):
        if not await self.ensure_voice(ctx):
            return

        vc: wavelink.Player = ctx.voice_client
        results = await wavelink.Playable.search(search)

        if not results:
            return await ctx.send("No results found.")

        track = results[0]
        queue = self.get_queue(ctx.guild.id)

        if not vc.playing and not vc.paused:
            await vc.play(track)
            await self.send_now_playing(ctx, track, vc)
        else:
            await vc.queue.put_wait(track)
            await ctx.send(f"➕ Added to queue: `{track.title}`")

    async def send_now_playing(self, ctx, track, vc):
        embed = discord.Embed(
            title="🎶 Now Playing",
            description=f"[{track.title}]({track.uri})",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Requested in #{ctx.channel.name}")
        embed.set_thumbnail(url=track.artwork)

        view = self.MusicControlView(vc, self)
        await ctx.send(embed=embed, view=view)

    @commands.command(name='queue')
    async def view_queue(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        if not queue:
            return await ctx.send("Queue is empty.")

        description = "\n".join(f"{i+1}. {t.title}" for i, t in enumerate(queue))
        embed = discord.Embed(title="🎶 Current Queue", description=description, color=discord.Color.dark_blue())
        await ctx.send(embed=embed)

    @commands.command(name='skip')
    async def skip_command(self, ctx):
        if ctx.voice_client is None or not ctx.voice_client.is_connected():
            return await ctx.send("Bot is not connected.")
        await ctx.voice_client.stop()
        await ctx.send("⏭️ Skipped!")

    @commands.command(name='stop')
    async def stop_command(self, ctx):
        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()
            self.queue[ctx.guild.id] = []
            await ctx.send("⏹️ Stopped and cleared queue.")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload):
        vc = payload.player
        track = payload.track
        reason = payload.reason.lower() if payload.reason else ""

        print(f"🔁 Track Ended: {track.title if track else 'Unknown'} | Reason: {reason}")

        # Don't autoplay if it was replaced or stopped manually
        if reason in ("replaced", "cleanup"):
            print("⏭️ Skipping handling due to manual skip/stop.")
            return

        if not vc or not track:
            print("❌ No player or track found.")
            return

        if not hasattr(vc, "autoplay_history"):
            vc.autoplay_history = []

        vc.autoplay_history.append(track.identifier)
        if len(vc.autoplay_history) > 10:
            vc.autoplay_history.pop(0)

        if not vc.queue.is_empty:
            next_track = await vc.queue.get_wait()
            print(f"📀 Playing next from queue: {next_track.title}")
            await vc.play(next_track)
            return

        # Autoplay logic
        query = f"ytsearch:{track.title} {track.author}"
        print(f"🔍 Searching for related tracks: {query}")
        results = await wavelink.Playable.search(query)

        if not results:
            print("⚠️ No related tracks found.")
            return

        filtered = [t for t in results if t.identifier not in vc.autoplay_history]
        if not filtered:
            print("⚠️ All related tracks already played.")
            return

        next_autoplay = filtered[0]
        print(f"▶️ Autoplaying: {next_autoplay.title}")
        await vc.play(next_autoplay)

    @commands.command(name='join')
    async def join(self, ctx: commands.Context):
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            return await ctx.send("Join a voice channel first!")

        channel = ctx.author.voice.channel
        if ctx.voice_client:
            return await ctx.send("I'm already connected.")
        await channel.connect(cls=wavelink.Player)
        await ctx.send(f"✅ Joined `{channel.name}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
