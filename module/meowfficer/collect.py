from module.base.button import Button, ButtonGrid
from module.base.timer import Timer
from module.logger import logger
from module.meowfficer.assets import *
from module.meowfficer.base import MeowfficerBase

MEOWFFICER_SKILL_GRID_1 = ButtonGrid(
    origin=(875, 559), delta=(105, 0), button_shape=(16, 16), grid_shape=(3, 1),
    name='MEOWFFICER_SKILL_GRID_1')
MEOWFFICER_SKILL_GRID_2 = MEOWFFICER_SKILL_GRID_1.move(vector=(-40, -20),
                                                       name='MEOWFFICER_SKILL_GRID_2')
MEOWFFICER_SHIFT_DETECT = Button(
    area=(1260, 669, 1280, 720), color=(117, 106, 84), button=(1260, 669, 1280, 720),
    name='MEOWFFICER_SHIFT_DETECT')


class MeowfficerCollect(MeowfficerBase):
    def _meow_detect_shift(self, skip_first_screenshot=True):
        """
        Serves as innate wait mechanism for loading
        of meowfficer acquisition complete screen
        During which screen may shift left randomly

        Args:
            skip_first_screenshot (bool):

        Returns:
            bool
        """
        flag = False
        confirm_timer = Timer(3, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End - Random left shift
            if self.image_color_count(MEOWFFICER_SHIFT_DETECT,
                                      color=MEOWFFICER_SHIFT_DETECT.color, threshold=221, count=650):
                if not flag:
                    confirm_timer.reset()
                    flag = True
                if confirm_timer.reached():
                    break
                continue

            # End - No shift at all
            if self.appear(MEOWFFICER_GET_CHECK, offset=(40, 40)):
                if flag:
                    confirm_timer.reset()
                    flag = False
                if confirm_timer.reached():
                    break
        return flag

    def _meow_get_sr(self):
        """
        Handle SR cat acquisition
        If has at least one unique skill
        then lock to prevent used as feed

        Pages:
            in: MEOWFFICER_GET_CHECK
            out: MEOWFFICER_GET_CHECK or MEOWFFICER_TRAIN
        """
        # Wait for complete load before examining skills
        logger.info('SR cat detected, wait complete load and examine base skills')
        grid = MEOWFFICER_SKILL_GRID_2 if self._meow_detect_shift() else MEOWFFICER_SKILL_GRID_1

        # Appropriate grid acquired, scan for unique skills
        has_unique = False
        for _ in grid.buttons:
            # Empty slot; check for many white pixels
            if self.image_color_count(_, color=(255, 255, 247), threshold=221, count=200):
                continue

            # Non-empty slot; check for few white pixels
            # i.e. roman numerals
            if self.image_color_count(_, color=(255, 255, 255), threshold=221, count=25):
                continue

            # Detected unique skill; break
            has_unique = True
            break

        # Execute appropriate route
        # Transition into lock popup
        logger.info('At least one unique skill detected; locking...') if has_unique else \
            logger.info('No unique skills detected; skipping...')
        self.ui_click(MEOWFFICER_TRAIN_CLICK_SAFE_AREA,
                      appear_button=MEOWFFICER_GET_CHECK, check_button=MEOWFFICER_CONFIRM,
                      offset=(40, 40), retry_wait=3, skip_first_screenshot=True)

        # Transition out of lock popup
        # Use callable as screen is variable
        def check_popup_exit():
            if self.appear(MEOWFFICER_GET_CHECK, offset=(40, 40)):
                return True

            if self.appear(MEOWFFICER_TRAIN_START, offset=(20, 20)):
                return True

            return False

        self.ui_click(MEOWFFICER_CONFIRM if has_unique else MEOWFFICER_CANCEL,
                      check_button=check_popup_exit, offset=(40, 20),
                      retry_wait=3, skip_first_screenshot=True)

    def meow_get(self, skip_first_screenshot=True):
        """
        Transition through all the necessary screens
        to acquire each trained meowfficer
        Animation is waited for as the amount can vary
        Only SR will prompt MEOWFFICER_LOCK_CONFIRM

        Args:
            skip_first_screenshot (bool): Skip first
            screen shot or not

        Pages:
            in: MEOWFFICER_GET_CHECK
            out: MEOWFFICER_TRAIN
        """
        # Loop through possible screen transitions
        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_meow_popup_dismiss()
                confirm_timer.reset()
                continue
            if self.appear(MEOWFFICER_SR_CHECK, offset=(40, 40)):
                self._meow_get_sr()
                skip_first_screenshot = True
                confirm_timer.reset()
                continue
            if self.appear(MEOWFFICER_GET_CHECK, offset=(40, 40), interval=3):
                # Susceptible to exception when collecting multiple
                # Mitigate by popping click_record
                self.device.click(MEOWFFICER_TRAIN_CLICK_SAFE_AREA)
                self.device.click_record.pop()
                confirm_timer.reset()
                continue

            # End
            if self.appear(MEOWFFICER_TRAIN_START, offset=(20, 20)):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

    def meow_collect(self, is_sunday=False):
        """
        Collect one or all trained meowfficer(s)
        Completed slots are automatically moved
        to top of queue, assume to check top-left
        slot only

        Args:
            is_sunday (bool): Whether today is Sunday or not

        Pages:
            in: MEOWFFICER_TRAIN
            out: MEOWFFICER_TRAIN

        Returns:
            Bool whether collected or not
        """
        logger.hr('Meowfficer collect', level=2)

        if self.appear(MEOWFFICER_TRAIN_COMPLETE, offset=(20, 20)):
            # Today is Sunday, finish all else get just one
            if is_sunday:
                logger.info('Collect all trained meowfficers')
                button = MEOWFFICER_TRAIN_FINISH_ALL
            else:
                logger.info('Collect single trained meowfficer')
                button = MEOWFFICER_TRAIN_COMPLETE
            self.ui_click(button, check_button=MEOWFFICER_GET_CHECK,
                          additional=self.handle_meow_popup_dismiss,
                          offset=(40, 40), skip_first_screenshot=True)

            # Get loop mechanism to collect trained meowfficer(s)
            self.meow_get()
            return True
        return False
