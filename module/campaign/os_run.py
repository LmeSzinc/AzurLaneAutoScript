from module.config.utils import get_os_reset_remain
from module.logger import logger
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
        try:
            self.load_campaign()
            self.campaign.os_explore()
        except ActionPointLimit:
            self.config.opsi_task_delay(ap_limit=True)

    def opsi_shop(self):
        try:
            self.load_campaign()
            self.campaign.os_shop()
        except ActionPointLimit:
            self.config.opsi_task_delay(ap_limit=True)

    def opsi_voucher(self):
        try:
            self.load_campaign()
            self.campaign.os_voucher()
        except ActionPointLimit:
            self.config.opsi_task_delay(ap_limit=True)

    def opsi_daily(self):
        try:
            self.load_campaign()
            self.campaign.os_daily()
        except ActionPointLimit:
            self.config.opsi_task_delay(ap_limit=True)

    def opsi_meowfficer_farming(self):
        try:
            self.load_campaign()
            self.campaign.os_check_leveling()
            self.campaign.os_meowfficer_farming()
        except ActionPointLimit:
            if get_os_reset_remain() > 0:
                self.config.task_delay(server_update=True)
                self.config.task_call('Reward')
            else:
                logger.info('Just less than 1 day to OpSi reset, delay 2.5 hours')
                self.config.task_delay(minute=150, server_update=True)

    def opsi_hazard1_leveling(self):
        try:
            self.load_campaign()
            self.campaign.os_check_leveling()
            self.campaign.os_hazard1_leveling()
        except ActionPointLimit:
            self.config.task_delay(server_update=True)

    def opsi_obscure(self):
        try:
            self.load_campaign()
            self.campaign.os_obscure()
        except ActionPointLimit:
            self.config.opsi_task_delay(ap_limit=True)

    def opsi_month_boss(self):
        if self.config.SERVER in ['tw']:
            logger.info(f'OpsiMonthBoss is not supported in {self.config.SERVER},'
                        ' please contact server maintainers')
            self.config.task_delay(server_update=True)
            self.config.task_stop()
            return
        try:
            self.load_campaign()
            self.campaign.clear_month_boss()
        except ActionPointLimit:
            self.config.opsi_task_delay(ap_limit=True)

    def opsi_abyssal(self):
        try:
            self.load_campaign()
            self.campaign.os_abyssal()
        except ActionPointLimit:
            self.config.opsi_task_delay(ap_limit=True)

    def opsi_archive(self):
        try:
            self.load_campaign()
            self.campaign.os_archive()
        except ActionPointLimit:
            self.config.opsi_task_delay(ap_limit=True)

    def opsi_stronghold(self):
        try:
            self.load_campaign()
            self.campaign.os_stronghold()
        except ActionPointLimit:
            self.config.opsi_task_delay(ap_limit=True)

    def opsi_cross_month(self):
        try:
            self.load_campaign()
            self.campaign.os_cross_month()
        except ActionPointLimit:
            self.campaign.os_cross_month_end()
