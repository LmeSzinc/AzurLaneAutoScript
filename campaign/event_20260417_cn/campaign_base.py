from module.base.button import Button
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger

EVENT_ANIMATION = Button(area=(49, 229, 119, 400), color=(118, 215, 240), button=(49, 229, 119, 400),
                         name='EVENT_ANIMATION')


class CampaignBase(CampaignBase_):
    @staticmethod
    def _campaign_ocr_result_process(result):
        result = CampaignBase_._campaign_ocr_result_process(result)
        if result in ['ysp', 'usp', 'vsp']:
            result = 'sp'
        return result

    def is_event_animation(self):
        """
        Animation in events after cleared an enemy.

        Returns:
            bool: If animation appearing.
        """
        appear = self.appear(EVENT_ANIMATION)
        if appear:
            logger.info('DOA animation, waiting')
        return appear

    def event_animation_end(self):
        if not self.appear(EVENT_ANIMATION):
            return False
        # wait until EVENT_ANIMATION closed
        for _ in self.loop():
            if self.is_event_animation():
                continue
            break
        # now in_map
        return True
