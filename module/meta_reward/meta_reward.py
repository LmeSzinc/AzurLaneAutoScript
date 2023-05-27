from module.base.timer import Timer
from module.combat.combat import Combat
from module.logger import logger
from module.meta_reward.assets import *
from module.ui.page import page_meta
from module.ui.ui import UI


class MetaReward(Combat, UI):
    def meta_reward_notice_appear(self):
        """
        Returns:
            bool: If appear.

        Page:
            in: page_meta
        """
        if self.appear(META_REWARD_NOTICE, threshold=30):
            logger.info('Found meta reward red dot')
            return True
        else:
            logger.info('No meta reward red dot')
            return False

    def meta_reward_enter(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_meta
            out: REWARD_CHECK
        """
        logger.info('Meta reward enter')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(REWARD_ENTER, offset=(20, 20), interval=3):
                continue

            # End
            if self.appear(REWARD_CHECK, offset=(20, 20)):
                break

    def meta_reward_receive(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Returns:
            bool: If received.

        Pages:
            in: REWARD_CHECK
            out: REWARD_CHECK
        """
        logger.hr('Meta reward receive', level=1)
        confirm_timer = Timer(1, count=3).start()
        received = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(REWARD_RECEIVE, offset=(20, 20), interval=3) and REWARD_RECEIVE.match_appear_on(
                    self.device.image):
                self.device.click(REWARD_RECEIVE)
                confirm_timer.reset()
                continue
            if self.handle_popup_confirm('META_REWARD'):
                # Lock new META ships
                confirm_timer.reset()
                continue
            if self.handle_get_items():
                received = True
                confirm_timer.reset()
                continue
            if self.handle_get_ship():
                received = True
                confirm_timer.reset()
                continue

            # End
            if self.appear(REWARD_CHECK, offset=(20, 20)) and \
               self.image_color_count(REWARD_RECEIVE, color=(49, 52, 49), threshold=221, count=400):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

        logger.info(f'Meta reward receive finished, received={received}')
        return received

    def run(self):
        if self.config.SERVER in ['cn', 'en', 'jp']:
            pass
        else:
            logger.info(f'MetaReward is not supported in {self.config.SERVER}, please contact server maintainers')
            return

        self.ui_ensure(page_meta)

        if self.meta_reward_notice_appear():
            self.meta_reward_enter()
            self.meta_reward_receive()
