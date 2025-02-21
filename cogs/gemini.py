import discord
import aiohttp
import json
from discord.ext import commands

GEMINI_API_KEY = "AIzaSyD6SLazFl1He7A5sfBNyuKLqrGItaLepIg"

class Gemini(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_gemini_response(self, prompt: str):
        """Fetch AI response from Google Gemini API."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                data = await response.json()
                # print("🔹 API Response:", json.dumps(data, indent=2))  # Debugging

                if response.status == 200 and "candidates" in data:
                    return data["candidates"][0]["content"]["parts"][0]["text"]
                return f"❌ Error {response.status}: {data.get('error', 'Unknown error')}"

    @commands.Cog.listener()
    async def on_message(self, message):
        """AI replies when bot is mentioned."""
        if message.author == self.bot.user:
            return
        
        if self.bot.user.mentioned_in(message):
            async with message.channel.typing():
                response = await self.get_gemini_response(message.content)
                await message.reply(response, mention_author=True)

async def setup(bot):
    await bot.add_cog(Gemini(bot))
