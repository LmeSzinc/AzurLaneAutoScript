import time

from PIL import ImageChops
import numpy as np

from module.base.button import Button
from module.base.utils import *
from module.config.config import AzurLaneConfig
from module.recycle.assets import *
from module.ui.ui import UI
from module.recycle.box_detect import box_detect
from module.logger import logger
from module.statistics.item import AmountOcr

SWIPE_DISTANCE = 250
SWIPE_RANDOM_RANGE = (-40, -20, 40, 20)

AMOUNT_OCR = AmountOcr([], threshold=64, name='Amount_ocr')
AMOUNT_AREA = (90, 72, 120, 120)

STABLE_AREA = (139, 82, 1200, 600)
STABLE_BUTTON = Button(STABLE_AREA, color=(),
                       button=STABLE_AREA, name='stable')


class Recycle(UI):

    def __init__(self, config, device=None):
        super().__init__(config, device=device)
        self.detect = box_detect(AzurLaneConfig)
        self.amount_ocr = AMOUNT_OCR
        self.amount_area = AMOUNT_AREA
        self.boxList = {'T1': self.config.Auto_box_remove_t1_box,
                        'T2': self.config.Auto_box_remove_t2_box, 'T3': self.config.Auto_box_remove_t3_box}

    def _view_swipe(self, distance=SWIPE_DISTANCE):

        new = self.device.screenshot()
        beforeSwipe = new

        self.device.swipe(vector=(0, -distance), box=STORAGE_AREA.area, random_range=SWIPE_RANDOM_RANGE,
                          padding=0, duration=(0.1, 0.12), name='STORAGE_SWIPE')
        self.wait_until_stable(STABLE_BUTTON)

        new, old = self.device.screenshot(), new
        diff = ImageChops.difference(new, old)
        if diff.getbbox():
            return True
        else:
            logger.info('reach the buttom')
            return False

    def run(self):

        # for debug
        # self.image = self.device.screenshot()
        # self.detect.detectBoxArea(self.image)
        # time.sleep(233)

        self.ui_goto_main()

        self.storageEnter()

        self.image = self.device.screenshot()
        image = np.array(self.image)

        boxArea = self.detect.detectBoxArea(self.image, self.boxList)
        not_reach_buttom = 1
        while boxArea or not_reach_buttom:
            if not boxArea:
                not_reach_buttom = self._view_swipe()
                image = self.device.screenshot()
                boxArea = self.detect.detectBoxArea(image, self.boxList)
                continue
            for area in boxArea:
                # TODO: use ocr

                self.useBox(area)

            image = self.device.screenshot()
            boxArea = self.detect.detectBoxArea(image, self.boxList)

        return

    def useBox(self, area):
        """
        use a box
        """
        self.device.click(area)

        while 1:
            # self.wait_until_stable(STABLE_BUTTON)
            self.device.screenshot()

            # if self.appear_then_click(area):
            #     continue
            if self.appear_then_click(GOTO_EQUIPMENT, offset=1):
                logger.info(
                    "the storage is full, goto destroy equipments")
                self.destroy()
                break
            if self.appear_then_click(GET_ITEM_CONFIRM, offset=True, interval=2):
                break
            if self.appear_then_click(GET_ITEM_CONFIRM2, offset=True, interval=2):
                break
            if self.appear_then_click(BOX_USE10_1, offset=1):
                continue
            if self.appear_then_click(BOX_USE10_2, offset=1):
                continue

        self.wait_until_stable(STABLE_BUTTON)

    def destroy(self):
        while 1:
            self.device.screenshot()

            # use upgrade to judge
            if self.appear(CHOOSE_UPGRADE_CONFIRM, offset=1, threshold=0.9):
                break
            # if self.appear_then_click(GOTO_EQUIPMENT):
            #     continue
            if self.appear_then_click(CHOOSE_UPGRADE):
                continue
            if self.appear_then_click(SELECT_SORT, offset=1):
                continue

        image = self.device.screenshot()
        equipButton = self.detect.detectWeaponArea(image)
        while equipButton:
            for area in equipButton:
                self.device.click(area)
                self.device.sleep((0.1, 0.15))

            while 1:

                self.device.screenshot()

                if self.appear_then_click(DESTROY):
                    continue
                if self.appear_then_click(DESTROY_CONFIRM):
                    break
                if self.appear(EQUIPMENT_T3_CHECK):
                    self.device.click(EQUIPMENT_T3_CONFIRM)
                    continue

            self.itemConfirm()

            image = self.device.screenshot()
            equipButton = self.detect.detectWeaponArea(image)

        while 1:
            self.device.screenshot()
            if self.appear_then_click(GOTO_MATERIAL):
                break
            if self.appear_then_click(DESTROY_QUICK):
                continue

        # self.wait_until_stable(STABLE_BUTTON)

    def itemConfirm(self):
        while 1:

            self.device.screenshot()

            if self.appear_then_click(GET_ITEM_CONFIRM, offset=1):
                break
            if self.appear_then_click(GET_ITEM_CONFIRM2, offset=1):
                break
        return

    def storageEnter(self):
        self.device.click(STORAGE_OPEN)
        self.wait_until_appear(STORAGE_CHECK)
        self.device.click(MATERIAL)
        self.wait_until_stable(STABLE_BUTTON)
