from module.base.button import Button
from module.campaign.assets import (
    EVENT_20260417_DETAIL,
    EVENT_20260417_DETAIL_CHECK,
    EVENT_20260417_DETAIL_WHITE,
    EVENT_20260417_ENTRANCE,
    EVENT_20260417_PT_ICON,
)
from module.campaign.campaign_base import CampaignBase as CampaignBase_
from module.logger import logger
from module.ui.page import page_event

EVENT_ANIMATION = Button(area=(49, 229, 119, 400), color=(118, 215, 240), button=(49, 229, 119, 400),
                         name='EVENT_ANIMATION')


class CampaignBase(CampaignBase_):
    def ui_goto_event(self):
        if self.event_entrance_ensure(EVENT_20260417_PT_ICON, offset=(40, 20),
                                      log_name='EVENT_20260417'):
            if self.config.SERVER == 'tw':
                self.ui_goto(page_event)
            else:
                self.ui_goto_main()
                self.event_entrance_from_main(
                    EVENT_20260417_DETAIL, EVENT_20260417_DETAIL_WHITE, EVENT_20260417_DETAIL_CHECK,
                    EVENT_20260417_ENTRANCE, EVENT_20260417_PT_ICON, offset=(40, 20))
            return True

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
