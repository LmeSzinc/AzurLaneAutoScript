from module.campaign.run import CampaignRun


RECORD_SINCE = (0,)
CAMPAIGN_NAME = ['a1', 'a2', 'a3', 'b1', 'b2', 'b3']


class CampaignAB(CampaignRun):
    def run(self, name, folder='campaign_main'):
        name = name.lower()
        option = ('EventABRecord', name)
        if not self.config.record_executed_since(option=option, since=RECORD_SINCE):
            super().run(name=name, folder=folder)
            self.config.record_save(option=option)

    def run_event_daily(self):
        for name in CAMPAIGN_NAME:
            self.run(name=name, folder=self.config.EVENT_NAME_AB)
