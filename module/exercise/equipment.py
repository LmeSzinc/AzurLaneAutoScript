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

    def equip_take_on_all(self):
        self._active_edit()
        self.equip_take_on_all_preset(enter=EQUIP_ENTER, long_click=True,
                                      out=BATTLE_PREPARATION,
                                      preset_record=self.config.EXERCISE_FLEET_EQUIPMENT)
        self._inactive_edit()

    def equip_take_off_all(self, enter=EQUIP_ENTER, long_click=True, out=BATTLE_PREPARATION):
        self._active_edit()
        super().equip_take_off_all(enter=enter, long_click=long_click, out=out)
        self._inactive_edit()
