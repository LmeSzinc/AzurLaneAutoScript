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
        # self.ensure_no_info_bar(timeout=3)

        self.device.swipe(vector=(0, -distance), box=STORAGE_AREA.area, random_range=SWIPE_RANDOM_RANGE,
                          padding=0, duration=(0.1, 0.12), name='STORAGE_SWIPE')
        time.sleep(5)

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
        # self.detect.detectWeaponArea(self.image)
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
                self.device.screenshot()
                if INFORM_FULL.match(self.device.screenshot()):
                    logger.info(
                        "the storage is full, goto destroy equipments")
                    self.destroy()
                else:
                    self.wait_until_appear_then_click(GET_ITEM_1)
                    self.device.sleep((0.2, 0.25))
                    # self.device.click(BOX_USE10_1)
            self.device.sleep((0.5, 0.55))
            image = self.device.screenshot()
            boxArea = self.detect.detectBoxArea(image, self.boxList)
        
        return

    def destroy(self):
        self.wait_until_appear_then_click(GOTO_EQUIPMENT)
        self.wait_until_appear_then_click(SELECT_SORT)
        self.wait_until_appear_then_click(CHOOSE_UPGRADE)

        time.sleep(1)

        image = self.device.screenshot()
        equipArea = self.detect.detectWeaponArea(self.image)
        while equipArea:
            for area in equipArea:
                self.device.click(Button(area=area, color=get_color(
                    self.image, area), button=area, name=''.join(str(area[0]))))
                self.device.sleep((0.1, 0.15))
            self.device.click(DESTROY)
            self.device.sleep((0.4, 0.45))
            self.device.screenshot()
            if self.appear(EQUIPMENT_T3_CHECK):
                self.device.click(EQUIPMENT_T3_CONFIRM)
            self.wait_until_appear_then_click(DESTROY_CONFIRM)

            self.itemConfirm()

            image = self.device.screenshot()
            equipArea = self.detect.detectWeaponArea(image)
        self.wait_until_appear_then_click(DESTROY_QUICK)
        self.wait_until_appear_then_click(GOTO_MATERIAL)

    def useBox(self, area):
        self.device.click(Button(area=area, color=get_color(
            self.image, area), button=area, name=''.join(str(area[0]))))
        self.wait_until_appear(INFORM_BOX)
        if BOX_COMBINE.match(self.device.screenshot()) > 0.7:
            self.device.click(BOX_USE10_2)
        else:
            self.device.click(BOX_USE10_1)

    def itemConfirm(self):
        self.device.sleep((0.4, 0.45))
        self.device.screenshot()
        if self.appear(GET_ITEM_CONFIRM):
            self.device.click(GET_ITEM_CONFIRM)
        elif self.appear(GET_ITEM_CONFIRM2):
            self.device.click(GET_ITEM_CONFIRM2)

    def storageEnter(self):
        self.device.click(STORAGE_OPEN)
        self.wait_until_appear(STORAGE_CHECK)
        self.device.click(MATERIAL)
