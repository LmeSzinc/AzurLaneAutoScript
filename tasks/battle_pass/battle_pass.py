import datetime
import re
from dataclasses import dataclass

import numpy as np

from module.base.timer import Timer
from module.base.utils import get_color
from module.config.stored.classes import StoredCounter
from module.config.utils import get_server_next_update
from module.logger.logger import logger
from module.ocr.keyword import KeywordDigitCounter
from module.ocr.ocr import Digit, DigitCounter, Duration, Ocr, OcrResultButton
from module.ocr.utils import pair_buttons
from module.ui.scroll import Scroll
from module.ui.switch import Switch
from tasks.base.assets.assets_base_page import BATTLE_PASS_CHECK, MAIN_GOTO_BATTLE_PASS
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
        if self.lang == 'cn':
            result = re.sub("[jJ]", "」", result)
        return result


@dataclass
class DataBattlePassQuest:
    quest: BattlePassQuest
    state: BattlePassQuestState = None
    digit: KeywordDigitCounter = ''

    def __eq__(self, other):
        return self.quest == other.quest

    @property
    def is_incomplete(self) -> bool:
        return self.state == KEYWORD_BATTLE_PASS_QUEST_STATE.Navigate


class BattlePassUI(UI):
    MAX_LEVEL = 70

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

    def _battle_pass_wait_missions_loaded(self, skip_first_screenshot=True):
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait missions tab loaded timeout')
                break

            # Has scroll and last mission loaded
            if self.appear(MISSION_PAGE_SCROLL):
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
                self._battle_pass_wait_missions_loaded()
            if state == KEYWORD_BATTLE_PASS_TAB.Rewards:
                self._battle_pass_wait_rewards_loaded()

    def battle_pass_mission_tab_goto(self, state: KEYWORD_BATTLE_PASS_MISSION_TAB):
        self.battle_pass_goto(KEYWORD_BATTLE_PASS_TAB.Missions)
        if SWITCH_BATTLE_PASS_MISSION_TAB.set(state, main=self):
            logger.info(f'Tab goto {state}, wait until loaded')
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
        timeout = Timer(5, count=15).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.reward_appear():
                logger.info('Get reward')
                break
            if self.appear(CLOSE_CHOOSE_GIFT):
                logger.info('Got reward but have gift to choose')
                break
            if timeout.reached():
                logger.warning('Claim reward timeout, no rewards to claim')
                break
            if self.appear_then_click(REWARDS_CLAIM_ALL, interval=2):
                timeout.reset()
                continue

        logger.info('Close reward popup')
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
        # Update level
        with self.config.multi_set():
            previous_level = self._get_battle_pass_level()
            self.config.stored.BattlePassLevel.set(previous_level)
            if previous_level == self.MAX_LEVEL:
                self.config.stored.BattlePassWeeklyQuest.write_quests([])
                return previous_level

        # Claim rewards
        claimed_exp = self._claim_exp()
        current_level = self._get_battle_pass_level()
        self.config.stored.BattlePassLevel.set(current_level)
        if claimed_exp and current_level > previous_level:
            logger.info("Upgraded, go to claim rewards")
            self._claim_rewards()
        else:
            # Missions refreshed
            self._battle_pass_wait_missions_loaded()

        # Update quests
        self.battle_pass_quests_recognition()

        return current_level

    def ocr_single_page(self) -> list[DataBattlePassQuest]:
        """
        Returns incomplete quests only
        """
        logger.hr('Battle pass ocr single page')
        ocr = BattlePassQuestOcr(OCR_BATTLE_PASS_QUEST)
        results = ocr.matched_ocr(
            self.device.image, keyword_classes=[BattlePassQuest, BattlePassQuestState, KeywordDigitCounter])

        # Product DataBattlePassQuest objects
        data_quest: dict[OcrResultButton, DataBattlePassQuest] = {
            result: DataBattlePassQuest(result.matched_keyword)
            for result in results if isinstance(result.matched_keyword, BattlePassQuest)
        }
        # Update quest state
        list_attr = [result for result in results if isinstance(result.matched_keyword, BattlePassQuestState)]
        for quest, state in pair_buttons(data_quest, list_attr, relative_area=(0, 0, 800, 100)):
            data_quest[quest].state = state.matched_keyword
        # Update quest progress
        list_attr = [result for result in results if isinstance(result.matched_keyword, str)]
        for quest, digit in pair_buttons(data_quest, list_attr, relative_area=(-50, 0, 200, 70)):
            data_quest[quest].digit = digit.matched_keyword

        return list(data_quest.values())

    def battle_pass_quests_recognition(self):
        """
        Pages:
            in: page_battle_pass, KEYWORD_BATTLE_PASS_TAB.Missions, weekly or period
        """
        logger.hr('Quest recognise', level=1)
        self.battle_pass_mission_tab_goto(
            KEYWORD_BATTLE_PASS_MISSION_TAB.This_Week_Missions)

        scroll = Scroll(MISSION_PAGE_SCROLL, color=(198, 198, 198))
        scroll.set_top(main=self)

        results: list[DataBattlePassQuest] = []
        while 1:
            results += [result for result in self.ocr_single_page() if result not in results]
            if scroll.at_bottom(main=self):
                logger.info('Quest list reached bottom')
                break
            if scroll.next_page(main=self):
                continue
            else:
                self.device.screenshot()

        # Convert quest keyword to stored object
        dic_quest_to_stored = {
            KEYWORD_BATTLE_PASS_QUEST.Complete_Simulated_Universe_1_times:
                self.config.stored.BattlePassSimulatedUniverse,
            KEYWORD_BATTLE_PASS_QUEST.Clear_Calyx_1_times:
                self.config.stored.BattlePassQuestCalyx,
            KEYWORD_BATTLE_PASS_QUEST.Complete_Echo_of_War_1_times:
                self.config.stored.BattlePassQuestEchoOfWar,
            KEYWORD_BATTLE_PASS_QUEST.Use_300000_credits:
                self.config.stored.BattlePassQuestCredits,
            KEYWORD_BATTLE_PASS_QUEST.Synthesize_Consumables_1_times:
                self.config.stored.BattlePassQuestSynthesizeConsumables,
            KEYWORD_BATTLE_PASS_QUEST.Clear_Cavern_of_Corrosion_1_times:
                self.config.stored.BattlePassQuestCavernOfCorrosion,
            KEYWORD_BATTLE_PASS_QUEST.Consume_a_total_of_1_Trailblaze_Power_1400_Trailblazer_Power_max:
                self.config.stored.BattlePassQuestTrailblazePower,
        }
        with self.config.multi_set():
            # Write incomplete quests
            quests = [result.quest for result in results if result.is_incomplete]
            self.config.stored.BattlePassWeeklyQuest.write_quests(quests)
            # Create an OCR object just for calling format_result()
            ocr = DigitCounter(OCR_BATTLE_PASS_QUEST)
            # Write quest progresses
            for result in results:
                ocr.name = result.quest.name
                current, _, total = ocr.format_result(result.digit)
                if total == 0:
                    logger.error(f'Battle pass quests {result.quest} progress invalid: {result.digit}')
                    continue
                stored: StoredCounter = dic_quest_to_stored.get(result.quest, None)
                # Check if exist
                if stored is None:
                    logger.error(f'Battle pass quest {result.quest} has not corresponding stored object')
                    continue
                # Check total
                if stored.FIXED_TOTAL and total != stored.FIXED_TOTAL:
                    logger.error(f'Battle pass quest progress {current}/{total} does not match its stored object')
                    continue
                if hasattr(stored, 'LIST_TOTAL') and total not in stored.LIST_TOTAL:
                    logger.error(f'Battle pass quest progress {current}/{total} is not in LIST_TOTAL')
                    continue
                # Set
                stored.set(current, total=total)

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
                continue

        logger.info('No battle pass entrance, probably a gap between two periods')
        return False

    def run(self):
        self.ui_ensure(page_main)
        if not self.has_battle_pass_entrance():
            self.config.stored.BattlePassWeeklyQuest.set(0)
            self.config.task_delay(server_update=True)
            self.config.task_stop()

        self.ui_goto(page_battle_pass)
        current_level = self.claim_battle_pass_rewards()
        if current_level == self.MAX_LEVEL:
            self.config.task_delay(target=self._get_battle_pass_end())
        else:
            self.config.task_delay(server_update=True)
