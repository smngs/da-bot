import openai
import os
import discord

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
    # embed.add_field(name="Prompt", value=prompt, inline=False)
    # embed.add_field(name="Answer", value=answer, inline=False)

    return embed
