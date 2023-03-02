import os
import discord
from discord import app_commands
from discord.ext import commands

import json
import ujson
import aiohttp

from config import DISCORD_SERVER_KEY, OPENAI_API_KEY

guild = discord.Object(id=DISCORD_SERVER_KEY)

async def get_chatapi_response(messages):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + str(OPENAI_API_KEY)
    }

    data_json = {
        "model": "gpt-3.5-turbo",
        "messages": messages
    }

    async with aiohttp.ClientSession("https://api.openai.com", json_serialize=ujson.dumps) as session:
        async with session.post("/v1/chat/completions", headers=headers, json=data_json) as r:
            if r.status == 200:
                json_body = await r.json()
                return json_body["choices"][0]["message"]["content"]

def generate_embed(prompt: str, user: discord.User) -> discord.Embed:
    embed = discord.Embed(
        title=prompt,
        color=0x80A89C,
    )
    embed.set_author(
        name=user.display_name,
        icon_url=user.avatar.url,
    )
    return embed

class Chat(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="chat", description="ChatGPT とおしゃべりします．")
    @app_commands.guilds(guild)
    @discord.app_commands.describe(
        prompt="ChatGPT に話しかける内容です．"
    )
    async def send_chat(self, ctx: discord.Interaction, prompt: str):
        await ctx.response.defer()
        await ctx.followup.send(embed=generate_embed(prompt, ctx.user))
        async with ctx.channel.typing():
            answer = await get_chatapi_response(
                [{
                    "role": "user",
                    "content": prompt
                }]
            )
        await ctx.followup.send(answer)

    @app_commands.command(name="tundere", description="ツンデレ美少女とおしゃべりします．")
    @app_commands.guilds(guild)
    @discord.app_commands.describe(
        prompt="ツンデレ美少女に話しかける内容です．"
    )
    async def send_tundere(self, ctx: discord.Interaction, prompt: str):
        await ctx.response.defer()
        await ctx.followup.send(embed=generate_embed(prompt, ctx.user))
        async with ctx.channel.typing():
            answer = await get_chatapi_response(
                [
                    {
                        "role": "system",
                        "content": "ツンデレとは、日本のアニメやマンガなどによく登場するキャラクターの性格タイプの一つです。ツンデレとはツンツン（つんつん）とデレデレ（でれでれ）の2つの言葉を合成したもので、最初は冷たく厳しい態度を取るが、徐々に愛情や優しさを表現するキャラクターを指します。例えば、初めは主人公に対して嫌悪感を示すが、次第にその気持ちを打ち明けたり、助けたりする、といった具合です。ツンデレ少女になりきって話してください．"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
        await ctx.followup.send(answer)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Chat(bot))
