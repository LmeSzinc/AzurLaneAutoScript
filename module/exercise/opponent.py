import numpy as np

from module.base.button import ButtonGrid
from module.base.ocr import Digit
from module.exercise.assets import *
from module.logger import logger
from module.ui.assets import BACK_ARROW
from module.ui.ui import UI

OPPONENT = ButtonGrid(origin=(104, 77), delta=(244, 0), button_shape=(212, 304), grid_shape=(4, 1))


class Opponent:
    def __init__(self, main_image, fleet_image, index):
        self.index = index
        self.power = self.get_power(image=main_image)
        self.level = self.get_level(image=fleet_image)
        self.priority = self.get_priority()

        # [OPPONENT_1] ( 8256) 120 120 120 | (12356) 100  80  80
        level = [str(x).rjust(3, ' ') for x in self.level]
        power = ['(' + str(x).rjust(5, ' ') + ')' for x in self.power]
        logger.attr(
            'OPPONENT_%s, %s' % (index, str(np.round(self.priority, 3)).ljust(5, '0')),
            ' '.join([power[0]] + level[:3] + ['|'] + [power[1]] + level[3:])
        )

    @staticmethod
    def process(image):
        # image[-6:, :] = 255
        letter_l = np.where(np.mean(image, axis=0) < 85)[0]
        if len(letter_l):
            letter_l = letter_l[0] + 75
            image = image[:, letter_l:]

        image = np.pad(image, ((0, 0), (0, 5)), mode='constant', constant_values=255)

        return image

    def get_level(self, image):
        level = []
        level += ButtonGrid(origin=(130, 259), delta=(168, 0), button_shape=(57, 21), grid_shape=(3, 1), name='LEVEL').buttons()
        level += ButtonGrid(origin=(832, 259), delta=(168, 0), button_shape=(57, 21), grid_shape=(3, 1), name='LEVEL').buttons()

        level = Digit(level, letter=(255, 255, 255), back=(102, 102, 102), limit=120, threshold=127, additional_preprocess=self.process, name='LEVEL')
        result = level.ocr(image)
        return result

    def get_power(self, image):
        grids = ButtonGrid(origin=(222, 266), delta=(244, 30), button_shape=(72, 15), grid_shape=(4, 2), name='POWER')
        power = [grids[self.index, 0], grids[self.index, 1]]

        power = Digit(power, letter=(255, 223, 57), back=(74, 109, 156), threshold=221, limit=17000, name='POWER')
        result = power.ocr(image)
        return result

    def get_priority(self):
        # level = np.sum(self.level) / 6
        # power = np.sum(self.power) / 6
        # return level - (power - 1000) / 30

        level = np.sum(self.level) / 6
        return level


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

    def _opponent_sort(self):
        priority = np.argsort([- x.priority for x in self.opponents])
        logger.attr('Order', str(priority))
        return priority
