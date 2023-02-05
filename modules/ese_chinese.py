import MeCab
import sys
import discord

def generate_embed(prompt: str, user: discord.User) -> discord.Embed:
    embed = discord.Embed(
        title=prompt,
        color=0xe60012,
    )
    embed.set_author(
        name=user.display_name,
        icon_url=user.avatar.url,
    )
    return embed

def get_wordclass(text: str) -> list:
    tagger = MeCab.Tagger()
    node = tagger.parseToNode(text)
    node_list = []

    while node:
        word = node.surface
        types = node.feature.split(',')

        if types[0] != "BOS/EOS":
            node_list.append({
                "word": word,
                "types": [type for type in types[0:5]]
            })

        node = node.next

    return node_list

def hira_to_blank(text: str) -> str:
    return "".join(["" if ("ぁ" <= ch <= "ん") else ch for ch in text])

def to_esechinese(text: str) -> str:
    token_list = get_wordclass(text)
    chinese_list = []

    for i, token in enumerate(token_list):
        word = token["word"]
        types = token["types"]
        prime = word

        # 助詞はスキップ
        if (types[0] == "助詞"):
            continue

        # 名詞，連体詞の処理
        if (word == "私") or (word == "俺") or (word == "わたし") or (word == "おれ"):
            prime = "我"
        elif (word == "君") or (word == "きみ") or (word == "あなた"):
            prime = "君" # TODO: 文字化け
        elif (types[0] == "連体詞") or (types[0] == "形容詞"):
            prime = word + "的"

        if (types[0] == "感動詞"):
            if (word == "おはよう") or (word == "こんにちは") or (word == "こんばんは"):
                prime = "你好"
            elif (word == "ありがとう"):
                prime = "謝謝茄子"

        # 文末の処理
        if (i == len(token_list)-1) or (token_list[i+1]["word"] == "。") or (token_list[i+1]["word"] == "．"):
            # 助動詞
            match types[0]:
                case "助動詞":
                    if (word == "する") or (word == "ます"):
                        prime = word + "也"
                    elif (word == "たい"):
                        prime = word + "希望"
                    elif (word == "ない"):
                        prime = word + "無"
                    else:
                        prime = word + "了"
                case "形容詞":
                    if (word == "ない"):
                        prime = word + "否"
                case "補助記号": 
                    # 感動詞
                    if ((word == "？") or (word == "?")):
                        prime = "如何？"

        chinese_list.append(hira_to_blank(prime))

    return "".join(chinese_list)


if __name__ == "__main__":
    print(to_esechinese(sys.argv[1]))
