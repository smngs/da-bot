import discord
from discord import app_commands
from discord.ext import commands

from config import DISCORD_SERVER_KEY

guild = discord.Object(id=DISCORD_SERVER_KEY)

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="help", description="Bot のヘルプを表示します．")
    @app_commands.guilds(guild)
    async def send_help(self, ctx: discord.Interaction):
        embed = discord.Embed(
            title="@da-bot Help",
            color=0x80A89C,
        )
        embed.set_author(
            name=self.bot.user.display_name
        )
        embed.add_field(name="`/hello`", value="ユーザに対して華麗に挨拶します．", inline=False)
        embed.add_field(name="`/chat`", value="GPT-3 とおしゃべりします．", inline=False)
        embed.add_field(name="`/home`", value="帰宅経路を検索します．", inline=False)
        embed.add_field(name="`/route`", value="出発地から目的地までの経路を検索します．", inline=False)
        embed.add_field(name="`/event`", value="新しいイベントをサーバに登録します．", inline=False)
        embed.add_field(name="`/speak`", value="ずんだもんがテキストチャネルに投稿された内容を VC で読み上げます．", inline=False)
        embed.set_footer(
            text="https://github.com/smngs/da-bot",
            icon_url="https://github.com/smngs.png"
        )

        await ctx.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))
