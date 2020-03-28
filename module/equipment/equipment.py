from module.base.timer import Timer
from module.equipment.assets import *
from module.handler.info_bar import InfoBarHandler
from module.logger import logger
from module.ui.assets import BACK_ARROW

SWIPE_DISTANCE = (350, 0)
SWIPE_RANDOM_RANGE = (-40, -20, 40, 20)


class Equipment(InfoBarHandler):
    equipment_has_take_on = False

    def _view_next(self):
        self.device.swipe(vector=(-SWIPE_DISTANCE[0], 0), box=SWIPE_AREA.area, random_range=SWIPE_RANDOM_RANGE,
                          padding=0, duration=(0.1, 0.12))
        self.wait_until_appear(EQUIPMENT_OPEN)

    def _view_prev(self):
        self.device.swipe(vector=(SWIPE_DISTANCE[0], 0), box=SWIPE_AREA.area, random_range=SWIPE_RANDOM_RANGE,
                          padding=0, duration=(0.1, 0.12))
        self.wait_until_appear(EQUIPMENT_OPEN)

    def _equip_enter(self, enter):
        enter_timer = Timer(5)

        while 1:
            if enter_timer.reached():
                self.device.long_click(enter, duration=(1.5, 1.7))
                enter_timer.reset()

            self.device.screenshot()

            # End
            if self.appear(EQUIPMENT_OPEN):
                break

    def _equip_exit(self, out):
        quit_timer = Timer(3)

        while 1:
            self.device.screenshot()

            # End
            if self.appear(out):
                break

            if quit_timer.reached() and self.appear(BACK_ARROW):
                # self.device.sleep(1)
                self.device.click(BACK_ARROW)
                self.device.sleep((0.2, 0.3))
                quit_timer.reset()
                continue

    def _equip_take_off_one(self):
        bar_timer = Timer(5)
        off_timer = Timer(5)
        confirm_timer = Timer(5)

        while 1:
            self.device.screenshot()
            if bar_timer.reached() and not self.appear(EQUIP_1, offset=10):
                self.device.click(EQUIPMENT_OPEN)
                bar_timer.reset()
                continue

            if off_timer.reached() and not self.info_bar_count() and self.appear_then_click(EQUIP_OFF, offset=10):
                off_timer.reset()
                continue

            if confirm_timer.reached() and self.appear_then_click(EQUIP_OFF_CONFIRM, offset=10):
                confirm_timer.reset()
                continue

            # End
            # if self.handle_info_bar():
            #     break
            if off_timer.started() and self.info_bar_count():
                break

    def equipment_take_off(self, enter, out, fleet):
        """
        Args:
            enter (Button): Long click to edit equipment.
            out (Button): Button to confirm exit success.
            fleet (list[int]): list of equipment record. [3, 1, 1, 1, 1, 1]
        """
        logger.hr('Equipment take off')
        self._equip_enter(enter)

        for index in '9'.join([str(x) for x in fleet if x > 0]):
            index = int(index)
            if index == 9:
                self._view_next()
            else:
                self._equip_take_off_one()

        self._equip_exit(out)
        self.equipment_has_take_on = False

    def _equip_take_on_one(self, index):
        bar_timer = Timer(5)
        on_timer = Timer(5)

        while 1:
            self.device.screenshot()

            if bar_timer.reached() and not self.appear(EQUIP_1, offset=10):
                self.device.click(EQUIPMENT_OPEN)
                # self.device.sleep(0.3)
                bar_timer.reset()
                continue

            if on_timer.reached() and self.appear(EQUIP_1, offset=10) and not self.info_bar_count():
                if index == 1:
                    self.device.click(EQUIP_1)
                elif index == 2:
                    self.device.click(EQUIP_2)
                elif index == 3:
                    self.device.click(EQUIP_3)

                on_timer.reset()
                continue

            # End
            # if self.handle_info_bar():
            #     break
            if on_timer.started() and self.info_bar_count():
                break

    def equipment_take_on(self, enter, out, fleet):
        """
        Args:
            enter (Button): Long click to edit equipment.
            out (Button): Button to confirm exit success.
            fleet (list[int]): list of equipment record. [3, 1, 1, 1, 1, 1]
        """
        logger.hr('Equipment take on')
        self._equip_enter(enter)

        for index in '9'.join([str(x) for x in fleet if x > 0]):
            index = int(index)
            if index == 9:
                self._view_next()
            else:
                self._equip_take_on_one(index=index)

        self._equip_exit(out)
        self.equipment_has_take_on = True
