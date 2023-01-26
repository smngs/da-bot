import os
import discord
from discord import Guild

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from datetime import datetime
import pytz
from typing import Tuple

def get_routes(user: str) -> Tuple[str, str, str, int]:
    if (user == 'negino_13'):
        return ("上智大学中央図書館", "神田", "与野", 2)
    elif (user == 'bata_yas'):
        return ("上智大学中央図書館", "渋谷", "元町・中華街", 0)
    elif (user == 'mrmapler'):
        return ("上智大学中央図書館", "永田町", "江田(神奈川県)", 0)
    elif (user == 'detteiu55'):
        return ("上智大学中央図書館", "渋谷", "妙蓮寺", 0)
    else:
        return ("", "", "", 0) # ｺﾞﾐｶｽ

def get_route_url(from_station: str, via_station: str, to_station: str, priority_mode: int=0):
    '''
    priority_mode: 0: 到着時刻順, 1: 料金の安い順, 2: 乗換回数順
    '''
    route_url = "https://transit.yahoo.co.jp/search/print?from="+from_station+"&flatlon=&to="+ to_station + "&via=" + via_station + "&s=" + str(priority_mode)
    return route_url

def get_route_picture(target_url: str, file_path: str):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')

    driver = webdriver.Chrome(options=options, service=Service("/usr/bin/chromedriver"))
    driver.get(target_url)

    png = driver.find_element(By.ID, 'srline').screenshot_as_png

    with open(file_path, 'wb') as f:
        f.write(png)

    driver.close()

# --- TODO: ここでファイル分割 ---

events = discord.ScheduledEvent
intents = discord.Intents.default()
intents.message_content = True
intents.guild_scheduled_events = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print('Logged on as', client.user)

@client.event
async def on_message(message: discord.Message):
    # don't respond to ourselves
    if message.author.bot:
        return

    if message.content == '帰宅':
        url = get_route_url(*get_routes(message.author.display_name))
        get_route_picture(url, './test.png')
        await message.channel.send(url, file=discord.File("./test.png"))

    if message.content.startswith("経路"):
        args = message.content.split()
        if len(args) < 2 or args[1] == "help":
            await message.channel.send("経路", delete_after=10)
        else:
            url = get_route_url(args[1], args[3], args[2])
            get_route_picture(url, './test.png')
            await message.channel.send(url, file=discord.File("./test.png"))

    if message.content == 'ping':
        await message.channel.send("pong")

    if message.content.startswith('event'):
        args = message.content.split(",")
        if len(args) < 5 or args[1] == "help":
            await message.channel.send("event <name> <description> <start_time> <end_time> <location_url>", delete_after=10)
        else:
            jst = pytz.timezone("Japan")
            start_time = datetime.strptime(args[3], "%Y/%m/%d %H:%M:%S").replace(tzinfo=jst)
            end_time = datetime.strptime(args[4], "%Y/%m/%d %H:%M:%S").replace(tzinfo=jst)
            new_event = await Guild.create_scheduled_event(
                self=message.guild,
                name=args[1], 
                description=args[2], 
                start_time=start_time,
                end_time=end_time,
                entity_type=discord.EntityType.external,
                location=args[5]
            )
            await message.channel.send(new_event.url)

client.run(os.environ.get('DISCORD_API_KEY'))
