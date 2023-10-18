from module.base.timer import Timer
from module.logger import logger
from tasks.base.assets.assets_base_page import MENU_CHECK
from tasks.base.assets.assets_base_popup import GET_REWARD
from tasks.base.page import page_menu
from tasks.base.ui import UI
from tasks.freebies.assets.assets_freebies_support_reward import (
    CAN_GET_REWARD,
    IN_PROFILE,
    MENU_TO_PROFILE,
    PROFILE
)


class SupportReward(UI):

    def run(self):
        """
        Run get support reward task
        """
        logger.hr('Support reward', level=1)
        self.ui_ensure(page_menu)

        self._goto_profile()
        self._get_reward()
        self._goto_menu()

    def _goto_profile(self):
        """
        Pages:
            in: MENU
            out: PROFILE
        """
        skip_first_screenshot = False
        logger.info('Going to profile')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(IN_PROFILE):
                logger.info('Successfully in profile')
                return True

            if self.appear_then_click(MENU_TO_PROFILE):
                continue

            if self.appear_then_click(PROFILE):
                continue

    def _get_reward(self, skip_first_screenshot=True):
        """
        Pages:
            in: PROFILE
            out: GET_REWARD
        """
        logger.info('Getting reward')
        claimed = False
        empty = Timer(0.3, count=1).start()
        timeout = Timer(5).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if not claimed and empty.reached():
                logger.info('No reward')
                break
            if self.appear(GET_REWARD):
                logger.info('Got reward')
                break
            if timeout.reached():
                logger.warning('Get support reward timeout')
                break

            if self.appear_then_click(CAN_GET_REWARD, similarity=0.70, interval=2):
                claimed = True
                timeout.reset()
                continue

    def _goto_menu(self):
        """
        Pages:
            in: PROFILE or GET_REWARD
            out: MENU
        """
        skip_first_screenshot = False
        logger.info('Going to menu')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(MENU_CHECK):
                return True

            if self.handle_ui_close(IN_PROFILE, interval=2):
                continue
            if self.handle_reward(click_button=CAN_GET_REWARD):
                # # Avoid clicking on some other buttons
                continue


if __name__ == '__main__':
    self = SupportReward('src')
    self.device.screenshot()
    self.run()
