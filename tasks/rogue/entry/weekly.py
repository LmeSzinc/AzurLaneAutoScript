from module.base.timer import Timer
from module.logger import logger
from tasks.rogue.assets.assets_rogue_weekly import CLAIM_ALL, REWARD_CHECK, REWARD_CLOSE, REWARD_ENTER, REWARD_RED_DOT
from tasks.rogue.bleesing.ui import RogueUI


class RogueRewardHandler(RogueUI):
    def _rogue_reward_appear(self) -> bool:
        """
        Pages:
            in: is_page_rogue_main()
        """
        if self.image_color_count(REWARD_RED_DOT, color=(214, 45, 47), threshold=221, count=50):
            return True

        return False

    def _rogue_reward_enter(self, skip_first_screenshot=True):
        """
        Pages:
            in: is_page_rogue_main()
            out: REWARD_CHECK
        """
        logger.info('Rogue reward enter')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(REWARD_CHECK):
                break

            if self.appear_then_click(REWARD_ENTER, interval=2):
                continue

    def _rogue_reward_exit(self, skip_first_screenshot=True):
        """
        Pages:
            in: REWARD_CHECK
            out: is_page_rogue_main()
        """
        logger.info('Rogue reward exit')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_page_rogue_main():
                break

            if self.appear_then_click(REWARD_CLOSE, interval=2):
                continue
            if self.handle_reward():
                continue

    def _rogue_reward_claim(self, skip_first_screenshot=True):
        """
        Pages:
            in: REWARD_CHECK, CLAIM_ALL
            out: REWARD_CHECK
        """
        logger.info('Rogue reward claim')
        claimed = False
        appear = False
        click_count = 0
        timeout = Timer(2, count=10).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if claimed:
                if self.appear(REWARD_CHECK):
                    return True
                if self.is_page_rogue_main():
                    return True
            if not appear and timeout.reached():
                logger.warning('Rogue reward claim timeout, CLAIM_ALL not found')
                return False
            if click_count > 3:
                logger.warning('Failed to claim weekly rewards, probably because immersifier is full')
                return False

            if self.handle_reward():
                claimed = True
                continue
            if self.interval_is_reached(CLAIM_ALL, interval=1):
                if self.image_color_count(CLAIM_ALL, color=(255, 199, 89), threshold=221, count=500):
                    self.device.click(CLAIM_ALL)
                    self.interval_reset(CLAIM_ALL, interval=1)
                    appear = True
                    click_count += 1
                    continue

    def rogue_reward_claim(self):
        """
        Claim possible rogue rewards.

        Returns:
            bool: If claimed.

        Pages:
            in: is_page_rogue_main()
            out: is_page_rogue_main()
        """
        logger.hr('Rogue reward claim', level=2)
        if self._rogue_reward_appear():
            self._rogue_reward_enter()
            success = self._rogue_reward_claim()
            self._rogue_reward_exit()
            return success
        else:
            logger.info('No rogue reward')
            return False
