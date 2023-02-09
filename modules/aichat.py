import os
import discord
from discord import app_commands
from discord.ext import commands

# サーバコマンドを設定するギルド
DISCORD_SERVER_KEY = os.environ.get("DISCORD_SERVER_KEY")
guild = discord.Object(id=DISCORD_SERVER_KEY)

import openai

class AIChat:
    def __init__(self):
        openai.api_key = os.environ.get('OPENAI_API_KEY')

    def response(self, prompt: str):
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=1024,
            temperature=0.5,
        )

        answer = response['choices'][0]['text']
        return answer

def trigger_chat(prompt: str):
    chatai = AIChat()
    response = chatai.response(prompt)
    return response

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

    @app_commands.command(name="chat", description="GPT-3 とおしゃべりします．")
    @app_commands.guilds(guild)
    @discord.app_commands.describe(
        prompt="GPT-3 に話しかける内容です．"
    )
    async def send_chat(self, ctx: discord.Interaction, prompt: str):
        await ctx.response.defer()
        await ctx.followup.send(embed=generate_embed(prompt, ctx.user))
        async with ctx.channel.typing():
            answer = trigger_chat(prompt)
        await ctx.followup.send(answer)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Chat(bot))
