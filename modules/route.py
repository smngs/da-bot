import os
import discord
from discord import app_commands
from discord.ext import commands

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import datetime
from typing import Tuple

# サーバコマンドを設定するギルド
DISCORD_SERVER_KEY = os.environ.get("DISCORD_SERVER_KEY")
guild = discord.Object(id=DISCORD_SERVER_KEY)

def get_nearest_station(user: str) -> Tuple[str, str, str, int]:
    '''
    みんなの自宅最寄り駅を返します． TODO: そのうち DB などに移す
    '''
    if (user == 'negino_13'): 
        return ("四ツ谷", "与野", "神田", 2)
    elif (user == 'bata_yas'):
        return ("四ツ谷", "元町・中華街", "新宿三丁目", 0)
    elif (user == 'mrmapler'):
        return ("四ツ谷", "江田(神奈川県)", "渋谷", 0)
    elif (user == 'detteiu55'):
        return ("四ツ谷", "妙蓮寺", "新宿三丁目", 0)
    else:
        return ("", "", "", 0) # ｺﾞﾐｶｽ

def get_route_url(from_station: str, to_station: str, via_station: str, priority_mode: int=0) -> str:
    '''
    priority_mode: 0: 到着時刻順, 1: 料金の安い順, 2: 乗換回数順
    '''
    dt = datetime.datetime.now() + datetime.timedelta(minutes=10)
    year, month, day, hour, minute = dt.year, dt.month, dt.day, dt.hour, dt.minute

    route_url = f"https://transit.yahoo.co.jp/search/print?from={from_station}&flatlon=&to={to_station}&via={via_station}&s={priority_mode}&y={year}&m={str(month).zfill(2)}&d={str(day).zfill(2)}&hh={hour}&m1={minute//10}&m2={minute%10}"
    return route_url

def save_route_screenshot(target_url: str, file_path: str, range_id: str="srline") -> None:
    '''
    与えられた URL のスクリーンショットを，png にして与えられた path に書き出します．
    '''
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')

    driver = webdriver.Chrome(options=options, service=Service("/usr/bin/chromedriver"))
    driver.get(target_url)

    png = driver.find_element(By.ID, range_id).screenshot_as_png

    with open(file_path, 'wb') as f:
        f.write(png)

    driver.close()

def get_route(user: str, file_path: str="./upload.png", from_station="", to_station="", via_station="") ->  str:
    if (from_station == ""):
        url = get_route_url(*get_nearest_station(user))
    else:
        url = get_route_url(from_station, to_station, via_station)

    save_route_screenshot(url, file_path)
    return url

# ---

class Route(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="home", description="帰宅経路を検索します．")
    @app_commands.guilds(guild)
    async def send_home(self, ctx: discord.Interaction):
        file_path = "./upload.png"
        await ctx.response.send_message(
            get_route(ctx.user.display_name, file_path),
            file=discord.File(file_path)
        )

    @app_commands.command(name="route", description="出発地から目的地までの経路を検索します．")
    @app_commands.guilds(guild)
    @discord.app_commands.describe(
        from_station="出発地を指定します．", 
        to_station="目的地を指定します．", 
        via_station="経由地を指定します．"
    )
    async def send_route(self, ctx: discord.Interaction, from_station: str, to_station: str, via_station: str=""):
        file_path = "./upload.png"
        await ctx.response.send_message(
            get_route(ctx.user.display_name, file_path, from_station, to_station, via_station), 
            file=discord.File(file_path)
        )

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Route(bot))

