from module.equipment.fleet_equipment import FleetEquipment
from module.logger import logger
from module.ui.page import page_main


class DailyEquipment(FleetEquipment):

    def fleet_enter(self, fleet=None):
        fleet = self.config.FLEET_DAILY
        if isinstance(fleet, list):
            logger.info(f'Multiple daily fleets are set, change equipment only for the first one. fleet: {fleet}')
            fleet = fleet[0]
        super().fleet_enter(fleet)

    def equipment_take_on(self):
        if self.config.FLEET_DAILY_EQUIPMENT is None:
            return False
        if self.equipment_has_take_on:
            return False

        self.fleet_enter()
        self.fleet_equipment_take_on_preset(preset_record=self.config.FLEET_DAILY_EQUIPMENT)
        self.ui_back(page_main.check_button)
        self.equipment_has_take_on = True
        self.device.sleep(1)
        return True

    def equipment_take_off(self):
        if self.config.FLEET_DAILY_EQUIPMENT is None:
            return False
        if not self.equipment_has_take_on:
            return False

        self.fleet_enter()
        self.fleet_equipment_take_off()
        self.ui_back(page_main.check_button)
        self.equipment_has_take_on = False
        self.device.sleep(1)
        return True
