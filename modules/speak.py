import os
import discord
from discord import app_commands
from discord.ext import tasks, commands

import requests
import json
import time
from datetime import datetime
from collections import deque

import asyncio

from config import DISCORD_SERVER_KEY

guild = discord.Object(id=DISCORD_SERVER_KEY)

def synthesis(text, filename, speaker=1, max_retry=20):
    query_payload = {"text": text, "speaker": speaker}
    for query_i in range(max_retry):
        r = requests.post("http://voicevox:50021/audio_query", 
                          params=query_payload, timeout=(10.0, 300.0))
        if r.status_code == 200:
            query_data = r.json()
            break
        else:
            raise ConnectionError("リトライ回数が上限に到達しました。 audio_query : ", filename, "/", text[:30], r.text)

    synth_payload = {"speaker": speaker}    
    for synth_i in range(max_retry):
        r = requests.post("http://voicevox:50021/synthesis", params=synth_payload, 
                          data=json.dumps(query_data), timeout=(10.0, 300.0))
        if r.status_code == 200:
            with open(filename, "wb") as fp:
                fp.write(r.content)
            break
        else:
            raise ConnectionError("リトライ回数が上限に到達しました。 synthesis : ", filename, "/", text[:30], r,text)

class Speak(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.voice_channel = discord.VoiceChannel
        self.watch_channel = discord.TextChannel
        self.voice_client = discord.VoiceClient
        self.queue = asyncio.Queue()


    def cog_unload(self):
        self.await_message.cancel()


    async def enqueue_message(self, text: str) -> None:
        """
        VoiceVox によって音声を生成し，そのファイルパスを enqueue する．
        この関数はずんだもんが VC 内にいるときに実行されることが保証される．
        """
        now = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
        file_path = f"./output_{now}.wav"
        synthesis(text, file_path)
        await self.queue.put(file_path)

    async def play_message(self):
        """
        Queue から一つファイルパスを pop し，そのファイルパスに保存されている音声を再生する．
        この関数はずんだもんが VC 内にいるときに実行されることが保証される．
        """
        file_path = await self.queue.get()
        source = discord.FFmpegPCMAudio(file_path)
        self.voice_client.play(source)

    @tasks.loop(seconds=1.0)
    async def await_message(self):
        """
        Queue を監視し，Queue にファイルパスが push された際に play_message() を実行する．
        本関数は asyncio によって定期的に実行される．
        """
        while True:
            print(self.queue)
            while self.queue.empty():
                await asyncio.sleep(1)

            if not self.voice_client.is_playing():
                await self.play_message()
                break
            else:
                await asyncio.sleep(1)


    @app_commands.command(name="speak-join", description="テキストチャンネルに投稿された音声を読み上げます．先に VC に入ってからコマンドを実行してください．")
    @app_commands.guilds(guild)
    @discord.app_commands.describe(
        channel="読み上げ対象のテキストチャンネルを指定します．"
    )
    async def send_speak_join(self, ctx: discord.Interaction, channel: discord.TextChannel):
        await ctx.response.defer(ephemeral=True)
        self.watch_channel = channel
        if ctx.user.voice == None:
            await ctx.followup.send(f"先に VC に入ってから，`/join` コマンドを実行してください．")
        else:
            self.voice_channel = await discord.VoiceChannel.connect(ctx.user.voice.channel)
            self.voice_client = ctx.guild.voice_client

            if not self.await_message.is_running():
                self.await_message.start()

            await ctx.followup.send(f"ずんだもんが {ctx.user.voice.channel} に入室しました．{channel} に投稿された内容を読み上げます．", ephemeral=True)


    @app_commands.command(name="speak-exit", description="読み上げ Bot をボイスチャンネルから退室させます．")
    @app_commands.guilds(guild)
    async def send_speak_exit(self, ctx: discord.Interaction):
        await ctx.response.defer(ephemeral=True)
        await self.voice_client.disconnect()
        self.voice_channel = discord.VoiceChannel
        self.watch_channel = discord.TextChannel
        self.voice_client = discord.VoiceClient

        if self.await_message.is_running():
            self.await_message.cancel()

            while not self.queue.empty():
                self.queue.get_nowait()
                self.queue.task_done()

        await ctx.followup.send("ずんだもんが退室しました．", ephemeral=True)


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if (type(message.channel) is discord.TextChannel and message.channel.name == self.watch_channel.name):
            await self.enqueue_message(message.content)



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Speak(bot))
