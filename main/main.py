import json
import os

from discord_bot import bot


def get_token():
    with open('./secrets.json') as f:
        secrets = json.load(f)
        return secrets["api_token"]


if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if token is None:
        token = get_token()

    bot.run(token)
