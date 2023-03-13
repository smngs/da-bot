import discord
from discord import app_commands
from discord.ext import commands

from config.discord import DISCORD_SERVER_ID
from db.client import db

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

import datetime
from typing import Tuple, Union

async def get_nearest_station(user_id: int) -> Union[Tuple[str, str, str, int], None]:
    '''
    自宅最寄り駅を返します． TODO: そのうち DB などに移す
    '''
    route_collection = db["route"]
    route = await route_collection.find_one({
        "user_id": user_id
    })

    if route is None:
        return None

    return (route["home_station"], route["work_station"], route["via_station"], route["search_method"])

def get_route_url(from_station: str, to_station: str, via_station: str, search_method: int=0) -> str:
    '''
    search_method: 0: 到着時刻順, 1: 料金の安い順, 2: 乗換回数順
    '''
    dt = datetime.datetime.now() + datetime.timedelta(minutes=10)
    year, month, day, hour, minute = dt.year, dt.month, dt.day, dt.hour, dt.minute

    route_url = f"https://transit.yahoo.co.jp/search/print?from={from_station}&flatlon=&to={to_station}&via={via_station}&s={search_method}&y={year}&m={str(month).zfill(2)}&d={str(day).zfill(2)}&hh={hour}&m1={minute//10}&m2={minute%10}"
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

async def get_home_route(user_id: int, file_path: str="./tmp/upload.png") -> Union[str, None]:
    route = await get_nearest_station(user_id)
    if route is None:
        return None
    url = get_route_url(*route)
    save_route_screenshot(url, file_path)
    return url

async def get_route(file_path: str="./tmp/upload.png", from_station="", to_station="", via_station="", search_method=0) ->  Union[str, None]:
    url = get_route_url(from_station, to_station, via_station, search_method)
    save_route_screenshot(url, file_path)
    return url

async def register_route(user_id: int, home_station: str, work_station: str, via_station: str, search_method: int) -> None:
    route_collection = db["route"]

    # 一旦取得して，なければ新しくつっこむ
    route = await route_collection.find_one({
        "user_id": user_id,
    })

    set_route = {
        "user_id": user_id,
        "home_station": home_station,
        "work_station": work_station,
        "via_station": via_station,
        "search_method": search_method
    }

    if route is None:
        await route_collection.insert_one(set_route)
    else:
        await route_collection.update_one(
            {
                "_id": route["_id"]
            }, {
                "$set": set_route
            }
        )

# ---

class Route(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="home", description="帰宅経路を検索します．")
    async def send_home(self, ctx: discord.Interaction):
        await ctx.response.defer()
        file_path = "./tmp/upload.png"
        route_url = await get_home_route(ctx.user.id, file_path)
        if route_url is None:
            await ctx.followup.send("自宅の最寄り駅が登録されていません．`/route-register` 機能を利用して登録してください．")
        else:
            await ctx.followup.send(route_url, file=discord.File(file_path))

    @app_commands.command(name="route", description="出発地から目的地までの経路を検索します．")
    @discord.app_commands.describe(
        from_station="出発地を指定します．", 
        to_station="目的地を指定します．", 
        via_station="経由地を指定します．",
        search_method="検索方法を指定します．"
    )
    @app_commands.choices(search_method=[
        app_commands.Choice(name="到着時間優先（早）", value=0),
        app_commands.Choice(name="料金優先（安）", value=1),
        app_commands.Choice(name="乗換回数優先（楽）", value=2),
    ])
    async def send_route(self, ctx: discord.Interaction, from_station: str, to_station: str, via_station: str="", search_method: int=0):
        file_path = "./tmp/upload.png"
        route_url = await get_route(file_path, from_station, to_station, via_station, search_method)
        await ctx.response.send_message(route_url, file=discord.File(file_path))

    @app_commands.command(name="route-register", description="自宅と職場の最寄り駅を登録します．")
    @discord.app_commands.describe(
        home_station="自宅の最寄り駅を登録します．", 
        work_station="職場の最寄り駅を登録します．", 
        via_station="経由する駅を指定します．",
        search_method="検索方法を指定します．"
    )
    @app_commands.choices(search_method=[
        app_commands.Choice(name="到着時間優先（早）", value=0),
        app_commands.Choice(name="料金優先（安）", value=1),
        app_commands.Choice(name="乗換回数優先（楽）", value=2),
    ])
    async def send_route_register(self, ctx: discord.Interaction, home_station: str, work_station: str, via_station: str, search_method: int=0):
        await ctx.response.defer(ephemeral=True)
        await register_route(ctx.user.id, home_station, work_station, via_station, search_method)
        await ctx.followup.send(f"最寄り駅を登録しました．user_id: <@{ctx.user.id}>, home_station: {home_station}, work_station: {work_station}, via_station: {via_station}")

async def setup(bot: commands.Bot) -> None:
    if DISCORD_SERVER_ID:
        guild = discord.Object(id=int(DISCORD_SERVER_ID))
        await bot.add_cog(Route(bot), guild=guild)
    else:
        await bot.add_cog(Route(bot))
 
