from module.campaign.campaign_event import CampaignEvent
from module.exception import ScriptEnd, ScriptError
from module.logger import logger
from module.raid.raid import OilExhausted, Raid
from module.ui.page import page_raid


class RaidRun(Raid, CampaignEvent):
    run_count: int
    run_limit: int

    def triggered_stop_condition(self):
        """
        Returns:
            bool: If triggered a stop condition.
        """
        # Run count limit
        if self.run_limit and self.config.StopCondition_RunCount <= 0:
            logger.hr('Triggered stop condition: Run count')
            self.config.StopCondition_RunCount = 0
            self.config.Scheduler_Enable = False
            return True

        return False

    def run(self, name='', mode='', total=0):
        """
        Args:
            name (str): Raid name, such as 'raid_20200624'
            mode (str): Raid mode, such as 'hard', 'normal', 'easy'
            total (int): Total run count
        """
        name = name if name else self.config.Campaign_Event
        mode = mode if mode else self.config.Raid_Mode
        if not name or not mode:
            raise ScriptError(f'RaidRun arguments unfilled. name={name}, mode={mode}')

        self.run_count = 0
        self.run_limit = self.config.StopCondition_RunCount
        while 1:
            # End
            if total and self.run_count == total:
                break
            if self.event_time_limit_triggered():
                self.config.task_stop()

            # Log
            logger.hr(f'{name}_{mode}', level=2)
            if self.config.StopCondition_RunCount > 0:
                logger.info(f'Count remain: {self.config.StopCondition_RunCount}')
            else:
                logger.info(f'Count: {self.run_count}')

            # End
            if self.triggered_stop_condition():
                break

            # UI ensure
            self.ui_ensure(page_raid)

            # Run
            try:
                self.raid_execute_once(mode=mode, raid=name)
            except OilExhausted:
                logger.hr('Triggered stop condition: Oil limit')
                self.config.task_delay(minute=(120, 240))
                break
            except ScriptEnd as e:
                logger.hr('Script end')
                logger.info(str(e))
                break

            # After run
            self.run_count += 1
            if self.config.StopCondition_RunCount:
                self.config.StopCondition_RunCount -= 1
            # End
            if self.triggered_stop_condition():
                break
            # Scheduler
            if self.config.task_switched():
                self.config.task_stop()
