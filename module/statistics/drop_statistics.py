import csv
import shutil

from tqdm import tqdm

from module.base.decorator import cached_property
from module.base.utils import load_image
from module.logger import logger
from module.ocr.al_ocr import AlOcr
from module.ocr.ocr import Ocr
from module.statistics.battle_status import BattleStatusStatistics
from module.statistics.campaign_bonus import CampaignBonusStatistics
from module.statistics.get_items import GetItemsStatistics
from module.statistics.utils import *


class DropStatistics:
    DROP_FOLDER = "./screenshots"
    TEMPLATE_FOLDER = "item_templates"
    TEMPLATE_BASIC = "./assets/stats_basic"
    CNOCR_CONTEXT = "cpu"
    CSV_FILE = "drop_result.csv"
    CSV_OVERWRITE = True
    CSV_ENCODING = "utf-8"

    def __init__(self):
        AlOcr.CNOCR_CONTEXT = DropStatistics.CNOCR_CONTEXT
        Ocr.SHOW_LOG = False
        if not os.path.exists(self.template_folder):
            shutil.copytree(DropStatistics.TEMPLATE_BASIC, self.template_folder)

        self.battle_status = BattleStatusStatistics()
        self.get_items = GetItemsStatistics()
        self.campaign_bonus = CampaignBonusStatistics()
        self.get_items.load_template_folder(self.template_folder)

    @property
    def template_folder(self):
        return os.path.join(DropStatistics.DROP_FOLDER, DropStatistics.TEMPLATE_FOLDER)

    @property
    def csv_file(self):
        return os.path.join(DropStatistics.DROP_FOLDER, DropStatistics.CSV_FILE)

    @staticmethod
    def drop_folder(campaign):
        return os.path.join(DropStatistics.DROP_FOLDER, campaign)

    @cached_property
    def csv_overwrite_check(self):
        """
        Remove existing csv file. This method only run once.
        """
        if DropStatistics.CSV_OVERWRITE:
            if os.path.exists(self.csv_file):
                logger.info(f"Remove existing csv file: {self.csv_file}")
                os.remove(self.csv_file)
        return True

    def parse_template(self, file):
        """
        Extract template from a single file.
        New templates will be given an auto-increased ID.
        """
        images = unpack(load_image(file))
        for image in images:
            if self.get_items.appear_on(image):
                self.get_items.extract_template(image, folder=self.template_folder)
            if self.campaign_bonus.appear_on(image):
                self.campaign_bonus.extract_template(image, folder=self.template_folder)

    def parse_drop(self, file):
        """
        Parse a single file.

        Args:
            file (str):

        Yields:
            list: [timestamp, campaign, enemy_name, drop_type, item, amount]
        """
        ts = os.path.splitext(os.path.basename(file))[0]
        campaign = os.path.basename(os.path.abspath(os.path.join(file, "../")))
        images = unpack(load_image(file))
        enemy_name = "unknown"
        for image in images:
            if self.battle_status.appear_on(image):
                enemy_name = self.battle_status.stats_battle_status(image)
            if self.get_items.appear_on(image):
                for item in self.get_items.stats_get_items(image):
                    yield [
                        ts,
                        campaign,
                        enemy_name,
                        "GET_ITEMS",
                        item.name,
                        item.amount,
                    ]
            if self.campaign_bonus.appear_on(image):
                for item in self.campaign_bonus.stats_get_items(image):
                    yield [
                        ts,
                        campaign,
                        enemy_name,
                        "CAMPAIGN_BONUS",
                        item.name,
                        item.amount,
                    ]

    def extract_template(self, campaign):
        """
        Extract images from a given folder.

        Args:
            campaign (str):
        """
        print("")
        logger.hr(f"Extract templates from {campaign}", level=1)
        for ts, file in tqdm(load_folder(self.drop_folder(campaign)).items()):
            try:
                self.parse_template(file)
            except ImageError as e:
                logger.warning(e)
                continue
            except Exception as e:
                logger.exception(e)
                logger.warning(f"Error on image {ts}")
                continue

    def extract_drop(self, campaign):
        """
        Parse images from a given folder.

        Args:
            campaign (str):
        """
        print("")
        logger.hr(f"extract drops from {campaign}", level=1)
        _ = self.csv_overwrite_check

        with open(
            self.csv_file, "a", newline="", encoding=DropStatistics.CSV_ENCODING
        ) as csv_file:
            writer = csv.writer(csv_file)
            for ts, file in tqdm(load_folder(self.drop_folder(campaign)).items()):
                try:
                    rows = list(self.parse_drop(file))
                    writer.writerows(rows)
                except ImageError as e:
                    logger.warning(e)
                    continue
                except Exception as e:
                    logger.exception(e)
                    logger.warning(f"Error on image {ts}")
                    continue


if __name__ == "__main__":
    # Drop screenshot folder. Default to './screenshots'
    DropStatistics.DROP_FOLDER = "./screenshots"
    # Folder to load templates and save new templates.
    # This will load {DROP_FOLDER}/{TEMPLATE_FOLDER}.
    # If folder doesn't exist, auto copy from './assets/stats_basic'
    DropStatistics.TEMPLATE_FOLDER = "campaign_13_1_template"
    # 'cpu' or 'gpu', default to 'cpu'.
    # Use 'gpu' for faster prediction, but you must have the gpu version of mxnet installed.
    DropStatistics.CNOCR_CONTEXT = "cpu"
    # Name of the output csv file.
    # This will write to {DROP_FOLDER}/{CSV_FILE}.
    DropStatistics.CSV_FILE = "drop_results.csv"
    # If True, remove existing file before extraction.
    DropStatistics.CSV_OVERWRITE = True
    # Usually to be 'utf-8'.
    # For better Chinese export to Excel, use 'gbk'.
    DropStatistics.CSV_ENCODING = "gbk"
    # campaign names to export under DROP_FOLDER.
    # This will load {DROP_FOLDER}/{CAMPAIGN}.
    # Just a demonstration here, you should modify it to your own.
    CAMPAIGNS = ["campaign_13_1"]

    stat = DropStatistics()

    """
    Step 1:
        Uncomment these code and run.
        After run, comment again.
    """
    # for i in CAMPAIGNS:
    #     stat.extract_template(i)

    """
    Step 2:
        Goto {DROP_FOLDER}/{TEMPLATE_FOLDER}.
        Manually rename the templates you interested in.
    """
    pass

    """
    Step 3:
        Uncomment these code and run.
        After run, comment again.
        Results are saved in {DROP_FOLDER}/{CSV_FILE}.
    """
    for i in CAMPAIGNS:
        stat.extract_drop(i)
