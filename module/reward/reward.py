from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.combat.assets import *
from module.logger import logger
from module.reward.assets import *
from module.ui.assets import MISSION_CHECK
from module.ui.navbar import Navbar
from module.ui.page import page_main, page_mission, page_reward
from module.ui.ui import UI
from module.ui_white.assets import MISSION_NOTICE_WHITE


class Reward(UI):
    def reward_receive(self, oil, coin, exp, skip_first_screenshot=True):
        """
        Args:
            oil (bool):
            coin (bool):
            exp (bool):
            skip_first_screenshot (bool):

        Returns:
            bool: If rewarded.

        Pages:
            in: page_reward
            out: page_reward, with info_bar if received
        """
        if not oil and not coin and not exp:
            return False

        logger.hr('Reward receive')
        logger.info(f'oil={oil}, coin={coin}, exp={exp}')
        confirm_timer = Timer(1, count=3).start()
        # Set click interval to 0.3, because game can't respond that fast.
        click_timer = Timer(0.3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if oil and click_timer.reached() and self.appear_then_click(OIL, offset=(20, 50), interval=60):
                confirm_timer.reset()
                click_timer.reset()
                continue
            if coin and click_timer.reached() and self.appear_then_click(COIN, offset=(25, 50), interval=60):
                confirm_timer.reset()
                click_timer.reset()
                continue
            if exp and click_timer.reached() and self.appear_then_click(EXP, offset=(30, 50), interval=60):
                confirm_timer.reset()
                click_timer.reset()
                continue

            # End
            if confirm_timer.reached():
                break

        logger.info('Reward receive end')
        return True

    def _reward_mission_collect(self, interval=1, skip_first_screenshot=True):
        """
        Streamline handling of mission rewards for
        both 'all' and 'weekly' pages

        Args:
            interval (int, float):
                Configure the interval for assets involved
            skip_first_screenshot:

        Returns:
            bool, if encountered at least 1 GET_ITEMS_*
        """
        # Reset any existing interval for the following assets
        self.interval_clear([GET_ITEMS_1, GET_ITEMS_2,
                             MISSION_MULTI, MISSION_SINGLE,
                             GET_SHIP])

        # Basic timers for certain scenarios
        exit_timer = Timer(2)
        click_timer = Timer(1)
        timeout = Timer(10)
        exit_timer.start()
        timeout.start()

        reward = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            for button in [GET_ITEMS_1, GET_ITEMS_2]:
                if self.appear_then_click(button, offset=(30, 30), interval=interval):
                    exit_timer.reset()
                    timeout.reset()
                    reward = True
                    continue

            for button in [MISSION_MULTI, MISSION_SINGLE]:
                if not click_timer.reached():
                    continue
                if self.match_template_color(button, offset=(20, 200), interval=interval):
                    self.device.click(button)
                    exit_timer.reset()
                    click_timer.reset()
                    timeout.reset()
                    continue

            if not self.appear(MISSION_CHECK):
                if self.appear_then_click(GET_SHIP, interval=interval):
                    exit_timer.reset()
                    click_timer.reset()
                    timeout.reset()
                    continue

            if self.handle_mission_popup_ack():
                exit_timer.reset()
                click_timer.reset()
                timeout.reset()
                continue

            # Story
            if self.handle_vote_popup():
                exit_timer.reset()
                click_timer.reset()
                timeout.reset()
                continue
            if self.story_skip():
                exit_timer.reset()
                click_timer.reset()
                timeout.reset()
                continue

            if self.handle_popup_confirm('MISSION_REWARD'):
                exit_timer.reset()
                click_timer.reset()
                timeout.reset()
                continue

            # End
            if reward and exit_timer.reached():
                break
            if timeout.reached():
                logger.warning('Wait get items timeout.')
                break

        return reward

    def _reward_mission_all(self):
        """
        Collects all page mission rewards

        Returns:
            bool, if handled
        """
        self.reward_side_navbar_ensure(upper=1)

        if not self.appear(MISSION_MULTI, offset=(20, 200)) and \
                not self.appear(MISSION_SINGLE, offset=(20, 200)):
            logger.info('No MISSION_MULTI or MISSION_SINGLE')
            return False

        # Uses default interval to account for
        # behavior differences and avoid
        # premature exit
        return self._reward_mission_collect()

    def _reward_mission_weekly(self):
        """
        Collects weekly page mission rewards

        Returns:
            bool, if handled
        """
        if not self.image_color_count(MISSION_WEEKLY_RED_DOT, color=(206, 81, 66), threshold=221, count=20):
            logger.info('No MISSION_WEEKLY_RED_DOT')
            return False

        self.reward_side_navbar_ensure(upper=5)

        # Uses no interval to account for
        # behavior differences and avoid
        # premature exit
        return self._reward_mission_collect(interval=0.2)

    def reward_mission_notice(self):
        """
        Returns:
            bool: If notice appear

        Pages:
            in: page_main
        """
        if self.appear(MISSION_NOTICE):
            logger.info('Found mission notice MISSION_NOTICE')
            return True
        if self.image_color_count(MISSION_NOTICE_WHITE, color=(214, 117, 99), threshold=221, count=20):
            logger.info('Found mission notice MISSION_NOTICE_WHITE')
            return True

        return False

    def reward_mission(self, daily=True, weekly=True):
        """
        Collects mission rewards

        Args:
            daily (bool): If collect daily rewards
            weekly (bool): If collect weekly rewards

        Returns:
            bool: If rewarded.

        Pages:
            in: page_main
            out: page_mission
        """
        if not daily and not weekly:
            return False
        logger.hr('Mission reward')
        if not self.reward_mission_notice():
            return False

        self.ui_goto(page_mission, skip_first_screenshot=True)

        reward = False
        if daily:
            reward |= self._reward_mission_all()
        if weekly:
            reward |= self._reward_mission_weekly()

        return reward

    @cached_property
    def _reward_side_navbar(self):
        """
        side_navbar options:
           all.
           main.
           side.
           daily.
           weekly.
           event.
        """
        reward_side_navbar = ButtonGrid(
            origin=(21, 118), delta=(0, 94.5),
            button_shape=(60, 75), grid_shape=(1, 6),
            name='REWARD_SIDE_NAVBAR')

        return Navbar(grids=reward_side_navbar,
                      active_color=(247, 255, 173),
                      inactive_color=(140, 162, 181))

    def reward_side_navbar_ensure(self, upper=None, bottom=None):
        """
        Ensure able to transition to page
        Whether page has completely loaded is handled
        separately and optionally

        Args:
            upper (int):
                1  for all.
                2  for main.
                3  for side.
                4  for daily.
                5  for weekly.
                6  for event.
            bottom (int):
                6  for all.
                5  for main.
                4  for side.
                3  for daily.
                2  for weekly.
                1  for event.

        Returns:
            bool: if side_navbar set ensured
        """
        if self._reward_side_navbar.set(self, upper=upper, bottom=bottom):
            return True
        return False

    def run(self):
        """
        Pages:
            in: Any page
            out: page_main or page_mission, may have info_bar
        """
        self.ui_ensure(page_reward)
        self.reward_receive(
            oil=self.config.Reward_CollectOil,
            coin=self.config.Reward_CollectCoin,
            exp=self.config.Reward_CollectExp)
        self.ui_goto(page_main)
        self.reward_mission(daily=self.config.Reward_CollectMission,
                            weekly=self.config.Reward_CollectWeeklyMission)
        self.config.task_delay(success=True)
