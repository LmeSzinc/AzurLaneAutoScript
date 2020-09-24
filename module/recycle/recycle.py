from PIL import ImageChops
import numpy as np

from module.base.button import Button
from module.config.config import AzurLaneConfig
from module.recycle.assets import *
from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2
from module.ui.ui import UI
from module.recycle.box_detect import BoxDetect
from module.logger import logger
from module.statistics.item import AmountOcr

SWIPE_DISTANCE = 250
SWIPE_RANDOM_RANGE = (-40, -20, 40, 20)

AMOUNT_OCR = AmountOcr([], threshold=64, name='Amount_ocr')
AMOUNT_AREA = (90, 72, 120, 120)

STABLE_AREA = (126, 57, 1232, 650)
STABLE_BUTTON = Button(STABLE_AREA, color=(),
                       button=STABLE_AREA, name='stable')


class Recycle(UI):

    def __init__(self, config, device=None):
        super().__init__(config, device=device)
        self.detect = BoxDetect(AzurLaneConfig)
        self.amount_ocr = AMOUNT_OCR
        self.amount_area = AMOUNT_AREA
        self.boxList = {'T1': self.config.AUTO_BOX_REMOVE_T1_BOX,
                        'T2': self.config.AUTO_BOX_REMOVE_T2_BOX, 'T3': self.config.AUTO_BOX_REMOVE_T3_BOX}

    def _view_swipe(self, distance=SWIPE_DISTANCE):

        new = self.device.screenshot()

        p1, p2 = random_rectangle_vector(
            (0, -distance), box=STABLE_AREA, random_range=(-20, -5, 20, 5))
        self.device.drag(p1, p2, segments=2, shake=(25, 0),
                         point_random=(0, 0, 0, 0), shake_random=(-5, 0, 5, 0))

        # self.device.swipe(vector=(0, -distance), box=STABLE_AREA, random_range=SWIPE_RANDOM_RANGE,
        #                   padding=0, duration=(0.1, 0.12), name='STORAGE_SWIPE')

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
        # self.detect.detectWeaponArea(self.image)
        # self.device.sleep((233,233.5))

        self.ui_goto_main()

        self.storage_enter()

        self.image = self.device.screenshot()
        image = np.array(self.image)

        box_buttons = self.detect.detect_box_area(self.image, self.boxList)
        not_reach_buttom = 1
        while box_buttons or not_reach_buttom:
            if not box_buttons:
                not_reach_buttom = self._view_swipe()
                image = self.device.screenshot()
                box_buttons = self.detect.detect_box_area(image, self.boxList)
                continue
            for button in box_buttons:
                # TODO: use ocr

                self.use_box(button)

            image = self.device.screenshot()
            box_buttons = self.detect.detect_box_area(image, self.boxList)

        return

    def use_box(self, area):
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
            if self.appear_then_click(GET_ITEMS_1, offset=True, interval=2):
                break
            if self.appear_then_click(GET_ITEMS_2, offset=True, interval=2):
                break
            if self.appear_then_click(BOX_USE10, offset=(100, 5)):
                continue

        self.wait_until_stable(STABLE_BUTTON)

    def destroy(self):
        while 1:
            self.device.screenshot()

            # use upgrade to judge
            if self.appear(CHOOSE_UPGRADE_CONFIRM, offset=1, threshold=0.9):
                break
            if self.appear_then_click(CHOOSE_UPGRADE):
                continue
            if self.appear_then_click(SELECT_SORT, offset=1):
                continue

        image = self.device.screenshot()
        equip_buttons = self.detect.detect_weapon_area(image)
        while equip_buttons:
            for button in equip_buttons:
                self.device.click(button)
                self.device.sleep((0.1, 0.15))

            while 1:

                self.device.screenshot()

                if self.appear_then_click(DESTROY):
                    continue
                if self.appear_then_click(DESTROY_CONFIRM):
                    break
                if self.handle_popup_confirm():
                    continue

            self.item_confirm()

            # this may fix the mistakenly identifies bug
            self.wait_until_stable(STABLE_BUTTON)

            image = self.device.screenshot()
            equip_buttons = self.detect.detect_weapon_area(image)

        while 1:
            self.device.screenshot()
            if self.appear_then_click(GOTO_MATERIAL):
                break
            if self.appear_then_click(DESTROY_QUICK):
                continue

        # self.wait_until_stable(STABLE_BUTTON)

    def item_confirm(self):
        while 1:

            self.device.screenshot()

            if self.appear_then_click(GET_ITEMS_1, offset=1):
                break
            if self.appear_then_click(GET_ITEMS_2, offset=1):
                break
        return

    def storage_enter(self):
        self.device.click(STORAGE_OPEN)
        self.wait_until_appear(STORAGE_CHECK)
        self.device.click(MATERIAL)
        self.wait_until_stable(STABLE_BUTTON)
