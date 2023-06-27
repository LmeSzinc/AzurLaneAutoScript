from module.base.timer import Timer
from module.logger import logger
from module.minigame.assets import *
from module.ui.assets import GAME_ROOM_CHECK
from module.ui.page import page_game_room
from module.ui.ui import UI


class Minigame(UI):
    NEW_YEAR_BATTLE_RED = (255, 150, 123)
    NEW_YEAR_BATTLE_YELLOW = (247, 223, 115)
    NEW_YEAR_BATTLE_BLUE = (82, 134, 239)
    NEW_YEAR_BATTLE_TMP_BUTTON = [GAME_ROOM_GAME_NEW_YEAR_BATTLE_TMP_1,
                                  GAME_ROOM_GAME_NEW_YEAR_BATTLE_TMP_2,
                                  GAME_ROOM_GAME_NEW_YEAR_BATTLE_TMP_3,
                                  GAME_ROOM_GAME_NEW_YEAR_BATTLE_TMP_4,
                                  GAME_ROOM_GAME_NEW_YEAR_BATTLE_TMP_5]
    NEW_YEAR_BATTLE_COLOR_BUTTON_DICT = {NEW_YEAR_BATTLE_RED: GAME_ROOM_GAME_NEW_YEAR_BATTLE_RED_BUTTON,
                                         NEW_YEAR_BATTLE_YELLOW: GAME_ROOM_GAME_NEW_YEAR_BATTLE_YELLOW_BUTTON,
                                         NEW_YEAR_BATTLE_BLUE: GAME_ROOM_GAME_NEW_YEAR_BATTLE_BLUE_BUTTON}

    def minigame_run(self):
        """
        Pages:
            in: page_game_room main_page
            out: page_game_room main_page
        """
        logger.info("Enter minigame")
        if self.appear(GAME_ROOM_GOTO_CHOOSE_GAME, offset=(5, 5)):
            self.appear_then_click(GAME_ROOM_GOTO_CHOOSE_GAME)
        logger.info("Choose game")
        self.choose_game_new_year_battle()
        logger.info("Add coins")
        self.add_coin_new_year_battle()
        logger.info("Play minigame")
        self.play_game_new_year_battle()
        logger.info("Exit minigame")
        self.exit_game_new_year_battle()

    def deal_popup(self):
        """
            deal possible popups
            need re-screenshot if return true
        """
        # enter NEW_YEAR_BATTLE first time
        if self.appear(GAME_ROOM_GAME_NEW_YEAR_BATTLE_FIRST_TIME, offset=(5, 5)):
            self.device.click(GAME_ROOM_SAFE_AREA)
            return True
        # coins more than 31, deal popup
        if self.appear(GAME_ROOM_COIN_POPUP, offset=(5, 5)):
            self.appear_then_click(GAME_ROOM_COIN_POPUP)
            return True
        # coins/tickets received
        if self.appear(GAME_ROOM_REWARD, offset=(5, 5)):
            self.appear_then_click(GAME_ROOM_REWARD)
            return True
        return False

    def choose_game_new_year_battle(self):
        swipe_interval = Timer(0.6, count=2)
        while 1:
            self.device.screenshot()
            if self.deal_popup():
                continue
            # choose game
            if self.appear(GAME_ROOM_GAME_NEW_YEAR_BATTLE, offset=(5, 5)):
                self.appear_then_click(GAME_ROOM_GAME_NEW_YEAR_BATTLE)
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
            if self.appear(GAME_ROOM_GAME_NEW_YEAR_BATTLE_START, offset=(5, 5)):
                self.appear_then_click(GAME_ROOM_GAME_NEW_YEAR_BATTLE_START)
                continue
            if self.appear(GAME_ROOM_GAME_NEW_YEAR_BATTLE_CHOOSING, offset=(5, 5)):
                # click on clock to avoid be detected as "Too many click between 2 buttons"
                self.appear_then_click(GAME_ROOM_GAME_NEW_YEAR_BATTLE_CHOOSING)
                # judge color and click
                for to_judge in self.NEW_YEAR_BATTLE_TMP_BUTTON:
                    for color, button in self.NEW_YEAR_BATTLE_COLOR_BUTTON_DICT.items():
                        if self.image_color_count(to_judge, color, threshold=221, count=10) \
                                and self.appear(button, offset=(5, 5)):
                            self.appear_then_click(button)
                            break
                continue
            # finished
            if self.appear(GAME_ROOM_REWARD, offset=(5, 5)):
                break
            # finished
            if self.appear(GAME_ROOM_GAME_NEW_YEAR_BATTLE_END, offset=(5, 5)):
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
            if self.appear(GAME_ROOM_BACK, offset=(5, 5)):
                if self.appear(GAME_ROOM_GOTO_CHOOSE_GAME, offset=(5, 5)):
                    break
                else:
                    self.appear_then_click(GAME_ROOM_BACK)
                    continue
            if self.appear(GAME_ROOM_GAME_NEW_YEAR_BATTLE_END, offset=(5, 5)):
                self.appear_then_click(GAME_ROOM_GAME_NEW_YEAR_BATTLE_END)
                continue
            if self.appear(GAME_ROOM_GAME_NEW_YEAR_BATTLE_EXIT, offset=(5, 5)):
                self.appear_then_click(GAME_ROOM_GAME_NEW_YEAR_BATTLE_EXIT)
                continue

    def add_coin_new_year_battle(self, count=1):
        self.device.screenshot()
        if self.deal_popup():
            self.device.screenshot()
        if self.appear(GAME_ROOM_GAME_NEW_YEAR_BATTLE_ADD_COIN, offset=(5, 5)):
            if count > 1:
                for i in range(count - 1):
                    self.appear_then_click(GAME_ROOM_GAME_NEW_YEAR_BATTLE_ADD_COIN)
            if count < 1:
                self.appear_then_click(GAME_ROOM_GAME_NEW_YEAR_BATTLE_DEC_COIN)

    def go_to_game_room_main_page(self):
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
                    and not self.appear(GAME_ROOM_GOTO_CHOOSE_GAME, offset=(5, 5)):
                self.appear_then_click(GAME_ROOM_BACK)
                continue
            if self.appear(GAME_ROOM_GOTO_CHOOSE_GAME, offset=(5, 5)):
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
                    and not self.appear(GAME_ROOM_GOTO_CHOOSE_GAME, offset=(5, 5)):
                self.appear_then_click(GAME_ROOM_BACK)
                continue
            # collect coins
            if not coin_collected and self.config.Minigame_Collect and self.appear(GAME_ROOM_COIN, offset=(5, 5)):
                self.appear_then_click(GAME_ROOM_COIN)
                coin_collected = True
                continue
            if self.appear(GAME_ROOM_GOTO_CHOOSE_GAME, offset=(5, 5)):
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
        self.go_to_game_room_main_page()
        # force play
        if self.config.Minigame_ForceExec > 0:
            logger.info("Force play")
            while self.config.Minigame_ForceExec > 0:
                self.minigame_run()
                self.config.Minigame_ForceExec = self.config.Minigame_ForceExec - 1
        # collect coins
        coin_collected = self.collect_coin()
        # play after collect
        self.minigame_run()
        if coin_collected and self.config.Minigame_PlayAfterCollect:
            logger.info("Play after collect")
            for i in range(2):
                self.minigame_run()

