from module.campaign.run import CampaignRun
from module.combat.level import LevelOcr
from module.equipment.assets import *
from module.equipment.fleet_equipment import OCR_FLEET_INDEX
from module.retire.dock import *
from module.ui.page import page_fleet
from module.logger import logger


class GemsFarming(CampaignRun):
    def flagship_change(self):
        self.ui_ensure(page_fleet)
        self.ui_ensure_index(self.config.FLEET_1, letter=OCR_FLEET_INDEX,
                             next_button=FLEET_NEXT, prev_button=FLEET_PREV, skip_first_screenshot=True)
        self.flagship_change_execute()

    def get_common_rarity_cv(self):
        """
        Returns:
            Button:
        """
        DOCK_SCROLL.total -= 14  # The bottom of the scroll is covered.
        if DOCK_SCROLL.appear(main=self):
            DOCK_SCROLL.set_bottom(main=self, skip_first_screenshot=True)
            grids = CARD_BOTTOM_LEVEL_GRIDS
        else:
            grids = CARD_LEVEL_GRIDS
        DOCK_SCROLL.total += 14  # Revert

        ocr = LevelOcr(grids.buttons, name='DOCK_LEVEL_OCR')
        list_level = ocr.ocr(self.device.image)
        for button, level in zip(grids.buttons, list_level):
            if level == 1:
                return button

        return None

    def flagship_change_execute(self):
        """
        Returns:
            bool: If success.

        Pages:
            in: page_fleet
            out: page_fleet
        """
        self.ui_click(FLEET_ENTER_FLAGSHIP,
                      appear_button=page_fleet.check_button, check_button=DOCK_CHECK, skip_first_screenshot=True)
        self.dock_filter_set_faster(index='cv', rarity='common', extra='enhanceable')

        self.device.screenshot()
        ship = self.get_common_rarity_cv()
        if ship is not None:
            self.dock_select_one(ship)
            self.dock_filter_set_faster()
            self.dock_select_confirm(check_button=page_fleet.check_button)
            logger.info('Change flagship success')
            return True
        else:
            logger.info('Change flagship failed, no CV in common rarity.')
            self.dock_filter_set_faster()
            self.ui_back(check_button=page_fleet.check_button)
            return False
