from datetime import timedelta

from module.base.utils import area_offset
from module.config.stored.classes import now
from module.config.utils import DEFAULT_TIME
from module.logger import logger
from tasks.combat.combat import Combat
from tasks.daily.keywords import KEYWORDS_DAILY_QUEST
from tasks.dungeon.event import DungeonEvent
from tasks.dungeon.keywords import DungeonList, KEYWORDS_DUNGEON_LIST, KEYWORDS_DUNGEON_TAB
from tasks.dungeon.ui import DungeonUI
from tasks.battle_pass.keywords import KEYWORD_BATTLE_PASS_QUEST


class Dungeon(DungeonUI, DungeonEvent, Combat):
    called_daily_support = False
    achieved_daily_quest = False
    running_double = False
    daily_quests = []

    def _dungeon_run(self, dungeon: DungeonList, team: int = None, wave_limit: int = 0, support_character: str = None,
                     skip_ui_switch: bool = False):
        """
        Args:
            dungeon:
            team: 1 to 6.
            wave_limit: Limit combat runs, 0 means no limit.
            support_character: Support character name
            skip_ui_switch: True if already at dungeon aside

        Returns:
            int: Run count

        Pages:
            in: page_main, DUNGEON_COMBAT_INTERACT
                or COMBAT_PREPARE
            out: page_main
        """
        if team is None:
            team = self.config.Dungeon_Team
        if support_character is None and self.config.DungeonSupport_Use == 'always_use':
            support_character = self.config.DungeonSupport_Character

        logger.hr('Dungeon run', level=1)
        logger.info(f'Dungeon: {dungeon}, team={team}, wave_limit={wave_limit}, support_character={support_character}')

        if not skip_ui_switch:
            interact = self.get_dungeon_interact()
            if interact is not None and interact == dungeon:
                logger.info('Already nearby dungeon')
            else:
                self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
                self.dungeon_goto(dungeon)

            if dungeon == KEYWORDS_DUNGEON_LIST.Stagnant_Shadow_Blaze:
                if self.handle_destructible_around_blaze():
                    self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
                    self.dungeon_goto(dungeon)

        self.combat_enter_from_map()
        # Check double event remain before combat
        # Conservatively prefer the smaller result
        if (dungeon.is_Calyx_Golden or dungeon.is_Calyx_Crimson) and \
                self.running_double and self.config.stored.DungeonDouble.calyx > 0:
            calyx = self.get_double_event_remain_at_combat()
            if calyx is not None and calyx < self.config.stored.DungeonDouble.calyx:
                self.config.stored.DungeonDouble.calyx = calyx
                wave_limit = calyx
            if calyx == 0:
                return 0
        if dungeon.is_Cavern_of_Corrosion and self.running_double and \
                self.config.stored.DungeonDouble.relic > 0:
            relic = self.get_double_event_remain_at_combat()
            if relic is not None and relic < self.config.stored.DungeonDouble.relic:
                self.config.stored.DungeonDouble.relic = relic
                wave_limit = relic
            if relic == 0:
                return 0
        # Combat
        count = self.combat(team=team, wave_limit=wave_limit, support_character=support_character)

        # Update quest states
        if dungeon.is_Calyx_Golden \
                and KEYWORDS_DAILY_QUEST.Clear_Calyx_Golden_1_times in self.daily_quests:
            logger.info('Achieved daily quest Clear_Calyx_Golden_1_times')
            self.achieved_daily_quest = True
        if dungeon.is_Calyx_Crimson \
                and KEYWORDS_DAILY_QUEST.Complete_Calyx_Crimson_1_time in self.daily_quests:
            logger.info('Achieve daily quest Complete_Calyx_Crimson_1_time')
            self.achieved_daily_quest = True
        if dungeon.is_Stagnant_Shadow \
                and KEYWORDS_DAILY_QUEST.Clear_Stagnant_Shadow_1_times in self.daily_quests:
            logger.info('Achieve daily quest Clear_Stagnant_Shadow_1_times')
            self.achieved_daily_quest = True
        if dungeon.is_Cavern_of_Corrosion \
                and KEYWORDS_DAILY_QUEST.Clear_Cavern_of_Corrosion_1_times in self.daily_quests:
            logger.info('Achieve daily quest Clear_Cavern_of_Corrosion_1_times')
            self.achieved_daily_quest = True
        if support_character is not None:
            self.called_daily_support = True
            if KEYWORDS_DAILY_QUEST.Obtain_victory_in_combat_with_support_characters_1_time:
                logger.info('Achieve daily quest Obtain_victory_in_combat_with_support_characters_1_time')
                self.achieved_daily_quest = True

        # Check trailblaze power, this may stop current task
        if self.is_trailblaze_power_exhausted():
            self.delay_dungeon_task(dungeon)
        return count

    def dungeon_run(
            self, dungeon: DungeonList, team: int = None, wave_limit: int = 0, support_character: str = None):
        """
        Run dungeon, and handle daily support

        Args:
            dungeon:
            team: 1 to 6.
            wave_limit: Limit combat runs, 0 means no limit.
            support_character: Support character name

        Returns:
            int: Run count

        Pages:
            in: Any
            out: page_main
        """
        require = self.require_compulsory_support()
        if require:
            logger.info('Run once with support')
            count = self._dungeon_run(dungeon=dungeon, team=team, wave_limit=1,
                                      support_character=self.config.DungeonSupport_Character)

            logger.info('Run the rest waves without compulsory support')
            if wave_limit >= 2 or wave_limit == 0:
                # Already at page_name with DUNGEON_COMBAT_INTERACT
                if wave_limit >= 2:
                    wave_limit -= 1
                count += self._dungeon_run(dungeon=dungeon, team=team, wave_limit=wave_limit,
                                           support_character=support_character, skip_ui_switch=True)

            return count

        else:
            # Normal run
            return self._dungeon_run(dungeon=dungeon, team=team, wave_limit=wave_limit,
                                     support_character=support_character)

    def run(self):
        self.config.update_battle_pass_quests()
        self.config.update_daily_quests()
        self.called_daily_support = False
        self.achieved_daily_quest = False
        self.running_double = False
        self.daily_quests = self.config.stored.DailyQuest.load_quests()

        # Update double event records
        if (self.config.stored.DungeonDouble.is_expired()
                or self.config.stored.DungeonDouble.calyx > 0
                or self.config.stored.DungeonDouble.relic > 0):
            logger.info('Get dungeon double remains')
            # UI switches
            switched = self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
            if not switched:
                # Nav must at top, reset nav states
                self.ui_goto_main()
                self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
            # Check remains
            calyx = 0
            relic = 0
            if self.has_double_calyx_event():
                self._dungeon_nav_goto(KEYWORDS_DUNGEON_LIST.Calyx_Golden_Treasures)
                calyx = self.get_double_event_remain()
            if self.has_double_relic_event():
                self._dungeon_nav_goto(KEYWORDS_DUNGEON_LIST.Cavern_of_Corrosion_Path_of_Gelid_Wind)
                relic = self.get_double_event_remain()
            with self.config.multi_set():
                self.config.stored.DungeonDouble.calyx = calyx
                self.config.stored.DungeonDouble.relic = relic

        # Run double events
        ran_calyx_golden = False
        ran_calyx_crimson = False
        ran_cavern_of_corrosion = False
        # Double calyx
        if self.config.Dungeon_NameAtDoubleCalyx != 'do_not_participate' \
                and self.config.stored.DungeonDouble.calyx > 0:
            logger.info('Run double calyx')
            dungeon = DungeonList.find(self.config.Dungeon_NameAtDoubleCalyx)
            self.running_double = True
            if self.dungeon_run(dungeon=dungeon, wave_limit=self.config.stored.DungeonDouble.calyx):
                if dungeon.is_Calyx_Golden:
                    ran_calyx_golden = True
                if dungeon.is_Calyx_Crimson:
                    ran_calyx_crimson = True
        # Double relic
        if self.config.Dungeon_NameAtDoubleRelic != 'do_not_participate' \
                and self.config.stored.DungeonDouble.relic > 0:
            logger.info('Run double relic')
            dungeon = DungeonList.find(self.config.Dungeon_NameAtDoubleRelic)
            self.running_double = True
            if self.dungeon_run(dungeon=dungeon, wave_limit=self.config.stored.DungeonDouble.relic):
                ran_cavern_of_corrosion = True
        self.running_double = False

        # Dungeon to clear all trailblaze power
        final = DungeonList.find(self.config.Dungeon_Name)

        # Run dungeon that required by daily quests
        # Calyx_Golden
        if KEYWORDS_DAILY_QUEST.Clear_Calyx_Golden_1_times in self.daily_quests \
                and self.config.DungeonDaily_CalyxGolden != 'do_not_achieve' \
                and not final.is_Calyx_Golden \
                and not ran_calyx_golden:
            logger.info('Run Calyx_Golden once')
            dungeon = DungeonList.find(self.config.DungeonDaily_CalyxGolden)
            self.dungeon_run(dungeon=dungeon, wave_limit=1)
        # Calyx_Crimson
        if KEYWORDS_DAILY_QUEST.Complete_Calyx_Crimson_1_time in self.daily_quests \
                and self.config.DungeonDaily_CalyxCrimson != 'do_not_achieve' \
                and not final.is_Calyx_Crimson \
                and not ran_calyx_crimson:
            logger.info('Run Calyx_Crimson once')
            dungeon = DungeonList.find(self.config.DungeonDaily_CalyxCrimson)
            self.dungeon_run(dungeon=dungeon, wave_limit=1)
        # Stagnant_Shadow
        if KEYWORDS_DAILY_QUEST.Clear_Stagnant_Shadow_1_times in self.daily_quests \
                and self.config.DungeonDaily_StagnantShadow != 'do_not_achieve' \
                and not final.is_Stagnant_Shadow:
            logger.info('Run Stagnant_Shadow once')
            dungeon = DungeonList.find(self.config.DungeonDaily_StagnantShadow)
            self.dungeon_run(dungeon=dungeon, wave_limit=1)
        # Cavern_of_Corrosion
        if KEYWORDS_DAILY_QUEST.Clear_Cavern_of_Corrosion_1_times in self.daily_quests \
                and self.config.DungeonDaily_CavernOfCorrosion != 'do_not_achieve' \
                and not final.is_Cavern_of_Corrosion \
                and not ran_cavern_of_corrosion:
            logger.info('Run Cavern_of_Corrosion once')
            dungeon = DungeonList.find(self.config.DungeonDaily_CavernOfCorrosion)
            self.dungeon_run(dungeon=dungeon, wave_limit=1)

        # Combat
        self.dungeon_run(final)
        self.delay_dungeon_task(final)

    def delay_dungeon_task(self, dungeon):
        if dungeon.is_Cavern_of_Corrosion:
            limit = 80
        elif dungeon.is_Echo_of_War:
            limit = 30
        else:
            limit = 60
        # Recover 1 trailbaze power each 6 minutes
        current = self.config.stored.TrailblazePower.value
        cover = max(limit - current, 0) * 6
        logger.info(f'Currently has {current} need {cover} minutes to reach {limit}')
        logger.attr('achieved_daily_quest', self.achieved_daily_quest)
        with self.config.multi_set():
            # Check battle pass
            quests = self.config.stored.BattlePassTodayQuest.load_quests()
            if KEYWORD_BATTLE_PASS_QUEST.Consume_1_Trailblaze_Power in quests:
                logger.info('Probably achieved battle pass quest Consume_1_Trailblaze_Power')
                if self.config.stored.BattlePassLevel.is_full():
                    logger.info('BattlePassLevel full, no task call')
                else:
                    self.config.task_call('BattlePass')
            # Check daily
            if self.achieved_daily_quest:
                self.config.task_call('DailyQuest')
            # Delay tasks
            future = now() + timedelta(minutes=cover)
            for task in ['Dungeon', 'Weekly']:
                next_run = self.config.cross_get(keys=f'{task}.Scheduler.NextRun', default=DEFAULT_TIME)
                if future > next_run:
                    logger.info(f"Delay task `{task}` to {future}")
                    self.config.cross_set(keys=f'{task}.Scheduler.NextRun', value=future)

        self.config.task_stop()

    def handle_destructible_around_blaze(self):
        """
        Stagnant_Shadow_Blaze has a destructible object nearby, attacks are aimed at it first
        so destroy it first

        Returns:
            bool: If handled.

        Pages:
            in: COMBAT_PREPARE
            out: page_main, map position changed if handled
        """
        logger.hr('Handle destructible around blaze')
        self.combat_exit()
        # Check if there's a front sight at bottom-left corner
        area = area_offset((-50, -150, 0, 0), offset=self.config.ASSETS_RESOLUTION)

        skip_first_screenshot = True
        self.map_A_timer.reset()
        handled = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.image_color_count(area, color=(48, 170, 204), threshold=221, count=50):
                logger.info(f'Found destructible object')
                if self.handle_map_A():
                    handled = True
                    continue
            else:
                logger.info(f'No destructible object')
                if not handled:
                    break
                if self.map_A_timer.reached():
                    break

        return handled

    def require_compulsory_support(self) -> bool:
        require = False

        if not self.config.stored.DailyActivity.is_full():
            if KEYWORDS_DAILY_QUEST.Obtain_victory_in_combat_with_support_characters_1_time \
                    in self.daily_quests:
                require = True

        logger.attr('called_daily_support', self.called_daily_support)
        if self.called_daily_support:
            require = False

        # Not required, cause any dungeon run will achieve the quest
        logger.attr('DungeonSupport_Use', self.config.DungeonSupport_Use)
        if self.config.DungeonSupport_Use == 'always_use':
            require = False

        logger.attr('Require compulsory support', require)
        return require
