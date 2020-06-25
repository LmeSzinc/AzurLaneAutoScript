from module.base.base import ModuleBase
from module.base.button import Button
from module.base.ocr import Ocr
from module.base.timer import Timer
from module.logger import logger
from module.ui.page import *


class UI(ModuleBase):
    ui_pages = [page_main, page_campaign, page_fleet, page_exercise, page_daily, page_event, page_sp, page_mission,
                page_raid]
    ui_current: Page

    def ui_page_appear(self, page):
        """
        Args:
            page (Page):
        """
        return self.appear(page.check_button, offset=(20, 20))

    def ui_click(self, click_button, check_button, appear_button=None, additional_button=None,
                 offset=(20, 20), retry_wait=10, additional_button_interval=3, skip_first_screenshot=False):
        """
        Args:
            click_button (Button):
            check_button (Button, callable):
            appear_button (Button):
            additional_button (Button, list[Button], callable):
            additional_button_interval (int, float):
            offset (bool, int, tuple):
            retry_wait (int, float):
            skip_first_screenshot (bool):
        """
        logger.hr('UI click')
        if appear_button is None:
            appear_button = click_button
        if not isinstance(additional_button, list):
            additional_button = [additional_button]
        click_timer = Timer(retry_wait, count=retry_wait // 0.5)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if isinstance(check_button, Button) and self.appear(check_button, offset=offset):
                break
            if callable(check_button) and check_button():
                break

            for button in additional_button:
                if button is None:
                    continue
                if isinstance(button, Button):
                    self.appear_then_click(button, offset=offset, interval=additional_button_interval)
                    continue
                if callable(button) and button():
                    continue

            if click_timer.reached() and self.appear(appear_button, offset=offset):
                self.device.click(click_button)
                click_timer.reset()
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
            self.wait_until_appear(MAIN_CHECK)
            self.ui_current = page_main
            return page_main

        if hasattr(self, 'ui_current'):
            logger.warning(f'Unrecognized ui_current, using previous: {self.ui_current}')
        else:
            logger.info('Unable to goto page_main')
            logger.warning('Starting from current page is not supported')
            logger.warning(f'Supported page: {[str(page) for page in self.ui_pages]}')
            logger.warning(f'Supported page: Any page with a "HOME" button on the upper-right')
            exit(1)

    def ui_goto(self, destination, skip_first_screenshot=False):
        """
        Args:
            destination (Page):
            skip_first_screenshot (bool):
        """
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
        route.reverse()
        if len(route) < 2:
            logger.warning('No page route found.')
        logger.attr('UI route', ' - '.join([p.name for p in route]))

        # Click
        for p1, p2 in zip(route[:-1], route[1:]):
            # self.ui_click(source=p1, destination=p2)
            self.ui_click(
                click_button=p1.links[p2],
                check_button=p2.check_button,
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
