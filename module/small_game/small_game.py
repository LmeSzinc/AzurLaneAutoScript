from module.logger import logger
from math import ceil
from module.ocr.ocr import Digit
from module.ui.page import page_main, page_game_room
from module.ui.ui import UI
from module.small_game.assets import *

MAX_GAME_COIN = 40
OCR_GAME_COIN_MAX_TO_BUY = Digit(GAME_COIN_MAX_TO_BUY)


class SmallGame(UI):
    def GetGameCoin(self) -> int:
        self.appear_then_click(GAME_COIN)
        self.wait_until_appear_then_click(BUY_MAX_GAME_COIN)
        Coin = MAX_GAME_COIN - OCR_GAME_COIN_MAX_TO_BUY.ocr(self.device.screenshot())
        self.appear_then_click(BUY_GAME_COIN_CANCEL)
        return Coin

    def BuyGameCoin(self, Count):
        self.appear_then_click(GAME_COIN)
        self.device.multi_click(ADD_GAME_COIN, Count)
        # self.device.click(BUY_GAME_COIN_CONFIRM)

    def SelectGame(self):
        while True:
            self.device.screenshot()
            if self.appear(START_TO_PLAY):
                self.device.click(START_TO_PLAY)
                continue
            if self.appear(GAME_JENGA):
                self.device.click(GAME_JENGA)
                break

    def PlayGame(self):
        while True:
            self.device.screenshot()
            if self.appear(ADD_PLAY_COUNT):
               break
        self.device.multi_click(ADD_PLAY_COUNT, 5)
        self.wait_until_appear_then_click(GAME_JENGA_START)
        self.wait_until_appear_then_click(GAME_JENGA_BACK)
        self.wait_until_appear_then_click(GAME_JENGA_QUIT_CONFIRM)
        self.wait_until_appear_then_click(GAME_JENGA_SAFE_AREA)
        self.wait_until_appear_then_click(GAME_JENGA_END_GAME)

    def CalculatePlayTime(self, GameCoin) -> int:
        return ceil(GameCoin / 5)

    def run(self):
        self.ui_ensure(page_game_room)
        Coin = self.GetGameCoin()
        BuyCoin = self.config.SmallGame_Buy
        while BuyCoin > 0 or Coin > 0:
            if BuyCoin + Coin > MAX_GAME_COIN:
                self.BuyGameCoin(MAX_GAME_COIN - Coin)
                BuyCoin = BuyCoin - (MAX_GAME_COIN - Coin)
                Coin = MAX_GAME_COIN
            else:
                self.BuyGameCoin(BuyCoin)
                Coin += BuyCoin
                BuyCoin = 0
            PlayTime = self.CalculatePlayTime(Coin)
            if PlayTime != 0:
                self.SelectGame()
                for _ in range(PlayTime):
                    self.PlayGame()
                    Coin = 0
                self.wait_until_appear_then_click(GAME_JENGA_BACK)
                self.wait_until_appear_then_click(GAME_ROOM_BACK)
        self.ui_goto(page_main)
        self.config.task_delay(success=True)
