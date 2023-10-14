from tasks.rogue.reward import RogueRewardHandler
from tasks.rogue.route.loader import RouteLoader


class RogueHandler(RouteLoader, RogueRewardHandler):
    def rogue_once(self):
        """
        Do a complete rogue run.

        Pages:
            in: page_rogue, is_page_rogue_main()
            out: page_rogue, is_page_rogue_main()
        """
        self.rogue_run()
        self.rogue_reward_claim()


if __name__ == '__main__':
    self = RogueHandler('src', task='Rogue')
    self.device.screenshot()
    self.rogue_once()
