import shutil

import numpy as np
from tqdm import tqdm

import module.config.server as server

server.server = "cn"  # Edit your server here.

from module.logger import logger
from module.statistics.battle_status import BattleStatusStatistics
from module.statistics.get_items import GetItemsStatistics
from module.statistics.utils import *

STATUS_ITEMS_INTERVAL = 10


class DropStatistics(BattleStatusStatistics, GetItemsStatistics):
    def __init__(self, folder):
        """
        Args:
            folder (str): Such as <your_drop_screenshot_folder>/campaign_7_2
        """
        self.folder = folder
        self.template_folder = os.path.join(self.folder, "item_template")
        if not os.path.exists(self.template_folder):
            shutil.copytree("./assets/stats_basic", self.template_folder)
        self.load_template_folder(self.template_folder)
        self.battle_status = load_folder(os.path.join(folder, "status"))
        self.get_items = load_folder(os.path.join(folder, "get_items"))
        self.battle_status_timestamp = np.array([int(f) for f in self.battle_status])

    def _items_to_status(self, get_items):
        """
        Args:
            get_items (str): get_items image filename.

        Returns:
            str: battle_status image filename.
        """
        interval = np.abs(self.battle_status_timestamp - int(get_items))
        if np.min(interval) > STATUS_ITEMS_INTERVAL * 1000:
            raise ImageError(f"Timestamp: {get_items}, battle_status image not found.")
        return str(self.battle_status_timestamp[np.argmin(interval)])

    def extract_template(self, image=None, folder=None):
        """
        Extract and save new templates into 'item_template' folder.
        """
        for ts, file in tqdm(self.get_items.items()):
            try:
                image = load_image(file)
                super().extract_template(image, folder=self.template_folder)
            except:
                logger.warning(f"Error image: {ts}")

    def stat_drop(self, timestamp):
        """
        Args:
            timestamp (str): get_items image timestamp.

        Returns:
            list: Drop data.
        """
        get_items = load_image(self.get_items[timestamp])
        battle_status_timestamp = self._items_to_status(timestamp)
        battle_status = load_image(self.battle_status[battle_status_timestamp])

        enemy_name = self.stats_battle_status(battle_status)
        items = self.stats_get_items(get_items)
        data = [
            [timestamp, battle_status_timestamp, enemy_name, item.name, item.amount]
            for item in items
        ]
        return data

    def generate_data(self):
        """
        Yields:
            list: Drop data.
        """
        for ts, file in tqdm(self.get_items.items()):
            try:
                data = self.stat_drop(ts)
                yield data
            except:
                logger.warning(f"Error image: {ts}")


"""
Args:
    FOLDER:   Alas drop screenshot folder.
              Examples: '<your_drop_screenshot_folder>/campaign_7_2'
    CSV_FILE: Csv file to save.
              Examples: 'c72.csv'
"""
FOLDER = ""
CSV_FILE = ""
drop = DropStatistics(FOLDER)

"""
First run:
    1. Uncomment this, and run.
    2. Rename templates in <your_drop_screenshot_folder>/campaign_7_2/item_template, for example.
"""
# drop.extract_template()

"""
Second Run:
    1. Comment the code in first run.
    2. Uncomment this, and run.
"""
# import csv
# with open(CSV_FILE, 'a', newline='', encoding='utf-8') as csv_file:
#     writer = csv.writer(csv_file)
#     for d in drop.generate_data():
#         writer.writerows(d)
