from module.base.timer import Timer
from module.combat.assets import BATTLE_PREPARATION
from module.equipment.equipment import Equipment
from module.exercise.assets import *


class ExerciseEquipment(Equipment):
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
        if self.config.EXERCISE_FLEET_EQUIPMENT is None:
            return False
        if self.equipment_has_take_on:
            return False

        self._active_edit()
        super().equipment_take_on(enter=EQUIP_ENTER, out=BATTLE_PREPARATION, fleet=self.config.EXERCISE_FLEET_EQUIPMENT)
        self._inactive_edit()
        return True

    def equipment_take_off(self):
        if self.config.EXERCISE_FLEET_EQUIPMENT is None:
            return False
        if not self.equipment_has_take_on:
            return False

        self._active_edit()
        super().equipment_take_off(enter=EQUIP_ENTER, out=BATTLE_PREPARATION, fleet=self.config.EXERCISE_FLEET_EQUIPMENT)
        self._inactive_edit()
        return True
