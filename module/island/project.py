from datetime import datetime, timedelta

from module.base.button import Button, ButtonGrid
from module.base.utils import crop
from module.island.assets import *
from module.island.project_data import *
from module.island.ui import OCR_PRODUCTION_TIME, OCR_PRODUCTION_TIME_REMAIN
from module.ocr.ocr import Ocr


class IslandProject:
    valid: bool
    name: str
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
        button = Button(area=area, color=(), button=area, name='NAME')
        ocr = Ocr(button, lang='cnocr')
        self.name = ocr.ocr(self.image)
        if not self.name:
            self.valid = False
            return

        # available slot
        area = (self.x1 - 383, self.y1 + 60, self.x1 - 39, self.y1 + 118)
        image = crop(self.image_gray, area, copy=False)
        locked = TEMPLATE_SLOT_LOCKED.match_multi(image)
        self.slot = name_to_slot_cn.get(self.name, 4) - len(locked)
        if not self.slot:
            self.valid = False
            return

        # slot grids
        self.slot_buttons = ButtonGrid(origin=(self.x1 - 383, self.y1 + 60), delta=(95, 0),
                                       button_shape=(58, 58), grid_shape=(self.slot, 1), name='PROJECT_SLOT')

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
            other (IslandProject):

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