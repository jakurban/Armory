import re

import requests
from bs4 import BeautifulSoup
from discord.utils import cached_property

from classes import Item


class Scraper:
    headers = {"User-Agent": "Mozilla/5.0"}

    def __init__(self, character_name):
        self.url = f"https://armory.warmane.com/character/{character_name}/Lordaeron/summary"
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.response = requests.get(self.url, headers=self.headers)
        self.soup = BeautifulSoup(self.response.text, "html.parser")

    @cached_property
    def _char_info(self):
        char_page = self.soup.find("div", {"class": "level-race-class"})
        return char_page.contents[0].split()

    @property
    def char_level(self):
        return self._char_info[1]

    @property
    def char_race(self):
        return self._char_info[2]

    @property
    def char_klass(self):
        return self._char_info[-2].replace(",", "")

    @property
    def ach_points(self):
        return int(self.soup.find("div", {"class": "achievement-points"}).text)

    @cached_property
    def items(self):
        return self.soup.find("div", {"class": "item-model"})

    @property
    def specs(self):
        specs = self.soup.find("div", {"class": "specialization"})
        first = specs.contents[1].text.strip().split()[0]
        second = specs.contents[3].text.strip().split()[0]
        return f"{first}/{second}"

    def item_quality(self):
        items = self.items.find_all("div", {"class": "icon-quality"})
        return [icon_quality["class"][1][-1] for icon_quality in items if "icon-quality" in icon_quality["class"][1]]

    def item_href(self):
        return [a.get("href") for a in self.items.find_all("a") if "wotlk.cavernoftime.com/item=" in a.get("href")]

    def fetch_item_data(self, item_href, item_quality):
        response = requests.get(item_href, headers=self.headers)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()
        match = re.search(r"Item Level\s*(\d+)", text)
        slot = None
        for slot_name in [
            "Head", "Neck", "Shoulder", "Back", "Chest", "Wrist", "Hands",
            "Waist", "Legs", "Feet", "Finger", "Trinket", "Thrown",
            "Main Hand", "Off-Hand", "One-hand", "Two-hand", "Ranged", "Shield", "Relic"
        ]:
            partial = text.strip().split("Item Level")[0].split("Binds when")
            if len(partial) < 2: continue
            if slot_name in partial[1]:
                slot = slot_name.strip().lower().replace(" ", "")
        if slot is None: return None
        if match:
            return Item(ilvl=int(match.group(1)), rarity=int(item_quality), slot=slot, url=item_href)
