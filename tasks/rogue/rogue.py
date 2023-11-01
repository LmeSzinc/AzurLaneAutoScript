from module.logger import logger
from tasks.rogue.entry.entry import RogueEntry
from tasks.rogue.exception import RogueReachedWeeklyPointLimit, RogueTeamNotPrepared
from tasks.rogue.route.loader import RouteLoader


class Rogue(RouteLoader, RogueEntry):
    def rogue_once(self):
        """
        Do a complete rogue run.

        Pages:
            in: Any
            out: page_rogue, is_page_rogue_main()
        """
        try:
            self.rogue_world_enter()
        except RogueTeamNotPrepared:
            logger.error(f'Please prepare your team in {self.config.RogueWorld_World}')
            self.rogue_world_exit()
            return False
        except RogueReachedWeeklyPointLimit:
            logger.hr('Reached rogue weekly point limit')
            return False

        self.rogue_run()
        self.rogue_reward_claim()
        return True

    def run(self):
        while 1:
            # Run
            success = self.rogue_once()
            if not success:
                break

            # Scheduler
            if self.config.task_switched():
                self.config.task_stop()

        self.config.task_delay(server_update=True)


if __name__ == '__main__':
    self = Rogue('src', task='Rogue')
    self.device.screenshot()
    self.rogue_once()
