from module.logger import logger
from tasks.rogue.entry.entry import RogueEntry
from tasks.rogue.exception import RogueTeamNotPrepared
from tasks.rogue.route.loader import RouteLoader


class RogueHandler(RouteLoader, RogueEntry):
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

        self.rogue_run()
        self.rogue_reward_claim()
        return True


if __name__ == '__main__':
    self = RogueHandler('src', task='Rogue')
    self.device.screenshot()
    self.rogue_once()
