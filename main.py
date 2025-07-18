import json
import math
import re

import discord
import requests
from bs4 import BeautifulSoup
from discord.ext import commands

from classes import Character, Item

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


def embed_message(character):
    embed = discord.Embed(
        title=f"{character.name} ({character.level})",
        description=f"{character.klass}",
        color=discord.Color.yellow()
    )
    # embed.set_thumbnail(url="https://example.com/image.png")  # Replace with actual thumbnail URL

    embed.add_field(name="GearScore", value=f"{character.gs}", inline=True)

    # embed.add_field(
    #     name="Icecrown Citadel",
    #     value=(
    #         "`9/12` 10-man NM\n"
    #         "`7/12` 10-man HC\n"
    #         "`12/12` 25-man NM\n"
    #         "`12/12` 25-man HC"
    #     ),
    #     inline=False
    # )

    # embed.add_field(
    #     name="Ruby Sanctum",
    #     value="✅ 25-man NM\n✅ 25-man HC",
    #     inline=False
    # )
    return embed


@bot.command()
async def user(ctx, character_name):
    url = f"https://armory.warmane.com/character/{character_name}/Lordaeron/summary"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if "The character you are looking for does not exist or does not meet the minimum required level." in response.text:
        await ctx.send("**Error:** Unable to get the info you need.")
        return
    soup = BeautifulSoup(response.text, "html.parser")
    char_page = soup.find("div", {"class": "level-race-class"})
    char_info = char_page.contents[0].split()
    character = Character(name=character_name, level=char_info[1], race=char_info[2],
                          klass=char_info[-2].replace(",", ""))
    item_left = soup.find("div", {"class": "item-left"})
    item_right = soup.find("div", {"class": "item-right"})
    item_bottom = soup.find("div", {"class": "item-bottom"})
    for html_snippet in [item_left, item_right, item_bottom]:
        item_quality = [icon_quality.attrs["class"][1][-1] for icon_quality in
                        html_snippet.find_all("div", {"class": "icon-quality"}) if
                        "icon-quality" in icon_quality.attrs["class"][1]]
        item_href = [a.get("href") for a in html_snippet.find_all("a") if
                     "wotlk.cavernoftime.com/item=" in a.get("href")]
        for i in range(len(item_href)):
            item_url = item_href[i]
            response = requests.get(item_url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()
            match = re.search(r"Item Level\s*(\d+)", text)
            for slot_name in [
                "Head", "Neck", "Shoulder", "Back", "Chest", "Wrist", "Hands",
                "Waist", "Legs", "Feet", "Finger", "Trinket", "Thrown",
                "Main Hand", "Off Hand", "One-hand", "Two-hand", "Ranged", "Shield", "Relic"
            ]:
                partial = text.strip().split("Item Level")[0].split("Binds when")
                if len(partial) < 2: continue
                if slot_name in partial[1]:
                    slot = slot_name.strip().lower().replace(" ", "")
            if match:
                character.items.append(
                    Item(ilvl=int(match.group(1)), rarity=int(item_quality[i]), slot=slot, url=item_url))

    if character.klass == "Warrior":
        titan_grip = [item for item in character.items if item.slot == "two-hand"]
        if len(titan_grip) == 2:
            for weapon in titan_grip:
                weapon.gs = math.floor(weapon.gs / 2)
    if character.klass == "Hunter":
        ranged = [item for item in character.items if item.slot == "ranged"][0]
        ranged.gs = math.floor(ranged.gs * 5.3224)
        melee = [item for item in character.items if item.slot == "two-hand"][0]
        melee.gs = math.floor(melee.gs * 0.3164)

    for item in character.items:
        character.gs += item.gs
        print(item)
    print(f"Character:{character.name} - {character.gs} GS")
    await ctx.send(embed=embed_message(character=character))

def get_token():
    with open('secrets.json') as f:
        secrets = json.load(f)
        return secrets["api_token"]

bot.run(get_token())
