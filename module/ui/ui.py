from module.base.button import Button
from module.base.timer import Timer
from module.combat.assets import *
from module.exception import GameNotRunningError
from module.handler.assets import *
from module.handler.info_handler import InfoHandler
from module.logger import logger
from module.ocr.ocr import Ocr
from module.reward.assets import COMMISSION_DAILY
from module.ui.page import *


class UI(InfoHandler):
    # Pages that Alas supported.
    ui_pages = [page_main, page_campaign_menu, page_campaign, page_fleet,
                page_exercise, page_daily, page_event, page_sp, page_mission,
                page_raid, page_reward, page_reshmenu, page_research, page_shipyard, page_dormmenu, page_dorm, page_meowfficer,
                page_archives, page_guild, page_os, page_academy, page_shop, page_munitions, page_build]
    # All pages defined.
    ui_pages_all = [page_main, page_campaign_menu, page_campaign, page_fleet,
                    page_exercise, page_daily, page_event, page_sp, page_mission,
                    page_raid, page_commission, page_event_list, page_tactical, page_reward, page_unknown,
                    page_reshmenu, page_research, page_shipyard, page_dormmenu, page_dorm, page_meowfficer, page_archives,
                    page_guild, page_os, page_academy, page_shop, page_munitions, page_build]
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

    def ui_get_current_page(self):
        self.device.screenshot()
        for page in self.ui_pages:
            if self.ui_page_appear(page=page):
                logger.attr('UI', page.name)
                self.ui_current = page
                return page

        logger.info('Unknown ui page')
        if self.appear_then_click(GOTO_MAIN, offset=(20, 20)):
            logger.info('Goto page_main')
            self.ui_current = page_unknown
            self.ui_goto(page_main, skip_first_screenshot=True)

        if hasattr(self, 'ui_current'):
            logger.warning(f'Unrecognized ui_current, using previous: {self.ui_current}')
        else:
            logger.info('Unable to goto page_main')
            logger.attr('DEVICE_SCREENSHOT_METHOD', self.config.DEVICE_SCREENSHOT_METHOD)
            logger.attr('DEVICE_CONTROL_METHOD', self.config.DEVICE_CONTROL_METHOD)
            logger.attr('SERVER', self.config.SERVER)
            logger.warning('Starting from current page is not supported')
            logger.warning(f'Supported page: {[str(page) for page in self.ui_pages]}')
            logger.warning(f'Supported page: Any page with a "HOME" button on the upper-right')
            if not self.device.app_is_running():
                raise GameNotRunningError('Game not running')
            else:
                exit(1)

    def ui_goto(self, destination, skip_first_screenshot=False):
        """
        Args:
            destination (Page):
            skip_first_screenshot (bool):
        """
        for page in self.ui_pages_all:
            page.parent = None
        # Iter
        visited = [self.ui_current]
        visited = set(visited)
        while 1:
            new = visited.copy()
            for page in visited:
                for link in page.links.keys():
                    if link in visited:
                        continue
                    link.parent = page
                    new.add(link)
            if len(new) == len(visited):
                break
            visited = new

        # Find path
        if destination.parent is None:
            return []
        route = [destination]
        while 1:
            destination = destination.parent
            if destination is not None:
                route.append(destination)
            else:
                break
            if len(route) > 30:
                logger.warning('UI route too long')
                logger.warning(str(route))
                exit(1)

        route.reverse()
        if len(route) < 2:
            logger.warning('No page route found.')
        logger.attr('UI route', ' - '.join([p.name for p in route]))

        # Click
        for p1, p2 in zip(route[:-1], route[1:]):
            additional = f'ui_additional_{str(p2)}'
            self.ui_click(
                click_button=p1.links[p2],
                check_button=p2.check_button,
                additional=self.__getattribute__(additional) if hasattr(self, additional) else None,
                offset=(20, 20),
                skip_first_screenshot=skip_first_screenshot)
            self.ui_current = p2
            skip_first_screenshot = True

        # Reset
        for page in visited:
            page.parent = None

    def ui_ensure(self, destination):
        """
        Args:
            destination (Page):
        """
        logger.hr('UI ensure')
        self.ui_get_current_page()
        if self.ui_current == destination:
            logger.info('Already at %s' % destination)
            return False
        else:
            logger.info('Goto %s' % destination)
            self.ui_goto(destination)
            return True

    def ui_goto_main(self):
        return self.ui_ensure(destination=page_main)

    def handle_stage_icon_spawn(self):
        self.device.sleep((1, 1.2))
        self.device.screenshot()

    def ui_weigh_anchor(self):
        if self.ui_ensure(destination=page_campaign):
            self.handle_stage_icon_spawn()
            return True
        else:
            return False

    def ui_goto_event(self):
        if self.ui_ensure(destination=page_event):
            self.handle_stage_icon_spawn()
            return True
        else:
            return False

    def ui_goto_sp(self):
        if self.ui_ensure(destination=page_sp):
            self.handle_stage_icon_spawn()
            return True
        else:
            return False

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

    def ui_additional_page_main(self):
        # Research popup, lost connection popup
        if self.handle_popup_confirm('PAGE_MAIN'):
            return True
        # Guild popup
        if self.handle_guild_popup_cancel():
            return True

        # Daily reset
        if self.appear_then_click(LOGIN_ANNOUNCE, offset=(30, 30), interval=5):
            return True
        if self.appear_then_click(GET_ITEMS_1, offset=(30, 30), interval=5):
            return True
        if self.appear_then_click(GET_SHIP, interval=5):
            return True
        if self.appear_then_click(LOGIN_RETURN_SIGN, offset=(30, 30), interval=5):
            return True
        if self.appear_then_click(GOTO_MAIN, offset=(30, 30), interval=5):
            return True

        return False

    _ui_additional_reward_goto_main_timer = Timer(5, count=5)

    def ui_additional_page_reward(self):
        # Research popup, lost connection popup
        if self.handle_popup_confirm('PAGE_REWARD'):
            return True
        # Guild popup
        if self.handle_guild_popup_cancel():
            return True

        # Daily reset
        if self.appear_then_click(LOGIN_ANNOUNCE, offset=(30, 30), interval=5):
            return True
        if self.appear_then_click(GET_ITEMS_1, offset=(30, 30), interval=5):
            return True
        if self.appear_then_click(GET_SHIP, interval=5):
            return True
        if self.appear_then_click(LOGIN_RETURN_SIGN, offset=(30, 30), interval=5):
            return True
        if self.appear(EVENT_LIST_CHECK, offset=(30, 30), interval=5) \
                or self.appear(RESHMENU_CHECK, offset=(30, 30), interval=5) \
                or self.appear(RESEARCH_CHECK, offset=(30, 30), interval=5) \
                or self.appear(SHIPYARD_CHECK, offset=(30, 30), interval=5):
            self.device.click(GOTO_MAIN)
            self._ui_additional_reward_goto_main_timer.reset()
            return True
        if not self._ui_additional_reward_goto_main_timer.reached():
            if self.appear(MAIN_CHECK, offset=(30, 30), interval=5):
                self.device.click(MAIN_GOTO_REWARD)
                return True

        return False

    def ui_additional_page_dorm(self):
        if self.appear_then_click(DORM_INFO, offset=(30, 30), interval=5):
            return True
        if self.appear_then_click(DORM_FEED_CANCEL, offset=(30, 30), interval=5):
            return True
        if self.appear_then_click(DORM_TROPHY_CONFIRM, offset=(30, 30), interval=5):
            return True

        return False

    def ui_additional_page_meowfficer(self):
        if self.appear_then_click(MEOWFFICER_INFO, offset=(30, 30), interval=5):
            return True

        return False

    def ui_additional_page_commission(self):
        # Event commission in Vacation Lane.
        if self.appear(GAME_TIPS, offset=(20, 20), interval=1):
            self.device.click(COMMISSION_DAILY)
            return True

        return False
