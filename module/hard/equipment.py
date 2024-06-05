<<<<<<< HEAD
from module.equipment.equipment import Equipment
=======
from module.equipment.equipment_change import EquipmentChange
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
from module.hard.assets import *
from module.map.assets import *


<<<<<<< HEAD
class HardEquipment(Equipment):
=======
class HardEquipment(EquipmentChange):

>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
    def equipment_take_on(self):
        if self.config.FLEET_HARD_EQUIPMENT is None:
            return False
        if self.equipment_has_take_on:
            return False

<<<<<<< HEAD
        enter = EQUIP_ENTER_1 if self.config.FLEET_HARD == 1 else EQUIP_ENTER_2
        super().equipment_take_on(enter=enter, out=FLEET_PREPARATION, fleet=self.config.FLEET_HARD_EQUIPMENT)
=======
        enter = EQUIP_ENTER_1 if self.config.Hard_HardFleet == 1 else EQUIP_ENTER_2
        self.fleet_equipment_take_on_preset(preset_record=self.config.FLEET_HARD_EQUIPMENT, enter=enter,
                                            long_click=True, out=FLEET_PREPARATION)
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
        return True

    def equipment_take_off(self):
        if self.config.FLEET_HARD_EQUIPMENT is None:
            return False
        if not self.equipment_has_take_on:
            return False

<<<<<<< HEAD
        enter = EQUIP_ENTER_1 if self.config.FLEET_HARD == 1 else EQUIP_ENTER_2
        super().equipment_take_off(enter=enter, out=FLEET_PREPARATION, fleet=self.config.FLEET_HARD_EQUIPMENT)
=======
        enter = EQUIP_ENTER_1 if self.config.Hard_HardFleet == 1 else EQUIP_ENTER_2
        self.fleet_equipment_take_off(enter=enter, long_click=True, out=FLEET_PREPARATION)
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
        return True
