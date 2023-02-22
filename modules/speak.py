import os
import discord
from discord import app_commands
from discord.ext import commands

import requests
import json
import time
from datetime import datetime
from collections import deque

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
        self.queue = deque()

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
            await ctx.followup.send(f"ずんだもんが {ctx.user.voice.channel} に入室しました．{channel} に投稿された内容を読み上げます．", ephemeral=True)

    @app_commands.command(name="speak-exit", description="読み上げ Bot をボイスチャンネルから退室させます．")
    @app_commands.guilds(guild)
    async def send_speak_exit(self, ctx: discord.Interaction):
        await ctx.response.defer(ephemeral=True)
        await self.voice_client.disconnect()
        self.voice_channel = discord.VoiceChannel
        self.watch_channel = discord.TextChannel
        self.voice_client = discord.VoiceClient
        await ctx.followup.send("ずんだもんが退室しました．", ephemeral=True)

    def play(self):
        """
        Play audio generated by voicebox
        """
        if not self.queue:
            return
        
        source = self.queue.popleft()
        self.voice_client.play(source)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if (type(message.channel) is discord.TextChannel and message.channel.name == self.watch_channel.name):
            now = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
            file_path = f"./output_{now}.wav"
            synthesis(message.content, file_path)
            source = discord.FFmpegPCMAudio(file_path)
            self.queue.append(source)
            while True:
                if not message.guild.voice_client.is_playing():
                    self.play()
                    break
                else:
                    time.sleep(1)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Speak(bot))