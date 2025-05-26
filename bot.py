import discord
from discord.ext import commands
import asyncio
import os


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
    
    # Sync slash commands
    print("🔄 Syncing slash commands...")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Failed to sync slash commands: {e}")
    
    bot.loop.create_task(update_presence())

bot.run('--------------')
