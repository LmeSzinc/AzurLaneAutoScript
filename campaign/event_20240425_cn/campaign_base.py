from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger


class CampaignBase(CampaignBase_):
    STAGE_INCREASE = [
        """
        SP1 > SP2 > SP3 > SP4 > SP5
        """,
        """
        ISP1 > ISP2 > ISP3 > ISP4 > ISP5 > ISP6
        """,
    ]

    def campaign_set_chapter_event(self, chapter, mode='normal'):
        self.ui_goto_event()
        self.campaign_ensure_chapter(chapter)
        return True

    def _campaign_get_chapter_index(self, name):
        """
        Args:
            name (str, int):

        Returns:
            int
        """
        if name == 'sp':
            return 1
        if name == 'isp':
            return 2
        if name == 'ex_sp':
            return 3
        if name == 'ex_ex':
            return 4

        return super(CampaignBase, CampaignBase)._campaign_get_chapter_index(name)

    @staticmethod
    def _campaign_ocr_result_process(result):
        result = CampaignBase_._campaign_ocr_result_process(result)
        if result in ['usp', 'iisp', 'ijsp', 'jjsp']:
            result = 'sp'
        return result

    def is_event_animation(self):
        # Blue banner
        if self.image_color_count((1180, 285, 1280, 335), color=(140, 215, 255), count=1000):
            logger.info('Live start!')
            return True
        # Red-black banner with white bottom border
        if self.image_color_count((1193, 428, 1273, 436), color=(255, 255, 255), count=500):
            logger.info('Live start!')
            return True

        return False
