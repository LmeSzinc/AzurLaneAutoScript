from module.base.timer import Timer
from module.logger import logger
from module.minigame.assets import *
from module.ocr.ocr import Digit
from module.ui.assets import GAME_ROOM_CHECK
from module.ui.page import page_game_room
from module.ui.ui import UI

OCR_COIN = Digit(COIN_HOLDER,
                 name='OCR_COIN',
                 letter=(255, 235, 115),
                 threshold=128)
OCR_GAME_NEW_YEAR_COIN_COST = Digit(GAME_NEW_YEAR_BATTLE_COIN_COST_HOLDER,
                                    name='OCR_GAME_NEW_YEAR_COIN_COST',
                                    letter=(33, 28, 49),
                                    threshold=128)
OCR_NEW_YEAR_BATTLE_SCORE = Digit(GAME_NEW_YEAR_BATTLE_SCORE_HOLDER,
                                  name='OCR_NEW_YEAR_BATTLE_SCORE',
                                  letter=(231, 215, 82),
                                  threshold=128)


class Minigame(UI):
    NEW_YEAR_BATTLE_RED = (255, 150, 123)
    NEW_YEAR_BATTLE_YELLOW = (247, 223, 115)
    NEW_YEAR_BATTLE_BLUE = (82, 134, 239)
    NEW_YEAR_BATTLE_TMP_BUTTON = [GAME_NEW_YEAR_BATTLE_TMP_1,
                                  GAME_NEW_YEAR_BATTLE_TMP_2,
                                  GAME_NEW_YEAR_BATTLE_TMP_3,
                                  GAME_NEW_YEAR_BATTLE_TMP_4,
                                  GAME_NEW_YEAR_BATTLE_TMP_5]
    NEW_YEAR_BATTLE_COLOR_BUTTON_DICT = {NEW_YEAR_BATTLE_RED: GAME_NEW_YEAR_BATTLE_RED_BUTTON,
                                         NEW_YEAR_BATTLE_YELLOW: GAME_NEW_YEAR_BATTLE_YELLOW_BUTTON,
                                         NEW_YEAR_BATTLE_BLUE: GAME_NEW_YEAR_BATTLE_BLUE_BUTTON}

    def minigame_run(self):
        """
        Pages:
            in: page_game_room main_page
            out: page_game_room main_page
        Return:
            False if unable to play
        """
        logger.info("Enter minigame")
        self.appear_then_click(GOTO_CHOOSE_GAME, offset=(5, 5))
        logger.info("Choose game")
        self.choose_game_new_year_battle()
        logger.info("Add coins")
        # try to add coins, if failed, skip play
        add_coin_result = self.use_coin_new_year_battle(5)
        if add_coin_result:
            logger.info("Play minigame")
            self.play_game_new_year_battle()
        logger.info("Exit minigame")
        self.exit_game_new_year_battle()
        return add_coin_result

    def deal_popup(self):
        """
            deal possible popups
            need re-screenshot if return true
        """
        # enter NEW_YEAR_BATTLE first time
        if self.appear(GAME_NEW_YEAR_BATTLE_FIRST_TIME, offset=(5, 5)):
            self.device.click(SAFE_AREA)
            return True
        # coins more than 31, deal popup
        if self.appear_then_click(COIN_POPUP, offset=(5, 5)):
            return True
        # coins/tickets received
        if self.appear_then_click(REWARD, offset=(5, 5)):
            return True
        return False

    def get_coin_amount(self):
        """
        Pages:
            in: page_game_room main_page
            out: page_game_room main_page
        Returns:
            int: Coin amount
        """
        amount = OCR_COIN.ocr(self.device.image)
        if amount >= 40:
            amount = 40
        return amount

    def get_game_new_year_battle_coin_cost(self):
        """
        Returns:
            int: Coin cost
        """
        return OCR_GAME_NEW_YEAR_COIN_COST.ocr(self.device.image)

    def get_game_new_year_battle_score(self):
        """
        Returns:
            int: Coin cost
        """
        return OCR_NEW_YEAR_BATTLE_SCORE.ocr(self.device.image)

    def choose_game_new_year_battle(self):
        swipe_interval = Timer(0.6, count=2).start()
        while 1:
            self.device.screenshot()
            if self.deal_popup():
                continue
            # choose game
            if self.appear_then_click(GAME_NEW_YEAR_BATTLE, offset=(5, 5)):
                break
            if swipe_interval.reached():
                self.device.swipe_vector((0, -500),
                                         box=(10, 110, 60, 1060),
                                         random_range=(-10, -10, 10, 10),
                                         padding=0)
                swipe_interval.reset()

    def play_game_new_year_battle(self):
        """
        Pages:
            in: page_game_room new_year_battle_prepare
            out: page_game_room new_year_battle_end
        """
        while 1:
            self.device.screenshot()
            if self.deal_popup():
                continue
            # game rule introduction
            if self.appear_then_click(GAME_NEW_YEAR_BATTLE_START, offset=(5, 5)):
                continue
            # choose, click on clock to avoid be detected as "Too many click between 2 buttons"
            if self.appear_then_click(GAME_NEW_YEAR_BATTLE_CHOOSING, offset=(5, 5)):
                # judge color and click
                for to_judge in self.NEW_YEAR_BATTLE_TMP_BUTTON:
                    for color, button in self.NEW_YEAR_BATTLE_COLOR_BUTTON_DICT.items():
                        if self.image_color_count(to_judge, color, threshold=221, count=10) \
                                and self.appear(button, offset=(5, 5)):
                            self.appear_then_click(button)
                            break
                continue
            # wait to choose
            if self.appear(GAME_NEW_YEAR_BATTLE_STOP_PLAY, offset=(5, 5)):
                # score is enough, stop play
                score = self.get_game_new_year_battle_score()
                if score > 1000 and self.appear_then_click(GAME_NEW_YEAR_BATTLE_STOP_PLAY):
                    break
            # finished
            if self.appear(REWARD, offset=(5, 5)):
                break
            # finished
            if self.appear(GAME_NEW_YEAR_BATTLE_END, offset=(5, 5)):
                break

    def exit_game_new_year_battle(self):
        """
        Pages:
            in: page_game_room new_year_battle_end
            out: page_game_room new_year_battle
        """
        while 1:
            self.device.screenshot()
            if self.deal_popup():
                continue
            if self.appear(BACK, offset=(5, 5)):
                if self.appear(GOTO_CHOOSE_GAME, offset=(5, 5)):
                    break
                else:
                    self.appear_then_click(BACK)
                    continue
            if self.appear_then_click(GAME_NEW_YEAR_BATTLE_END, offset=(5, 5)):
                continue
            if self.appear_then_click(GAME_NEW_YEAR_BATTLE_EXIT, offset=(5, 5)):
                continue

    def use_coin_new_year_battle(self, count=1):
        self.device.screenshot()
        if self.deal_popup():
            self.device.screenshot()
        if self.appear(GAME_NEW_YEAR_BATTLE_ADD_COIN, offset=(5, 5)):
            if count > 1:
                for i in range(count - 1):
                    self.appear_then_click(GAME_NEW_YEAR_BATTLE_ADD_COIN)
                self.device.screenshot()
                coin_cost_after_add = self.get_game_new_year_battle_coin_cost()
                logger.info(f"coin cost after add : {coin_cost_after_add}")
                if coin_cost_after_add <= 0:
                    # can't add coin because all monthly reward is gotten or coin left is 0
                    return False
            # spend no coins for test
            if count < 1:
                self.appear_then_click(GAME_NEW_YEAR_BATTLE_DEC_COIN)
        return True

    def go_to_main_page(self):
        """
        Pages:
            in: page_game_room
            out: page_game_room main_page
        """
        while 1:
            self.device.screenshot()
            if self.deal_popup():
                continue
            if self.appear(GAME_ROOM_CHECK, offset=(5, 5)) \
                    and not self.appear(GOTO_CHOOSE_GAME, offset=(5, 5)):
                self.appear_then_click(BACK)
                continue
            if self.appear(GOTO_CHOOSE_GAME, offset=(5, 5)):
                break

    def collect_coin(self):
        """
        Pages:
            in: page_game_room main_page/choose_game_page
            out: page_game_room main_page
        """
        coin_collected = False
        while 1:
            self.device.screenshot()
            if self.deal_popup():
                continue
            # game room and choose game have same header, go to game room first
            if self.appear(GAME_ROOM_CHECK, offset=(5, 5)) \
                    and not self.appear(GOTO_CHOOSE_GAME, offset=(5, 5)):
                self.appear_then_click(BACK)
                continue
            # collect coins
            if not coin_collected and self.config.Minigame_Collect and self.appear(COIN, offset=(5, 5)):
                self.appear_then_click(COIN)
                coin_collected = True
                continue
            if self.appear(GOTO_CHOOSE_GAME, offset=(5, 5)):
                break
        return coin_collected

    def run(self):
        """
        Pages:
            in: Any page
            out: page_game_room
        """

        self.ui_ensure(page_game_room)
        # game room and choose game have same header, go to game room first
        self.go_to_main_page()
        coin_collected = False
        play_count = 0
        while 1:
            # play count limit
            if play_count >= 10:
                break
            # ocr to get coin count and ticket count
            coin_count = self.get_coin_amount()
            logger.info(f"coin count : {coin_count}")
            # collect coins
            if coin_count <= 30 and not coin_collected:
                coin_collected = True
                if self.collect_coin():
                    continue
            # no coin left
            if coin_count == 0:
                logger.info(f"coin count : {coin_count}, finished")
                break
            logger.info(f"coin count > 0, spend")
            if self.minigame_run():
                play_count += 1
                continue
            else:
                break
