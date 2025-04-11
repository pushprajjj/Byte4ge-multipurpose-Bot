import discord
from discord.ext import commands
import wavelink

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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

        results = await wavelink.Playable.search(search)

        if not results:
            return await ctx.send("No results found.")

        track = results[0]

        await vc.play(track)
        await ctx.send(f"🎶 Now playing: `{track.title}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
