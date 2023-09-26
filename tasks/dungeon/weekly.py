from module.logger import logger
from module.ocr.ocr import DigitCounter
from tasks.daily.keywords import KEYWORDS_DAILY_QUEST
from tasks.dungeon.assets.assets_dungeon_ui import OCR_DUNGEON_LIST, OCR_WEEKLY_LIMIT
from tasks.dungeon.dungeon import Dungeon
from tasks.dungeon.keywords import DungeonList, KEYWORDS_DUNGEON_TAB
from tasks.dungeon.ui import DUNGEON_LIST


class WeeklyDungeon(Dungeon):
    def require_compulsory_support(self) -> bool:
        return False

    def _dungeon_run(self, dungeon: DungeonList, team: int = None, wave_limit: int = 0, support_character: str = None,
                     skip_ui_switch: bool = False):
        if team is None:
            team = self.config.Weekly_Team
        # No support
        support_character = ''
        skip_ui_switch = True
        return super()._dungeon_run(
            dungeon=dungeon, team=team, wave_limit=wave_limit,
            support_character=support_character, skip_ui_switch=skip_ui_switch)

    def get_weekly_remain(self) -> int:
        """
        Pages:
            in: page_guide, Survival_Index, KEYWORDS_DUNGEON_NAV.Echo_of_War
        """
        ocr = DigitCounter(OCR_WEEKLY_LIMIT)
        current, _, _ = ocr.ocr_single_line(self.device.image)
        total = self.config.stored.EchoOfWar.FIXED_TOTAL
        remain = total - current
        if current <= total:
            logger.attr('EchoOfWar', f'{current}/{total}')
            self.config.stored.EchoOfWar.value = current
            return current
        else:
            logger.warning(f'Invalid EchoOfWar limit: {current}/{total}')
            return 0

    def run(self):
        # self.config.update_battle_pass_quests()
        self.config.update_daily_quests()
        self.called_daily_support = False
        self.achieved_daily_quest = False
        self.daily_quests = self.config.stored.DailyQuest.load_quests()

        dungeon = DungeonList.find(self.config.Weekly_Name)

        # UI switches
        self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
        # Equivalent to self.dungeon_goto(dungeon), but check limit remains
        DUNGEON_LIST.search_button = OCR_DUNGEON_LIST
        self._dungeon_nav_goto(dungeon)

        # Check limit
        remain = self.get_weekly_remain()
        if remain <= 0:
            if KEYWORDS_DAILY_QUEST.Complete_Echo_of_War_1_times in self.daily_quests:
                logger.info('Reached the limit to get Echo_of_War rewards, continue cause daily quests require it')
                remain = 1
            else:
                logger.info('Reached the limit to get Echo_of_War rewards, stop')
                self.config.task_delay(server_update=True)
                self.config.task_stop()

        self._dungeon_insight(dungeon)
        self._dungeon_enter(dungeon)

        # Combat
        count = self.dungeon_run(dungeon, wave_limit=min(remain, 3))

        with self.config.multi_set():
            # Check daily quests
            if count:
                if KEYWORDS_DAILY_QUEST.Complete_Echo_of_War_1_times in self.daily_quests:
                    logger.info('Achieve daily quest Complete_Echo_of_War_1_times')
                    self.config.task_call('DailyQuest')
            # Finished all remains
            if count >= remain:
                logger.info('All Echo_of_War rewards got')
                self.config.task_delay(server_update=True)
                self.config.task_stop()

            logger.warning(f'Unexpected Echo_of_War case, count={count}, remain={remain}')
            self.config.task_delay(server_update=True)
            self.config.task_stop()
