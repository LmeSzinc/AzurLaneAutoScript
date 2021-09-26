from module.os.config import OSConfig
from module.os.map_operation import OSMapOperation
from module.os.operation_siren import OperationSiren
from module.os_handler.action_point import ActionPointLimit


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

    def opsi_explore(self):
        self.load_campaign()
        try:
            self.campaign.os_explore()
        except ActionPointLimit:
            self.campaign.config.task_delay(minute=360)

    def opsi_daily(self):
        self.load_campaign()
        try:
            self.campaign.os_daily()
        except ActionPointLimit:
            self.campaign.config.task_delay(minute=360)

    def opsi_meowfficer_farming(self):
        self.load_campaign()
        try:
            self.campaign.os_meowfficer_farming()
        except ActionPointLimit:
            self.campaign.config.task_delay(server_update=True)

    def opsi_obscure(self):
        self.load_campaign()
        try:
            self.campaign.os_obscure()
        except ActionPointLimit:
            self.campaign.config.task_delay(minute=360)
