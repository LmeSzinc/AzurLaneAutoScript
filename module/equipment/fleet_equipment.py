from module.base.ocr import Digit
from module.equipment.assets import *
from module.equipment.equipment import Equipment
from module.ui.assets import FLEET_CHECK
from module.ui.ui import UI, page_fleet

OCR_FLEET_INDEX = Digit(OCR_FLEET_INDEX, letter=(90, 154, 255), back=(24, 32, 49), length=1, white_list='123456')


class DailyEquipment(Equipment):
    equipment_has_take_on = False

    def equipment_take_on(self):
        if self.config.FLEET_DAILY_EQUIPMENT is None:
            return False
        if self.equipment_has_take_on:
            return False

        self.ui_ensure(page_fleet)
        self.ui_ensure_index(self.config.FLEET_DAILY, letter=OCR_FLEET_INDEX, next_button=FLEET_NEXT, prev_button=FLEET_PREV)
        super().equipment_take_on(enter=FLEET_ENTER, out=FLEET_CHECK, fleet=self.config.FLEET_DAILY_EQUIPMENT)
        self.equipment_has_take_on = True
        self.device.sleep(1)
        return True

    def equipment_take_off(self):
        if self.config.FLEET_DAILY_EQUIPMENT is None:
            return False
        if not self.equipment_has_take_on:
            return False

        self.ui_ensure(page_fleet)
        self.ui_ensure_index(self.config.FLEET_DAILY, letter=OCR_FLEET_INDEX, next_button=FLEET_NEXT, prev_button=FLEET_PREV)
        super().equipment_take_off(enter=FLEET_ENTER, out=FLEET_CHECK, fleet=self.config.FLEET_DAILY_EQUIPMENT)
        self.equipment_has_take_on = False
        self.device.sleep(1)
        return True
