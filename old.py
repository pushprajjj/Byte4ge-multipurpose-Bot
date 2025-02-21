import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from yt_dlp import YoutubeDL
import asyncio
import requests
import random

# Enable intents
intents = discord.Intents.default()
intents.members = True  # Enable Server Members Intent
intents.message_content = True  # Enable Message Content Intent

# Initialize the bot with a command prefix and intents
# bot = commands.Bot(command_prefix=".", intents=intents)
bot = commands.Bot(
    command_prefix='.',
    intents=discord.Intents.all(),
    allowed_mentions=discord.AllowedMentions(
        everyone=False,
        roles=False
    ),
    activity=discord.CustomActivity(name='byte4ge.com | Weaving Web Magic With Excellence.', emoji="😎"),
    help_command=None  # Disable the default help command
)



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
    'default_search': 'auto',
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

# Queue for each server
queues = {}

# Function to check if there is a queue for the server
def check_queue(ctx, id):
    if id in queues and queues[id]:  # Check if the queue exists and is not empty
        voice = ctx.guild.voice_client
        song = queues[id].pop(0)  # Get the first song in the queue
        source = song['source']  # Extract the FFmpegPCMAudio object
        voice.play(source, after=lambda x=None: check_queue(ctx, id))
        
        
        # Command: Respond to !hello
@bot.command()
async def hello(ctx):
    await ctx.send(f'Hello, {ctx.author.mention}!')

# Command: Roll a dice
@bot.command()
async def roll(ctx):
    result = random.randint(1, 6)
    await ctx.send(f'🎲 You rolled: **{result}**')

# Ping command
@bot.command()
async def ping(ctx):
    await ctx.send(f'🏓 Pong! Latency: {round(bot.latency * 1000)}ms')

# Clear messages command
@bot.command()
@commands.has_permissions(manage_messages=True)  # Only users with "Manage Messages" permission can use this
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)  # +1 to include the command message
    await ctx.send(f'🧹 Cleared {amount} messages!', delete_after=5)  # Delete the confirmation after 5 seconds

# Command: Join the voice channel
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"Joined {channel}!")
    else:
        await ctx.send("You are not in a voice channel!")

# Command: Leave the voice channel
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.guild.voice_client.disconnect()
        await ctx.send("Left the voice channel.")
    else:
        await ctx.send("I'm not in a voice channel!")

# Command: Play music from YouTube
@bot.command()
async def play(ctx, *, url):
    if ctx.author.voice:
        # Join the voice channel if not already connected
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        # Extract audio from YouTube
        with ytdl as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                if 'entries' in info:
                    info = info['entries'][0]
                url2 = info['url']
                print(f"Extracted URL: {url2}")  # Debug: Print the extracted URL

                # Debug: Print FFmpeg command
                ffmpeg_cmd = f"ffmpeg -i '{url2}' -f s16le -ar 48000 -ac 2 pipe:1"
                print(f"FFmpeg Command: {ffmpeg_cmd}")

                source = FFmpegPCMAudio(url2, **ffmpeg_options)
                voice = ctx.guild.voice_client

                # Create a dictionary to store the source and title
                song = {
                    'source': source,
                    'title': info['title']
                }

                # Play the audio
                if not voice.is_playing():
                    voice.play(source, after=lambda x=None: check_queue(ctx, ctx.guild.id))
                    await ctx.send(f"Now playing: **{info['title']}**")
                else:
                    # Add to queue if something is already playing
                    if ctx.guild.id not in queues:
                        queues[ctx.guild.id] = []  # Initialize the queue if it doesn't exist
                    queues[ctx.guild.id].append(song)
                    await ctx.send(f"Added to queue: **{info['title']}**")
            except Exception as e:
                print(f"Error: {e}")  # Debug: Print any errors
                await ctx.send("Failed to play the song. Please try again.")
    else:
        await ctx.send("You are not in a voice channel!")

# Command: Pause the music
@bot.command()
async def pause(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Paused ⏸️")
    else:
        await ctx.send("Nothing is playing!")

# Command: Resume the music
@bot.command()
async def resume(ctx):
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Resumed ▶️")
    else:
        await ctx.send("Nothing is paused!")

# Command: Stop the music
@bot.command()
async def stop(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Stopped ⏹️")
    else:
        await ctx.send("Nothing is playing!")

# Command: Skip the current song
@bot.command()
async def skip(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Skipped ⏭️")
        check_queue(ctx, ctx.guild.id)
    else:
        await ctx.send("Nothing is playing!")

# Command: Show the queue
@bot.command()
async def queue(ctx):
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        queue_list = "\n".join([f"{i+1}. {song['title']}" for i, song in enumerate(queues[ctx.guild.id])])
        await ctx.send(f"**Queue:**\n{queue_list}")
    else:
        await ctx.send("The queue is empty!")

# Help command
@bot.command()
async def help(ctx):
    help_message = """
    **Available Commands:**
     - `.join`: Makes the bot join your voice channel.
     - `.leave`: Makes the bot leave the voice channel.
     - `.play <url>`: Plays music from a YouTube URL or search query.
     - `.pause`: Pauses the current song.
     - `.resume`: Resumes the paused song.
     - `.stop`: Stops the current song and clears the queue.
     - `.skip`: Skips the current song and plays the next one in the queue.
     - `.queue`: Displays the current queue.
     - `.hello`: Say hello to the bot.
     - `.roll`: Roll a dice.
     - `.ping`: Check the bot's latency.
     - `.clear <amount>`: Clear messages (requires Manage Messages permission).
     - `mention bot to ask question and talk with.
     - `Developer`: Mr.MorningStar😎
    """
    await ctx.send(help_message)


# Slash Command: Help command
@bot.tree.command(name="help", description="Shows the list of available commands")
async def slash_help(interaction: discord.Interaction):
    help_message = """
    **Available Commands:**
      - `.join`: Makes the bot join your voice channel.
     - `.leave`: Makes the bot leave the voice channel.
     - `.play <url>`: Plays music from a YouTube URL or search query.
     - `.pause`: Pauses the current song.
     - `.resume`: Resumes the paused song.
     - `.stop`: Stops the current song and clears the queue.
     - `.skip`: Skips the current song and plays the next one in the queue.
     - `.queue`: Displays the current queue.
     - `.hello`: Say hello to the bot.
     - `.roll`: Roll a dice.
     - `.ping`: Check the bot's latency.
     - `.clear <amount>`: Clear messages (requires Manage Messages permission).
     - `mention bot to ask question and talk with.
     - `Developer`: Mr.MorningStar😎
    """
    await interaction.response.send_message(help_message)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        GEMINI_API_KEY = "AIzaSyD6SLazFl1He7A5sfBNyuKLqrGItaLepIg"
        
        question = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if question:
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": question}]}]}

            async with message.channel.typing():  # Keep typing until response is ready
                response = await get_gemini_response(url, headers, payload)

            await message.channel.send(f"{message.author.mention} {response}")

    await bot.process_commands(message)  # Ensure bot still processes other commands

async def get_gemini_response(url, headers, payload):
    """Handles Gemini API request while keeping typing effect active."""
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: requests.post(url, headers=headers, json=payload))

    if response.status_code == 200:
        try:
            data = response.json()
            answer = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            answer = "I couldn't find an answer."
    else:
        answer = f"Error {response.status_code}: Failed to communicate with Gemini API."

    return answer



# Event: When the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

# Run the bot with your token
bot.run('Njc0NTI5MTMzMTc0MTk0MjE2.GKYAzo.LqZvrZpknZyhfiA0wDpDm3R2pBx46qHj7XSyAo')



