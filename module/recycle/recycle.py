import time

from PIL import ImageChops
import numpy as np

from module.base.button import Button
from module.base.utils import *
from module.config.config import AzurLaneConfig
from module.recycle.assets import *
from module.recycle.box_detect import box_detect
from module.handler.info_handler import InfoHandler
from module.logger import logger
from module.statistics.item import AmountOcr

SWIPE_DISTANCE = 250
SWIPE_RANDOM_RANGE = (-40, -20, 40, 20)

AMOUNT_OCR = AmountOcr([], threshold=64, name='Amount_ocr')
AMOUNT_AREA = (90, 72, 120, 120)

class Recycleandler):

    def __init__(self, config, device=None):
        super().__init__(config, device=device)
        self.detect = box_detect(AzurLaneConfig)
        self.amount_ocr = AMOUNT_OCR
        self.amount_area = AMOUNT_AREA



    def _view_swipe(self, distance=SWIPE_DISTANCE):

        new = self.device.screenshot()
        self.ensure_no_info_bar(timeout=3)

        self.device.swipe(vector=(0, -distance), box=STORAGE_AREA.area, random_range=SWIPE_RANDOM_RANGE,
                          padding=0, duration=(0.1, 0.12), name='STORAGE_SWIPE')
        time.sleep(2)

        new, old = self.device.screenshot(), new
        diff = ImageChops.difference(new, old)
        if diff.getbbox():

            logger.info('reach the buttom')
            return False

        return True

    def run(self):
        # self.storageEnter()

        # self._view_swipe(250)


        # self.destroy()
        self.image = self.device.screenshot()
        image = np.array(self.image)
        logger.info(image.shape)
        boxArea = self.detect.detectBoxArea(self.image)
        if boxArea:
            for grid in boxArea:
                # logger.info(grid)
                # amount = crop(image, area=np.rint(grid).astype(int))
                # amount = crop(amount, area=self.amount_area)
                # amount = self.amount_ocr.ocr(amount, direct_ocr=True)
                # logger.info(amount)
                self.useBox(grid)
                self.device.screenshot()
                if INFORM_FULL.match(self.device.screenshot()):
                    logger.info("the storage is full, goto decomopose equipments")

    def destroy(self):
        self.wait_until_appear_then_click(GOTO_EQUIPMENT)
        self.wait_until_appear_then_click(SELECT_SORT)
        self.wait_until_appear_then_click(CHOOSE_UPGRADE)

        time.sleep(1)
        
        self.image = self.device.screenshot()
        equipArea = self.detect.detectWeaponArea(self.image)
        while equipArea:
            for area in equipArea:
                self.device.click(Button(area, get_color(self.image, area), area))
                self.device.sleep((0.1, 0.15))
            equipArea = self.detect.detectWeaponArea(self.image)


    def useBox(self, area):
        self.device.click(Button(area, get_color(self.image, area), area))
        self.wait_until_appear(INFORM_BOX)
        if BOX_COMBINE.match(self.device.screenshot()) > 0.7:
            self.device.click(BOX_USE10_2)
        else:
            self.device.click(BOX_USE10_1)

    def storageEnter(self):
        self.device.click(STORAGE_OPEN)
        self.wait_until_appear(STORAGE_CHECK)
        self.device.click(MATERIAL)
