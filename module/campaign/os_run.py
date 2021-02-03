from module.os.config import OSConfig
from module.os.map import OSMap
from module.os.map_operation import OSMapOperation


class OSCampaignRun(OSMapOperation):
    campaign: OSMap

    def load_campaign(self):
        config = self.config.merge(OSConfig())
        self.campaign = OSMap(config=config, device=self.device)

    def run(self):
        self.load_campaign()
        self.campaign.run()
