from module.base.utils import area_offset
from module.logger import logger
from tasks.combat.combat import Combat
from tasks.dungeon.keywords import DungeonList, KEYWORDS_DUNGEON_LIST
from tasks.dungeon.ui import DungeonUI


class Dungeon(DungeonUI, Combat):
    def run(self, dungeon: DungeonList = None, team: int = None):
        if dungeon is None:
            dungeon = DungeonList.find(self.config.Dungeon_Name)
        if team is None:
            team = self.config.Dungeon_Team

        # Run
        if not self.dungeon_goto(dungeon):
            logger.error('Please check you dungeon settings')
            self.config.Scheduler_Enable = False
            self.config.task_stop()

        if dungeon == KEYWORDS_DUNGEON_LIST.Stagnant_Shadow_Blaze:
            if self.handle_destructible_around_blaze():
                self.dungeon_goto(dungeon)

        self.combat(team)

        # Scheduler
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
