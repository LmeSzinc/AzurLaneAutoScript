from module.logger import logger
from tasks.combat.combat import Combat
from tasks.dungeon.keywords import DungeonList
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
