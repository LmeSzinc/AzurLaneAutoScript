from module.handler.assets import *
from module.handler.info_bar import InfoBarHandler
from module.logger import logger


class UrgentCommissionHandler(InfoBarHandler):
    def handle_urgent_commission(self, save_get_items=None):
        """
        Args:
            save_get_items (bool):

        Returns:
            bool:
        """
        if save_get_items is None:
            save_get_items = self.config.ENABLE_SAVE_GET_ITEMS

        appear = self.appear(GET_MISSION, offset=True, interval=2)
        if appear:
            logger.info('Get urgent commission')
            if save_get_items:
                self.handle_info_bar()
                self.device.save_screenshot('get_mission')
            self.device.click(GET_MISSION)
        return appear
