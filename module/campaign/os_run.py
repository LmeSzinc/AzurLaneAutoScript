from module.os.config import OSConfig
from module.os.map_operation import OSMapOperation
from module.os.operation_siren import OperationSiren


class OSCampaignRun(OSMapOperation):
    campaign: OperationSiren

    campaign_loaded = False

    def load_campaign(self):
        if self.campaign_loaded:
            return False

        config = self.config.merge(OSConfig())
        self.campaign = OperationSiren(config=config, device=self.device)
        self.campaign.os_init()

        self.campaign_loaded = True
        return True

    def run(self):
        self.load_campaign()
        self.campaign.run()

    def run_operation_siren(self):
        self.load_campaign()
        self.campaign.operation_siren()
