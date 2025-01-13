from ..campaign_war_archives.campaign_base import CampaignBase as CampaignBase_


class CampaignBase(CampaignBase_):
    def handle_clear_mode_config_cover(self):
        if super().handle_clear_mode_config_cover():
            self.config.MAP_SIREN_TEMPLATE = ['SS']
            self.config.MAP_HAS_SIREN = True
