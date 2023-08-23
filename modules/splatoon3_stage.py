import discord
from discord import app_commands
from discord.ext import commands

from config.discord import DISCORD_SERVER_ID
import datetime

import aiohttp
import ujson

async def fetch_splatoon3_stage(match: app_commands.Choice):
    url = "https://spla3.yuu26.com"
    async with aiohttp.ClientSession(url, json_serialize=ujson.dumps) as session:
        async with session.get(f"/api/{match.value}/schedule") as r:
            if r.status == 200:
                res = await r.json()
                return res

async def generate_embed(res: dict, match: app_commands.Choice, schedule: bool, user: discord.User):
    match match.value:
        case "regular":
            color = 0xcef522
        case "bankara-open":
            color = 0xf4480e
        case "bankara-challenge":
            color = 0xf4480e
        case "x":
            color = 0x0cdb9a
        case "event":
            color = 0xf1297e
        case "fest":
            color = 0xfbf82a
        case "coop-grouping":
            color = 0xf85e3c
        case "coop-grouping-team-contest":
            color = 0xf85e3c
        case captured:
            color = 0xFFFFFF

    embed = discord.Embed(
        title=match.name,
        color=color,
    )

    embed.set_author(
        name=user.display_name,
        icon_url=user.avatar.url
    )

    if schedule == True:
        times = ["いま", "つぎ", "そのつぎ"]
    else:
        times = ["いま"]

    for i, time in enumerate(times):
        res_json = res["results"][i]

        time_format = "%Y-%m-%dT%H:%M:%S%z"

        start_time = datetime.datetime.strptime(res_json["start_time"], time_format)
        end_time = datetime.datetime.strptime(res_json["end_time"], time_format)

        start_time_text = start_time.strftime("%Y/%m/%d %H:%M")
        end_time_text = end_time.strftime("%H:%M")

        embed.add_field(
            name=f"{time} ({start_time_text} ~ {end_time_text})",
            value="",
            inline=False
        )

        if match.value not in ["coop-grouping", "coop-grouping-team-contest"]:
            rule = res_json["rule"]["name"]
            embed.add_field(
                name="ルール",
                value=f'- {rule}',
                inline=True
            )

            stages = res_json["stages"]
            embed.add_field(
                name="ステージ",
                value=f'- {stages[0]["name"]}\n- {stages[1]["name"]}',
                inline=True
            )

            if match.value == "event":
                event = res_json["event"]
                event_name = event["name"]
                event_desc = event["desc"]
                embed.add_field(
                    name="イベント名",
                    value=f'- {event_name}',
                    inline=False
                )
                embed.add_field(
                    name="イベント説明",
                    value=f'- {event_desc}',
                    inline=False
                )
            embed.set_thumbnail(url=res["results"][0]["stages"][0]["image"])
        else:
            stage = res_json["stage"]
            embed.add_field(
                name="ステージ",
                value=f'- {stage["name"]}',
                inline=True
            )

            weapons = res_json["weapons"]
            embed.add_field(
                name="ブキ",
                value=f'- {weapons[0]["name"]}\n- {weapons[1]["name"]}\n- {weapons[2]["name"]}\n- {weapons[3]["name"]}',
                inline=True
            )
            embed.set_thumbnail(url=res["results"][0]["stage"]["image"])

    return embed

# ---

class Splatoon3Stage(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="splatoon3-stage", description="ゲーム「スプラトゥーン 3」のステージ情報を取得します．")
    @discord.app_commands.describe(
        match="ステージ情報を取得するプレイモードを指定します．",
        schedule="今後のスケジュールを合わせて取得します．"
    )
    @app_commands.choices(match=[
        app_commands.Choice(name="レギュラーマッチ", value="regular"),
        app_commands.Choice(name="バンカラマッチ（チャレンジ）", value="bankara-challenge"),
        app_commands.Choice(name="バンカラマッチ（オープン）", value="bankara-open"),
        app_commands.Choice(name="X マッチ", value="x"),
        app_commands.Choice(name="イベントマッチ", value="event"),
        app_commands.Choice(name="SALMON RUN", value="coop-grouping"),
    ])
    async def send_splatoon3_stage(self, ctx: discord.Interaction, match: app_commands.Choice[str], schedule: bool=False):
        await ctx.response.defer(ephemeral=False)
        res = await fetch_splatoon3_stage(match)
        embed = await generate_embed(res, match, schedule, ctx.user)
        await ctx.followup.send(embed=embed)

async def setup(bot: commands.Bot) -> None:
    if DISCORD_SERVER_ID:
        guild = discord.Object(id=int(DISCORD_SERVER_ID))
        await bot.add_cog(Splatoon3Stage(bot), guild=guild)
    else:
        await bot.add_cog(Splatoon3Stage(bot))
 
