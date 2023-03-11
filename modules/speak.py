import discord
from discord import app_commands
from discord.ext import tasks, commands

import ujson
from datetime import datetime

import aiohttp
import asyncio

from config import DISCORD_SERVER_KEY, SPEAK_CHAT_DEFAULT_CHANNEL_ID

guild = discord.Object(id=DISCORD_SERVER_KEY)

async def synthesis(text, filename, speaker=1, max_retry=20):

    query_payload = {"text": text, "speaker": speaker}
    synth_payload = {"speaker": speaker}
    async with aiohttp.ClientSession("http://voicevox:50021", json_serialize=ujson.dumps) as session:
        async with session.post("/audio_query", params=query_payload) as r:
            if r.status == 200:
                query_data = await r.json()
            else:
                raise ConnectionError("リトライ回数が上限に到達しました。 audio_query : ", filename, "/", text[:30], r.text)

        async with session.post("/synthesis", params=synth_payload, json=query_data) as r:
            if r.status == 200:
                with open(filename, 'wb') as fd:
                    chunk_size = 4
                    async for chunk in r.content.iter_chunked(chunk_size):
                        fd.write(chunk)
            else:
                raise ConnectionError("リトライ回数が上限に到達しました。 audio_query : ", filename, "/", text[:30], r.text)

class Speak(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        self.voice_channels = {}
        self.watch_channels = {}
        self.voice_clients = {}
        self.queues = {}

        # これだと起動時にギルドが登録されている前提が生まれる？
        for guild in bot.guilds:
            self.voice_channels[guild.id] = None
            self.watch_channels[guild.id] = None
            self.voice_clients[guild.id] = None
            self.queues[guild.id] = asyncio.Queue()

    def cog_unload(self):
        self.await_message.cancel()


    async def enqueue_message(self, text: str, guild_id: int) -> None:
        """
        VoiceVox によって音声を生成し，そのファイルパスを enqueue する．
        この関数はずんだもんが VC 内にいるときに実行されることが保証される．
        """
        now = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
        file_path = f"./tmp/output_{now}.wav"
        await synthesis(text, file_path)
        await self.queues[guild_id].put(file_path)

    async def play_message(self, guild_id: int):
        """
        Queue から一つファイルパスを pop し，そのファイルパスに保存されている音声を再生する．
        この関数はずんだもんが VC 内にいるときに実行されることが保証される．
        """
        file_path = await self.queues[guild_id].get()
        source = discord.FFmpegPCMAudio(file_path)
        self.voice_clients[guild_id].play(source)

    @tasks.loop(seconds=0.1)
    async def await_message(self):
        """
        Queue を監視し，Queue にファイルパスが push された際に play_message() を実行する．
        本関数は asyncio によって定期的に実行される．
        """

        while True:
            for guild_id, queue in self.queues.items():
                if queue.empty():
                    continue

                if self.voice_clients[guild_id] is not None and not self.voice_clients[guild_id].is_playing():
                    await self.play_message(guild_id)

            await asyncio.sleep(1)


    @app_commands.command(name="speak-join", description="テキストチャンネルに投稿された音声を読み上げます．先に VC に入ってからコマンドを実行してください．")
    @discord.app_commands.describe(
        channel="読み上げ対象のテキストチャンネルを指定します．"
    )
    async def send_speak_join(self, ctx: discord.Interaction, channel: discord.TextChannel = None):
        await ctx.response.defer(ephemeral=True)

        if channel == None:
            # channel = ctx.guild.get_channel(int(SPEAK_CHAT_DEFAULT_CHANNEL_ID))
            channel = ctx.guild.get_channel(ctx.channel_id)


        self.watch_channels[ctx.guild_id] = channel

        if ctx.user.voice == None:
            await ctx.followup.send(f"先に VC に入ってから，`/join` コマンドを実行してください．")
        else:
            self.voice_channels[ctx.guild_id] = await discord.VoiceChannel.connect(ctx.user.voice.channel)
            self.voice_clients[ctx.guild_id] = ctx.guild.voice_client

            if not self.await_message.is_running():
                self.await_message.start()

            await ctx.followup.send(f"ずんだもんが {ctx.user.voice.channel} に入室しました．{channel} に投稿された内容を読み上げます．", ephemeral=True)


    @app_commands.command(name="speak-exit", description="読み上げ Bot をボイスチャンネルから退室させます．")
    async def send_speak_exit(self, ctx: discord.Interaction):
        await ctx.response.defer(ephemeral=True)

        if self.voice_clients[ctx.guild_id] is not None:
            await self.voice_clients[ctx.guild_id].disconnect()
        else:
            await ctx.followup.send("ずんだもんはどのサーバにも参加していません．", ephemeral=True)
            return

        self.voice_channels[ctx.guild_id] = None
        self.watch_channels[ctx.guild_id] = None
        self.voice_clients[ctx.guild_id] = None

        if self.await_message.is_running():
            self.await_message.cancel()

            while not self.queues[ctx.guild_id].empty():
                self.queues[ctx.guild_id].get_nowait()
                self.queues[ctx.guild_id].task_done()

        await ctx.followup.send("ずんだもんが退室しました．", ephemeral=True)


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if type(message.channel) is discord.TextChannel and type(message.guild) is discord.Guild:
            guild_id = message.guild.id

            if type(self.watch_channels[guild_id]) is discord.TextChannel and message.channel.name == self.watch_channels[guild_id].name:
                await self.enqueue_message(message.content, guild_id)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.User, before: discord.VoiceState, after: discord.VoiceState):
        if ((self.await_message.is_running()) and (member.bot == False) and (before.channel != after.channel)):
            if (before.channel is None):
                message = f"{member.name} が入室したのだ．"
                guild_id = after.channel.guild.id
            elif (after.channel is None):
                message = f"{member.name} が退室したのだ．"
                guild_id = before.channel.guild.id

            await self.enqueue_message(message, guild_id)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Speak(bot))
