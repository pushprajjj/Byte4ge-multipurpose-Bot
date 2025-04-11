import discord
from discord.ext import commands
import wavelink

class MusicQueue:
    def __init__(self):
        self.queue = []

    def add(self, track):
        self.queue.append(track)

    def get_next(self):
        return self.queue.pop(0) if self.queue else None

    def clear(self):
        self.queue.clear()

    def is_empty(self):
        return len(self.queue) == 0

    def __len__(self):
        return len(self.queue)

    def __iter__(self):
        return iter(self.queue)


class MusicControlView(discord.ui.View):
    def __init__(self, vc: wavelink.Player, queue: MusicQueue):
        super().__init__(timeout=300)
        self.vc = vc
        self.queue = queue

    @discord.ui.button(label="⏸ Pause", style=discord.ButtonStyle.primary)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.vc.pause(True)
        await interaction.response.send_message("⏸️ Paused", ephemeral=True)

    @discord.ui.button(label="▶ Resume", style=discord.ButtonStyle.primary)
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.vc.pause(False)
        await interaction.response.send_message("▶ Resumed", ephemeral=True)

    @discord.ui.button(label="⏭ Skip", style=discord.ButtonStyle.success)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.queue.is_empty():
            next_track = self.queue.get_next()
            await self.vc.play(next_track)
            await interaction.response.send_message(f"⏭ Skipping to `{next_track.title}`", ephemeral=True)
        else:
            await self.vc.stop()
            await interaction.response.send_message("⏹ No more tracks in queue.", ephemeral=True)

    @discord.ui.button(label="⏹ Stop", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.queue.clear()
        await self.vc.stop()
        await interaction.response.send_message("⏹ Stopped and cleared queue.", ephemeral=True)


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues = {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]

    @commands.command(name='join')
    async def join(self, ctx: commands.Context):
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            return await ctx.send("Join a voice channel first!")

        channel = ctx.author.voice.channel

        if ctx.voice_client is not None:
            return await ctx.send("I'm already connected!")

        await channel.connect(cls=wavelink.Player)
        await ctx.send(f"Joined {channel.name} ✅")

    @commands.command(name='play')
    async def play(self, ctx: commands.Context, *, search: str):
        if ctx.voice_client is None:
            await ctx.invoke(self.join)

        vc: wavelink.Player = ctx.voice_client
        queue = self.get_queue(ctx.guild.id)

        results = await wavelink.Playable.search(search)
        if not results:
            return await ctx.send("No results found.")

        track = results[0]
        if not vc.playing:
            await vc.play(track)
            embed = discord.Embed(
                title="🎶 Now Playing",
                description=f"[{track.title}]({track.uri})",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}")
            view = MusicControlView(vc, queue)
            await ctx.send(embed=embed, view=view)
        else:
            queue.add(track)
            await ctx.send(f"🔒 Added to queue: `{track.title}`")

    @commands.command(name='queue')
    async def show_queue(self, ctx: commands.Context):
        queue = self.get_queue(ctx.guild.id)
        if queue.is_empty():
            return await ctx.send("📭 The queue is currently empty.")

        embed = discord.Embed(
            title="🎶 Music Queue",
            description="\n".join([f"{idx+1}. {track.title}" for idx, track in enumerate(queue)]),
            color=discord.Color.blurple()
        )
        await ctx.send(embed=embed)

    @commands.command(name='skip')
    async def skip_command(self, ctx: commands.Context):
        vc: wavelink.Player = ctx.voice_client
        queue = self.get_queue(ctx.guild.id)

        if not vc or not vc.is_playing():
            return await ctx.send("Nothing is playing!")

        if not queue.is_empty():
            next_track = queue.get_next()
            await vc.play(next_track)
            await ctx.send(f"⏭ Skipping to: `{next_track.title}`")
        else:
            await vc.stop()
            await ctx.send("⏹ No more tracks in queue.")

    @commands.command(name='stop')
    async def stop_command(self, ctx: commands.Context):
        vc: wavelink.Player = ctx.voice_client
        queue = self.get_queue(ctx.guild.id)

        queue.clear()
        await vc.stop()
        await vc.disconnect()
        await ctx.send("⏹ Music stopped and bot disconnected.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
