import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}  # Dictionary to store music queues for each server

    # YouTube DL options
    ytdl_options = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',  # 🔹 This enables YouTube search when no URL is provided
        'source_address': '0.0.0.0',
        'cookiefile': 'cookies.txt',  # Path to your cookies file
    }

    # FFmpeg options
    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    # YouTube DL instance
    ytdl = YoutubeDL(ytdl_options)

    def check_queue(self, ctx):
        """Checks and plays the next song in the queue."""
        if ctx.guild.id in self.queues and self.queues[ctx.guild.id]:
            song = self.queues[ctx.guild.id].pop(0)
            source = song['source']
            ctx.voice_client.play(source, after=lambda e: self.check_queue(ctx))

            embed = discord.Embed(
                title="🎶 Now Playing",
                description=f"**{song['title']}**",
                color=discord.Color.green()
            )
            return ctx.send(embed=embed)

    @commands.command()
    async def play(self, ctx, *, query=None):
        """Plays a song from YouTube or adds it to the queue."""
        async with ctx.typing():
            if query is None:
                embed = discord.Embed(
                    title="❌ Error",
                    description="You need to provide a song name or URL!",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)

            if query.startswith('http') and 'playlist' in query:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Playlists are not supported. Please provide a single song URL or name.",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)

            if not ctx.author.voice:
                embed = discord.Embed(
                    title="❌ Error",
                    description="You need to be in a voice channel to play music!",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)

            # Connect to voice if not connected
            if not ctx.voice_client:
                await ctx.author.voice.channel.connect()

            try:
                info = self.ytdl.extract_info(query, download=False)
                if 'entries' in info:
                    entries = info['entries']
                else:
                    entries = [info]

                for entry in entries:
                    url2 = entry['url']
                    source = discord.FFmpegOpusAudio(url2, **self.ffmpeg_options)
                    song = {'source': source, 'title': entry['title']}

                    voice = ctx.voice_client
                    if not voice.is_playing():
                        voice.play(source, after=lambda _: self.check_queue(ctx))

                        embed = discord.Embed(
                            title="🎶 Now Playing",
                            description=f"**{entry['title']}**",
                            color=discord.Color.green()
                        )
                        await ctx.send(embed=embed)
                    else:
                        if ctx.guild.id not in self.queues:
                            self.queues[ctx.guild.id] = []
                        self.queues[ctx.guild.id].append(song)

                        embed = discord.Embed(
                            title="📥 Added to Queue",
                            description=f"**{entry['title']}**",
                            color=discord.Color.blue()
                        )
                        await ctx.send(embed=embed)

            except Exception as e:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Failed to play song: `{e}`",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)


    @commands.command()
    async def skip(self, ctx):
        """Skips the current song and plays the next one in the queue."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()  # Stop the current song
            self.check_queue(ctx)  # Play the next song if available

            embed = discord.Embed(
                title="⏭️ Skipped",
                description="Skipping to the next song in the queue...",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No song is currently playing.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command()
    async def queue(self, ctx):
        """Displays the current music queue."""
        if ctx.guild.id in self.queues and self.queues[ctx.guild.id]:
            queue_list = [f"{idx + 1}. {song['title']}" for idx, song in enumerate(self.queues[ctx.guild.id])]
            embed = discord.Embed(
                title="📜 Music Queue",
                description="\n".join(queue_list),
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="The queue is currently empty.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command()
    async def resume(self, ctx):
        """Resumes the current song if paused."""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            embed = discord.Embed(
                title="▶️ Resumed",
                description="Music playback has been resumed.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No song is currently paused.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command()
    async def pause(self, ctx):
        """Pauses the current song."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            embed = discord.Embed(
                title="⏸️ Paused",
                description="Music playback has been paused.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No song is currently playing.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    @commands.command()
    async def stop(self, ctx):
        """Stops music playback."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            embed = discord.Embed(title="⏹️ Stopped", description="Music playback has been stopped.", color=discord.Color.red())
            await ctx.send(embed=embed)

    @commands.command()
    async def leave(self, ctx):
        """Disconnects from the voice channel."""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            embed = discord.Embed(title="🔌 Disconnected", description="Left the voice channel.", color=discord.Color.greyple())
            await ctx.send(embed=embed)

# Adding the cog properly
async def setup(bot):
    await bot.add_cog(Music(bot))
