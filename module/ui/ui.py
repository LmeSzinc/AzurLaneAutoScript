from module.base.button import Button
from module.base.timer import Timer
from module.combat.assets import *
from module.exception import GameNotRunningError, RequestHumanTakeover
from module.handler.assets import *
from module.handler.info_handler import InfoHandler
from module.logger import logger
from module.map.assets import *
from module.ocr.ocr import Ocr
from module.ui.page import *


class UI(InfoHandler):
    # All pages defined.
    ui_pages = [
        page_unknown,
        page_main, page_fleet, page_guild, page_mission, page_event_list,
        page_campaign_menu, page_campaign, page_exercise, page_daily,
        page_event, page_sp, page_raid, page_archives,
        page_reward, page_commission, page_tactical,
        page_reshmenu, page_research, page_shipyard,
        page_dormmenu, page_dorm, page_meowfficer,
        page_academy, page_shop, page_munitions, page_build,
        page_os
    ]
    ui_current: Page

    def ui_page_appear(self, page):
        """
        Args:
            page (Page):
        """
        return self.appear(page.check_button, offset=(20, 20))

    def ensure_button_execute(self, button, offset=0):
        if isinstance(button, Button) and self.appear(button, offset=offset):
            return True
        elif callable(button) and button():
            return True
        else:
            return False

    def ui_click(self, click_button, check_button, appear_button=None, additional=None, confirm_wait=1,
                 offset=(20, 20), retry_wait=10, skip_first_screenshot=False):
        """
        Args:
            click_button (Button):
            check_button (Button, callable):
            appear_button (Button, callable):
            additional (callable):
            confirm_wait (int, float):
            offset (bool, int, tuple):
            retry_wait (int, float):
            skip_first_screenshot (bool):
        """
        logger.hr('UI click')
        if appear_button is None:
            appear_button = click_button

        click_timer = Timer(retry_wait, count=retry_wait // 0.5)
        confirm_wait = confirm_wait if additional is not None else 0
        confirm_timer = Timer(confirm_wait, count=confirm_wait // 0.5).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if (isinstance(check_button, Button) and self.appear(check_button, offset=offset)) \
                    or (callable(check_button) and check_button()):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

            if click_timer.reached():
                if (isinstance(appear_button, Button) and self.appear(appear_button, offset=offset)) \
                        or (callable(appear_button) and appear_button()):
                    self.device.click(click_button)
                    click_timer.reset()
                    continue

            if additional is not None:
                if additional():
                    continue

    def ui_get_current_page(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Returns:
            Page:
        """
        if not skip_first_screenshot or not hasattr(self.device, 'image') or self.device.image is None:
            self.device.screenshot()

        # Known pages
        for page in self.ui_pages:
            if page.check_button is None:
                continue
            if self.ui_page_appear(page=page):
                logger.attr('UI', page.name)
                self.ui_current = page
                return page

        # Unknown page but able to handle
        logger.info('Unknown ui page')
        if self.appear_then_click(GOTO_MAIN, offset=(20, 20)) or self.ui_additional():
            logger.info('Goto page_main')
            self.ui_current = page_unknown
            self.ui_goto(page_main, skip_first_screenshot=True)

        # Unknown page, need manual switching
        if hasattr(self, 'ui_current'):
            logger.warning(f'Unrecognized ui_current, using previous: {self.ui_current}')
        else:
            logger.info('Unable to goto page_main')
            logger.attr('EMULATOR__SCREENSHOT_METHOD', self.config.Emulator_ScreenshotMethod)
            logger.attr('EMULATOR__CONTROL_METHOD', self.config.Emulator_ControlMethod)
            logger.attr('SERVER', self.config.SERVER)
            logger.warning('Starting from current page is not supported')
            logger.warning(f'Supported page: {[str(page) for page in self.ui_pages]}')
            logger.warning(f'Supported page: Any page with a "HOME" button on the upper-right')
            if not self.device.app_is_running():
                raise GameNotRunningError('Game not running')
            else:
                logger.critical('Please switch to a supported page before starting Alas')
                raise RequestHumanTakeover

    def ui_goto(self, destination, offset=(20, 20), confirm_wait=0, skip_first_screenshot=True):
        """
        Args:
            destination (Page):
            offset:
            confirm_wait:
            skip_first_screenshot:
        """
        # Reset connection
        for page in self.ui_pages:
            page.parent = None

        # Create connection
        visited = [destination]
        visited = set(visited)
        while 1:
            new = visited.copy()
            for page in visited:
                for link in self.ui_pages:
                    if link in visited:
                        continue
                    if page in link.links:
                        link.parent = page
                        new.add(link)
            if len(new) == len(visited):
                break
            visited = new

        logger.hr(f'UI goto {destination}')
        confirm_timer = Timer(confirm_wait, count=int(confirm_wait // 0.5)).start()
        while 1:
            GOTO_MAIN.clear_offset()
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Destination page
            if self.appear(destination.check_button, offset=offset):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

            # Other pages
            for page in visited:
                if page.parent is None or page.check_button is None:
                    continue
                if self.appear(page.check_button, offset=offset, interval=3):
                    self.device.click(page.links[page.parent])
                    confirm_timer.reset()
                    break

            # Additional
            if self.ui_additional():
                continue

        # Reset connection
        for page in self.ui_pages:
            page.parent = None

    def ui_ensure(self, destination, skip_first_screenshot=True):
        """
        Args:
            destination (Page):
            skip_first_screenshot:

        Returns:
            bool: If UI switched.
        """
        logger.hr('UI ensure')
        self.ui_get_current_page(skip_first_screenshot=skip_first_screenshot)
        if self.ui_current == destination:
            logger.info('Already at %s' % destination)
            return False
        else:
            logger.info('Goto %s' % destination)
            self.ui_goto(destination, skip_first_screenshot=True)
            return True

    def ui_goto_main(self):
        return self.ui_ensure(destination=page_main)

    def ui_goto_event(self):
        return self.ui_ensure(destination=page_event)

    def ui_goto_sp(self):
        return self.ui_ensure(destination=page_sp)

    def ui_ensure_index(self, index, letter, next_button, prev_button, skip_first_screenshot=False, fast=True,
                        interval=(0.2, 0.3), step_sleep=(0.2, 0.3), finish_sleep=(0.5, 0.8)):
        """
        Args:
            index (int):
            letter (Ocr, callable): OCR button.
            next_button (Button):
            prev_button (Button):
            skip_first_screenshot (bool):
            fast (bool): Default true. False when index is not continuous.
            interval (tuple, int, float): Seconds between two click.
            step_sleep (tuple, int, float): Seconds between two step.
            finish_sleep (tuple, int, float): Second to wait when arrive.
        """
        logger.hr('UI ensure index')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if isinstance(letter, Ocr):
                current = letter.ocr(self.device.image)
            else:
                current = letter(self.device.image)

            logger.attr('Index', current)
            diff = index - current
            if diff == 0:
                break

            button = next_button if diff > 0 else prev_button
            if fast:
                self.device.multi_click(button, n=abs(diff), interval=interval)
            else:
                self.device.click(button)
            self.device.sleep(step_sleep)

        self.device.sleep(finish_sleep)

    def ui_back(self, check_button, appear_button=None, offset=(20, 20), retry_wait=10, skip_first_screenshot=False):
        return self.ui_click(click_button=BACK_ARROW, check_button=check_button, appear_button=appear_button,
                             offset=offset, retry_wait=retry_wait, skip_first_screenshot=skip_first_screenshot)

    def ui_additional(self):
        """
        Handle all annoying popups during UI switching.
        """
        # Research popup, lost connection popup
        if self.handle_popup_confirm('UI_ADDITIONAL'):
            return True
        if self.handle_urgent_commission():
            return True

        # Guild popup
        if self.handle_guild_popup_cancel():
            return True

        # Daily reset
        if self.appear_then_click(LOGIN_ANNOUNCE, offset=(30, 30), interval=3):
            return True
        if self.appear_then_click(GET_ITEMS_1, offset=(30, 30), interval=3):
            return True
        if self.appear_then_click(GET_SHIP, interval=3):
            return True
        if self.appear_then_click(LOGIN_RETURN_SIGN, offset=(30, 30), interval=3):
            return True
        if self.appear(EVENT_LIST_CHECK, offset=(30, 30), interval=3):
            if self.appear_then_click(GOTO_MAIN, offset=(30, 30)):
                return True

        # Mistaken click
        if self.appear(PLAYER_CHECK, offset=(30, 30), interval=3):
            if self.appear_then_click(GOTO_MAIN, offset=(30, 30)):
                return True

        # Story
        if self.handle_story_skip():
            return True

        # Game tips
        # Event commission in Vacation Lane.
        if self.appear(GAME_TIPS, offset=(30, 30), interval=3):
            if self.appear_then_click(GOTO_MAIN, offset=(30, 30)):
                return True

        # Dorm popup
        if self.appear_then_click(DORM_INFO, offset=(30, 30), interval=3):
            return True
        if self.appear_then_click(DORM_FEED_CANCEL, offset=(30, 30), interval=3):
            return True
        if self.appear_then_click(DORM_TROPHY_CONFIRM, offset=(30, 30), interval=3):
            return True

        # Meowfficer popup
        if self.appear_then_click(MEOWFFICER_INFO, offset=(30, 30), interval=3):
            return True

        # Campaign preparation
        if self.appear(MAP_PREPARATION, offset=(20, 20), interval=3) \
                or self.appear(FLEET_PREPARATION, offset=(20, 20), interval=3):
            self.device.click(MAP_PREPARATION_CANCEL)
            return True
        if self.appear_then_click(AUTO_SEARCH_MENU_EXIT, offset=(200, 20), interval=3):
            return True
        if self.appear_then_click(WITHDRAW, offset=(20, 20), interval=1.5):
            return True

        return False
