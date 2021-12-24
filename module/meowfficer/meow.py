import copy
from module.base.button import *
from module.ocr.ocr import Ocr
from module.logger import logger

class Meow:
    # Button to choose Meow
    button: Button
    # Level of Meow
    level: str

    def __init__(self, button, level):
        self.button = button
        self.level = level

class MeowLine:
    # Button of this line
    button: Button
    # Button to choose meowfficer
    buttonList = []
    # Level List of the line, str
    levelList = []

    def __init__(self, image, y):
        self.y = y
        self.area = (740, y-119, 1258, y)
        self.image = image
        self.meowLine_prase()

    def meowLine_prase(self):
        area = area_offset((17, 71, 429, 89), self.area[0:2])
        buttonList = ButtonGrid(origin=area[0:2], delta=(130, 20), button_shape=(22, 19), 
                                  grid_shape=(4, 1)).buttons
        levelList = Ocr(buttons = buttonList, name = 'meowfficer_level', letter = (49, 48, 49), 
                                  threshold = 96, alphabet='0123456789').ocr(image=self.image)
        # Correct wrong level
        for i in range(4):
            if levelList[i] != '' and int(levelList[i]) == 0:
                levelList[i] = str(30)
            if levelList[i] != '' and int(levelList[i]) >= 70:
                levelList[i] = str(int(levelList[i]) - 50)

        self.buttonList = buttonList
        self.button = self.buttonList[0]
        self.levelList = levelList

        logger.attr('MeowLevelList', levelList)
        self.buttonList = buttonList

    def meows(self):
        meows = []
        for i in range(len(self.buttonList)):
            meow = Meow(button=self.buttonList[i], level=self.levelList[i])
            meows.append(meow)
        return meows
    