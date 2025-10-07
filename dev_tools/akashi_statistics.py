import csv
from tqdm import tqdm
from typing import List

from module.base.decorator import cached_property, run_once
from module.base.utils import load_image
from module.logger import logger
from module.ocr.al_ocr import AlOcr
from module.ocr.ocr import Ocr
from module.os_shop.akashi_shop import AkashiShop
from module.os_shop.item import OSShopItem as Item
from module.statistics.utils import *


class AkashiStatistics(AkashiShop):
    DROP_FOLDER = './screenshots'
    CNOCR_CONTEXT = 'cpu'
    CSV_FILE = 'drop_result.csv'
    CSV_OVERWRITE = True
    CSV_ENCODING = 'utf-8'
    COLUMNS = ['File Name', 'Item Name', 'Item Amount']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        AlOcr.CNOCR_CONTEXT = AkashiStatistics.CNOCR_CONTEXT
        Ocr.SHOW_LOG = False

    def os_shop_get_items_in_akashi(self, image) -> List[Item]:
        """
        Args:
            image (np.ndarray): image to detect

        Returns:
            list[Item]:
        """
        self.os_akashi_shop_items.predict(image)

        items = self.os_akashi_shop_items.items
        if len(items):
            min_row = self.os_akashi_shop_items.grids[0, 0].area[1]
            row = [str(item) for item in items if item.button[1] == min_row]
            logger.info(f'Shop row 1: {row}')
            row = [str(item) for item in items if item.button[1] != min_row]
            logger.info(f'Shop row 2: {row}')
            return items
        else:
            logger.info('No shop items found')
            return []

    @property
    def csv_file(self):
        return os.path.join(AkashiStatistics.DROP_FOLDER, AkashiStatistics.CSV_FILE)

    @staticmethod
    def drop_folder(campaign):
        return os.path.join(AkashiStatistics.DROP_FOLDER, campaign)

    @cached_property
    def csv_overwrite_check(self):
        """
        Remove existing csv file. This method only run once.
        """
        if AkashiStatistics.CSV_OVERWRITE:
            if os.path.exists(self.csv_file):
                logger.info(f'Remove existing csv file: {self.csv_file}')
                os.remove(self.csv_file)
        return True

    @staticmethod
    @run_once
    def csv_write_column_name(writer, columns):
        writer.writerows([columns])

    last = None

    def parse_drop(self, file):
        ts = os.path.splitext(os.path.basename(file))[0]
        images = unpack(load_image(file))
        for image in images:
            items = self.os_shop_get_items_in_akashi(image)
            if len(items) < 6:
                logger.info(f'Skip image {ts} due to duplication')
                continue
            if self.last is not None:
                drop = True
                for item, last_item in zip(items, self.last):
                    if item.name != last_item.name or item.amount != last_item.amount:
                        drop = False
                        break
                if drop:
                    logger.info(f'Skip image {ts} due to duplication')
                    continue
            self.last = items

            for item in items:
                yield ['\'' + ts, item.name, item.amount]


    def extract_drop(self, folder):
        """
        Extract images from a given folder.

        Args:
            campaign (str):
        """
        print('')
        logger.hr(f'extract akashi statistics from {folder}', level=1)
        _ = self.csv_overwrite_check

        with open(self.csv_file, 'a', newline='', encoding=AkashiStatistics.CSV_ENCODING) as csv_file:
            writer = csv.writer(csv_file)
            self.csv_write_column_name(writer, AkashiStatistics.COLUMNS)
            for ts, file in tqdm(load_folder(self.drop_folder(folder)).items()):
                try:
                    rows = self.parse_drop(file)
                    writer.writerows(rows)
                except ImageError as e:
                    logger.warning(e)
                    continue
                except Exception as e:
                    logger.exception(e)
                    logger.warning(f'Error on image {ts}')
                    continue


if __name__ == '__main__':
    # Drop screenshot folder. Default to './screenshots'
    AkashiStatistics.DROP_FOLDER = './screenshots'
    # 'cpu' or 'gpu', default to 'cpu'.
    # Use 'gpu' for faster prediction, but you must have the gpu version of mxnet installed.
    AkashiStatistics.CNOCR_CONTEXT = 'cpu'
    # Name of the output csv file.
    # This will write to {DROP_FOLDER}/{CSV_FILE}.
    AkashiStatistics.CSV_FILE = 'akashi_result.csv'
    # If True, remove existing file before extraction.
    AkashiStatistics.CSV_OVERWRITE = True
    # Usually to be 'utf-8'.
    # For better Chinese export to Excel, use 'gbk'.
    AkashiStatistics.CSV_ENCODING = 'gbk'
    # campaign names to export under DROP_FOLDER.
    # This will load {DROP_FOLDER}/{CAMPAIGN}.
    # Just a demonstration here, you should modify it to your own.
    CAMPAIGNS = ['opsi_akashi']

    stat = AkashiStatistics(config='alas')

    """
    Step 1:
        Run this code.
    """
    for i in CAMPAIGNS:
        stat.extract_drop(i)
