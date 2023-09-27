import cv2
import numpy as np

from module.base.timer import Timer
from module.base.utils import crop
from module.logger import logger
from module.ocr.ocr import Ocr, OcrResultButton
from module.ocr.utils import split_and_pair_buttons
from tasks.battle_pass.keywords import KEYWORD_BATTLE_PASS_QUEST
from tasks.daily.assets.assets_daily_reward import *
from tasks.daily.camera import CameraUI
from tasks.daily.keywords import (
    DailyQuest,
    DailyQuestState,
    KEYWORDS_DAILY_QUEST,
    KEYWORDS_DAILY_QUEST_STATE,
)
from tasks.daily.synthesize import SynthesizeConsumablesUI, SynthesizeMaterialUI
from tasks.daily.use_technique import UseTechniqueUI
from tasks.dungeon.assets.assets_dungeon_ui import DAILY_TRAINING_CHECK
from tasks.dungeon.keywords import KEYWORDS_DUNGEON_TAB
from tasks.dungeon.ui import DungeonUI
from tasks.item.consumable_usage import ConsumableUsageUI
from tasks.item.relics import RelicsUI
from tasks.map.route.loader import RouteLoader
from tasks.map.route.route import ROUTE_DAILY


class DailyQuestOcr(Ocr):
    merge_thres_y = 20

    def pre_process(self, image):
        image = super().pre_process(image)
        image = crop(image, OCR_DAILY_QUEST.area)
        mask = MASK_DAILY_QUEST.matched_button.image
        # Remove "+200Activity"
        cv2.bitwise_and(image, mask, dst=image)
        return image

    def after_process(self, result):
        result = super().after_process(result)
        if self.lang == 'cn':
            result = result.replace("J", "」")
            result = result.replace(";", "」")
            result = result.replace("了", "」")
            result = result.replace("宇审", "宇宙")
            result = result.replace("凝带", "凝滞")
            # 进行中」hbadarin
            if "进行中" in result:
                result = "进行中"
            if "已领取" in result:
                result = "已领取"
        if self.lang == 'en':
            result = result.replace('wor(d', 'world')
            # Echo/ofWar
            result = result.replace('cho/of', 'cho of')
            # Catyx(Golden).1.times
            result = result.replace('atyx', 'alyx')
            if "progress" in result.lower():
                result = "In Progress"
            if "claimed" in result.lower():
                result = "Claimed"
        return result


class DailyQuestUI(DungeonUI, RouteLoader):
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
        results = ocr.matched_ocr(self.device.image, [DailyQuestState, DailyQuest], direct_ocr=True)
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

            if self.appear(DAILY_QUEST_FULL):
                logger.info('No more quests to get, activity full')
                break
            if self.appear(DAILY_QUEST_GOTO):
                logger.info('No more quests to get, have quests uncompleted')
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
                logger.info('No more reward to get')
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
        logger.hr('Get daily rewards', level=1)
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
        if KEYWORDS_DAILY_QUEST.Complete_Forgotten_Hall_1_time in quests:
            self.route_run(ROUTE_DAILY.ForgottenHallStage1__route)
            done += 1

        """
        enemy x1 In_a_single_battle_inflict_3_Weakness_Break_of_different_Types
        enemy x1 Inflict_Weakness_Break_5_times
        enemy x2 Defeat_a_total_of_20_enemies
        enemy x3 Enter_combat_by_attacking_enemy_Weakness_and_win_3_times
        item x1 Destroy_3_destructible_objects
        enemy x1 Use_an_Ultimate_to_deal_the_final_blow_1_time
        """
        enemy = 0
        item = 0
        if KEYWORDS_DAILY_QUEST.In_a_single_battle_inflict_3_Weakness_Break_of_different_Types in quests:
            enemy = max(enemy, 1)
        if KEYWORDS_DAILY_QUEST.Inflict_Weakness_Break_5_times in quests:
            enemy = max(enemy, 1)
        if KEYWORDS_DAILY_QUEST.Defeat_a_total_of_20_enemies in quests:
            enemy = max(enemy, 2)
        if KEYWORDS_DAILY_QUEST.Enter_combat_by_attacking_enemy_Weakness_and_win_3_times in quests:
            enemy = max(enemy, 3)
        if KEYWORDS_DAILY_QUEST.Destroy_3_destructible_objects in quests:
            item = max(item, 1)
        if KEYWORDS_DAILY_QUEST.Use_an_Ultimate_to_deal_the_final_blow_1_time in quests:
            enemy = max(enemy, 1)
        logger.info(f'Himeko trial, enemy={enemy}, item={item}')
        for run in [1, 2, 3]:
            if enemy >= run and item >= run:
                self.route_run(ROUTE_DAILY.HimekoTrial__route_item_enemy)
                done += 1
            elif enemy >= run:
                self.route_run(ROUTE_DAILY.HimekoTrial__route_enemy)
                done += 1
            elif item >= run:
                self.route_run(ROUTE_DAILY.HimekoTrial__route_item)
                done += 1
            else:
                break
        if max(enemy, item) > 0:
            self.route_run(ROUTE_DAILY.HimekoTrial__exit)

        return done

    def run(self):
        self.config.update_battle_pass_quests()

        for _ in range(5):
            got = self.get_daily_rewards()
            if got:
                break
            done = self.do_daily_quests()
            if not done:
                logger.info('No more quests able to do')
                break

        # Scheduler
        with self.config.multi_set():
            # Check battle pass
            if self.config.stored.DailyActivity.value == 500:
                quests = self.config.stored.BattlePassTodayQuest.load_quests()
                if KEYWORD_BATTLE_PASS_QUEST.Reach_500_on_Daily_Training_Activity in quests:
                    logger.info('Achieved battle pass quest Reach_500_on_Daily_Training_Activity')
                    if self.config.stored.BattlePassLevel.is_full():
                        logger.info('BattlePassLevel full, no task call')
                    else:
                        self.config.task_call('BattlePass')
                    self.config.task_call('DataUpdate')
            # Delay self
            self.config.task_delay(server_update=True)


if __name__ == '__main__':
    self = DailyQuestUI('src')
    self.device.screenshot()
    self.route_run(ROUTE_DAILY.HimekoTrial__route_enemy)
