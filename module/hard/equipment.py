from module.equipment.equipment import Equipment
from module.hard.assets import *
from module.map.assets import *


class HardEquipment(Equipment):
    def equipment_take_on(self):
        if self.config.FLEET_HARD_EQUIPMENT is None:
            return False
        if self.equipment_has_take_on:
            return False

        enter = EQUIP_ENTER_1 if self.config.FLEET_HARD == 1 else EQUIP_ENTER_2
        super().equipment_take_on(
            enter=enter, out=FLEET_PREPARATION, fleet=self.config.FLEET_HARD_EQUIPMENT
        )
        return True

    def equipment_take_off(self):
        if self.config.FLEET_HARD_EQUIPMENT is None:
            return False
        if not self.equipment_has_take_on:
            return False

        enter = EQUIP_ENTER_1 if self.config.FLEET_HARD == 1 else EQUIP_ENTER_2
        super().equipment_take_off(
            enter=enter, out=FLEET_PREPARATION, fleet=self.config.FLEET_HARD_EQUIPMENT
        )
        return True
