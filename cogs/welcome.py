import discord
from discord.ext import commands

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.welcome_channel_id = 962746897787920396  # Replace with your welcome channel ID
        self.default_role_id = 1334522873959813170  # Replace with your default role ID
        self.server_id = 962746896877756536  # The specific server ID

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Triggered when a new member joins the server."""
        if member.guild.id != self.server_id:
            return  # Exit if the member did not join the specified server

        channel = self.bot.get_channel(self.welcome_channel_id)
        if channel:
            custom_emoji1 = self.bot.get_emoji(1337651913306411048)  
            custom_emoji2 = self.bot.get_emoji(1337651191408103434)
            custom_emoji3 = self.bot.get_emoji(1337651908017393696)

            guidelines_channel_id = 962746897787920397 
            guidelines_channel = self.bot.get_channel(guidelines_channel_id)
            guidelines_mention = guidelines_channel.mention if guidelines_channel else "#guidelines"

            embed = discord.Embed(
                title=f"{custom_emoji1} Welcome!",
                description=f"Hey{custom_emoji2} {member.mention}, welcome to {member.guild.name}! 🎊\nMake sure to check the rules in the {guidelines_mention} channel and have fun!{custom_emoji3}",
                color=discord.Color.orange()
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.add_field(name="Username", value=member.name, inline=True)
            embed.add_field(name="Member Count", value=f"{member.guild.member_count}", inline=True)
            embed.set_footer(text="We hope you enjoy your stay!")
            embed.set_image(url="https://cdn.discordapp.com/attachments/962746899201421348/1342358871963996212/Discord_Bot-Banner.jpg?ex=67b9589e&is=67b8071e&hm=2c29d79f18296582bf3f7ce94cfb3b4302961162a8a9a679c04c5ae0f5fc1d83&")  # Add a welcome image URL

            await channel.send(embed=embed)

        # Assign the default role to the new member
        default_role = member.guild.get_role(self.default_role_id)
        if default_role:
            await member.add_roles(default_role)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
