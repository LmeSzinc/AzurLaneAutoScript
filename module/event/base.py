import re

from module.base.filter import Filter
from module.campaign.run import CampaignRun

STAGE_FILTER = Filter(regex=re.compile("^(.*?)$"), attr=("stage",))


class EventStage:
    def __init__(self, filename):
        self.filename = filename
        self.stage = "unknown"
        if filename[-3:] == ".py":
            self.stage = filename[:-3]

    def __str__(self):
        return self.stage

    def __eq__(self, other):
        return str(self) == str(other)


class EventBase(CampaignRun):
    def load_campaign(self, *args, **kwargs):
        super().load_campaign(*args, **kwargs)
        self.campaign.config.temporary(MAP_IS_ONE_TIME_STAGE=False)
