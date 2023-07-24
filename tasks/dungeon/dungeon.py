from module.base.utils import area_offset
from module.logger import logger
from tasks.combat.combat import Combat
from tasks.dungeon.event import DungeonEvent
from tasks.dungeon.keywords import DungeonList, KEYWORDS_DUNGEON_LIST, KEYWORDS_DUNGEON_TAB
from tasks.dungeon.ui import DungeonUI


class Dungeon(DungeonUI, DungeonEvent, Combat):
    def run(self, dungeon: DungeonList = None, team: int = None, use_support: str = None, is_daily: bool = False,
            support_character: str = None):
        if dungeon is None:
            dungeon = DungeonList.find(self.config.Dungeon_Name)
        if team is None:
            team = self.config.Dungeon_Team
        if use_support is None:
            use_support = self.config.Dungeon_Support
        if support_character is None:
            support_character = self.config.Dungeon_SupportCharacter if use_support == "always_use" or use_support == "when_daily" and is_daily else None

        # UI switches
        switched = self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
        if not switched:
            # Nav must at top, reset nav states
            self.ui_goto_main()
            self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)

        # Check double events
        if self.config.Dungeon_NameAtDoubleCalyx != 'do_not_participate' and self.has_double_calyx_event():
            calyx = DungeonList.find(self.config.Dungeon_NameAtDoubleCalyx)
            self._dungeon_nav_goto(calyx)
            if remain := self.get_double_event_remain():
                self.dungeon_goto(calyx)
                if self.combat(team, wave_limit=remain, support_character=support_character):
                    self.delay_dungeon_task(calyx)
                self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)

        # Combat
        self.dungeon_goto(dungeon)

        if dungeon == KEYWORDS_DUNGEON_LIST.Stagnant_Shadow_Blaze:
            if self.handle_destructible_around_blaze():
                self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
                self.dungeon_goto(dungeon)

        self.combat(team=team, support_character=support_character)
        self.delay_dungeon_task(dungeon)

    def delay_dungeon_task(self, dungeon):
        if dungeon.is_Cavern_of_Corrosion:
            limit = 80
        else:
            limit = 60
        # Recover 1 trailbaze power each 6 minutes
        cover = max(limit - self.state.TrailblazePower, 0) * 6
        logger.info(f'Currently has {self.state.TrailblazePower} need {cover} minutes to reach {limit}')
        self.config.task_delay(minute=cover)

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
        self._map_A_timer.reset()
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
                if self._map_A_timer.reached():
                    break

        return handled
