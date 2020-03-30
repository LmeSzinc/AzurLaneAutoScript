from module.ui.ui import page_mission
from module.reward.assets import *
from module.combat.combat import Combat
from module.base.timer import Timer
from module.logger import logger


class RewardMission(Combat):
    def reward_mission(self):
        """
        Returns:
            bool: If rewarded.
        """
        logger.hr('Mission reward')
        if not self.appear(MISSION_NOTISE):
            logger.info('No mission reward')
            return False

        self.ui_ensure(page_mission)

        reward = False
        click_timer = Timer(1)
        click_timer.start()
        while 1:
            self.device.screenshot()

            if self.handle_get_items(save_get_items=False):
                click_timer.reset()
                continue
            if self.handle_get_ship():
                click_timer.reset()
                continue
            if self.appear_then_click(MISSION_MULTI, interval=1):
                click_timer.reset()
                reward = True
                continue
            if self.appear_then_click(MISSION_SINGAL, interval=1):
                click_timer.reset()
                reward = True
                continue

            # End
            if click_timer.reached():
                break

        self.ui_goto_main()
        return reward
