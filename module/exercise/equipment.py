from module.base.timer import Timer
from module.combat.assets import BATTLE_PREPARATION
<<<<<<< HEAD
from module.equipment.equipment import Equipment
from module.exercise.assets import *


class ExerciseEquipment(Equipment):
=======
from module.equipment.equipment_change import EquipmentChange
from module.exercise.assets import *


class ExerciseEquipment(EquipmentChange):
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
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
<<<<<<< HEAD
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
=======
        self._active_edit()
        self.fleet_equipment_take_on_preset(preset_record=self.config.EXERCISE_FLEET_EQUIPMENT, enter=EQUIP_ENTER,
                                            long_click=True, out=BATTLE_PREPARATION)
        self._inactive_edit()

    def equipment_take_off(self):
        self._active_edit()
        self.fleet_equipment_take_off(enter=EQUIP_ENTER, long_click=True, out=BATTLE_PREPARATION)
        self._inactive_edit()
>>>>>>> 24aa3e00bd9af9a6a050df54c6a0cef959a9c6c0
