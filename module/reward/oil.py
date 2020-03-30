from module.ui.ui import UI, page_reward, page_main
from module.reward.assets import *
from module.base.timer import Timer
from module.logger import logger


class RewardOil(UI):
    def reward_oil(self):
        """
        Returns:
            bool: If rewarded.
        """
        logger.hr('Oil Reward')
        self.ui_ensure(page_reward)

        reward = False
        click_timer = Timer(1)
        click_timer.start()
        while 1:
            self.device.screenshot()
            if self.appear_then_click(OIL, interval=1):
                click_timer.reset()
                reward = True
                continue
            if self.appear_then_click(COIN, interval=1):
                click_timer.reset()
                reward = True
                continue

            # End
            if click_timer.reached():
                break

        self.ui_current = page_reward
        self.ui_goto(page_main)
        return reward
