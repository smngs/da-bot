import os
import discord
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from typing import List, Tuple

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

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message: discord.Message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content == '帰宅':
            url = get_route_url(*get_routes(message.author.display_name))
            get_route_picture(url, './test.png')
            await message.channel.send(url, file=discord.File("./test.png"))

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
client.run(os.environ.get('DISCORD_API_KEY'))
