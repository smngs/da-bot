import discord
from discord import app_commands
from discord.ext import commands

from config import DISCORD_SERVER_KEY

guild = discord.Object(id=DISCORD_SERVER_KEY)

class Hello(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="hello", description="ユーザに対して華麗に挨拶します．")
    @app_commands.guilds(guild)
    async def send_hello(self, ctx: discord.Interaction):
        await ctx.response.send_message(f"Hello, {ctx.user.display_name}.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Hello(bot))
