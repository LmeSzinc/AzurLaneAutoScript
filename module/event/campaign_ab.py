import os

from module.config.config import TaskEnd
from module.config.utils import get_server_last_update
from module.event.base import STAGE_FILTER, EventBase, EventStage
from module.logger import logger


class CampaignAB(EventBase):
    def run(self, *args, **kwargs):
        # Filter map files
        stages = [EventStage(file) for file in os.listdir(f'./campaign/{self.config.Campaign_Event}')]
        stages = self.convert_stages(stages)
        logger.attr('Stage', [str(stage) for stage in stages])
        logger.attr('StageFilter', self.config.EventAb_StageFilter)
        STAGE_FILTER.load(self.config.EventAb_StageFilter)
        self.convert_stages(STAGE_FILTER)
        stages = [str(stage) for stage in STAGE_FILTER.apply(stages)]
        logger.attr('Filter sort', ' > '.join(stages))

        if not stages:
            logger.warning('No stage satisfy current filter')
            self.config.Scheduler_Enable = False
            self.config.task_stop()

        # Start from last stage
        logger.info(f'LastStage {self.config.EventAb_LastStage}, recorded at {self.config.Scheduler_NextRun}')
        if get_server_last_update(self.config.Scheduler_ServerUpdate) >= self.config.Scheduler_NextRun:
            logger.info('LastStage outdated, reset')
            self.config.EventAb_LastStage = 0
        else:
            last = str(self.config.EventAb_LastStage).lower()
            last = self.convert_stages(last)
            if last in stages:
                stages = stages[stages.index(last) + 1:]
                logger.attr('Filter sort', ' > '.join(stages))
            else:
                logger.info('Start from the beginning')

        # Run
        for stage in stages:
            stage = str(stage)
            try:
                super().run(name=stage, folder=self.config.Campaign_Event, total=1)
            except TaskEnd:
                # Catch task switch
                pass
            if self.run_count > 0:
                with self.config.multi_set():
                    self.config.EventAb_LastStage = stage
                    self.config.task_delay(minute=0)
            else:
                self.config.task_stop()
            if self.config.task_switched():
                self.config.task_stop()

        # Scheduler
        self.config.task_delay(server_update=True)
