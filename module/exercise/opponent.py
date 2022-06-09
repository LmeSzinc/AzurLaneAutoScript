import numpy as np

from module.base.button import ButtonGrid
from module.base.utils import image_left_strip
from module.exercise.assets import *
from module.logger import logger
from module.ocr.ocr import Digit
from module.ui.assets import BACK_ARROW
from module.ui.ui import UI

OPPONENT = ButtonGrid(origin=(104, 77), delta=(244, 0), button_shape=(212, 304), grid_shape=(4, 1))

# Mode 'easiest' constants
# MAX_LVL_SUM = Max Fleet Size (6) * Max Lvl (125)
# PWR_FACTOR used to make overall PWR manageable
MAX_LVL_SUM = 750
PWR_FACTOR = 100


class Level(Digit):
    def pre_process(self, image):
        image = super().pre_process(image)
        image = image_left_strip(image, threshold=85, length=22)

        image = np.pad(image, ((5, 6), (0, 5)), mode='constant', constant_values=255)
        return image.astype(np.uint8)


class Opponent:
    def __init__(self, main_image, fleet_image, index):
        self.index = index
        self.power = self.get_power(image=main_image)
        self.level = self.get_level(image=fleet_image)

        # [OPPONENT_1] ( 8256) 120 120 120 | (12356) 100  80  80
        level = [str(x).rjust(3, ' ') for x in self.level]
        power = ['(' + str(x).rjust(5, ' ') + ')' for x in self.power]
        logger.attr(
            'OPPONENT_%s' % index,
            ' '.join([power[0]] + level[:3] + ['|'] + [power[1]] + level[3:])
        )

    @staticmethod
    def get_level(image):
        """
        Args:
            image: Screenshot in EXERCISE_PREPARATION.

        Returns:
            list[int]: Fleet level, such as [120, 120, 120, 120, 120, 120].
        """
        level = []
        level += ButtonGrid(origin=(130, 259), delta=(168, 0), button_shape=(58, 21), grid_shape=(3, 1), name='LEVEL').buttons
        level += ButtonGrid(origin=(832, 259), delta=(168, 0), button_shape=(58, 21), grid_shape=(3, 1), name='LEVEL').buttons

        level = Level(level, name='LEVEL', letter=(255, 255, 255), threshold=128)
        result = level.ocr(image)
        return result

    def get_power(self, image):
        """
        Args:
            image: Screenshot in page_exercise.

        Returns:
            list[int]: Fleet power, such as [14848, 13477].
        """
        grids = ButtonGrid(origin=(222, 257), delta=(244, 30), button_shape=(72, 28), grid_shape=(4, 2), name='POWER')
        power = [grids[self.index, 0], grids[self.index, 1]]

        power = Digit(power, name='POWER', letter=(255, 223, 57), threshold=128)
        result = power.ocr(image)
        return result

    def get_priority(self, method="max_exp"):
        """
        Args:
            method: EXERCISE_CHOOSE_MODE

        Returns:
            np.ndarray: Priority of 4 opponents, such as [120, 113.2, 120, 95.3].
                        Higher priority means attack first.
        """
        if "easiest" in method:
            level = (1 - (np.sum(self.level) / MAX_LVL_SUM)) * 100
            team_pwr_div = np.count_nonzero(self.level) * PWR_FACTOR
            avg_team_pwr = np.sum(self.power) / team_pwr_div
            priority = level - avg_team_pwr
        else:
            priority = np.sum(self.level) / 6
        return priority


class OpponentChoose(UI):
    main_image = None
    opponents = []

    def _opponent_fleet_check_all(self):
        self.opponents = []
        self.main_image = self.device.image

        for index in range(4):
            self.ui_click(click_button=OPPONENT[index, 0], check_button=EXERCISE_PREPARATION,
                          appear_button=NEW_OPPONENT, skip_first_screenshot=True)

            self.opponents.append(Opponent(main_image=self.main_image, fleet_image=self.device.image, index=index))

            self.ui_click(click_button=BACK_ARROW, check_button=NEW_OPPONENT,
                          appear_button=EXERCISE_PREPARATION, skip_first_screenshot=True)

    def _opponent_sort(self, method="max_exp"):
        """
        Args:
            method: EXERCISE_CHOOSE_MODE

        Returns:
            list[int]: List of opponent index, such as [2, 1, 0, 3].
                       Attack one by one.
        """
        order = np.argsort([- x.get_priority(method) for x in self.opponents])
        logger.attr('Order', str(order))
        return order
