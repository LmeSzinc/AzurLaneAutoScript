import cv2
import numpy as np

from module.base.utils import color_similarity_2d, get_color
from module.logger import logger
from tasks.base.ui import UI
from tasks.forgotten_hall.assets.assets_forgotten_hall_team import *
from tasks.forgotten_hall.assets.assets_forgotten_hall_ui import ENTER_FORGOTTEN_HALL_DUNGEON, ENTRANCE_CHECKED


class ForgottenHallTeam(UI):
    def team_prepared(self):
        # White button, with a color of (214, 214, 214)
        color = get_color(self.device.image, ENTER_FORGOTTEN_HALL_DUNGEON.area)
        return np.mean(color) > 180

    def team_choose_first(self, skip_first_screenshot=True):
        """
        A temporary method used to choose the first character only
        """
        logger.info('Team choose first')
        self.interval_clear(ENTRANCE_CHECKED)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.team_prepared():
                logger.info("First character is chosen")
                break
            if self.appear(ENTRANCE_CHECKED, interval=2):
                self.device.click(CHARACTER_1)
                continue

    def is_character_chosen(self, button: ButtonWrapper) -> bool:
        image = color_similarity_2d(self.image_crop(button), color=(255, 255, 255))
        color = cv2.mean(image)[0]
        # print(button, color)
        # Chosen:
        # CHARACTER_1 210.0230034722222
        # CHARACTER_2 210.12022569444443
        # CHARACTER_3 211.09244791666666
        # CHARACTER_4 210.48046875
        # Not chosen
        # CHARACTER_1 122.38671875
        # CHARACTER_2 124.72960069444444
        # CHARACTER_3 136.55989583333331
        # CHARACTER_4 129.76432291666666
        return color > 180

    def team_choose_first_4(self, skip_first_screenshot=True):
        """
        Choose the first 4 characters in list.
        """
        logger.info('Team choose first 4')
        self.interval_clear(ENTRANCE_CHECKED)
        characters = [CHARACTER_1, CHARACTER_2, CHARACTER_3, CHARACTER_4]
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            chosen_list = [self.is_character_chosen(c) for c in characters]
            if all(chosen_list):
                logger.info("First 4 characters are chosen")
                break
            if self.appear(ENTRANCE_CHECKED, interval=2):
                for character, chosen in zip(characters, chosen_list):
                    if not chosen:
                        self.device.click(character)
                        # Casual sleep, game may not respond that fast
                        self.device.sleep((0.1, 0.2))
