import time

from PIL import ImageChops

from module.config.config import AzurLaneConfig
from module.decomposition.assets import *
from module.decomposition.box_detect import box_detect
from module.handler.info_handler import InfoHandler
from module.logger import logger
from module.base.utils import *
from module.base.button import Button


SWIPE_DISTANCE = 250
SWIPE_RANDOM_RANGE = (-40, -20, 40, 20)


class Decomposition(InfoHandler):

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

    def Decomps(self):
        # self.storageEnter()

        # self._view_swipe(250)
        
        detect = box_detect(AzurLaneConfig)
        self.image = self.device.screenshot()
        
        boxArea = detect.detectBoxArea(self.image)
        if boxArea:
            for grid in boxArea:
                self.useBox(grid)
                self.device.screenshot()
                if INFORM_FULL.match(self.device.screenshoot()):
                    

    def useBox(self, area):
        self.device.click(Button(area, get_color(self.image, area), area))
        self.wait_until_appear(INFORM_BOX)
        self.device.click(BOX_USE10_1)

    def storageEnter(self):
        self.device.click(STORAGE_OPEN)
        self.wait_until_appear(STORAGE_CHECK)
        self.device.click(MATERIAL)
        
