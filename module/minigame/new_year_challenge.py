from module.base.timer import Timer
from module.logger import logger
from module.minigame.assets import *
from module.minigame.minigame import MinigameRun
from module.ocr.ocr import Digit
from module.ui.page import page_game_room
from module.ui.scroll import Scroll

OCR_GAME_NEW_YEAR_COIN_COST = Digit(NEW_YEAR_CHALLENGE_COIN_COST_HOLDER,
                                    name='OCR_GAME_NEW_YEAR_COIN_COST',
                                    letter=(33, 28, 49),
                                    threshold=128)
OCR_NEW_YEAR_BATTLE_SCORE = Digit(NEW_YEAR_CHALLENGE_SCORE_HOLDER,
                                  name='OCR_NEW_YEAR_BATTLE_SCORE',
                                  letter=(231, 215, 82),
                                  threshold=128)
MINIGAME_SCROLL = Scroll(MINIGAME_SCROLL_AREA, color=(247, 247, 247), name='MINIGAME_SCROLL')


class NewYearChallenge(MinigameRun):
    NEW_YEAR_BATTLE_RED = (255, 150, 123)
    NEW_YEAR_BATTLE_YELLOW = (247, 223, 115)
    NEW_YEAR_BATTLE_BLUE = (82, 134, 239)
    NEW_YEAR_BATTLE_TMP_BUTTON = [NEW_YEAR_CHALLENGE_TMP_1,
                                  NEW_YEAR_CHALLENGE_TMP_2,
                                  NEW_YEAR_CHALLENGE_TMP_3,
                                  NEW_YEAR_CHALLENGE_TMP_4,
                                  NEW_YEAR_CHALLENGE_TMP_5]
    NEW_YEAR_BATTLE_COLOR_BUTTON_DICT = {NEW_YEAR_BATTLE_RED: NEW_YEAR_CHALLENGE_RED_BUTTON,
                                         NEW_YEAR_BATTLE_YELLOW: NEW_YEAR_CHALLENGE_YELLOW_BUTTON,
                                         NEW_YEAR_BATTLE_BLUE: NEW_YEAR_CHALLENGE_BLUE_BUTTON}

    def deal_specific_popup(self):
        # enter NEW_YEAR_BATTLE first time
        if self.appear(NEW_YEAR_CHALLENGE_FIRST_TIME, offset=(5, 5), interval=3):
            self.device.click(NEW_YEAR_CHALLENGE_SAFE_AREA)
            return True
        return False

    def choose_game(self, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.deal_popup():
                continue
            # entrance
            if self.appear(NEW_YEAR_CHALLENGE_START, offset=(5, 5), interval=3):
                break
            # choose game
            if self.appear(NEW_YEAR_CHALLENGE_ENTRANCE, offset=(5, 5), interval=3):
                self.device.click(NEW_YEAR_CHALLENGE_ENTRANCE)
                continue
            # swipe down
            if self.ui_page_appear(page_game_room) and MINIGAME_SCROLL.appear(main=self) \
                    and not MINIGAME_SCROLL.at_bottom(main=self):
                MINIGAME_SCROLL.set_bottom(main=self)
                continue

    def use_coin(self, skip_first_screenshot=True):
        return self.use_coin_new_year_challenge(count=5)

    def play_game(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_game_room new_year_challenge_prepare
            out: page_game_room new_year_challenge_end/new_year_challenge_prepare
        """
        score_ocr_interval = Timer(0.6, count=5).start()
        started = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.deal_popup():
                continue
            # a turn
            if self.appear(NEW_YEAR_CHALLENGE_CHOOSING, offset=(5, 5), interval=3):
                # choose, click on clock to avoid be detected as "Too many click between 2 buttons"
                self.device.click(NEW_YEAR_CHALLENGE_CHOOSING)
                self.new_year_challenge_turn(skip_first_screenshot=False)
                continue
            # wait to choose
            if score_ocr_interval.reached() and self.appear(NEW_YEAR_CHALLENGE_STOP_PLAY, offset=(5, 5)):
                # score is enough, stop play
                score = OCR_NEW_YEAR_BATTLE_SCORE.ocr(self.device.image)
                score_ocr_interval.reset()
                if score > 1000 and self.appear_then_click(NEW_YEAR_CHALLENGE_STOP_PLAY, offset=(5, 5), interval=3):
                    continue
            # finished
            if self.appear(NEW_YEAR_CHALLENGE_END, offset=(5, 5), interval=3):
                break
            # game rule introduction
            if self.appear(NEW_YEAR_CHALLENGE_START, offset=(5, 5), interval=3):
                if started:
                    break
                else:
                    started = True
                    self.device.click(NEW_YEAR_CHALLENGE_START)
                    continue

    def exit_game(self, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.deal_popup():
                continue
            if self.appear(BACK, offset=(5, 5)):
                if self.appear(GOTO_CHOOSE_GAME, offset=(5, 5)):
                    break
                else:
                    self.appear_then_click(BACK, offset=(5, 5), interval=3)
                    continue
            if self.appear_then_click(NEW_YEAR_CHALLENGE_END, offset=(5, 5), interval=3):
                continue
            if self.appear_then_click(NEW_YEAR_CHALLENGE_EXIT, offset=(5, 5), interval=3):
                continue

    def use_coin_new_year_challenge(self, skip_first_screenshot=True, count=1):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.deal_popup():
                continue
            if self.appear(NEW_YEAR_CHALLENGE_ADD_COIN, offset=(5, 5)):
                # add coins
                if count > 1:
                    for i in range(count - 1):
                        self.device.click(NEW_YEAR_CHALLENGE_ADD_COIN)
                    self.device.screenshot()
                # spend no coins for test
                if count < 1:
                    self.appear_then_click(NEW_YEAR_CHALLENGE_DEC_COIN, offset=(5, 5), interval=3)
                    self.device.screenshot()
                coin_cost_after_add = OCR_GAME_NEW_YEAR_COIN_COST.ocr(self.device.image)
                logger.info(f"coin cost after add : {coin_cost_after_add}")
                if count >= 1 and coin_cost_after_add <= 0:
                    # can't add coin because all monthly reward is gotten or coin left is 0
                    return False
                return True

    def new_year_challenge_turn(self, skip_first_screenshot=True):
        if not skip_first_screenshot:
            self.device.screenshot()
        to_clicks = []
        # judge to click
        for to_judge in self.NEW_YEAR_BATTLE_TMP_BUTTON:
            for color, button in self.NEW_YEAR_BATTLE_COLOR_BUTTON_DICT.items():
                if self.image_color_count(to_judge, color, threshold=221, count=10):
                    to_clicks.append(button)
                    break
        logger.info(f"to clicks: {to_clicks}")
        to_clicks.reverse()
        # click
        click_interval = Timer(0.2, count=5).start()
        while 1:
            if to_clicks and click_interval.reached():
                self.device.click(to_clicks.pop())
                click_interval.reset()
            if not to_clicks:
                break
