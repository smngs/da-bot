import discord
from discord import app_commands
from discord.ext import commands

from config.discord import DISCORD_SERVER_ID

class AdminSetting(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="admin-setting", description="管理者用のデバッグ用設定です．")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.choices(choices=[
        app_commands.Choice(name="ギルドコマンドの全削除", value="clean_guild_commands"),
        app_commands.Choice(name="グローバルコマンドの全削除", value="clean_global_commands"),
    ])
    async def admin_setting(self, ctx: discord.Interaction, choices: app_commands.Choice[str]):
        await ctx.response.defer()

        if (choices.value == "clean_guild_commands"):
            await ctx.followup.send("ギルドコマンドを削除します．サーバを再起動してください．", ephemeral=True)
            self.bot.tree.clear_commands(guild=ctx.guild)
            await self.bot.tree.sync(guild=ctx.guild)
        elif (choices.value == "clean_global_commands"):
            await ctx.followup.send("グローバルコマンドを削除します．サーバを再起動してください．", ephemeral=True)
            self.bot.tree.clear_commands(guild=None)
            await self.bot.tree.sync(guild=None)
        else:
            await ctx.followup.send("コマンドが見つかりません．")
            

async def setup(bot: commands.Bot) -> None:
    if DISCORD_SERVER_ID:
        guild = discord.Object(id=int(DISCORD_SERVER_ID))
        await bot.add_cog(AdminSetting(bot), guild=guild)
    else:
        await bot.add_cog(AdminSetting(bot))
