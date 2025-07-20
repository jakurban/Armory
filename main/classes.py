import math

from modifiers import SLOT_MODIFIERS, QUALITY_MODIFIERS


class Character:
    def __init__(self, name, level=None, race=None, klass=None, items=None, specs=None, ach_points=0, killed_bosses=None):
        if items is None:
            self.items = []
        self.name = name
        self.level = level
        self.race = race
        self.klass = klass
        self.gs = 0
        self.specs = specs
        self.ach_points = ach_points
        if killed_bosses is None:
            killed_bosses = {
                "Fall of the Lich King 10": {"nm": 0, "hc": 0},
                "Fall of the Lich King 25": {"nm": 0, "hc": 0},
                "Lich King 10-Player Raid": {"nm": 0, "hc": 0},
                "Lich King 25-Player Raid": {"nm": 0, "hc": 0},
            }
        self.killed_bosses = killed_bosses


class Item:
    def __init__(self, url=None, rarity=None, slot=None, ilvl=None, name=None):
        self.url = url
        self.rarity = rarity  # integer 2, 3, 4, 5
        self.slot = slot  # "head", "neck", etc.
        self.ilvl = ilvl  # integer like 264
        self.name = name  # optional item name
        self.gs = self.calculate_item_gs()  # will be computed

    def __str__(self):
        return (
            f"Item: {self.name or "Unknown"}\n"
            f"  Slot: {self.slot or "Unknown"}\n"
            f"  iLvl: {self.ilvl or "Unknown"}\n"
            f"  Rarity: {self.rarity or "Unknown"}\n"
            f"  GearScore: {self.gs if self.gs is not None else "Not Calculated"}\n"
            f"  URL: {self.url}"
        )

    def calculate_item_gs(self):
        gs_formula_section = "A" if self.ilvl > 120 else "B"
        a = QUALITY_MODIFIERS[gs_formula_section][self.rarity]["A"]
        b = QUALITY_MODIFIERS[gs_formula_section][self.rarity]["B"]
        slot_mod = SLOT_MODIFIERS.get(self.slot)
        quality_scale = {0: 0.005, 1: 0.005, 5: 1.3}
        base_score = ((self.ilvl - a) / b) * slot_mod * 1.8618 * quality_scale.get(self.rarity, 1.0)
        return math.floor(base_score)
