import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL
from discord.ui import Button, View
import asyncio
import aiohttp
import urllib.parse
import re

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}  # Dictionary to store music queues for each server
        self.disconnect_timers = {}  # Dictionary to store disconnect timers for each server
        self.current_url = {} 

    async def get_youtube_suggestions(self, query: str) -> list[str]:
        """Get YouTube search suggestions for a query."""
        if not query:
            return []
        
        try:
            # Encode the query for URL
            encoded_query = urllib.parse.quote(query)
            
            # Use YouTube's suggestion API
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://suggestqueries.google.com/complete/search?client=youtube&ds=yt&q={encoded_query}"
                ) as response:
                    if response.status == 200:
                        data = await response.text()
                        # Extract suggestions from the response
                        suggestions = re.findall(r'"([^"]*)"', data)[1:6]  # Get up to 5 suggestions
                        return suggestions
                    return []
        except Exception:
            return []

    async def song_autocomplete(
        self, 
        interaction: discord.Interaction, 
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """Autocomplete callback for the play command."""
        suggestions = await self.get_youtube_suggestions(current)
        return [
            app_commands.Choice(name=suggestion[:100], value=suggestion)  # Discord limits name to 100 characters
            for suggestion in suggestions
        ]

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

    async def play_song(self, ctx, query):
        """Common function for playing songs (used by both prefix and slash commands)."""
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
    async def play(self, ctx, *, query=None):
        """Plays a song from YouTube or adds it to the queue."""
        async with ctx.typing():
            await self.play_song(ctx, query)

    @app_commands.command(name="play", description="Play a song from YouTube")
    @app_commands.describe(query="Song name or YouTube URL")
    @app_commands.autocomplete(query=song_autocomplete)
    async def play_slash(self, interaction: discord.Interaction, query: str):
        """Slash command to play music."""
        await interaction.response.defer()
        ctx = await commands.Context.from_interaction(interaction)
        await self.play_song(ctx, query)

    @app_commands.command(name="skip", description="Skip the current song")
    async def skip_slash(self, interaction: discord.Interaction):
        """Slash command to skip the current song."""
        await interaction.response.defer()
        ctx = await commands.Context.from_interaction(interaction)
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await interaction.followup.send("⏭️ Skipped the current song!")
            await self.check_queue(ctx)
        else:
            await interaction.followup.send("❌ No song is currently playing!", ephemeral=True)

    @app_commands.command(name="queue", description="Show the current music queue")
    async def queue_slash(self, interaction: discord.Interaction):
        """Slash command to show the queue."""
        await interaction.response.defer()
        if interaction.guild.id not in self.queues or not self.queues[interaction.guild.id]:
            await interaction.followup.send("Queue is empty!", ephemeral=True)
            return

        queue_list = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(self.queues[interaction.guild.id])])
        embed = discord.Embed(
            title="🎵 Current Queue",
            description=queue_list,
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="pause", description="Pause the current song")
    async def pause_slash(self, interaction: discord.Interaction):
        """Slash command to pause music."""
        await interaction.response.defer()
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.pause()
            await interaction.followup.send("⏸️ Paused the music!")
        else:
            await interaction.followup.send("❌ No music is playing!", ephemeral=True)

    @app_commands.command(name="resume", description="Resume the paused song")
    async def resume_slash(self, interaction: discord.Interaction):
        """Slash command to resume music."""
        await interaction.response.defer()
        if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
            interaction.guild.voice_client.resume()
            await interaction.followup.send("▶️ Resumed the music!")
        else:
            await interaction.followup.send("❌ No music is paused!", ephemeral=True)

    @app_commands.command(name="stop", description="Stop playing and clear the queue")
    async def stop_slash(self, interaction: discord.Interaction):
        """Slash command to stop music."""
        await interaction.response.defer()
        if interaction.guild.voice_client:
            self.queues[interaction.guild.id] = []
            interaction.guild.voice_client.stop()
            await interaction.guild.voice_client.disconnect()
            await interaction.followup.send("⏹️ Stopped the music and cleared the queue!")
        else:
            await interaction.followup.send("❌ Not connected to a voice channel!", ephemeral=True)

    @app_commands.command(name="leave", description="Make the bot leave the voice channel")
    async def leave_slash(self, interaction: discord.Interaction):
        """Slash command to make the bot leave."""
        await interaction.response.defer()
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            await interaction.followup.send("👋 Left the voice channel!")
        else:
            await interaction.followup.send("❌ Not in a voice channel!", ephemeral=True)

    # Keep the original prefix commands
    @commands.command()
    async def skip(self, ctx):
        """Skips the current song."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Skipped!")
            await self.check_queue(ctx)

    @commands.command()
    async def queue(self, ctx):
        """Shows the current queue."""
        if ctx.guild.id not in self.queues or not self.queues[ctx.guild.id]:
            await ctx.send("Queue is empty!")
            return

        queue_list = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(self.queues[ctx.guild.id])])
        embed = discord.Embed(title="🎵 Current Queue", description=queue_list, color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command()
    async def pause(self, ctx):
        """Pauses the current song."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Paused!")

    @commands.command()
    async def resume(self, ctx):
        """Resumes the paused song."""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Resumed!")

    @commands.command()
    async def stop(self, ctx):
        """Stops playing and clears the queue."""
        if ctx.voice_client:
            self.queues[ctx.guild.id] = []
            ctx.voice_client.stop()
            await ctx.voice_client.disconnect()
            await ctx.send("⏹️ Stopped and cleared queue!")

    @commands.command()
    async def leave(self, ctx):
        """Makes the bot leave the voice channel."""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Left the voice channel!")

async def setup(bot):
    """Load the Music cog."""
    await bot.add_cog(Music(bot))
