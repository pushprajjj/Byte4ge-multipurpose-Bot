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

bot.run('Njc1MjUwOTc2MTc2NzM0MjA4.GBjbqD.zwLlmqbLajQG0yb__Fm3DpJ_MConDTGNDZm3Hs') #testing token
