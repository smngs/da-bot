import discord
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
