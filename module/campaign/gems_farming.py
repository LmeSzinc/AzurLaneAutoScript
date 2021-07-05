from module.campaign.run import CampaignRun
from module.combat.level import LevelOcr
from module.equipment.assets import *
from module.equipment.fleet_equipment import OCR_FLEET_INDEX
from module.retire.dock import *
from module.ui.page import page_fleet
from module.logger import logger


from module.equipment.equipment_change import EquipmentChange

SIM_VALUE = 0.95


class GemsFarming(CampaignRun, EquipmentChange):

    def _fleet_detail_enter(self):
        self.ui_ensure(page_fleet)
        self.ui_ensure_index(self.config.FLEET_1, letter=OCR_FLEET_INDEX,
                             next_button=FLEET_NEXT, prev_button=FLEET_PREV)

    def _ship_detail_enter(self, button):
        self._fleet_detail_enter()
        self.equip_enter(button)

    def flagship_change(self):
        self._ship_detail_enter(FLEET_ENTER_FLAGSHIP)
        self.record_equipment()
        self._equip_take_off_one()

        self._fleet_detail_enter()

        self.flagship_change_execute()

        self._ship_detail_enter(FLEET_ENTER_FLAGSHIP)
        self._equip_take_off_one()

        self.equipment_take_on()

    def _ship_change_confirm(self, button):

        self.dock_select_one(button)
        self.dock_filter_set_faster()
        self.dock_select_confirm(check_button=page_fleet.check_button)

    def get_common_rarity_cv(self):
        """
        Returns:
            Button:
        """
        DOCK_SCROLL.total -= 14  # The bottom of the scroll is covered.
        if DOCK_SCROLL.appear(main=self):
            DOCK_SCROLL.set_bottom(main=self, skip_first_screenshot=True)
            level_grids = CARD_BOTTOM_LEVEL_GRIDS
            card_grids = CARD_BOTTOM_GRIDS
        else:
            level_grids = CARD_LEVEL_GRIDS
            card_grids = CARD_GRIDS
        DOCK_SCROLL.total += 14  # Revert


        ocr = LevelOcr(level_grids.buttons, name='DOCK_LEVEL_OCR')
        list_level = ocr.ocr(self.device.image)

        for button, level in zip(card_grids.buttons, list_level):
            if level == 1:
                template = globals()[f'TEMPLATE_{self.config.COMMON_CV_NAME}']
                if template.match(self.device.image.crop(button.area), similarity=SIM_VALUE):
                    return button

        return None

    def get_common_rarity_dd(self):
        """
        Returns:
            Button:
        """
        DOCK_SCROLL.total -= 14  # The bottom of the scroll is covered.
        if DOCK_SCROLL.appear(main=self):
            DOCK_SCROLL.set_bottom(main=self, skip_first_screenshot=True)
            level_grids = CARD_BOTTOM_LEVEL_GRIDS
            card_grids = CARD_BOTTOM_GRIDS
        else:
            level_grids = CARD_LEVEL_GRIDS
            card_grids = CARD_GRIDS
        DOCK_SCROLL.total += 14  # Revert

        if DOCK_SCROLL.appear(main=self):
            DOCK_SCROLL.set_bottom(main=self, skip_first_screenshot=True)
            emotion_grids = CARD_BOTTOM_EMOTION_GRIDS
        else:
            emotion_grids = CARD_EMOTION_GRIDS
        DOCK_SCROLL.total += 14  # Revert


        ocr = LevelOcr(level_grids.buttons, name='DOCK_LEVEL_OCR')
        list_level = ocr.ocr(self.device.image)
        print(list_level)

        for button, level in zip(card_grids.buttons, list_level):
            if level == 1:
                self.device.image.crop(button.area).show()
                template = globals()[f'TEMPLATE_{self.config.COMMON_CV_NAME}']
                sim, _ = template.match_result(self.device.image.crop(button.area))
                print(sim)
                if template.match(self.device.image.crop(button.area), similarity=SIM_VALUE):
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
        self.dock_filter_set_faster(
            index='cv', rarity='common', extra='enhanceable')

        self.device.screenshot()
        ship = self.get_common_rarity_cv()
        if ship is not None:
            self._ship_change_confirm(ship)

            logger.info('Change flagship success')
            return True
        else:
            logger.info('Change flagship failed, no CV in common rarity.')
            self.dock_filter_set_faster()
            self.ui_back(check_button=page_fleet.check_button)
            return False


if __name__ == '__main__':
    from module.config.config import AzurLaneConfig
    from module.device.device import Device
    config = AzurLaneConfig('alas_cn')
    az = GemsFarming(config, Device(config=config))
    az.device.screenshot()
    az.flagship_change()
