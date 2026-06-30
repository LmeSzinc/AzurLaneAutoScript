from module.campaign.campaign_base import CampaignBase as CampaignBase_


class CampaignBase(CampaignBase_):
    def campaign_set_chapter_sp(self, chapter, mode='normal'):
        # SP event but has an `event` UI
        from module.logger import logger
        logger.info('Set chapter SP')
        if chapter in ['sp', 'sp_sp']:
            self.ui_goto_event()
            self.campaign_ensure_chapter(chapter)
            return True
        else:
            return False

    @staticmethod
    def _campaign_separate_name(name):
        if name in ['esp', 'sp']:
            return 'sp_sp', '2'
        if name in ['ex']:
            return 'sp_ex', '3'
        return CampaignBase_._campaign_separate_name(name)

    def campaign_get_entrance(self, name):
        if name == 'sp':
            name = 'esp'
        return super().campaign_get_entrance(name)

    @staticmethod
    def _campaign_get_chapter_index(name):
        if name in ['sp_sp']:
            return 2
        if name in ['sp_ex']:
            return 3
        return CampaignBase_._campaign_get_chapter_index(name)