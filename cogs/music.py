import discord
from discord.ext import commands, tasks
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL
from discord.ui import Button, View
import asyncio

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}  # Dictionary to store music queues for each server
        self.disconnect_timers = {}  # Dictionary to store disconnect timers for each server
        self.current_url = {} 

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

    async def check_queue(self, ctx):
        """Checks and plays the next song in the queue."""
        if ctx.guild.id in self.queues and self.queues[ctx.guild.id]:
            song = self.queues[ctx.guild.id].pop(0)
            source = song['source']
            ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.check_queue(ctx)))

            embed = discord.Embed(
                title="🎶 Now Playing",
                description=f"**{song['title']}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed, view=self.create_player_controls(ctx))
        else:
            await self.start_disconnect_timer(ctx)

    def create_player_controls(self, ctx):
        """Creates a view with player control buttons."""
        view = View()

        button_pause = Button(label="Pause", style=discord.ButtonStyle.primary)
        button_resume = Button(label="Resume", style=discord.ButtonStyle.primary)
        button_skip = Button(label="Skip", style=discord.ButtonStyle.primary)
        button_stop = Button(label="Stop", style=discord.ButtonStyle.danger)

        async def pause_callback(interaction):
            await self.pause(ctx)
            await interaction.response.defer()

        async def resume_callback(interaction):
            await self.resume(ctx)
            await interaction.response.defer()

        async def skip_callback(interaction):
            await self.skip(ctx)
            await interaction.response.defer()

        async def stop_callback(interaction):
            await self.stop(ctx)
            await interaction.response.defer()

        button_pause.callback = pause_callback
        button_resume.callback = resume_callback
        button_skip.callback = skip_callback
        button_stop.callback = stop_callback

        view.add_item(button_pause)
        view.add_item(button_resume)
        view.add_item(button_skip)
        view.add_item(button_stop)

        return view

    async def start_disconnect_timer(self, ctx):
        """Starts a timer to disconnect the bot if no song is played for 1 minute."""
        if ctx.guild.id in self.disconnect_timers:
            self.disconnect_timers[ctx.guild.id].cancel()

        async def disconnect():
            await asyncio.sleep(60)
            if ctx.voice_client and not ctx.voice_client.is_playing():
                await ctx.voice_client.disconnect()
                embed = discord.Embed(
                    title="🔌 Disconnected",
                    description="No song was played for 1 minute. Disconnecting from the voice channel. Jarurat pare to yad krna. 😊[.play] apna command h",
                    color=discord.Color.greyple()
                )
                await ctx.send(embed=embed)

        self.disconnect_timers[ctx.guild.id] = self.bot.loop.create_task(disconnect())

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
                    
                    self.current_url[ctx.guild.id] = url2

                    voice = ctx.voice_client
                    if not voice.is_playing():
                        voice.play(source, after=lambda _: self.bot.loop.create_task(self.check_queue(ctx)))

                        embed = discord.Embed(
                            title="🎶 Now Playing",
                            description=f"**{entry['title']}**",
                            color=discord.Color.green()
                        )
                        await ctx.send(embed=embed, view=self.create_player_controls(ctx))
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

            await self.start_disconnect_timer(ctx)

    @commands.command()
    async def skip(self, ctx):
        """Skips the current song and plays the next one in the queue."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()  # Stop the current song
            await self.check_queue(ctx)  # Play the next song if available

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

        await self.start_disconnect_timer(ctx)

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

        await self.start_disconnect_timer(ctx)

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

        await self.start_disconnect_timer(ctx)

    @commands.command()
    async def stop(self, ctx):
        """Stops music playback."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            embed = discord.Embed(title="⏹️ Stopped", description="Music playback has been stopped.", color=discord.Color.red())
            await ctx.send(embed=embed)

        await self.start_disconnect_timer(ctx)

    @commands.command()
    async def leave(self, ctx):
        """Disconnects from the voice channel."""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            embed = discord.Embed(title="🔌 Disconnected", description="Left the voice channel.", color=discord.Color.greyple())
            await ctx.send(embed=embed)

    @commands.command()
    async def seek(self, ctx, seconds: int):
        """Seeks the current song by the specified number of seconds."""
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            embed = discord.Embed(
                title="❌ Error",
                description="No song is currently playing.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        # Retrieve stored song URL
        song_url = self.current_url.get(ctx.guild.id)
        if not song_url:
            embed = discord.Embed(
                title="❌ Error",
                description="Cannot seek, as the current song URL is unknown.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        # Get current playback position (estimate)
        if ctx.voice_client.source and hasattr(ctx.voice_client.source, "_process"):
            try:
                # Extract the original seek time from FFmpeg args
                current_time = float(ctx.voice_client.source._process.args[2].split('=')[1])
            except:
                current_time = 0
        else:
            current_time = 0

        # Calculate new seek time
        seek_time = max(0, current_time + seconds)

        # Stop current playback
        ctx.voice_client.stop()

        # Recreate the FFmpeg source with seek time
        ffmpeg_opts = {
            'before_options': f"-ss {seek_time} -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            'options': '-vn'
        }
        new_source = discord.FFmpegPCMAudio(song_url, **ffmpeg_opts)
        
        # Play the new source
        ctx.voice_client.play(new_source, after=lambda _: self.bot.loop.create_task(self.check_queue(ctx)))

        # Confirm seek operation
        embed = discord.Embed(
            title="⏩ Seek",
            description=f"Seeked to `{seek_time}` seconds.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)





# Adding the cog properly
async def setup(bot):
    await bot.add_cog(Music(bot))
