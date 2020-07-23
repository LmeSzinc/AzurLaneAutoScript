from datetime import datetime, timedelta

from module.base.timer import Timer
from module.combat.assets import *
from module.handler.login import LoginHandler
from module.logger import logger
from module.reward.assets import *
from module.reward.commission import RewardCommission
from module.reward.tactical_class import RewardTacticalClass
from module.ui.page import *
from module.update import Update
from module.research.research import RewardResearch


class Reward(RewardCommission, RewardTacticalClass, RewardResearch, LoginHandler, Update):
    def reward(self):
        if not self.config.ENABLE_REWARD:
            return False

        logger.hr('Reward start')
        self.ui_goto_main()

        self.ui_goto(page_reward, skip_first_screenshot=True)

        self._reward_receive()
        self.handle_info_bar()
        self.handle_commission_start()
        self.handle_tactical_class()

        self.handle_research_reward()
        self.ui_goto(page_main, skip_first_screenshot=True)
        self._reward_mission()

        self.config.REWARD_LAST_TIME = datetime.now()
        logger.hr('Reward end')

        if self.config.ENABLE_DAILY_REWARD:
            logger.hr('Daily reward')
            count = self.daily_wrapper_run()
            if count > 0:
                return self.reward()

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
        logger.hr('Reward receive')

        reward = False
        exit_timer = Timer(1, count=3).start()
        click_timer = Timer(1)
        while 1:
            self.device.screenshot()

            for button in [EXP_INFO_S_REWARD, GET_ITEMS_1, GET_ITEMS_2, GET_ITEMS_3, GET_SHIP]:
                if self.appear(button, interval=1):
                    REWARD_SAVE_CLICK.name = button.name
                    self.device.click(REWARD_SAVE_CLICK)
                    click_timer.reset()
                    exit_timer.reset()
                    reward = True
                    continue

            if click_timer.reached() and (
                    (self.config.ENABLE_OIL_REWARD and self.appear_then_click(OIL, interval=60))
                    or (self.config.ENABLE_COIN_REWARD and self.appear_then_click(COIN, interval=60))
                    or (self.config.ENABLE_COMMISSION_REWARD and self.appear_then_click(REWARD_1, interval=1))
                    or (self.config.ENABLE_RESEARCH_REWARD and not self.config.ENABLE_SAVE_GET_ITEMS and self.appear_then_click(REWARD_3, interval=1))
            ):
                exit_timer.reset()
                click_timer.reset()
                reward = True
                continue

            if not self.appear(page_reward.check_button) or self.info_bar_count():
                exit_timer.reset()
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
        if not self.config.ENABLE_MISSION_REWARD:
            return False

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
                    timeout.reset()
                    reward = True
                    continue

            for button in [MISSION_MULTI, MISSION_SINGLE]:
                if not click_timer.reached():
                    continue
                if self.appear_then_click(button, interval=1):
                    exit_timer.reset()
                    click_timer.reset()
                    timeout.reset()
                    continue

            if not self.appear(MISSION_CHECK):
                if self.appear_then_click(GET_SHIP, interval=1):
                    click_timer.reset()
                    exit_timer.reset()
                    timeout.reset()
                    continue

            if self.story_skip():
                click_timer.reset()
                exit_timer.reset()
                timeout.reset()
                continue

            # End
            if reward and exit_timer.reached():
                break
            if timeout.reached():
                logger.warning('Wait get items timeout.')
                break

        self.ui_goto(page_main, skip_first_screenshot=True)
        return reward

    def reward_loop(self):
        logger.hr('Reward loop')
        while 1:
            if self.config.triggered_app_restart():
                self.app_restart()

            self.reward()

            logger.info('Reward loop wait')
            logger.attr('Reward_loop_wait', f'{self.config.REWARD_INTERVAL} min')
            self.device.sleep(self.config.REWARD_INTERVAL * 60)

    def daily_wrapper_run(self):
        count = 0
        total = 5
        if self.config.ENABLE_DAILY_MISSION:
            from module.daily.daily import Daily
            az = Daily(self.config, device=self.device)
            if not az.record_executed_since():
                az.run()
                az.record_save()
                count += 1

        if self.config.ENABLE_HARD_CAMPAIGN:
            from module.hard.hard import CampaignHard
            az = CampaignHard(self.config, device=self.device)
            if not az.record_executed_since():
                az.run()
                az.record_save()
                count += 1

        if self.config.ENABLE_EXERCISE:
            from module.exercise.exercise import Exercise
            az = Exercise(self.config, device=self.device)
            if not az.record_executed_since():
                az.run()
                az.record_save()
                count += 1

        if self.config.ENABLE_EVENT_AB:
            from module.event.campaign_ab import CampaignAB
            az = CampaignAB(self.config, device=self.device)
            if az.run_event_daily():
                count += 1

        if self.config.ENABLE_RAID_DAILY:
            from module.raid.daily import RaidDaily
            az = RaidDaily(self.config, device=self.device)
            if not az.record_executed_since():
                az.run()
                az.record_save()
                count += 1

        logger.attr('Daily_executed', f'{count}/{total}')
        return count

    _enable_daily_reward = False

    def reward_backup_daily_reward_settings(self):
        """
        Method to avoid event_daily_ab calls reward, and reward calls event_daily_ab itself again.
        """
        self._enable_daily_reward = self.config.ENABLE_DAILY_REWARD
        self.config.ENABLE_DAILY_REWARD = False

    def reward_recover_daily_reward_settings(self):
        self.config.ENABLE_DAILY_REWARD = self._enable_daily_reward
