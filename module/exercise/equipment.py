from module.base.timer import Timer
from module.combat.assets import BATTLE_PREPARATION
from module.equipment.equipment_change import EquipmentChange
from module.exercise.assets import *


class ExerciseEquipment(EquipmentChange):
    def _active_edit(self):
        timer = Timer(5)
        while 1:
            self.device.screenshot()

            if timer.reached() and self.appear_then_click(EQUIP_EDIT_INACTIVE):
                timer.reset()

            # End
            if self.appear(EQUIP_EDIT_ACTIVE):
                self.device.sleep((0.2, 0.3))
                break

    def _inactive_edit(self):
        timer = Timer(5)
        while 1:
            self.device.screenshot()

            if timer.reached() and self.appear_then_click(EQUIP_EDIT_ACTIVE):
                timer.reset()

            # End
            if self.appear(EQUIP_EDIT_INACTIVE):
                self.device.sleep((0.2, 0.3))
                break

    def equipment_take_on(self):
        self._active_edit()
        self.fleet_equipment_take_on_preset(preset_record=self.config.EXERCISE_FLEET_EQUIPMENT, enter=EQUIP_ENTER,
                                            long_click=True, out=BATTLE_PREPARATION)
        self._inactive_edit()

    def equipment_take_off(self):
        self._active_edit()
        self.fleet_equipment_take_off(enter=EQUIP_ENTER, long_click=True, out=BATTLE_PREPARATION)
        self._inactive_edit()
