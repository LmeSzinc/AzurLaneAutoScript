from module.combat.assets import GET_ITEMS_1
from module.logger import logger
from module.minigame.assets import *
from module.ocr.ocr import Digit
from module.ui.assets import GAME_ROOM_CHECK
from module.ui.page import page_game_room
from module.ui.scroll import Scroll
from module.ui.ui import UI

OCR_COIN = Digit(COIN_HOLDER,
                 name='OCR_COIN',
                 letter=(255, 235, 115),
                 threshold=128)
MINIGAME_SCROLL = Scroll(MINIGAME_SCROLL_AREA, color=(247, 247, 247), name='MINIGAME_SCROLL')

class MinigameRun(UI):

    def minigame_run(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_game_room main_page
            out: page_game_room main_page
        Return:
            False if unable or unnecessary to play
        """
        logger.hr('Minigame run', level=1)

        logger.info("Enter minigame")
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # unable to get more ticket popup
            if self.deal_popup():
                continue
            if self.appear_then_click(GOTO_CHOOSE_GAME, offset=(5, 5), interval=3):
                continue
            if self.appear(GAME_ROOM_CHECK, offset=(5, 5)) \
                    and MINIGAME_SCROLL.appear(main=self):
                break
        logger.info("Choose minigame")
        self.choose_game()
        # try to add coins, if failed, skip play
        add_coin_result = self.use_coin()
        if add_coin_result:
            logger.hr("Play minigame", level=2)
            self.play_game()
        logger.info("Exit minigame")
        self.exit_game()
        return add_coin_result

    def deal_popup(self):
        """
            deal possible popups
            need re-screenshot if return true
        """
        # specific
        if self.deal_specific_popup():
            return True
        if self.handle_popup_confirm('TICKETS_FULL'):
            return True
        # coins more than 31, deal popup
        if self.appear_then_click(COIN_POPUP, offset=(5, 5), interval=3):
            return True
        # coins/tickets received
        if self.appear_then_click(GET_ITEMS_1, offset=(5, 5), interval=3):
            return True
        return False

    def deal_specific_popup(self):
        return False

    def choose_game(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_game_room choosing_game
            out: page_game_room game_entrance
        """
        pass

    def use_coin(self, skip_first_screenshot=True):
        return False

    def play_game(self, skip_first_screenshot=True):
        pass

    def exit_game(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_game_room new_year_challenge_end
            out: page_game_room choose_game
        """
        pass


class Minigame(UI):

    def get_coin_amount(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_game_room main_page
            out: page_game_room main_page
        Returns:
            int: Coin amount
        """
        if not skip_first_screenshot:
            self.device.screenshot()
        amount = OCR_COIN.ocr(self.device.image)
        if amount >= 40:
            amount = 40
        return amount

    def go_to_main_page(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_game_room main_page/choose_game_page
            out: page_game_room main_page
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.ui_additional():
                continue
            if self.appear_then_click(COIN_POPUP, offset=(5, 5), interval=2):
                continue
            if self.appear(GAME_ROOM_CHECK, offset=(5, 5)) \
                    and not self.appear(GOTO_CHOOSE_GAME, offset=(5, 5)):
                self.appear_then_click(BACK, offset=(5, 5), interval=2)
                continue
            if self.appear(GOTO_CHOOSE_GAME, offset=(5, 5)):
                break

    def collect_coin(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_game_room main_page/choose_game_page
            out: page_game_room main_page
        """
        coin_collected = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.ui_additional():
                continue
            if self.appear_then_click(COIN_POPUP, offset=(5, 5), interval=3):
                continue
            # game room and choose game have same header, go to game room first
            if self.appear(GAME_ROOM_CHECK, offset=(5, 5)) \
                    and not self.appear(GOTO_CHOOSE_GAME, offset=(5, 5)):
                self.appear_then_click(BACK, offset=(5, 5), interval=3)
                continue
            # collect coins
            if not coin_collected and self.appear(COIN, offset=(5, 5)):
                self.appear_then_click(COIN, offset=(5, 5), interval=3)
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

        # choose game
        specific_game_name = "new_year_challenge"
        minigame_instance = None
        if specific_game_name == "new_year_challenge":
            from module.minigame.new_year_challenge import NewYearChallenge
            minigame_instance = NewYearChallenge(config=self.config, device=self.device)

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
            # specific game logic
            if minigame_instance is not None and minigame_instance.minigame_run():
                play_count += 1
                continue
            elif minigame_instance is None:
                logger.error(f"unknown game name {specific_game_name}")
                break
            else:
                break

        self.config.task_delay(server_update=True)
