import os
from contextlib import suppress

from module.config.config import TaskEnd
from module.event.base import EventBase
from module.logger import logger


class CampaignSP(EventBase):
    def run(self, *args, **kwargs):
        if not os.path.exists(f"./campaign/{self.config.Campaign_Event}/sp.py"):
            logger.info(f"./campaign/{self.config.Campaign_Event}/sp.py not exists")
            logger.info("This event do not have SP, skip")
            self.config.Scheduler_Enable = False
            self.config.task_stop()

        # Catch task switch
        with suppress(TaskEnd):
            super().run(name=self.config.Campaign_Name, folder=self.config.Campaign_Event, total=1)
        if self.run_count > 0:
            self.config.task_delay(server_update=True)
        else:
            self.config.task_stop()
