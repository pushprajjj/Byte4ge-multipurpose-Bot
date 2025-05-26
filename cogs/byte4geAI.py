import discord
from discord import app_commands
import aiohttp
import json
from discord.ext import commands

class Byte4geAI(commands.Cog):
    """Byte4ge AI Integration Cog"""

    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://ai.byte4ge.com/api/v1/"

    async def get_ai_response(self, message: str, user: discord.Member) -> str:
        """Fetch AI response from Byte4ge API."""
        async with aiohttp.ClientSession() as session:
            try:
                payload = {
                    "message": message,
                    "user_id": str(user.id)
                }
                headers = {
                    "Content-Type": "application/json"
                }
                
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("reply", "Sorry, I couldn't process that request.")
                    else:
                        return f"Error: Unable to get response (Status: {response.status})"
            except Exception as e:
                return f"Error: {str(e)}"

    @app_commands.command(name="ask", description="Ask a question to Byte4ge AI")
    async def ask(self, interaction: discord.Interaction, question: str):
        """Slash command to ask questions to the AI."""
        await interaction.response.defer()  # Defer the response as API call might take time
        
        try:
            # Get response from AI
            response = await self.get_ai_response(question, interaction.user)
            
            # Create and send embed
            embed = discord.Embed(
                title="🤖 AI Response",
                description=response,
                color=discord.Color.blue()
            )
            embed.set_footer(text="Powered by Byte4ge AI")
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)

    @app_commands.command(name="chat", description="Start a chat with Byte4ge AI")
    @app_commands.describe(message="Your message to the AI")
    async def chat(self, interaction: discord.Interaction, message: str):
        """Slash command for chatting with the AI."""
        await interaction.response.defer()
        
        try:
            # Get response from AI
            response = await self.get_ai_response(message, interaction.user)
            
            # Create and send embed
            embed = discord.Embed(
                title="💬 Chat Response",
                description=response,
                color=discord.Color.green()
            )
            embed.set_footer(text="Powered by Byte4ge AI")
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for bot mentions and respond with AI."""
        # Ignore messages from the bot itself
        if message.author == self.bot.user:
            return
        
        # Check if the bot is mentioned
        if self.bot.user.mentioned_in(message):
            # Remove the bot mention and clean the message content
            clean_message = message.content.replace(f'<@{self.bot.user.id}>', '').strip()
            if not clean_message:
                clean_message = "hi"  # Default message if only the bot is mentioned
            
            # Show typing indicator while processing
            async with message.channel.typing():
                # Get response from AI with user information
                response = await self.get_ai_response(clean_message, message.author)
                
                # Create and send embed
                embed = discord.Embed(
                    description=response,
                    color=discord.Color.blue()
                )
                embed.set_footer(text="Powered by Byte4ge AI")
                
                await message.reply(embed=embed, mention_author=True)

async def setup(bot):
    """Load the Byte4ge AI cog."""
    await bot.add_cog(Byte4geAI(bot)) 