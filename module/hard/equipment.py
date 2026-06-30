from module.equipment.equipment_change import EquipmentChange
from module.hard.assets import *
from module.map.assets import *


class HardEquipment(EquipmentChange):

    def equipment_take_on(self):
        if self.config.FLEET_HARD_EQUIPMENT is None:
            return False
        if self.equipment_has_take_on:
            return False

        enter = EQUIP_ENTER_1 if self.config.Hard_HardFleet == 1 else EQUIP_ENTER_2
        self.fleet_equipment_take_on_preset(preset_record=self.config.FLEET_HARD_EQUIPMENT, enter=enter,
                                            long_click=True, out=FLEET_PREPARATION)
        return True

    def equipment_take_off(self):
        if self.config.FLEET_HARD_EQUIPMENT is None:
            return False
        if not self.equipment_has_take_on:
            return False

        enter = EQUIP_ENTER_1 if self.config.Hard_HardFleet == 1 else EQUIP_ENTER_2
        self.fleet_equipment_take_off(enter=enter, long_click=True, out=FLEET_PREPARATION)
        return True
