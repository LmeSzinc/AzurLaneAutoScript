from module.base.button import match_template
from module.base.timer import Timer
from module.logger import logger
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_skill import *


class CombatSkill(UI):
    def is_in_skill(self) -> bool:
        """
        Combat paused, require manual skill use
        """
        if not self.appear(IN_SKILL):
            return False

        if not self.image_color_count(IN_SKILL, color=(255, 255, 255), threshold=221, count=50):
            return False

        return True

    def _skill_click(self, button, skip_first_screenshot=True):
        """
        Click a skill button.
        Not in skill page means skill has been used and skill animation is ongoing
        """
        logger.info(f'Skill use: {button}')
        interval = Timer(1)
        clicked = False
        prev_image = None
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.is_in_skill():
                if interval.reached():
                    prev_image = self.image_crop(button)
                    self.device.click(button)
                    interval.reset()
                    clicked = True
                    continue
            else:
                # Skill animation on going
                if clicked:
                    logger.info(f'Skill used: {button} (skill ongoing)')
                    break
                # New skill icon
                if prev_image is not None:
                    if not match_template(self.image_crop(button), prev_image):
                        logger.info(f'Skill used: {button} (icon changed)')
                        break

    def _is_skill_active(self, button):
        flag = self.image_color_count(button, color=(220, 196, 145), threshold=221, count=50)
        return flag

    def _skill_switch(self, check_button, click_button, skip_first_screenshot=True):
        """
        Switch to A or E
        """
        logger.info(f'Skill switch: {check_button}')
        interval = Timer(1)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Raw brown border
            if self._is_skill_active(check_button):
                logger.info(f'Skill switched: {check_button}')
                break

            if self.is_in_skill() and (self._is_skill_active(CHECK_A) or self._is_skill_active(CHECK_E)):
                if interval.reached():
                    self.device.click(click_button)
                    interval.reset()
                    continue

    def wait_next_skill(self, expected_end=None, skip_first_screenshot=True):
        """
        Args:
            expected_end: A function returns bool, True represents end.
            skip_first_screenshot:

        Returns:
            bool: True if is_in_skill
                False if triggered expected_end
        """
        logger.info('Wait next skill')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.is_in_skill():
                return True
            if callable(expected_end) and expected_end():
                logger.info(f'Combat execute ended at {expected_end.__name__}')
                return False

    def use_A(self) -> bool:
        logger.hr('Use A')
        self._skill_switch(check_button=CHECK_A, click_button=USE_A)
        self._skill_click(USE_A)
        return True

    def use_E(self) -> bool:
        logger.hr('Use E')
        self._skill_switch(check_button=CHECK_E, click_button=USE_E)
        self._skill_click(USE_E)
        return True

    def use_Q(self, position: int) -> bool:
        """
        Args:
            position: 1 to 4
        """
        logger.hr(f'Use Q {position}')
        try:
            button = [USE_Q1, USE_Q2, USE_Q3, USE_Q4][position - 1]
        except IndexError:
            logger.error(f'use_Q: position {position} does not exist')
            return False

        self._skill_click(button)
        self.wait_next_skill()
        self._skill_click(USE_Q_AIM)
        return True
