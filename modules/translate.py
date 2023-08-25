import os
import io
import copy

import discord
from discord import app_commands
from discord.ext import commands

import json
import ujson
import asyncio
import aiohttp

from config.discord import DISCORD_SERVER_ID
from config.deepl import DEEPL_API_KEY 

async def get_deepl_translate(text, source_lang, target_lang):
    headers = {
        "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}",
        "Content-Type": "application/json"
    }
    data_json = {
        "text": [
            text
        ],
        "source_lang": source_lang,
        "target_lang": target_lang
    }

    async with aiohttp.ClientSession("https://api-free.deepl.com", json_serialize=ujson.dumps) as session:
        async with session.post("/v2/translate", headers=headers, json=data_json) as r:
            if r.status == 200:
                json_body = await r.json()
                return json_body["translations"][0]["text"]
            else:
                return r.text

class TranslateDocument:
    def __init__(self, document: bytes, document_name: str, source_lang: str, target_lang: str):
        self.document = document
        self.document_name = document_name
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.document_id = -1
        self.document_key = -1

    async def upload(self):
        headers = {
            "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}"
        }

        async with aiohttp.ClientSession("https://api-free.deepl.com", json_serialize=ujson.dumps) as session:
            with aiohttp.MultipartWriter("form-data") as mp:
                part = mp.append(self.source_lang)
                part.set_content_disposition("form-data", name="source_lang")

                part = mp.append(self.target_lang)
                part.set_content_disposition("form-data", name="target_lang")

                part = mp.append(self.document)
                part.set_content_disposition('form-data', name="file", filename=self.document_name)

                async with session.post("/v2/document", headers=headers, data=mp) as r:
                    if r.status == 200:
                        json_body = await r.json()
                        self.document_id = json_body["document_id"]
                        self.document_key = json_body["document_key"]
                        return True
                    else:
                        return False

    async def check_translate(self):
        if self.document_id == -1:
            return { "status": "not uploaded" }

        headers = {
            "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}",
            "Content-Type": "application/json"
        }
        data_json = {
            "document_key": self.document_key
        }

        async with aiohttp.ClientSession("https://api-free.deepl.com", json_serialize=ujson.dumps) as session:
            async with session.post(f"/v2/document/{self.document_id}", headers=headers, json=data_json) as r:
                if r.status == 200:
                    json_body = await r.json()
                    status = json_body["status"]
                    
                    if (status == "translating"):
                        return {
                            "status": status,
                            "seconds_remaining": json_body["seconds_remaining"]
                        }
                    else:
                        return { "status": status }

                else:
                    return { "status": r.text }


    async def download(self):
        if self.document_id == -1:
            return { "status": "not uploaded" }

        headers = {
            "Authorization": f"DeepL-Auth-Key {DEEPL_API_KEY}",
            "Content-Type": "application/json"
        }
        data_json = {
            "document_key": self.document_key
        }

        async with aiohttp.ClientSession("https://api-free.deepl.com", json_serialize=ujson.dumps) as session:
            async with session.post(f"/v2/document/{self.document_id}/result", headers=headers, json=data_json) as r:
                if r.status == 200:
                    translated_doc_byte = io.BytesIO()
                    chunk_size = 4
                    async for chunk in r.content.iter_chunked(chunk_size):
                        translated_doc_byte.write(chunk)
                    translated_doc_byte.seek(0)
                    return translated_doc_byte
                else:
                    return { "status": r.text }

def generate_embed(source_lang: str, target_lang: str, user: discord.User) -> discord.Embed:
    embed = discord.Embed(
        title=f"DeepL Translation ({source_lang} → {target_lang})",
        color=0x2f343d,
    )
    embed.set_author(
        name=user.display_name,
        icon_url=user.avatar.url,
    )
    return embed

def write_txtfile(text: str):
    fp = io.StringIO()
    for c in text:
        fp.write(c)
        if (c == ".") or (c == "．") or (c == "。"):
            fp.write("\n")
    fp.seek(0)
    return fp

class Translate(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def translate(self, ctx: discord.Interaction, text: str, source_lang: str="JA", target_lang: str="EN"):
        await ctx.response.defer()
        #  await ctx.followup.send(embed=generate_embed(text, ctx.user))
        async with ctx.channel.typing():
            answer = await get_deepl_translate(text, source_lang, target_lang)

        embed = generate_embed(source_lang, target_lang, ctx.user)

        if len(text) >= 1000 or len(answer) >= 1000:
            await ctx.followup.send(embed=embed)

            fp = write_txtfile(text)
            await ctx.followup.send(file=discord.File(fp, filename="original.txt"))

            fp = write_txtfile(answer)
            await ctx.followup.send(file=discord.File(fp, filename="translated.txt"))

        else:
            embed.add_field(
                name=f"Original ({source_lang})",
                value=f"```{text}```",
                inline=False
            )

            embed.add_field(
                name=f"Translate ({target_lang})",
                value=f"```{answer}```",
                inline=False
            )
            await ctx.followup.send(embed=embed)

    @app_commands.command(name="translate", description="与えられた文章を翻訳します．")
    @discord.app_commands.describe(
        text="翻訳する文章を入力します．",
        source_lang="原文の言語を指定します．",
        target_lang="翻訳文の言語を指定します．"
    )
    async def send_translate(self, ctx: discord.Interaction, text: str, source_lang: str="JA", target_lang: str="EN"):
        await self.translate(ctx, text, source_lang, target_lang)

    @app_commands.command(name="translate_ja", description="与えられた文章を英語から日本語に翻訳します．")
    @discord.app_commands.describe(
        text="翻訳する文章を入力します．",
    )
    async def send_translate_ja(self, ctx: discord.Interaction, text: str):
        await self.translate(ctx, text, "EN", "JA")

    @app_commands.command(name="translate_en", description="与えられた文章を日本語から英語に翻訳します．")
    @discord.app_commands.describe(
        text="翻訳する文章を入力します．",
    )
    async def send_translate_en(self, ctx: discord.Interaction, text: str):
        await self.translate(ctx, text, "JA", "EN")

    async def translate_doc(self, ctx: discord.Interaction, document: discord.Attachment, source_lang: str="JA", target_lang: str="EN"):
        await ctx.response.defer()

        document_byte = io.BytesIO()
        await document.save(document_byte)
        document_name = document.filename
        document_byte.seek(0)

        origin_doc = copy.deepcopy(document_byte)
        origin_file = discord.File(origin_doc, filename=f"origin_{document_name}")

        embed = generate_embed(source_lang, target_lang, ctx.user)
        embed.add_field(name="ファイルを受け取りました．DeepL のサーバにアップロードしています……", value="", inline=False)
        message = await ctx.followup.send(file=origin_file, embed=embed)

        translate = TranslateDocument(document_byte, document_name, source_lang, target_lang)
        result = await translate.upload()

        if result == False:
            embed.remove_field(0)
            embed.add_field(name="アップロードに失敗しました．やり直してください．", value="")
            await ctx.followup.edit_message(message_id=message.id, embed=embed)
            return
        else:
            embed.remove_field(0)
            embed.add_field(name="アップロードに成功しました．", value=f"- ID: `{translate.document_id}`\n- KEY: `{translate.document_key}`")
            await ctx.followup.edit_message(message_id=message.id, embed=embed)

        while True:
            progress = await translate.check_translate()
            embed.remove_field(0)

            if progress["status"] == "done":
                embed.add_field(name="翻訳に成功しました．アップロード中です……", value=f"- ID: `{translate.document_id}`\n- KEY: `{translate.document_key}`")
                await ctx.followup.edit_message(message_id=message.id, embed=embed)
                break

            elif progress["status"] == "error":
                embed.add_field(name="翻訳に失敗しました．", value=f"- ID: `{translate.document_id}`\n- KEY: `{translate.document_key}`")
                await ctx.followup.edit_message(message_id=message.id, embed=embed)
                return

            elif progress["status"] == "translating":
                embed.add_field(name=f"翻訳中です…… ({progress['status']}, 残り {progress['seconds_remaining']} 秒)", value=f"- ID: `{translate.document_id}`\n- KEY: `{translate.document_key}`")

            else:
                embed.add_field(name=f"翻訳中です…… ({progress['status']})", value=f"- ID: `{translate.document_id}`\n- KEY: `{translate.document_key}`")

            await ctx.followup.edit_message(message_id=message.id, embed=embed)
            await asyncio.sleep(1)

        translated_doc = await translate.download()
        file = discord.File(translated_doc, filename=f"translated_{document_name}")

        embed.remove_field(0)
        embed.add_field(name="翻訳に成功しました．", value=f"- ID: `{translate.document_id}`\n- KEY: `{translate.document_key}`")
        await ctx.followup.edit_message(message_id=message.id, embed=embed)
        await ctx.followup.send(file=file)

    @app_commands.command(name="translate_doc", description="与えられたドキュメントを翻訳します．PDF ファイルや Word ファイルなどに対応しています．")
    @discord.app_commands.describe(
        document="翻訳するドキュメントを指定します．",
        source_lang="原文の言語を指定します．",
        target_lang="翻訳文の言語を指定します．"
    )
    async def send_translate_doc(self, ctx: discord.Interaction, document: discord.Attachment, source_lang: str="JA", target_lang: str="EN"):
        await self.translate_doc(ctx, document, source_lang, target_lang)


    @app_commands.command(name="translate_doc_en", description="与えられたドキュメントを日本語から英語に翻訳します．PDF ファイルや Word ファイルなどに対応しています．")
    @discord.app_commands.describe(
        document="翻訳するドキュメントを指定します．",
    )
    async def send_translate_doc_en(self, ctx: discord.Interaction, document: discord.Attachment):
        await self.translate_doc(ctx, document, "JA", "EN")

    @app_commands.command(name="translate_doc_ja", description="与えられたドキュメントを英語から日本語に翻訳します．PDF ファイルや Word ファイルなどに対応しています．")
    @discord.app_commands.describe(
        document="翻訳するドキュメントを指定します．",
    )
    async def send_translate_doc_ja(self, ctx: discord.Interaction, document: discord.Attachment):
        await self.translate_doc(ctx, document, "EN", "JA")

async def setup(bot: commands.Bot) -> None:
    if DISCORD_SERVER_ID:
        guild = discord.Object(id=int(DISCORD_SERVER_ID))
        await bot.add_cog(Translate(bot), guild=guild)
    else:
        await bot.add_cog(Translate(bot))
