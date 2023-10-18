from tasks.rogue.entry.entry import RogueEntry
from tasks.rogue.route.loader import RouteLoader


class RogueHandler(RouteLoader, RogueEntry):
    def rogue_once(self):
        """
        Do a complete rogue run.

        Pages:
            in: Any
            out: page_rogue, is_page_rogue_main()
        """
        self.rogue_world_enter(7)
        self.rogue_run()
        self.rogue_reward_claim()


if __name__ == '__main__':
    self = RogueHandler('src', task='Rogue')
    self.device.screenshot()
    self.rogue_once()
