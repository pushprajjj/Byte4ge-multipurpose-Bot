import discord
from discord.ext import commands
import asyncio
import os
import wavelink



intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix='+',
    intents=intents,
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=False),
    activity=discord.CustomActivity(name='byte4ge.com | Weaving Web Magic With Excellence.', emoji="😎"),
    help_command=None 
)

async def update_presence():
    statuses = [
        discord.Game(name="With code!"),
        discord.Streaming(name="The Forest😂", url="https://www.youtube.com/watch?v=q41E9DAJNxY"),
        discord.Activity(type=discord.ActivityType.listening, name=".play & .help"),
        discord.Activity(type=discord.ActivityType.watching, name="BYTE4GE DEV's PORTAL"),
    ]

    while True:
        for status in statuses:
            await bot.change_presence(activity=status)
            await asyncio.sleep(5)

async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name}')

    try:
        await wavelink.Pool.connect(
            client=bot,
            nodes=[
                wavelink.Node(
                    uri='http://mo.devamop.in:8807',
                    password='youshallnotpass',
                    identifier='MAIN',
                   
                )
            ]
        )
        print("🎧 Lavalink node connected.")
    except Exception as e:
        print(f"❌ Error connecting Lavalink node: {e}")

    await load_cogs()
    bot.loop.create_task(update_presence())

bot.run('___Your token____')  # testing token
