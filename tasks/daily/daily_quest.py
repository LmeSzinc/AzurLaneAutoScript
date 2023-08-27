import numpy as np

from module.base.timer import Timer
from module.logger import *
from module.ocr.ocr import Ocr, OcrResultButton
from module.ocr.utils import split_and_pair_buttons
from tasks.daily.assets.assets_daily_reward import *
from tasks.daily.camera import CameraUI
from tasks.daily.keywords import DailyQuest, DailyQuestState, KEYWORDS_DAILY_QUEST, KEYWORDS_DAILY_QUEST_STATE
from tasks.daily.synthesize import SynthesizeConsumablesUI, SynthesizeMaterialUI
from tasks.daily.use_technique import UseTechniqueUI
from tasks.dungeon.assets.assets_dungeon_ui import DAILY_TRAINING_CHECK
from tasks.dungeon.keywords import KEYWORDS_DUNGEON_TAB
from tasks.dungeon.ui import DungeonUI
from tasks.item.consumable_usage import ConsumableUsageUI
from tasks.item.relics import RelicsUI


class DailyQuestOcr(Ocr):
    def __init__(self, button: ButtonWrapper, lang=None, name=None):
        super().__init__(button, lang, name)

    def after_process(self, result):
        result = super().after_process(result)
        if self.lang == 'ch':
            result = result.replace("J", "」")
            result = result.replace(";", "」")
            result = result.replace("宇审", "宇宙")
            # 进行中」hbadarin
            if "进行中" in result:
                result = "进行中"
            if "已领取" in result:
                result = "已领取"
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

            # Might be a screenshot mixed with daily_training and get_reward
            # Swipe at daily training page only
            if interval.reached() and self.match_template_color(DAILY_TRAINING_CHECK):
                self._daily_quests_swipe(direction)
                interval.reset()
                continue

    def _daily_quests_swipe(self, direction: str):
        vector = np.random.uniform(0.4, 0.5)
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

    def daily_quests_recognition(self) -> list[DailyQuest]:
        """
        Returns incomplete quests only
        """
        logger.info("Recognizing daily quests")
        self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Daily_Training)
        self._ensure_position('left')
        results = self._ocr_single_page()
        self._ensure_position('right')
        results += [result for result in self._ocr_single_page() if result not in results]
        results = [result.matched_keyword for result in results]
        logger.info("Daily quests recognition complete")
        logger.info(f"Daily quests: {results}")
        self.config.stored.DailyQuest.write_quests(results)
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

    def _all_reward_got(self):
        return self.appear(ACTIVE_POINTS_5_CHECKED)

    def _get_active_point_reward(self, skip_first_screenshot=True):
        def get_active():
            for b in [
                ACTIVE_POINTS_1_UNLOCK,
                ACTIVE_POINTS_2_UNLOCK,
                ACTIVE_POINTS_3_UNLOCK,
                ACTIVE_POINTS_4_UNLOCK,
                ACTIVE_POINTS_5_UNLOCK
            ]:
                # Black gift icon
                if self.image_color_count(b, color=(61, 53, 53), threshold=221, count=100):
                    return b
            return None

        interval = Timer(2)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._no_reward_to_get():
                break
            if self.handle_reward():
                continue
            if interval.reached():
                if active := get_active():
                    self.device.click(active)
                    interval.reset()

        # Write stored
        point = 0
        for progress, button in zip(
                [100, 200, 300, 400, 500],
                [
                    ACTIVE_POINTS_1_CHECKED,
                    ACTIVE_POINTS_2_CHECKED,
                    ACTIVE_POINTS_3_CHECKED,
                    ACTIVE_POINTS_4_CHECKED,
                    ACTIVE_POINTS_5_CHECKED
                ]
        ):
            if self.appear(button):
                point = progress
        logger.attr('Daily activity', point)
        with self.config.multi_set():
            self.config.stored.DailyActivity.set(point)
            if point == 500:
                self.config.stored.DailyQuest.write_quests([])

    def get_daily_rewards(self):
        """
        Returns:
            int: If all reward got.

        Pages:
            in: Any
            out: page_guide, Daily_Training
        """
        logger.hr('Get daily rewards', level=2)
        self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Daily_Training)
        logger.info("Getting quest rewards")
        self._get_quest_reward()
        logger.info("Getting active point rewards")
        self._get_active_point_reward()
        if self._all_reward_got():
            logger.info("All daily reward got")
            return True
        else:
            logger.info('Daily reward got but not yet claimed')
            return False

    def do_daily_quests(self):
        """
        Returns:
            int: Number of quests done
        """
        logger.hr('Recognize quests', level=1)
        quests = self.daily_quests_recognition()

        done = 0
        logger.hr('Do quests', level=1)
        if KEYWORDS_DAILY_QUEST.Take_1_photo in quests:
            CameraUI(self.config, self.device).take_picture()
            done += 1
        if KEYWORDS_DAILY_QUEST.Synthesize_Consumable_1_time in quests:
            if SynthesizeConsumablesUI(self.config, self.device).synthesize_consumables():
                done += 1
        if KEYWORDS_DAILY_QUEST.Synthesize_material_1_time in quests:
            if SynthesizeMaterialUI(self.config, self.device).synthesize_material():
                done += 1
        if KEYWORDS_DAILY_QUEST.Use_Consumables_1_time in quests:
            if ConsumableUsageUI(self.config, self.device).use_consumable():
                done += 1
        if KEYWORDS_DAILY_QUEST.Use_Technique_2_times in quests:
            UseTechniqueUI(self.config, self.device).use_technique(2)
            done += 1
        if KEYWORDS_DAILY_QUEST.Salvage_any_Relic in quests:
            if RelicsUI(self.config, self.device).salvage_relic():
                done += 1

        return done

    def run(self):
        for _ in range(5):
            got = self.get_daily_rewards()
            if got:
                break
            done = self.do_daily_quests()
            if not done:
                logger.info('No more quests able to do')
                break

        # Scheduler
        self.config.task_delay(server_update=True)
