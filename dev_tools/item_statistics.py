import os

# os.chdir('../')
import module.config.server as server

server.server = 'cn'  # Edit server here.
print(os.getcwd())

import numpy as np
from PIL import Image
import cv2
import time
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2
from module.handler.assets import INFO_BAR_1
from module.base.button import ButtonGrid, Button
from module.base.ocr import Ocr
from module.logger import logger


"""
Set your folder here
Examples: xxx/campaign_7_2
"""
IMAGE_FOLDER = ''
STATUS_ITEMS_INTERVAL = 10
TEMPLATE_THRESHOLD = 0.9

BATTLE_STATUS_FOLDER = f'{IMAGE_FOLDER}/status'
GET_ITEMS_FOLDER = f'{IMAGE_FOLDER}/get_items'
TEMPLATE_FOLDER = f'{IMAGE_FOLDER}/item_template'
for f_ in [TEMPLATE_FOLDER]:
    if not os.path.exists(f_):
        os.mkdir(f_)
BATTLE_STATUS_TIMESTAMP = np.array([int(f.split('.')[0]) for f in os.listdir(BATTLE_STATUS_FOLDER)])
ITEM_GRIDS_1_ODD = ButtonGrid(origin=(336, 298), delta=(128, 0), button_shape=(96, 96), grid_shape=(5, 1))
ITEM_GRIDS_1_EVEN = ButtonGrid(origin=(400, 298), delta=(128, 0), button_shape=(96, 96), grid_shape=(4, 1))
ITEM_GRIDS_2 = ButtonGrid(origin=(336, 227), delta=(128, 142), button_shape=(96, 96), grid_shape=(5, 2))
ENEMY_GENRE_BUTTON = Button(area=(782, 285, 961, 319), color=(), button=(), name='ENEMY_GENRE')


class AmountOcr(Ocr):
    def ocr(self, image):
        start_time = time.time()

        image_list = [self.pre_process(i) for i in image]
        result_list = self.cnocr.ocr_for_single_lines(image_list)
        result_list = [self.after_process(result) for result in result_list]

        if len(self.buttons) == 1:
            result_list = result_list[0]
        logger.attr(name='%s %ss' % (self.name, str(round(time.time() - start_time, 3)).ljust(5, '0')),
                    text=str(result_list))

        return result_list

    def after_process(self, raw):
        """
        Returns:
            int:
        """
        raw = super().after_process(raw)
        if not raw:
            result = 0
        else:
            result = int(raw)

        return result


AMOUNT_OCR = AmountOcr([], back=(-200, -200, -200), lang='digit', name='Amount_ocr')
ENEMY_GENRE_OCR = Ocr(ENEMY_GENRE_BUTTON, lang='cnocr', use_binary=False, back=(127, 127, 127))


class ImageError(Exception):
    pass


class ItemTemplate:
    def __init__(self, image):
        self.image = np.array(image)

    def match(self, image):
        res = cv2.matchTemplate(self.image, np.array(image), cv2.TM_CCOEFF_NORMED)
        _, similarity, _, _ = cv2.minMaxLoc(res)
        return similarity > TEMPLATE_THRESHOLD

    def save(self, name):
        image = Image.fromarray(self.image)
        image.save(f'{TEMPLATE_FOLDER}/{name}.png')


class ItemTemplateGroup:
    def __init__(self):
        self.templates = {}
        for file in os.listdir(TEMPLATE_FOLDER):
            name = file[:-4]
            image = Image.open(f'{TEMPLATE_FOLDER}/{file}').convert('RGB')
            self.templates[name] = ItemTemplate(image)

    def match(self, item):
        for name, template in self.templates.items():
            if template.match(item.image):
                return name

        template = ItemTemplate(item.get_template())
        name = [int(n) for n in self.templates.keys() if n.isdigit()]
        if len(name):
            name = str(max(name) + 1)
        else:
            name = str(len(self.templates.keys()) + 1)

        logger.info(f'New item template: {name}')
        self.templates[name] = template
        template.save(name)
        return name


template_group = ItemTemplateGroup()


class Item:
    def __init__(self, image):
        self.image = image
        self.is_valid = np.mean(np.array(image.convert('L')) > 127) > 0.1
        self.name = 'Default_item'
        self.amount = 1
        if self.is_valid:
            self.name = template_group.match(self)
            if not self.name.startswith('_') and '_' in self.name:
                self.name = '_'.join(self.name.split('_')[:-1])

    def __str__(self):
        return f'{self.name}_x{self.amount}'

    @property
    def has_amount(self):
        return 'T' in self.name or self.name == '物资'

    def get_template(self):
        # return self.image.crop((5, 5, 90, 68))
        return self.image.crop((40, 21, 89, 70))

    def get_amount(self):
        return self.image.crop((60, 75, 91, 88))


class Items:
    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.get_items = Image.open(f'{GET_ITEMS_FOLDER}/{timestamp}.png').convert('RGB')

        # Enemy genre
        interval = np.abs(BATTLE_STATUS_TIMESTAMP - timestamp)
        if np.min(interval) > STATUS_ITEMS_INTERVAL * 1000:
            raise ImageError(f'Timestamp: {timestamp}, battle_status image not found.')
        self.status_timestamp = BATTLE_STATUS_TIMESTAMP[np.argmin(interval)]
        self.enemy = 'Default_enemy'

        # get_item image properties
        if INFO_BAR_1.appear_on(self.get_items):
            raise ImageError(f'Timestamp: {timestamp}, Info bar')
        if GET_ITEMS_1.appear_on(self.get_items):
            self.row = 1
            self.is_odd = self.get_is_odd(self.get_items)
            self.grids = ITEM_GRIDS_1_ODD if self.is_odd else ITEM_GRIDS_1_EVEN
        elif GET_ITEMS_2.appear_on(self.get_items):
            self.row = 2
            self.is_odd = True
            self.grids = ITEM_GRIDS_2
        else:
            raise ImageError(f'Timestamp: {timestamp}, Image is not a get_items image.')

        # Crop items
        self.items = []
        for button in self.grids.buttons():
            item = Item(self.get_items.crop(button.area))
            if item.is_valid:
                self.items.append(item)

    @staticmethod
    def get_is_odd(image):
        image = image.crop((628, 294, 651, 396))
        return np.mean(np.array(image.convert('L')) > 127) > 0.1

    def predict(self):
        self.battle_status = Image.open(f'{BATTLE_STATUS_FOLDER}/{self.status_timestamp}.png').convert('RGB')
        self.enemy = ENEMY_GENRE_OCR.ocr(self.battle_status)
        enemy = self.enemy
        # Delete wrong OCR result
        for letter in '-一个―~(':
            enemy = enemy.replace(letter, '')
        self.enemy = enemy

        amount_items = [item for item in self.items if item.has_amount]
        amount = AMOUNT_OCR.ocr([item.get_amount() for item in amount_items])
        for a, i in zip(amount, amount_items):
            i.amount = a

    def get_data(self):
        return [[self.timestamp, self.status_timestamp, self.enemy, item.name, item.amount] for item in self.items]

"""
Edit server at the top of this file first.
"""

"""
These code is for testing
Set your image name here
Examples: 159022xxxxxxx (int)
"""
# ts = 1590227624035
# items = Items(ts)
# for item in items.items:
#     print(item.amount, item.name)

"""
These code is for template extracting
"""
# from tqdm import tqdm
# for ts in tqdm([int(f.split('.')[0]) for f in os.listdir(GET_ITEMS_FOLDER)]):
#     try:
#         items = Items(ts)
#     except Exception:
#         logger.warning(f'Error image: {ts}')
#         continue

"""
These code is for final statistic
Set your csv file name here
Examples: c64.csv
"""
# csv_file = 'c64.csv'
# import csv
# from tqdm import tqdm
# with open(csv_file, 'a', newline='') as file:
#     writer = csv.writer(file)
#     for ts in tqdm([int(f.split('.')[0]) for f in os.listdir(GET_ITEMS_FOLDER)]):
#         try:
#             items = Items(ts)
#             items.predict()
#             writer.writerows(items.get_data())
#         except Exception:
#             logger.warning(f'Error image: {ts}')
#             continue
