from module.base.timer import Timer
from module.exception import GameStuckError
from module.handler.assets import STORY_SKIP
from module.island.ui import IslandUI
from module.island.assets import *
from module.logger import logger
from module.ui.page import page_island, page_island_manage, page_island_phone


class IslandFreebie(IslandUI):
    def island_freebie_notice_appear(self):
        """
        Returns:
            bool: If appear.

        Page:
            in: page_island_manage
        """
        for _ in self.loop(timeout=5):
            if self.match_template_color(ISLAND_FREEBIE_AVAILABLE, offset=(20, 20)):
                return True
            if self.match_template_color(ISLAND_FREEBIE_UNAVAILABLE, offset=(20, 20)):
                return False
        return False

    def freebie_move_to(self):
        """
        Page:
            in: page_island_manage
            out: page_island
        """
        for _ in self.loop(timeout=30):
            if self.appear_then_click(ISLAND_FREEBIE_AVAILABLE, offset=(20, 20), interval=3):
                continue

            if self.ui_page_appear(page_island_phone):
                logger.info('Moved to location of freebie')
                self.ui_goto(page_island)
                break
        else:
            logger.warning('Failed to move to location of freebie after 30 seconds')
            raise GameStuckError(f'Failed to move to location of freebie after 30 seconds')

    def freebie_claim(self):
        if not self.appear(ISLAND_FREEBIE_CLAIM, offset=(20, 20)):
            logger.warning('No freebie claim button')
            return False
        retry_wait = Timer(3, count=5).reset()
        for _ in self.loop(timeout=30):
            if self.appear_then_click(ISLAND_FREEBIE_CLAIM, offset=(20, 20), interval=3):
                continue

            if self.appear(ISLAND_FREEBIE_COOLDOWN, offset=(20, 20)):
                logger.info('Claimed freebie')
                break
            elif self.ui_page_appear(page_island_phone):
                logger.info('Misclicked into page_island_phone, go back')
                self.ui_goto(page_island)
                continue
            elif retry_wait.reached_and_reset():
                self.device.click(STORY_SKIP)
                continue

    def freebie_receive(self):
        p1 = (217, 507)
        p2 = (217 - 8, 507 + 36)
        self.device.drag(p1, p2, point_random=(0, 0, 0, 0), shake_random=(0, 0, 0, 0), hold_duration=1.05)
        self.device.screenshot()
        if not self.appear(ISLAND_FREEBIE_RECEIVE, offset=(20, 20)):
            logger.warning('Failed to receive freebie')
            return False
        confirm_timer = Timer(3, count=5).reset()
        for _ in self.loop(skip_first=False):
            if self.appear_then_click(ISLAND_FREEBIE_RECEIVE, offset=(20, 20), interval=3):
                confirm_timer.reset()
                continue

            if self.handle_island_additional():
                confirm_timer.reset()
                continue

            # End
            if self.appear(ISLAND_FREEBIE_SHARE, offset=(20, 20)):
                if confirm_timer.reached():
                    logger.info('Received freebie')
                    return True

    def freebie_share(self):
        if not self.appear(ISLAND_FREEBIE_SHARE, offset=(20, 20)):
            logger.warning('No freebie share button')
            return False

        for _ in self.loop(skip_first=False):
            if self.appear_then_click(ISLAND_FREEBIE_SHARE, offset=(20, 20), interval=3):
                continue
            if self.appear_then_click(ISLAND_FREEBIE_SHARE_ALL, offset=(20, 20), interval=3):
                break

        for _ in self.loop(skip_first=False):
            if self.appear_then_click(ISLAND_FREEBIE_SHARE_BACK, offset=(20, 20), interval=3):
                continue
            if self.ui_page_appear(page_island):
                logger.info('Shared freebie')
                return True

    def run(self):
        self.ui_ensure(page_island_manage)

        if self.island_freebie_notice_appear():
            self.freebie_move_to()
            self.freebie_claim()
            self.freebie_receive()
            if self.config.IslandFreebie_Share:
                self.freebie_share()
        else:
            logger.info('No freebie notice')

        self.config.task_delay(server_update=True)
        