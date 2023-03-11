import os
import discord
from discord.ext import commands

from config import DISCORD_API_KEY, DISCORD_SERVER_ID

bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())
COGS = [
    "modules.admin_setting",
    "modules.hello",
    "modules.help",
    "modules.route",
    "modules.event",
    "modules.speak",
    "modules.aichat",
    "modules.ese_chinese"
]

@bot.event
async def on_ready():
    print('Logged on as', bot.user)

    print('------')
    for cogs in COGS:
        await bot.load_extension(cogs)
        print(f"Loaded: {cogs}")

    if DISCORD_SERVER_ID:
        # 開発用にギルドコマンドとしてコマンドを定義
        guild = discord.Object(id=int(DISCORD_SERVER_ID))
        print("DISCORD_SERVER_ID is exist. sync guild commands...")
        await bot.tree.sync(guild=guild)
    else:
        # 本番環境用
        print("DISCORD_SERVER_ID is not exist. sync global commands...")
        await bot.tree.sync(guild=None)

bot.run(DISCORD_API_KEY)
