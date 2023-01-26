import os
import discord
from selenium import webdriver
from selenium.webdriver.common.by import By
from typing import List, Tuple

def get_routes(user: str) -> Tuple[str, str, str]:
    if (user == 'negino_13'):
        return ("四ツ谷", "神田", "与野")
    elif (user == 'bata_yas'):
        return ("四ツ谷", "渋谷", "元町・中華街")
    elif (user == 'mrmapler'):
        return ("四ツ谷", "永田町", "江田(神奈川県)")
    elif (user == 'detteiu55'):
        return ("四ツ谷", "渋谷", "妙蓮寺")
    else:
        return ("", "", "")

def get_route_url(from_station: str, via_station: str, to_station: str):
    route_url = "https://transit.yahoo.co.jp/search/print?from="+from_station+"&flatlon=&to="+ to_station + "&via=" + via_station
    return route_url

def get_route_picture(target_url: str, file_path: str):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    driver = webdriver.Chrome(options=options)
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
