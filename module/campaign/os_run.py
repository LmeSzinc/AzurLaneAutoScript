from module.config.utils import get_os_reset_remain
from module.logger import logger
from module.os.config import OSConfig
from module.os.map_operation import OSMapOperation
from module.os.operation_siren import OperationSiren
from module.os_handler.action_point import ActionPointLimit


class OSCampaignRun(OSMapOperation):
    def load_campaign(self, cls=OperationSiren):
        config = self.config.merge(OSConfig())
        campaign = cls(config=config, device=self.device)
        campaign.os_init()
        return campaign

    def opsi_explore(self):
        try:
            campaign = self.load_campaign()
            campaign.os_explore()
        except ActionPointLimit:
            self.config.opsi_task_delay(ap_limit=True)

    def opsi_shop(self):
        try:
            campaign = self.load_campaign()
            campaign.os_shop()
        except ActionPointLimit:
            self.config.opsi_task_delay(ap_limit=True)

    def opsi_voucher(self):
        try:
            campaign = self.load_campaign()
            campaign.os_voucher()
        except ActionPointLimit:
            self.config.opsi_task_delay(ap_limit=True)

    def opsi_daily(self):
        try:
            campaign = self.load_campaign()
            campaign.os_daily()
        except ActionPointLimit:
            self.config.opsi_task_delay(ap_limit=True)

    def opsi_meowfficer_farming(self):
        try:
            campaign = self.load_campaign()
            campaign.os_meowfficer_farming()
        except ActionPointLimit:
            if get_os_reset_remain() > 0:
                self.config.task_delay(server_update=True)
                self.config.task_call('Reward')
                if self.config.is_task_enabled('OpsiHazard1Leveling') \
                        and self.get_yellow_coins() > self.config.OS_CL1_YELLOW_COINS_PRESERVE:
                    self.config.task_call('OpsiHazard1Leveling')
            else:
                logger.info('Just less than 1 day to OpSi reset, delay 2.5 hours')
                self.config.task_delay(minute=150, server_update=True)

    def opsi_hazard1_leveling(self):
        try:
            campaign = self.load_campaign()
            campaign.os_hazard1_leveling()
        except ActionPointLimit:
            self.config.task_delay(server_update=True)

    def opsi_obscure(self):
        try:
            campaign = self.load_campaign()
            campaign.os_obscure()
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
            campaign = self.load_campaign()
            campaign.clear_month_boss()
        except ActionPointLimit:
            self.config.opsi_task_delay(ap_limit=True)

    def opsi_abyssal(self):
        try:
            campaign = self.load_campaign()
            campaign.os_abyssal()
        except ActionPointLimit:
            self.config.opsi_task_delay(ap_limit=True)

    def opsi_archive(self):
        try:
            campaign = self.load_campaign()
            campaign.os_archive()
        except ActionPointLimit:
            self.config.opsi_task_delay(ap_limit=True)

    def opsi_stronghold(self):
        try:
            campaign = self.load_campaign()
            campaign.os_stronghold()
        except ActionPointLimit:
            self.config.opsi_task_delay(ap_limit=True)

    def opsi_cross_month(self):
        campaign = self.load_campaign()
        try:
            campaign.os_cross_month()
        except ActionPointLimit:
            campaign.os_cross_month_end()
