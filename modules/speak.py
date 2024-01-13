import discord
from discord import app_commands
from discord.ext import tasks, commands

from config.discord import DISCORD_SERVER_ID
from db.client import db

import ujson
from datetime import datetime

import aiohttp
import asyncio

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

async def get_voicevox_dict():
    async with aiohttp.ClientSession("http://voicevox:50021", json_serialize=ujson.dumps) as session:
        async with session.get("/user_dict") as r:
            if r.status == 200:
                response_json = await r.json()
                return response_json
            else:
                return None

async def post_voicevox_dict(surface: str, pronunciation: str, accent_type: int):
    query_payload = {"surface": surface, "pronunciation": pronunciation, "accent_type": accent_type}
    async with aiohttp.ClientSession("http://voicevox:50021", json_serialize=ujson.dumps) as session:
        async with session.post("/user_dict_word", params=query_payload) as r:
            if r.status == 200:
                return r.text
            else:
                return None

async def put_voicevox_dict(uuid: str, surface: str, pronunciation: str, accent_type: int):
    query_payload = {"surface": surface, "pronunciation": pronunciation, "accent_type": accent_type}
    async with aiohttp.ClientSession("http://voicevox:50021", json_serialize=ujson.dumps) as session:
        async with session.put(f"/user_dict_word/{uuid}", params=query_payload) as r:
            if r.status == 204:
                return r.text
            else:
                return None

async def delete_voicevox_dict(uuid: str):
    async with aiohttp.ClientSession("http://voicevox:50021", json_serialize=ujson.dumps) as session:
        async with session.delete(f"/user_dict_word/{uuid}") as r:
            if r.status == 204:
                return r.text
            else:
                return None

async def get_voicevox_speaker(guild_id: int, user_id: int) -> int:
    speaker_collection = db["voicevox_speaker"]
    speaker = await speaker_collection.find_one({
        "guild_id": guild_id,
        "user_id": user_id
    })

    if speaker is None:
        # 登録がない場合はずんだもん（あまあま）を利用
        return 1 

    return speaker["speaker_id"]

async def regist_voicevox_speaker(guild_id: int, user_id: int, speaker_id: int) -> None:
    speaker_collection = db["voicevox_speaker"]

    # 一旦取得して，なければ新しくつっこむ
    speaker = await speaker_collection.find_one({
        "guild_id": guild_id,
        "user_id": user_id
    })

    set_speaker = {
        "guild_id": guild_id,
        "user_id": user_id,
        "speaker_id": speaker_id
    }

    if speaker is None:
        await speaker_collection.insert_one(set_speaker)
    else:
        await speaker_collection.update_one(
            {
                "_id": speaker["_id"]
            }, {
                "$set": set_speaker
            }
        )

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


    async def enqueue_message(self, text: str, guild_id: int, speaker_id: int=1) -> None:
        """
        VoiceVox によって音声を生成し，そのファイルパスを enqueue する．
        この関数はずんだもんが VC 内にいるときに実行されることが保証される．
        """
        now = datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')
        file_path = f"./tmp/output_{now}.wav"
        await synthesis(text, file_path, speaker_id)
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

    @app_commands.command(name="speak-dict", description="読み上げ Bot の発音辞書を追加します．この辞書はサーバ全体で共有されます．")
    @discord.app_commands.describe(
        method="実行する内容を選択します．",
        surface="言葉の表層系を表します．読み上げの対象となる単語を，漢字や英語で入力してください．",
        pronunciation="言葉の発音をカタカナで入力します．",
        accent_type="アクセント位置（音が下がる場所）を，先頭文字を 1 とする整数値で入力します．例えば「テスト（→↓↓）」の場合は 1 を入力します．"
    )
    @discord.app_commands.choices(method=[
        app_commands.Choice(name="確認 (GET)", value="get"),
        app_commands.Choice(name="追加 (POST)", value="post"),
        app_commands.Choice(name="変更 (PUT)", value="put"),
        app_commands.Choice(name="削除 (DELETE)", value="delete")
    ])
    async def send_speak_dict(self, ctx: discord.Interaction, method: str, surface: str="", pronunciation: str="", accent_type: int=0, uuid: str=""):
        await ctx.response.defer(ephemeral=True)

        if (method == "get"):
            response = await get_voicevox_dict()
            if response is None:
                await ctx.followup.send("閲覧に失敗しました．")
            else:
                response_text = "辞書内容\n\n"

                for key, value in response.items():
                    response_text += f"`UUID`: `{key}`\n`surface`: `{value['surface']}`, `pronunciation`: `{value['pronunciation']}`, `accent_type`: `{value['accent_type']}`\n\n"

                await ctx.followup.send(response_text, ephemeral=True)

        elif (method == "post"):
            new_uuid = await post_voicevox_dict(surface, pronunciation, accent_type)
            if new_uuid is None:
                await ctx.followup.send("登録に失敗しました．")
            else:
                await ctx.followup.send("登録に成功しました．")

        elif (method == "put"):
            response_json = await put_voicevox_dict(uuid, surface, pronunciation, accent_type)
            if response_json is None:
                await ctx.followup.send("変更に失敗しました．")
            else:
                await ctx.followup.send("変更に成功しました．")

        elif (method == "delete"):
            response_json = await delete_voicevox_dict(uuid)
            if response_json is None:
                await ctx.followup.send("削除に失敗しました．")
            else:
                await ctx.followup.send("削除に成功しました．")


    @app_commands.command(name="speak-set", description="読み上げ Bot における話者を選択します．")
    @discord.app_commands.describe(
        speaker = "設定する話者を選択します．"
    )
    @discord.app_commands.choices(speaker=[
        app_commands.Choice(name="ずんだもん（あまあま）", value=1),
        app_commands.Choice(name="ずんだもん（ノーマル）", value=3),
        app_commands.Choice(name="ずんだもん（ツンツン）", value=7),
        app_commands.Choice(name="ずんだもん（セクシー）", value=5),
        app_commands.Choice(name="ずんだもん（ささやき）", value=22),
        app_commands.Choice(name="ずんだもん（ヒソヒソ）", value=38),
        app_commands.Choice(name="ずんだもん（ヘロヘロ）", value=75),
        app_commands.Choice(name="ずんだもん（なみだめ）", value=76),
        app_commands.Choice(name="春日部つむぎ", value=8),
        app_commands.Choice(name="四国めたん", value=2),
        app_commands.Choice(name="冥鳴ひまり", value=14),
        app_commands.Choice(name="中国うさぎ", value=61),
        app_commands.Choice(name="栗田まろん", value=67),
        app_commands.Choice(name="白上虎太郎", value=12),
        app_commands.Choice(name="青山龍星", value=13),
        app_commands.Choice(name="ちび式じい", value=42),
    ])
    async def send_speak_set(self, ctx: discord.Interaction, speaker: int):
        await ctx.response.defer(ephemeral=True)
        await regist_voicevox_speaker(ctx.guild_id, ctx.user.id, speaker)
        await ctx.followup.send(f"登録しました．")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if type(message.channel) is discord.TextChannel and type(message.guild) is discord.Guild:
            guild_id = message.guild.id
            user_id = message.author.id

            if type(self.watch_channels[guild_id]) is discord.TextChannel and message.channel.name == self.watch_channels[guild_id].name:
                speaker_id = await get_voicevox_speaker(guild_id, user_id)
                await self.enqueue_message(message.content, guild_id, speaker_id)

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
    if DISCORD_SERVER_ID:
        guild = discord.Object(id=int(DISCORD_SERVER_ID))
        await bot.add_cog(Speak(bot), guild=guild)
    else:
        await bot.add_cog(Speak(bot))
