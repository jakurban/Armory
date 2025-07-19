import math

import discord
import requests
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
    scraper = Scraper(character_name=character_name)
    if "The character you are looking for does not exist or does not meet the minimum required level." in scraper.response.text:
        await ctx.send("**Error:** Unable to get the info you need.")
        return

    character = Character(name=character_name, level=scraper.char_level, race=scraper.char_race,
                          klass=scraper.char_klass, ach_points=scraper.ach_points, specs=scraper.specs)

    item_quality = scraper.item_quality()
    item_href = scraper.item_href()

    for i in range(len(item_href)):
        item = await bot.loop.run_in_executor(None, scraper.fetch_item_data, item_href[i], item_quality[i])
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
    #     print(item)
    # print(f"Character:{character.name} - {character.gs} GS")
    await ctx.send(embed=embed_message(character=character))
