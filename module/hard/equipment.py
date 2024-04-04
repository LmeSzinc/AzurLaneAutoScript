from module.equipment.equipment_change import EquipmentChange
from module.hard.assets import *
from module.map.assets import *


class HardEquipment(EquipmentChange):
    def equip_take_on_all(self):
        if self.config.FLEET_HARD_EQUIPMENT is None:
            return False
        if self.equipment_has_take_on:
            return False

        enter = EQUIP_ENTER_1 if self.config.Hard_HardFleet == 1 else EQUIP_ENTER_2
        self.equip_take_on_all_preset(enter=enter, long_click=True, out=FLEET_PREPARATION,
                                      preset_record=self.config.FLEET_HARD_EQUIPMENT)
        return True

    def equip_take_off_all(self, enter=None, long_click=True, out=FLEET_PREPARATION):
        if self.config.FLEET_HARD_EQUIPMENT is None:
            return False
        if not self.equipment_has_take_on:
            return False

        enter = EQUIP_ENTER_1 if self.config.Hard_HardFleet == 1 else EQUIP_ENTER_2
        super().equip_take_off_all(enter=enter, long_click=long_click, out=out)
        return True
