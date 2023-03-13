import discord
from discord import app_commands
from discord.ext import commands

from config.discord import DISCORD_SERVER_ID

class Hello(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="hello", description="ユーザに対して華麗に挨拶します．")
    async def send_hello(self, ctx: discord.Interaction):
        await ctx.response.send_message(f"Hello, {ctx.user.display_name}.")

async def setup(bot: commands.Bot) -> None:
    if DISCORD_SERVER_ID:
        guild = discord.Object(id=int(DISCORD_SERVER_ID))
        await bot.add_cog(Hello(bot), guild=guild)
    else:
        await bot.add_cog(Hello(bot))
 
