import os
import discord
from discord import app_commands
from discord.ext import commands

from config import DISCORD_SERVER_KEY

guild = discord.Object(id=DISCORD_SERVER_KEY)

from datetime import datetime

async def create_event(guild: discord.Guild, name: str, description: str, start_time: str, end_time: str, location: str):
    start = datetime.strptime(start_time, "%Y/%m/%d %H:%M:%S").astimezone()
    end = datetime.strptime(end_time, "%Y/%m/%d %H:%M:%S").astimezone()
    new_event = await guild.create_scheduled_event(
        # self=guild,
        name=name, 
        description=description, 
        start_time=start,
        end_time=end,
        entity_type=discord.EntityType.external,
        location=location
    )

    return new_event

class Event(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="event", description="新しいイベントをサーバに登録します．")
    @app_commands.guilds(guild)
    @discord.app_commands.describe(
        name="イベントの名前を指定します．", 
        description="イベントの目的を指定します．", 
        start_time="開始日時を指定します (YYYY-MM-DD HH:MM:SS)．", 
        end_time="終了日時を指定します (YYYY-MM-DD HH:MM:SS)．", 
        location="実施場所（URL）を指定します．"
    )
    async def send_event(self, ctx: discord.Interaction, name: str, description: str, start_time: str, end_time: str, location: str):
        new_event = await create_event(ctx.guild, name, description, start_time, end_time, location)
        await ctx.response.send_message(new_event.url)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Event(bot))
