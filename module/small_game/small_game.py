from module.config.utils import get_first_day_of_next_week
from math import ceil
from module.ocr.ocr import Digit
from module.ui.page import page_main, page_game_room
from module.ui.ui import UI
from module.small_game.assets import *
from module.config.utils import deep_set

MAX_GAME_COIN = 40
LIMIT = 10000
OCR_GAME_COIN_MAX_TO_BUY = Digit(GAME_COIN_MAX_TO_BUY)
OCR_GAME_JENGA_COIN = Digit(GAME_JENGA_COIN)

class SmallGame(UI):
    def GetGameCoin(self) -> int:
        self.appear_then_click(GAME_COIN)
        self.wait_until_appear_then_click(BUY_MAX_GAME_COIN)
        for _ in range(3):
            Coin = MAX_GAME_COIN - OCR_GAME_COIN_MAX_TO_BUY.ocr(self.device.screenshot())
        self.appear_then_click(BUY_GAME_COIN_CANCEL)
        return Coin

    def BuyGameCoin(self, Count):
        while True:
            if self.appear_then_click(GAME_COIN):
                break
        self.device.multi_click(ADD_GAME_COIN, Count)
        while True:
            if self.device.click(BUY_GAME_COIN_CONFIRM):
                break

    def SelectGame(self) -> bool:
        while True:
            self.device.screenshot()
            if self.appear_then_click(START_TO_PLAY):
                break
        while True:
            self.device.screenshot()
            if self.appear_then_click(POP_UP_REACH_LIMIT):
                return False
            if self.appear_then_click(GAME_JENGA):
                break
        return True
    def PlayGame(self) -> bool:
        while True:
            self.device.screenshot()
            if self.appear(ADD_PLAY_COUNT):
               break
        self.device.multi_click(ADD_PLAY_COUNT, 5)
        if OCR_GAME_JENGA_COIN.ocr(self.device.screenshot()) == 0:
            return False
        while True:
            self.device.screenshot()
            if self.appear(POP_UP_REACH_LIMIT):
                self.ui_click(POP_UP_REACH_LIMIT)
                return False
            if self.appear_then_click(GAME_JENGA_START):
                continue
            if self.appear_then_click(GAME_JENGA_BACK):
                continue
            if self.appear_then_click(GAME_JENGA_QUIT_CONFIRM):
                continue
            if self.appear_then_click(GAME_JENGA_SAFE_AREA):
                continue
            if self.appear_then_click(GAME_JENGA_END_GAME):
                break
        return True

    def CalculatePlayTime(self, GameCoin) -> int:
        return ceil(GameCoin / 5)

    def GotoGameRoom(self):
        while True:
            self.device.screenshot()
            if self.appear_then_click(GAME_JENGA_BACK):
                continue
            if self.appear_then_click(GAME_ROOM_BACK):
                break
    def run(self):
        self.ui_ensure(page_game_room)
        Coin = self.GetGameCoin()
        BuyCoin = self.config.SmallGame_Buy
        if self.SelectGame():
            for _ in range(self.CalculatePlayTime(Coin)):
                if not self.PlayGame():
                    self.GotoGameRoom()
                    self.ui_goto(page_main)
                    self.config.task_delay(target=get_first_day_of_next_week())
                    return
            self.GotoGameRoom()
            if BuyCoin:
                if self.config.SmallGame_Count > MAX_GAME_COIN:
                    deep_set(self.config.data, "SmallGame.SmallGame.Count", MAX_GAME_COIN)
                self.BuyGameCoin(self.config.SmallGame_Count)
                self.SelectGame()
                for _ in range(self.CalculatePlayTime(self.config.SmallGame_Count)):
                    if not self.PlayGame():
                        self.GotoGameRoom()
                        self.ui_goto(page_main)
                        self.config.task_delay(target=get_first_day_of_next_week())
                        return
                self.GotoGameRoom()
            else:
                self.ui_goto(page_main)
                self.config.task_delay(target=get_first_day_of_next_week())
                return
        else:
            self.ui_goto(page_main)
            self.config.task_delay(target=get_first_day_of_next_week())
