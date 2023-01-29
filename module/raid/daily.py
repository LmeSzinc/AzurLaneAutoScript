import re

from module.base.filter import Filter
from module.logger import logger
from module.raid.run import RaidRun
from module.reward.reward import Reward
from module.ui.page import page_raid


class RaidStage:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


STAGES = ['easy', 'normal', 'hard']
STAGE_FILTER = Filter(regex=re.compile('(\w+)'), attr=['name'])


class RaidDaily(RaidRun):
    def run(self, name=''):
        """
        Args:
            name (str): Raid name, such as 'raid_20200624'
        """
        name = name if name else self.config.Campaign_Event
        stages = [RaidStage(name) for name in STAGES]
        STAGE_FILTER.load(self.config.RaidDaily_StageFilter)
        stages = STAGE_FILTER.apply(stages)

        self.ui_ensure(page_raid)

        for stage in stages:
            mode = stage.name
            logger.hr(mode, level=1)
            for _ in range(15):
                remain = self.get_remain(mode=mode)
                if remain <= 0:
                    break
                super().run(name=name, mode=mode, total=1)

        # If configured for EX, always do last
        # So does not use stage filtering
        stages = [stage.lower().strip()\
            for stage in\
            self.config.RaidDaily_StageFilter.split('>')]
        if 'ex' in stages:
            # Collect raid tickets from clearing
            # any difficulty 5+ and 10+ times
            self.ui_goto_main()
            Reward(self.config, self.device).reward_mission(
                   daily=self.config.Reward_CollectMission,
                   weekly=False)

            logger.hr('ex', level=1)
            super().run(name=name, mode='ex', total=self.get_remain('ex'))

        self.config.task_delay(server_update=True)
