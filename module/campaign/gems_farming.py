from module.campaign.run import CampaignRun
from module.combat.level import LevelOcr
from module.equipment.assets import *
from module.equipment.fleet_equipment import OCR_FLEET_INDEX
from module.retire.dock import *
from module.ui.page import page_fleet
from module.logger import logger
from module.config.config import AzurLaneConfig
from module.device.device import Device

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

    def _ship_change_confirm(self, point, offset=(30, 30)):

        self.dock_select_one(Button(button=(
            point[0], point[1], point[0]+offset[0], point[1]+offset[1]), color=None, area=None))
        self.dock_filter_set_faster()
        self.dock_select_confirm(check_button=page_fleet.check_button)

    def get_common_rarity_cv(self):
        """
        Returns:
            Point:
        """
        # TODO use alConfig
        sim, point = TEMPLATE_BOGUE.match_result(self.device.screenshot())

        if sim > SIM_VALUE:
            return point

        for _ in range(0, 15):
            self._equipment_swipe()

            sim, point = TEMPLATE_BOGUE.match_result(self.device.screenshot())

            if sim > SIM_VALUE:
                return point

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
    config = AzurLaneConfig('alas_cn')
    az = GemsFarming(config, Device(config=config))
    az.device.screenshot()
    az.flagship_change()
