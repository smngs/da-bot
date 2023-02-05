import os
import discord
from typing import List, Tuple

from modules import route, event, aichat, ese_chinese

events = discord.ScheduledEvent
intents = discord.Intents.default()
intents.message_content = True
intents.guild_scheduled_events = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

DISCORD_API_KEY = os.environ.get("DISCORD_API_KEY")
DISCORD_SERVER_KEY = os.environ.get("DISCORD_SERVER_KEY")

guild = discord.Object(id=DISCORD_SERVER_KEY)

# -----
@tree.command(name="hello", guild=guild, description="ユーザに対して華麗に挨拶します．")
async def send_hello(ctx: discord.Interaction, user_name: str):
    await ctx.response.send_message("Hello, World.", ephemeral=True)
    await ctx.followup.send(f"{user_name}-san!")

@tree.command(name="help", guild=guild, description="Bot のヘルプを表示します．")
async def send_help(ctx: discord.Interaction):
    embed = discord.Embed(
        title="@da-bot Help",
        color=0x80A89C,
    )
    embed.set_author(
        name=client.user.display_name
    )
    embed.add_field(name="`/hello`", value="ユーザに対して華麗に挨拶します．", inline=False)
    embed.add_field(name="`/chat`", value="GPT-3 とおしゃべりします．", inline=False)
    embed.add_field(name="`/home`", value="帰宅経路を検索します．", inline=False)
    embed.add_field(name="`/route`", value="出発地から目的地までの経路を検索します．", inline=False)
    embed.add_field(name="`/event`", value="新しいイベントをサーバに登録します．", inline=False)
    embed.set_footer(
        text="https://github.com/smngs/da-bot",
        icon_url="https://github.com/smngs.png"
    )

    await ctx.response.send_message(embed=embed, ephemeral=True)

# -----
@tree.command(name="ping", guild=guild, description="疎通確認のための ping を送信します．")
async def send_ping(ctx: discord.Interaction, number: int):
    await ctx.response.send_message(f'ping: {number}', ephemeral=True)

# -----
@tree.command(name="home", guild=guild, description="帰宅経路を検索します．")
async def send_home(ctx: discord.Interaction):
    file_path = "./upload.png"
    await ctx.response.send_message(
        route.get_route(ctx.user.display_name, file_path),
        file=discord.File(file_path)
    )

# -----
@tree.command(name="route", guild=guild, description="出発地から目的地までの経路を検索します．")
@discord.app_commands.describe(
    from_station="出発地を指定します．", 
    to_station="目的地を指定します．", 
    via_station="経由地を指定します．"
)
async def send_route(ctx: discord.Interaction, from_station: str, to_station: str, via_station: str=""):
    file_path = "./upload.png"
    await ctx.response.send_message(
        route.get_route(ctx.user.display_name, file_path, from_station, to_station, via_station), 
        file=discord.File(file_path)
    )

# -----
@tree.command(name="event", guild=guild, description="新しいイベントをサーバに登録します．")
@discord.app_commands.describe(
    name="イベントの名前を指定します．", 
    description="イベントの目的を指定します．", 
    start_time="開始日時を指定します (YYYY-MM-DD HH:MM:SS)．", 
    end_time="終了日時を指定します (YYYY-MM-DD HH:MM:SS)．", 
    location="実施場所（URL）を指定します．"
)
async def send_event(ctx: discord.Interaction, name: str, description: str, start_time: str, end_time: str, location: str):
    new_event = await event.create_event(ctx.guild, name, description, start_time, end_time, location)
    await ctx.response.send_message(new_event.url)

# -----
@tree.command(name="chat", guild=guild, description="GPT-3 とおしゃべりします．")
@discord.app_commands.describe(
    prompt="GPT-3 に話しかける内容です．"
)
async def send_chat(ctx: discord.Interaction, prompt: str):
    await ctx.response.defer()
    await ctx.followup.send(embed=aichat.generate_embed(prompt, ctx.user))
    async with ctx.channel.typing():
        answer = aichat.trigger_chat(prompt)
    await ctx.followup.send(answer)

# -----
@tree.command(name="ese_chinese", guild=guild, description="文章を偽中国語に翻訳します．")
@discord.app_commands.describe(
    prompt="偽中国語に翻訳する内容です．"
)
async def send_chat(ctx: discord.Interaction, prompt: str):
    await ctx.response.defer()
    await ctx.followup.send(embed=ese_chinese.generate_embed(prompt, ctx.user))
    await ctx.followup.send(ese_chinese.to_esechinese(prompt))

@client.event
async def on_ready():
    print('Logged on as', client.user)
    await tree.sync(guild=guild)

client.run(DISCORD_API_KEY)
