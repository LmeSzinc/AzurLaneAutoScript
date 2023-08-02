import datetime
import re

import numpy as np

from module.base.timer import Timer
from module.base.utils import get_color
from module.config.utils import get_server_next_update
from module.logger.logger import logger
from module.ocr.ocr import Digit, Duration, Ocr
from module.ocr.utils import split_and_pair_buttons
from module.ui.scroll import Scroll
from module.ui.switch import Switch
from tasks.base.assets.assets_base_page import BATTLE_PASS_CHECK, MAIN_GOTO_BATTLE_PASS
from tasks.base.assets.assets_base_popup import GET_REWARD
from tasks.base.page import page_battle_pass, page_main
from tasks.base.ui import UI
from tasks.battle_pass.assets.assets_battle_pass import *
from tasks.battle_pass.keywords import *

SWITCH_BATTLE_PASS_TAB = Switch('BattlePassTab', is_selector=True)
SWITCH_BATTLE_PASS_TAB.add_state(
    KEYWORD_BATTLE_PASS_TAB.Rewards,
    check_button=REWARDS_CHECK,
    click_button=REWARDS_CLICK
)
SWITCH_BATTLE_PASS_TAB.add_state(
    KEYWORD_BATTLE_PASS_TAB.Missions,
    check_button=MISSIONS_CHECK,
    click_button=MISSIONS_CLICK
)


class BattlePassMissionTab(Switch):
    def get(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            str: state name or 'unknown'.
        """
        for data in self.state_list:
            if main.image_color_count(data['check_button'], color=(250, 233, 153)):
                return data['state']

        return 'unknown'


SWITCH_BATTLE_PASS_MISSION_TAB = BattlePassMissionTab('BattlePassMissionTab', is_selector=True)
SWITCH_BATTLE_PASS_MISSION_TAB.add_state(
    KEYWORD_BATTLE_PASS_MISSION_TAB.Today_Missions,
    check_button=TODAY_MISSION_CLICK,
    click_button=TODAY_MISSION_CLICK
)
SWITCH_BATTLE_PASS_MISSION_TAB.add_state(
    KEYWORD_BATTLE_PASS_MISSION_TAB.This_Week_Missions,
    check_button=WEEK_MISSION_CLICK,
    click_button=WEEK_MISSION_CLICK
)
SWITCH_BATTLE_PASS_MISSION_TAB.add_state(
    KEYWORD_BATTLE_PASS_MISSION_TAB.This_Period_Missions,
    check_button=PERIOD_MISSION_CLICK,
    click_button=PERIOD_MISSION_CLICK
)


class BattlePassQuestOcr(Ocr):
    def after_process(self, result):
        result = super().after_process(result)
        if self.lang == 'ch':
            result = re.sub("[jJ]", "」", result)
        return result


class BattlePassUI(UI):
    MAX_LEVEL = 50

    def _battle_pass_wait_rewards_loaded(self, skip_first_screenshot=True):
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait rewards tab loaded timeout')
                break
            if self.appear(REWARDS_LOADED):
                logger.info('Rewards tab loaded')
                break

    def _battle_pass_wait_missions_loaded(self, skip_first_screenshot=True, has_scroll=True):
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait missions tab loaded timeout')
                break
            if has_scroll:
                if self.appear(MISSION_PAGE_SCROLL):
                    logger.info('Rewards tab loaded')
                    break
            else:
                color = get_color(self.device.image, MISSIONS_LOADED.area)
                if np.mean(color) > 128:
                    logger.info('Missions tab loaded')
                    break

    def battle_pass_goto(self, state: KEYWORD_BATTLE_PASS_TAB):
        """
        Args:
            state:

        Examples:
            self = BattlePassUI('alas')
            self.device.screenshot()
            self.battle_pass_goto(KEYWORDS_DUNGEON_TAB.Missions)
            self.battle_pass_goto(KEYWORDS_DUNGEON_TAB.Rewards)
        """
        self.ui_ensure(page_battle_pass)
        if SWITCH_BATTLE_PASS_TAB.set(state, main=self):
            logger.info(f'Tab goto {state}, wait until loaded')
            if state == KEYWORD_BATTLE_PASS_TAB.Missions:
                self._battle_pass_wait_missions_loaded(has_scroll=False)
            if state == KEYWORD_BATTLE_PASS_TAB.Rewards:
                self._battle_pass_wait_rewards_loaded()

    def battle_pass_mission_tab_goto(self, state: KEYWORD_BATTLE_PASS_MISSION_TAB):
        self.battle_pass_goto(KEYWORD_BATTLE_PASS_TAB.Missions)
        if SWITCH_BATTLE_PASS_MISSION_TAB.set(state, main=self):
            logger.info(f'Tab goto {state}, wait until loaded')
            if state == KEYWORD_BATTLE_PASS_MISSION_TAB.Today_Missions:
                self._battle_pass_wait_missions_loaded(has_scroll=False)
            if state == KEYWORD_BATTLE_PASS_MISSION_TAB.This_Week_Missions:
                self._battle_pass_wait_missions_loaded()
            if state == KEYWORD_BATTLE_PASS_MISSION_TAB.This_Period_Missions:
                self._battle_pass_wait_missions_loaded()

    def handle_choose_gifts(self, interval=5):
        """
        Popup when you have purchase Nameless Glory

        Args:
            interval:

        Returns:
            If handled
        """
        if self.appear_then_click(CLOSE_CHOOSE_GIFT, interval=interval):
            return True

        return False

    def _claim_exp(self, skip_first_screenshot=True):
        logger.hr('Claim EXP', level=1)
        self.battle_pass_goto(KEYWORD_BATTLE_PASS_TAB.Missions)
        claimed = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if not self.appear(EXP_CLAIM_ALL):
                logger.info('No more EXP to claim')
                break
            if self.appear_then_click(EXP_CLAIM_ALL):
                claimed = True
                logger.info("All EXP claimed")
                continue

        logger.attr('EXP claimed', claimed)
        return claimed

    def _claim_rewards(self, skip_first_screenshot=True):
        logger.hr('Claim rewards', level=1)
        self.battle_pass_goto(KEYWORD_BATTLE_PASS_TAB.Rewards)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GET_REWARD):
                logger.info('Get reward')
                break
            if self.appear(CLOSE_CHOOSE_GIFT):
                logger.info('Got reward but have gift to choose')
                break
            if self.appear_then_click(REWARDS_CLAIM_ALL):
                continue

        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(BATTLE_PASS_CHECK):
                logger.info("Claiming rewards complete")
                break
            if self.handle_choose_gifts():
                logger.info("You have unclaimed gift to choose")
                continue
            if self.handle_reward():
                continue

    def _get_battle_pass_level(self) -> int:
        digit = Digit(OCR_LEVEL)
        return digit.ocr_single_line(self.device.image)

    def _get_battle_pass_end(self) -> datetime.datetime:
        remain = Duration(OCR_REMAINING_TIME).ocr_single_line(self.device.image)
        future = get_server_next_update(self.config.Scheduler_ServerUpdate)
        future += datetime.timedelta(days=remain.days)
        return future

    def claim_battle_pass_rewards(self):
        """
        Returns:
            int: Current battle pass level

        Examples:
            self = BattlePassUI('alas')
            self.device.screenshot()
            self.claim_battle_pass_rewards()
        """
        previous_level = self._get_battle_pass_level()
        if previous_level == self.MAX_LEVEL:
            return previous_level
        claimed_exp = self._claim_exp()
        current_level = self._get_battle_pass_level()
        if claimed_exp and current_level > previous_level:
            logger.info("Upgraded, go to claim rewards")
            self._claim_rewards()
        return current_level

    def ocr_single_page(self):
        """
        Returns incomplete quests only
        """
        ocr = BattlePassQuestOcr(OCR_BATTLE_PASS_QUEST)
        results = ocr.matched_ocr(self.device.image, [BattlePassQuest, BattlePassQuestState])

        def completed_state(state):
            return state != KEYWORD_BATTLE_PASS_QUEST_STATE.Navigate

        return [incomplete_quest for incomplete_quest, _ in
                split_and_pair_buttons(results, split_func=completed_state, relative_area=(0, 0, 800, 100))]

    def battle_pass_quests_recognition(self, page: KEYWORD_BATTLE_PASS_MISSION_TAB,
                                       has_scroll=True) -> list[BattlePassQuest]:
        """
        Args:
            page:
            has_scroll: need to scroll to recognize all quests

        Returns:

        """
        logger.info(f"Recognizing battle pass quests at {page}")
        self.battle_pass_mission_tab_goto(page)
        if not has_scroll:
            results = self.ocr_single_page()
        else:
            scroll = Scroll(MISSION_PAGE_SCROLL, color=(198, 198, 198))
            scroll.set_top(main=self)
            results = self.ocr_single_page()
            while not scroll.at_bottom(main=self):
                scroll.next_page(main=self)
                results += [result for result in self.ocr_single_page() if result not in results]
                results = [result.matched_keyword for result in results]
        return results

    def has_battle_pass_entrance(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_main
        """
        timeout = Timer(0.5, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                break

            if self.appear(MAIN_GOTO_BATTLE_PASS, similarity=0.75):
                return True
            else:
                logger.info('No battle pass entrance, probably a gap between two periods')
                continue

        return False

    def run(self):
        self.ui_ensure(page_main)
        if not self.has_battle_pass_entrance():
            self.config.task_delay(server_update=True)
            self.config.task_stop()

        self.ui_goto(page_battle_pass)
        current_level = self.claim_battle_pass_rewards()
        if current_level == self.MAX_LEVEL:
            self.config.task_delay(target=self._get_battle_pass_end())
        else:
            self.config.task_delay(server_update=True)
