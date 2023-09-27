from module.alas import AzurLaneAutoScript
from module.logger import logger


class StarRailCopilot(AzurLaneAutoScript):
    def restart(self):
        from tasks.login.login import Login
        Login(self.config, device=self.device).app_restart()

    def start(self):
        from tasks.login.login import Login
        Login(self.config, device=self.device).app_start()

    def goto_main(self):
        from tasks.login.login import Login
        from tasks.base.ui import UI
        if self.device.app_is_running():
            logger.info('App is already running, goto main page')
            UI(self.config, device=self.device).ui_goto_main()
        else:
            logger.info('App is not running, start app and goto main page')
            Login(self.config, device=self.device).app_start()
            UI(self.config, device=self.device).ui_goto_main()

    def dungeon(self):
        from tasks.dungeon.dungeon import Dungeon
        Dungeon(config=self.config, device=self.device).run()

    def weekly(self):
        from tasks.dungeon.weekly import WeeklyDungeon
        WeeklyDungeon(config=self.config, device=self.device).run()

    def daily_quest(self):
        from tasks.daily.daily_quest import DailyQuestUI
        DailyQuestUI(config=self.config, device=self.device).run()

    def battle_pass(self):
        from tasks.battle_pass.battle_pass import BattlePassUI
        BattlePassUI(config=self.config, device=self.device).run()

    def assignment(self):
        from tasks.assignment.assignment import Assignment
        Assignment(config=self.config, device=self.device).run()

    def data_update(self):
        from tasks.item.data_update import DataUpdate
        DataUpdate(config=self.config, device=self.device).run()


if __name__ == '__main__':
    src = StarRailCopilot('src')
    src.loop()
