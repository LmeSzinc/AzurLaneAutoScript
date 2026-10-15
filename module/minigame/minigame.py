import numpy as np

import module.config.server as server
from module.base.timer import Timer
from module.base.utils import random_rectangle_point
from module.combat.assets import GET_ITEMS_1
from module.exception import RequestHumanTakeover
from module.logger import logger
from module.minigame.assets import *
from module.ocr.ocr import Digit
from module.ui.assets import ACADEMY_GOTO_GAME_ROOM
from module.ui.page import page_academy, page_game_room
from module.ui.scroll import Scroll
from module.ui.ui import UI

if server.server != 'jp':
    OCR_COIN = Digit(COIN_HOLDER,
                    name='OCR_COIN',
                    letter=(255, 235, 115),
                    threshold=128)
else:
    OCR_COIN = Digit(COIN_HOLDER,
                    name='OCR_COIN',
                    letter=(211, 196, 95),
                    threshold=128)


class MinigameScroll(Scroll):
    def cal_position(self, main):
        """Locate the knob without counting the persistent start button's white border."""
        y = main.minigame_scroll_y()
        if y is None:
            return None
        # The reference asset is captured with the slider at the top of the track.
        reference_y = (MINIGAME_SCROLL_KNOB.area[1] + MINIGAME_SCROLL_KNOB.area[3]) / 2
        self.length = 2 * (reference_y - self.area[1])
        position = (y - reference_y) / (self.total - self.length)
        position = min(max(position, 0.0), 1.0)
        logger.attr(self.name, f'{position:.2f} (knob y={y})')
        return position

    def set(self, position, main, random_range=(-0.05, 0.05), distance_check=True, skip_first_screenshot=True):
        """Keep percentage positioning, recovering through the cards when the knob is covered."""
        logger.info(f'{self.name} set to {position}')
        timeout = Timer(20).start()
        interval = Timer(1)
        dragged = 0
        previous = None
        stationary = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()
            current = self.cal_position(main)
            if current is not None and abs(position - current) < self.drag_threshold:
                return dragged
            if dragged >= 8 or timeout.reached():
                raise RequestHumanTakeover('Unable to position the minigame scrollbar')
            if not interval.reached():
                continue
            if position >= 1 - self.edge_threshold:
                # The knob is covered at the bottom. Confirm the cards stop moving instead.
                cards = main.image_crop((300, 110, 600, 500))
                if previous is not None and np.mean(np.abs(cards.astype(float) - previous)) < 1:
                    stationary += 1
                    if stationary >= 2:
                        return dragged
                else:
                    stationary = 0
                previous = cards.astype(float)
                p1, p2 = (600, 550), (600, 250)
            elif current is None:
                # Move toward the top through the cards until the knob is visible again.
                p1, p2 = (600, 250), (600, 550)
            else:
                p1 = random_rectangle_point(self.position_to_screen(current), n=1)
                p2 = random_rectangle_point(self.position_to_screen(position, random_range=random_range), n=1)
            main.device.swipe(p1, p2, name=self.name, distance_check=distance_check)
            dragged += 1
            interval.reset()


MINIGAME_SCROLL = MinigameScroll(MINIGAME_SCROLL_AREA, color=(247, 247, 247), name='MINIGAME_SCROLL')


class MinigameUI(UI):
    def minigame_scroll_y(self):
        """Return the scrollbar knob's screen coordinate, or None if covered."""
        if self.appear(MINIGAME_SCROLL_KNOB, offset=(-9, -73, 12, 495)):
            return int((MINIGAME_SCROLL_KNOB.button[1] + MINIGAME_SCROLL_KNOB.button[3]) // 2)
        return None

    def minigame_list_appear(self):
        """Identify the shared card marker together with the list scrollbar."""
        # Each asset anchors its own column; search vertically as the list scrolls.
        return MINIGAME_SCROLL.appear(main=self) and (
            self.appear(GAME_LIST_CHECK_LEFT, offset=(5, 500))
            or self.appear(GAME_LIST_CHECK_RIGHT, offset=(5, 500))
        )


class MinigameRun(MinigameUI):

    def minigame_run(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_game_room main_page
            out: page_game_room main_page/choose_game_page
        Return:
            False if unable or unnecessary to play
        """
        logger.hr('Minigame run', level=1)

        # page_game_room main_page -> MINIGAME_SCROLL
        logger.info("Enter minigame")
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # End
            if self.minigame_list_appear():
                break
            # unable to get more ticket popup
            if self.deal_popup():
                continue
            if self.appear_then_click(GOTO_CHOOSE_GAME, offset=(5, 5), interval=3):
                # note: GOTO_CHOOSE_GAME is some where safe to click
                # that won't enter any minigame on the minigame list page
                continue

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
            self.interval_reset(COIN_POPUP, interval=3)
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


class Minigame(MinigameUI):

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
        logger.info('minigame go_to_main_page')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.ui_additional():
                continue
            if self.appear_then_click(COIN_POPUP, offset=(5, 5), interval=2):
                continue
            if self.minigame_list_appear():
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
            if self.minigame_list_appear():
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
        # TEMP: 2026.10.15 Game bug that -1 +1 button is not functioning at all,
        # skip minigame before game client patches
        logger.info('Skip minigame before game client patches')
        self.config.task_delay(server_update=True)
        self.config.task_stop()

        # TEMP: 2026.02.18 separate self.ui_ensure(page_game_room) into 2 steps
        # EN has different page_academy detection, to use ui_ensure(page_game_room),
        # ui_goto must use `if self.ui_page_appear(page)` instead of `if self.appear(page.check_button)`
        # But that would cause page_main/page_main_white clicking a static switch button
        self.ui_ensure(page_academy)
        # page_academy -> page_game_room
        for _ in self.loop():
            if self.ui_page_appear(page_game_room):
                break
            if self.ui_page_appear(page_academy, interval=5):
                self.device.click(ACADEMY_GOTO_GAME_ROOM)
                continue
            # You've reached your monthly limit of Game Tickets, and will not be able to earn any more.
            # Continue playing the minigame?
            if self.handle_popup_confirm('MINIGAME_ENTER'):
                continue

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
