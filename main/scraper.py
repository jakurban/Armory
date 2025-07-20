import logging
import re
from time import sleep

import requests
from bs4 import BeautifulSoup
from discord.utils import cached_property
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from classes import Item
from modifiers import ACHIEVEMENTS


class Scraper:
    headers = {"User-Agent": "Mozilla/5.0"}
    earned_achs = {
        "Fall of the Lich King 10": {"nm": 0, "hc": 0},
        "Fall of the Lich King 25": {"nm": 0, "hc": 0},
        "Lich King 10-Player Raid": {"nm": 0, "hc": 0},
        "Lich King 25-Player Raid": {"nm": 0, "hc": 0},
    }
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[logging.StreamHandler()]
    )

    def __init__(self, character_name):
        self.url = f"https://armory.warmane.com/character/{character_name}/Lordaeron/summary"
        self.ach_url = f"https://armory.warmane.com/character/{character_name}/Lordaeron/achievements"
        self.headers = {"User-Agent": "Mozilla/5.0"}
        self.logger = logging.getLogger('discord_bot')
        self.logger.info(f"Getting data from {self.url}")
        self.response = requests.get(self.url, headers=self.headers)
        self.soup = BeautifulSoup(self.response.text, "html.parser")
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(options=self.options)

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
        klass = self._char_info[-2].replace(",", "")
        if klass == "Knight":
            return "Death Knight"
        return klass

    @cached_property
    def ach_points(self):
        return int(self.soup.find("div", {"class": "achievement-points"}).text)

    @cached_property
    def items(self):
        return self.soup.find("div", {"class": "item-model"})

    @cached_property
    def specs(self):
        self.logger.info(f"Getting specs")
        specs = self.soup.find("div", {"class": "specialization"})
        first = specs.contents[1].text.strip().split()[0]
        second = ""
        if len(specs.contents) > 3:
            second = specs.contents[3].text.strip().split()[0]
        return f"{first}/{second}"

    def item_quality(self):
        items = self.items.find_all("div", {"class": "icon-quality"})
        return [icon_quality["class"][1][-1] for icon_quality in items if "icon-quality" in icon_quality["class"][1]]

    def item_href(self):
        return [a.get("href") for a in self.items.find_all("a") if "wotlk.cavernoftime.com/item=" in a.get("href")]

    def fetch_item_data(self, item_href, item_quality):
        self.logger.info(f"Getting item data from {item_href}")
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

    @cached_property
    def achievements(self):
        self.logger.info(f"Getting achievements data from {self.ach_url}")
        self.driver.get(self.ach_url)
        self.driver.find_element(By.LINK_TEXT, "Dungeons & Raids").click()
        for page in ACHIEVEMENTS.keys():
            self.driver.find_element(By.LINK_TEXT, page).click()
            sleep(1)
            for diff in ACHIEVEMENTS[page].keys():
                self.logger.info(f"Checking achievements for {page} {diff}")
                for ach, ach_value in ACHIEVEMENTS[page][diff].items():
                    if "locked" not in self.driver.find_element(value=ach_value).get_attribute("class"):
                        self.earned_achs[page][diff] = ach
        return self.earned_achs
