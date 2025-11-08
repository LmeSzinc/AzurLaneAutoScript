from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.combat.assets import *
from module.logger import logger
from module.reward.assets import *
from module.ui.navbar import Navbar
from module.ui.page import page_main, page_mission, page_reward
from module.ui.ui import UI
from module.ui_white.assets import MISSION_NOTICE_WHITE


class Reward(UI):
    def reward_receive(self, oil, coin, exp):
        """
        Args:
            oil (bool):
            coin (bool):
            exp (bool):

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
        for _ in self.loop():
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

    def _reward_get_state(self):
        if self.appear(MISSION_MULTI, offset=(20, 20)):
            return MISSION_MULTI
        if self.match_template_color(MISSION_SINGLE, offset=(50, 200)):
            return MISSION_SINGLE
        if self.appear(MISSION_EMPTY, offset=(20, 20)):
            return MISSION_EMPTY
        if self.appear(MISSION_UNFINISH, offset=(50, 200)):
            return MISSION_UNFINISH
        return None

    def _reward_mission_claim_click(self):
        """
        Returns:
            bool: If claimed

        Pages:
            in: page_mission, MISSION_MULTI or MISSION_SINGLE
            out: unknown popup
        """
        clicked = False
        click_interval = Timer(1, count=2)
        for _ in self.loop():
            if clicked and not self.ui_page_appear(page_mission):
                return clicked
            if click_interval.reached():
                if self.appear_then_click(MISSION_MULTI, offset=(20, 20)):
                    click_interval.reset()
                    clicked = True
                    continue
                if self.match_template_color(MISSION_SINGLE, offset=(50, 200)):
                    self.device.click(MISSION_SINGLE)
                    click_interval.reset()
                    clicked = True
                    continue

    def _reward_mission_claim_receive(self):
        """
        Returns:
            Button | str: Button object or state string

        Pages:
            in: unknown popup
            out: page_mission
        """
        logger.info('Mission claim receive')
        timeout = Timer(2, count=6).start()
        for _ in self.loop():
            if self.ui_page_appear(page_mission):
                state = self._reward_get_state()
                if state:
                    return state
                if timeout.reached():
                    logger.warning('Wait mission receive timeout')
                    return 'timeout'
            else:
                timeout.reset()

            # click
            if self.appear_then_click(GET_ITEMS_1, offset=(30, 30), interval=1):
                continue
            if self.appear_then_click(GET_ITEMS_2, offset=(30, 30), interval=1):
                continue
            if self.appear_then_click(GET_SHIP, interval=1):
                continue
            if self.handle_mission_popup_ack():
                continue
            if self.handle_vote_popup():
                continue
            if self.handle_story_skip():
                continue
            if self.handle_popup_confirm('MISSION_REWARD'):
                continue

    def _reward_wait_mission_list(self):
        """
        Wait until mission list fully loaded

        Pages:
            in: page_mission
            out: page_mission, any mission state, or timeout
        """
        timeout = Timer(1, count=2).start()
        for _ in self.loop():
            state = self._reward_get_state()
            if state:
                return state
            if timeout.reached():
                return 'timeout'

    def _reward_mission_collect(self):
        """
        Streamline handling of mission rewards for
        both 'all' and 'weekly' pages

        Returns:
            Button | str: Last state, Button object or state string
        """
        state = self._reward_wait_mission_list()
        while 1:
            logger.attr('MissionState', state)
            self.device.stuck_record_clear()
            self.device.click_record_clear()
            if state == 'timeout':
                logger.warning('Reward wait mission list timeout')
                return state
            if state in [MISSION_EMPTY, MISSION_UNFINISH]:
                logger.info('Mission collect finished')
                break
            elif state in [MISSION_MULTI, MISSION_SINGLE]:
                # Clear any existing interval for the following assets
                self.interval_clear([GET_ITEMS_1, GET_ITEMS_2, MISSION_MULTI, MISSION_SINGLE, GET_SHIP])
                self._reward_mission_claim_click()
                state = self._reward_mission_claim_receive()
                continue
            else:
                logger.warning('Empty mission state, mission collect finished')

        return state

    def _reward_mission_all(self):
        """
        Collects all page mission rewards

        Returns:
            bool, if handled
        """
        self.reward_side_navbar_ensure(upper=1)
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
        return self._reward_mission_collect()

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

        if daily:
            self._reward_mission_all()
        if weekly:
            self._reward_mission_weekly()

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
