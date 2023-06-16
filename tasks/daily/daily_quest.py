import numpy as np

from module.base.timer import Timer
from module.logger import *
from module.ocr.ocr import Ocr, OcrResultButton
from module.ocr.utils import split_and_pair_buttons
from tasks.daily.assets.assets_daily_reward import *
from tasks.daily.keywords import DailyQuest, DailyQuestState, KEYWORDS_DAILY_QUEST_STATE
from tasks.dungeon.keywords import KEYWORDS_DUNGEON_TAB
from tasks.dungeon.ui import DungeonUI


class DailyQuestOcr(Ocr):
    def __init__(self, button: ButtonWrapper, lang=None, name=None):
        super().__init__(button, lang, name)

    def after_process(self, result):
        result = super().after_process(result)
        if self.lang == 'ch':
            result = result.replace("J", "」")
            result = result.replace(";", "」")
            result = result.replace("宇审", "宇宙")
        return result


class DailyQuestUI(DungeonUI):
    def _ensure_position(self, direction: str, skip_first_screenshot=True):
        interval = Timer(5)
        if direction == 'left':
            template = DAILY_QUEST_LEFT_START
        elif direction == 'right':
            template = DAILY_QUEST_RIGHT_END
        else:
            logger.warning(f'Unknown drag direction: {direction}')
            return
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(template):
                logger.info(f"Ensure position: {direction}")
                break
            if interval.reached():
                self._daily_quests_swipe(direction)
                interval.reset()
                continue

    def _daily_quests_swipe(self, direction: str):
        vector = np.random.uniform(0.65, 0.85)
        if direction == 'left':
            swipe_vector = (vector * OCR_DAILY_QUEST.width, 0)
        elif direction == 'right':
            swipe_vector = (-vector * OCR_DAILY_QUEST.width, 0)
        else:
            logger.warning(f'Unknown drag direction: {direction}')
            return
        self.device.swipe_vector(swipe_vector, box=OCR_DAILY_QUEST.button,
                                 random_range=(-10, -10, 10, 10), name='DAILY_QUEST_DRAG')

    def _ocr_single_page(self) -> list[OcrResultButton]:
        ocr = DailyQuestOcr(OCR_DAILY_QUEST)
        ocr.merge_thres_y = 20
        results = ocr.matched_ocr(self.device.image, [DailyQuestState, DailyQuest])
        if len(results) < 8:
            logger.warning(f"Recognition failed at {8 - len(results)} quests on one page")

        def completed_state(state):
            return state != KEYWORDS_DAILY_QUEST_STATE.Go and state != KEYWORDS_DAILY_QUEST_STATE.In_Progress

        return [quest for quest, _ in
                split_and_pair_buttons(results, split_func=completed_state, relative_area=(0, 0, 200, 720))]

    def daily_quests_recognition(self):
        """
        Returns incomplete quests only
        """
        logger.info("Recognizing daily quests")
        self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Daily_Training)
        self._ensure_position('left')
        results = self._ocr_single_page()
        self._ensure_position('right')
        results += [result for result in self._ocr_single_page() if result not in results]
        logger.info("Daily quests recognition complete")
        return results

    def _get_quest_reward(self, skip_first_screenshot=True):
        self._ensure_position('left')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(DAILY_QUEST_FULL) or self.appear(DAILY_QUEST_GOTO):
                break
            if self.appear_then_click(DAILY_QUEST_REWARD, interval=1):
                continue

    def _no_reward_to_get(self):
        return (
                (self.appear(ACTIVE_POINTS_1_LOCKED) or self.appear(ACTIVE_POINTS_1_CHECKED))
                and (self.appear(ACTIVE_POINTS_2_LOCKED) or self.appear(ACTIVE_POINTS_2_CHECKED))
                and (self.appear(ACTIVE_POINTS_3_LOCKED) or self.appear(ACTIVE_POINTS_3_CHECKED))
                and (self.appear(ACTIVE_POINTS_4_LOCKED) or self.appear(ACTIVE_POINTS_4_CHECKED))
                and (self.appear(ACTIVE_POINTS_5_LOCKED) or self.appear(ACTIVE_POINTS_5_CHECKED))
        )

    def _get_active_point_reward(self, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._no_reward_to_get():
                break
            if self.handle_reward():
                continue
            if self.appear_then_click(ACTIVE_POINTS_1_UNLOCK):
                continue
            if self.appear_then_click(ACTIVE_POINTS_2_UNLOCK):
                continue
            if self.appear_then_click(ACTIVE_POINTS_3_UNLOCK):
                continue
            if self.appear_then_click(ACTIVE_POINTS_4_UNLOCK):
                continue
            if self.appear_then_click(ACTIVE_POINTS_5_UNLOCK):
                continue

    def get_daily_rewards(self):
        self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Daily_Training)
        logger.info("Getting quest rewards")
        self._get_quest_reward()
        logger.info("Getting active point rewards")
        self._get_active_point_reward()
        logger.info("All daily reward got")
