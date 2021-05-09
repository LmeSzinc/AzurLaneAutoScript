from module.base.button import ButtonGrid
from module.base.timer import Timer
from module.equipment.assets import *
from module.handler.info_handler import InfoHandler
from module.logger import logger
from module.ui.ui import UI
from module.base.utils import color_similarity_2d
import numpy as np

SWIPE_DISTANCE = 250
SWIPE_RANDOM_RANGE = (-40, -20, 40, 20)
DETAIL_SIDEBAR = ButtonGrid(
    origin=(21, 118), delta=(0, 94.5), button_shape=(60, 75), grid_shape=(1, 5), name='DETAIL_SIDEBAR')


class Equipment(UI):
    equipment_has_take_on = False

    def _equip_view_swipe(self, distance, check_button=EQUIPMENT_OPEN):
        swipe_count = 0
        swipe_timer = Timer(5, count=10)
        self.ensure_no_info_bar(timeout=3)
        SWIPE_CHECK.load_color(self.device.image)
        SWIPE_CHECK._match_init = True # Disable ensure_template() on match(), allows ship to be properly determined whether different or not
        while 1:
            if not swipe_timer.started() or swipe_timer.reached():
                swipe_timer.reset()
                self.device.swipe(vector=(distance, 0), box=SWIPE_AREA.area, random_range=SWIPE_RANDOM_RANGE,
                                  padding=0, duration=(0.1, 0.12), name='EQUIP_SWIPE')
                self.wait_until_appear(check_button)
                swipe_count += 1

            self.device.screenshot()
            if SWIPE_CHECK.match(self.device.image):
                if swipe_count > 1:
                    logger.info('Same ship on multiple swipes')
                    return False
                continue

            if self.appear(check_button, offset=(30, 30)) and not SWIPE_CHECK.match(self.device.image):
                logger.info('New ship detected on swipe')
                return True

    def equip_view_next(self, check_button=EQUIPMENT_OPEN):
        return self._equip_view_swipe(distance=-SWIPE_DISTANCE, check_button=check_button)

    def equip_view_prev(self, check_button=EQUIPMENT_OPEN):
        return self._equip_view_swipe(distance=SWIPE_DISTANCE, check_button=check_button)

    def equip_enter(self, click_button, check_button=EQUIPMENT_OPEN, long_click=True):
        enter_timer = Timer(10)

        while 1:
            if enter_timer.reached():
                if long_click:
                    self.device.long_click(click_button, duration=(1.5, 1.7))
                else:
                    self.device.click(click_button)
                enter_timer.reset()

            self.device.screenshot()

            # End
            if self.appear(check_button):
                break

    def _equip_sidebar_click(self, index):
        """
        Args:
            index (int):
                5 for retrofit.
                4 for enhancement.
                3 for limit break.
                2 for gem / equipment.
                1 for detail.

        Returns:
            bool: if changed.
        """
        if index <= 0 or index > 5:
            logger.warning(f'Sidebar index cannot be clicked, {index}, limit to 1 through 5 only')
            return False

        current = 0
        total = 0

        for idx, button in enumerate(DETAIL_SIDEBAR.buttons()):
            image = np.array(self.device.image.crop(button.area))
            if np.sum(image[:, :, 0] > 235) > 100:
                current = idx + 1
                total = idx + 1
                continue
            if np.sum(color_similarity_2d(image, color=(140, 162, 181)) > 221) > 100:
                total = idx + 1
            else:
                break
        if not current:
            logger.warning('No ship details sidebar active.')
        if total == 3:
            current = 4 - current
        elif total == 4:
            current = 5 - current
        elif total == 5:
            current = 6 - current
        else:
            logger.warning('Ship details sidebar total count error.')

        logger.attr('Detail_sidebar', f'{current}/{total}')
        if current == index:
            return False

        diff = total - index
        if total == 3 and index == 3:
            logger.warning('Ship is PRY, equipment research not supported')
        elif diff >= 0:
            self.device.click(DETAIL_SIDEBAR[0, diff])
        else:
            logger.warning(f'Target index {index} cannot be clicked for this ship')
        return True

    def equip_sidebar_ensure(self, index, skip_first_screenshot=True):
        """
        Args:
            index (int):
                5 for retrofit.
                4 for enhancement.
                3 for limit break.
                2 for gem / equipment.
                1 for detail.

            Returns:
                bool: whether sidebar could be ensured
                      at most 3 attempts are made before
                      return False otherwise True
        """
        if index <= 0 or index > 5:
            logger.warning(f'Sidebar index cannot be ensured, {index}, limit 1 through 5 only')
            return False

        counter = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._equip_sidebar_click(index):
                if counter >= 2:
                    logger.warning('Sidebar could not be ensured')
                    return False
                counter += 1
                self.device.sleep((0.3, 0.5))
                continue
            else:
                return True

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

            if confirm_timer.reached() and self.handle_popup_confirm():
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
        self.equip_enter(enter)

        for index in '9'.join([str(x) for x in fleet if x > 0]):
            index = int(index)
            if index == 9:
                self.equip_view_next()
            else:
                self._equip_take_off_one()

        self.ui_back(out)
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
        self.equip_enter(enter)

        for index in '9'.join([str(x) for x in fleet if x > 0]):
            index = int(index)
            if index == 9:
                self.equip_view_next()
            else:
                self._equip_take_on_one(index=index)

        self.ui_back(out)
        self.equipment_has_take_on = True
