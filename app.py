import os
import discord
from discord.ext import commands

from config import DISCORD_API_KEY, DISCORD_SERVER_KEY

guild = discord.Object(id=DISCORD_SERVER_KEY)

bot = commands.Bot(command_prefix='/', intents=discord.Intents.all())
COGS = [
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

    await bot.tree.sync(guild=guild)

bot.run(DISCORD_API_KEY)
