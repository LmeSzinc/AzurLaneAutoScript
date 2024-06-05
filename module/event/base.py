import re

from module.base.filter import Filter
from module.campaign.run import CampaignRun

STAGE_FILTER = Filter(regex=re.compile('^(.*?)$'), attr=('stage',))


class EventStage:
    def __init__(self, filename):
        self.filename = filename
        self.stage = 'unknown'
        if filename[-3:] == '.py':
            self.stage = filename[:-3]

    def __str__(self):
        return self.stage

    def __eq__(self, other):
        return str(self) == str(other)


class EventBase(CampaignRun):
    def load_campaign(self, *args, **kwargs):
        super().load_campaign(*args, **kwargs)
        self.campaign.config.temporary(
            MAP_IS_ONE_TIME_STAGE=False
        )

    def convert_stages(self, stages):
        """
        Convert whatever input to the correct stage name
        """

        def convert(n):
            return self.handle_stage_name(n, folder=self.config.Campaign_Event)[0]

        if isinstance(stages, str):
            return convert(stages)
        if isinstance(stages, list):
            out = []
            for name in stages:
                if isinstance(name, EventStage):
                    name.stage = convert(name.stage)
                    out.append(name)
                elif isinstance(name, str):
                    out.append(convert(name))
                else:
                    out.append(name)
            return out
        if isinstance(stages, Filter):
            stages.filter = [[convert(selection[0])] for selection in stages.filter]
            return stages
        return stages
