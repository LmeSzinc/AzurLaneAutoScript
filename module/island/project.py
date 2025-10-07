from datetime import datetime, timedelta
import re

from module.base.button import Button, ButtonGrid
from module.base.utils import crop
from module.config.deep import deep_values
from module.island.assets import *
from module.island.project_data import *
from module.island.ui import OCR_PRODUCTION_TIME, OCR_PRODUCTION_TIME_REMAIN
from module.ocr.ocr import Ocr


class ProjectNameOcr(Ocr):
    def after_process(self, result):
        result = super().after_process(result)
        result = re.sub(r'[^\u4e00-\u9fff]', '', result)
        return result


class IslandProject:
    valid: bool
    name: str
    id: int
    max_slot: int
    slot: int
    slot_buttons: ButtonGrid

    def __init__(self, image, image_gray, button):
        self.image = image
        self.image_gray = image_gray
        self.button = button
        self.x1, self.y1, self.x2, self.y2 = button.area
        self.valid = True
        self.project_parse()

    def project_parse(self):
        # invalid
        if self.y2 + 110 >= 653:
            self.valid = False
            return

        # locked
        area = (self.x1 - 228, self.y1 + 57, self.x1 - 195, self.y1 + 95)
        image = crop(self.image_gray, area, copy=False)
        if TEMPLATE_PROJECT_LOCKED.match(image):
            self.valid = False
            return

        # name
        area = (self.x1 - 446, self.y1, self.x1 - 326, self.y2)
        button = Button(area=area, color=(), button=area, name='PROJECT_NAME')
        ocr = ProjectNameOcr(button, lang='cnocr')
        self.name = ocr.ocr(self.image)
        if not self.name:
            self.valid = False
            return

        # id
        keys = list(name_to_slot_cn.keys())
        if self.name in keys:
            self.id = keys.index(self.name) + 1
        else:
            self.valid = False
            return

        # max slot
        self.max_slot = name_to_slot_cn.get(self.name, 2)

        # available slot
        area = (self.x1 - 383, self.y1 + 60, self.x1 - 39, self.y1 + 118)
        image = crop(self.image_gray, area, copy=False)
        locked = TEMPLATE_SLOT_LOCKED.match_multi(image)
        self.slot = self.max_slot - len(locked)
        if not self.slot:
            self.valid = False
            return

        # slot grids
        self.slot_buttons = ButtonGrid(origin=(self.x1 - 383, self.y1 + 60), delta=(95, 0),
                                       button_shape=(58, 58), grid_shape=(self.slot, 1), name='PROJECT_SLOT')

    def __eq__(self, other):
        """
        Args:
            other (IslandProject):

        Returns:
            bool:
        """
        if not isinstance(other, IslandProject):
            return False
        if not self.valid or not other.valid:
            return False
        if self.name != other.name:
            return False
        if self.id != other.id:
            return False

        return True


class ItemNameOcr(Ocr):
    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace('蛮', '蜜').replace('茉', '末').replace('汗', '汁')
        result = re.sub(r'[^\u4e00-\u9fff]', '', result)
        return result


class IslandProduct:
    duration: timedelta
    valid: bool

    def __init__(self, image, new=False):
        if new:
            self.duration = OCR_PRODUCTION_TIME.ocr(image)
        else:
            self.duration = OCR_PRODUCTION_TIME_REMAIN.ocr(image)
        self.valid = True

        if not self.duration.total_seconds():
            self.valid = False

        self.create_time = datetime.now()

    @property
    def finish_time(self):
        if self.valid:
            return (self.create_time + self.duration).replace(microsecond=0)
        else:
            return None

    def __eq__(self, other):
        """
        Args:
            other (IslandProduct):

        Returns:
            bool:
        """
        if not isinstance(other, IslandProduct):
            return False
        threshold = timedelta(seconds=120)
        if not self.valid or not other.valid:
            return False
        if (other.duration < self.duration - threshold) or (other.duration > self.duration + threshold):
            return False

        return True

class IslandItem:
    def __init__(self, image, y, get_button=True):
        self.image = image
        self.y = y
        self.valid = True
        self.name = None
        self.button = None
        self.parse_item(get_button=get_button)

    def parse_item(self, get_button):
        if len(self.y) < 2:
            self.valid = False
            return

        y1, y2 = self.y

        # name
        if get_button:
            self.ocr_name(y1, y2)

        # button
        x1, x2 = ISLAND_PRODUCT_ITEMS.area[0] + 20, ISLAND_PRODUCT_ITEMS.area[2] - 20
        area = (x1, y1, x2, y2)
        self.button = Button(area=area, color=(), button=area, name='ISLAND_ITEM')
        if get_button:
            delta = 149
            up, down = self.grid_num(delta, y1, y2)
            shape_y = up + down + 1
            origin_y = y1 - up * delta
            self.item_buttons = ButtonGrid(origin=(x1, origin_y), delta=(0, delta),
                                           button_shape=(x2 - x1, y2 - y1),
                                           grid_shape=(1, shape_y), name='ITEMS')
            self.items = [IslandItem(self.image, (item.area[1], item.area[3]), get_button=False)
                          for item in self.item_buttons.buttons]
        else:
            self.ocr_name(y1, y2)


    @staticmethod
    def grid_num(delta, y1, y2):
        """
        Args:
            delta (int): grid delta
            y1 (int):
            y2 (int):

        Returns:
            tuple(int, int): grids above and below current grid
        """
        up = 0
        down = 0
        while y1 - delta > ISLAND_PRODUCT_ITEMS.area[1]:
            up += 1
            y1 -= delta
        while y2 + delta < ISLAND_PRODUCT_ITEMS.area[3]:
            down += 1
            y2 += delta
        return up, down

    def ocr_name(self, y1, y2):
        """
        Args:
            y1 (int):
            y2 (int):
        """
        area = (300, y1 + 14, 440, y2 - 84)
        button = Button(area=area, color=(), button=area, name='ITEM_NAME')
        ocr = ItemNameOcr(button, lang='cnocr', letter=(70, 70, 70))
        self.name = ocr.ocr(self.image)
        if not self.name or self.name not in deep_values(items_data_cn, depth=2):
            self.valid = False

    def __eq__(self, other):
        """
        Args:
            other (IslandItem):

        Returns:
            bool:
        """
        if not isinstance(other, IslandItem):
            return False
        if not self.valid or not other.valid:
            return False
        if self.name != other.name:
            return False

        return True