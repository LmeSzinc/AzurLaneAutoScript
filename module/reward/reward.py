from datetime import datetime, timedelta

from module.base.timer import Timer
from module.combat.assets import *
from module.logger import logger
from module.reward.assets import *
from module.ui.page import *
from module.reward.commission import RewardCommission


class Reward(RewardCommission):
    def reward(self):
        if not self.config.ENABLE_REWARD:
            return False

        logger.hr('Reward start')
        self.ui_goto_main()

        self.ui_goto(page_reward, skip_first_screenshot=True)

        self._reward_receive()
        self.handle_info_bar()
        self.handle_commission_start()

        self.ui_click(
            click_button=page_reward.links[page_main],
            check_button=page_main.check_button,
            appear_button=page_reward.check_button,
            skip_first_screenshot=True)

        self._reward_mission()

        self.config.REWARD_LAST_TIME = datetime.now()
        logger.hr('Reward end')
        return True

    def handle_reward(self):
        if datetime.now() - self.config.REWARD_LAST_TIME < timedelta(minutes=self.config.REWARD_INTERVAL):
            return False

        flag = self.reward()

        return flag

    def _reward_receive(self):
        """
        Returns:
            bool: If rewarded.
        """
        logger.hr('Oil Reward')

        reward = False
        exit_timer = Timer(1)
        click_timer = Timer(1)
        exit_timer.start()
        btn = []
        if self.config.ENABLE_REWARD:
            btn.append(REWARD_3)
        if self.config.ENABLE_COMMISSION_REWARD:
            btn.append(REWARD_1)
        if self.config.ENABLE_OIL_REWARD:
            btn.append(OIL)
        if self.config.ENABLE_COIN_REWARD:
            btn.append(COIN)

        while 1:
            self.device.screenshot()

            for button in [EXP_INFO_S_REWARD, GET_ITEMS_1, GET_ITEMS_2, GET_SHIP]:
                if self.appear(button, interval=1):
                    self.device.click(REWARD_SAVE_CLICK)
                    click_timer.reset()
                    exit_timer.reset()
                    reward = True
                    continue

            for button in btn:
                if not click_timer.reached():
                    continue
                if self.appear_then_click(button, interval=1):
                    btn.remove(button)
                    exit_timer.reset()
                    click_timer.reset()
                    reward = True
                    continue

            # End
            if exit_timer.reached():
                break

        return reward

    def _reward_mission(self):
        """
        Returns:
            bool: If rewarded.
        """
        logger.hr('Mission reward')
        if not self.appear(MISSION_NOTICE):
            logger.info('No mission reward')
            return False

        self.ui_goto(page_mission, skip_first_screenshot=True)

        reward = False
        exit_timer = Timer(2)
        click_timer = Timer(1)
        timeout = Timer(10)
        exit_timer.start()
        timeout.start()
        while 1:
            self.device.screenshot()

            for button in [GET_ITEMS_1, GET_ITEMS_2]:
                if self.appear_then_click(button, offset=(30, 30), interval=1):
                    exit_timer.reset()
                    reward = True
                    continue

            for button in [MISSION_MULTI, MISSION_SINGLE]:
                if not click_timer.reached():
                    continue
                if self.appear_then_click(button, interval=1):
                    exit_timer.reset()
                    click_timer.reset()
                    continue

            if not self.appear(MISSION_CHECK):
                if self.appear_then_click(GET_SHIP, interval=1):
                    click_timer.reset()
                    exit_timer.reset()
                    continue

            # End
            if reward and exit_timer.reached():
                break
            if timeout.reached():
                logger.warning('Wait get items timeout.')
                break

        self.ui_goto(page_main, skip_first_screenshot=True)
        return reward
