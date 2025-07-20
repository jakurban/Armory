import math

import discord
from discord.ext import commands

from classes import Character
from modifiers import IMAGES
from scraper import Scraper

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


def embed_message(character):
    embed = discord.Embed(
        title=f"{character.name} ({character.level})",
        description=f"{f"{character.specs}"}",
        color=discord.Color.yellow()
    )
    embed.set_thumbnail(url=IMAGES[character.klass])  # Replace with actual thumbnail URL
    embed.add_field(name="Gear Score", value=f"{character.gs}", inline=True)
    embed.add_field(name="Achievement Points", value=f"{character.ach_points}", inline=True)

    embed.add_field(
        name="Icecrown Citadel",
        value=(
            f"`{character.killed_bosses["Fall of the Lich King 10"]["nm"]}/12` icc10 NM\n"
            f"`{character.killed_bosses["Fall of the Lich King 10"]["hc"]}/12` icc10 HC\n"
            f"`{character.killed_bosses["Fall of the Lich King 25"]["nm"]}/12` icc25 NM\n"
            f"`{character.killed_bosses["Fall of the Lich King 25"]["hc"]}/12` icc25 HC"
        ),
        inline=False
    )

    rs_string = "   "
    if character.killed_bosses["Lich King 10-Player Raid"]["nm"] == 1:
        rs_string += "✅ rs10 NM\n"
    if character.killed_bosses["Lich King 10-Player Raid"]["hc"] == 1:
        rs_string += "✅ rs10 HC\n"
    if character.killed_bosses["Lich King 25-Player Raid"]["nm"] == 1:
        rs_string += "✅ rs25 NM\n"
    if character.killed_bosses["Lich King 25-Player Raid"]["hc"] == 1:
        rs_string += "✅ rs25 HC\n"

    embed.add_field(
        name="Ruby Sanctum",
        value=rs_string,
        inline=False
    )
    return embed


def build_character(character_name):
    scraper = Scraper(character_name=character_name)
    if "The character you are looking for does not exist or does not meet the minimum required level." in scraper.response.text:
        return None
    killed_bosses = scraper.killed_bosses if int(scraper.char_level) == 80 else None
    character = Character(name=character_name, level=scraper.char_level, race=scraper.char_race,
                          klass=scraper.char_klass, ach_points=scraper.ach_points, specs=scraper.specs,
                          killed_bosses=killed_bosses)
    item_quality = scraper.item_quality()
    item_href = scraper.item_href()

    for i in range(len(item_href)):
        item = scraper.fetch_item_data(item_href[i], item_quality[i])
        if item is None: continue
        if character.klass == "Hunter":
            if item.slot == "ranged":
                item.gs = math.floor(item.gs * 5.3224)
            if item.slot == "two-hand":
                item.gs = math.floor(item.gs * 0.3164)

        if item: character.items.append(item)

    if character.klass == "Warrior":
        titan_grip = [item for item in character.items if item.slot == "two-hand"]
        if len(titan_grip) == 2:
            for weapon in titan_grip:
                weapon.gs = math.floor(weapon.gs / 2)

    for item in character.items:
        character.gs += item.gs
    return embed_message(character)


@bot.command()
async def user(ctx, character_name):
    character = await bot.loop.run_in_executor(None, build_character, character_name)
    if character is None:
        await ctx.send("**Error:** Unable to get the info you need.")
    else:
        await ctx.send(embed=character)
