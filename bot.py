import discord
from discord.ext import commands
import asyncio
import os
from gemini import get_gemini_response

intents = discord.Intents.default()
intents.members = True 
intents.message_content = True  


bot = commands.Bot(
    command_prefix='+',
    intents=discord.Intents.all(),
    allowed_mentions=discord.AllowedMentions(
        everyone=False,
        roles=False
    ),
    activity=discord.CustomActivity(name='byte4ge.com | Weaving Web Magic With Excellence.', emoji="😎"),
    help_command=None 
)

async def update_presence():
    """Update the bot's rich presence periodically with images."""
    statuses = [
        discord.Game(name="With code!"),
        discord.Streaming(
            name="The Forest😂", 
            url="https://www.youtube.com/watch?v=q41E9DAJNxY" 
        ),
        discord.Activity(type=discord.ActivityType.listening, name=".play & .help"),
        discord.Activity(type=discord.ActivityType.watching, name="BYTE4GE DEV's PORTAL"),
    ]

    while True:
        for status in statuses:
            await bot.change_presence(activity=status)
            await asyncio.sleep(5)  # Change status every 10 seconds


@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore bot messages

    if bot.user.mentioned_in(message):  # If bot is mentioned
        async with message.channel.typing():
            response = await get_gemini_response(message.content)
        await message.reply(response, mention_author=False)

    await bot.process_commands(message)  # Process other commands


async def load_cogs():
    """Dynamically load all cogs from the 'cogs' folder."""
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')  

@bot.event
async def on_ready():
    """Bot startup event."""
    print(f'✅ Logged in as {bot.user.name}')
    await load_cogs()
    bot.loop.create_task(update_presence())

bot.run('Njc1MjUwOTc2MTc2NzM0MjA4.GBjbqD.zwLlmqbLajQG0yb__Fm3DpJ_MConDTGNDZm3Hs') #testing token
