from module.equipment.assets import *
from module.equipment.equipment import Equipment
from module.equipment.equipment_change import EquipmentChange
from module.logger import logger
from module.ocr.ocr import Digit
from module.ui.assets import FLEET_CHECK
from module.ui.page import page_fleet

OCR_FLEET_INDEX = Digit(OCR_FLEET_INDEX, letter=(90, 154, 255), threshold=128, alphabet='123456')


class DailyEquipment(Equipment):
    equipment_has_take_on = False

    @property
    def _fleet_daily(self):
        fleet = self.config.FLEET_DAILY
        if isinstance(fleet, list):
            logger.info(f'Multiple daily fleets are set, change equipment only for the first one. fleet: {fleet}')
            return fleet[0]
        else:
            return fleet

    def equipment_take_on(self):
        if self.config.FLEET_DAILY_EQUIPMENT is None:
            return False
        if self.equipment_has_take_on:
            return False

        self.ui_ensure(page_fleet)
        self.ui_ensure_index(self._fleet_daily, letter=OCR_FLEET_INDEX, next_button=FLEET_NEXT, prev_button=FLEET_PREV)
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
        self.ui_ensure_index(self._fleet_daily, letter=OCR_FLEET_INDEX, next_button=FLEET_NEXT, prev_button=FLEET_PREV)
        super().equipment_take_off(enter=FLEET_ENTER, out=FLEET_CHECK, fleet=self.config.FLEET_DAILY_EQUIPMENT)
        self.equipment_has_take_on = False
        self.device.sleep(1)
        return True


class FleetEquipmentNew(EquipmentChange):
    def fleet_enter(self, fleet):
        self.ui_ensure(page_fleet)
        self.ui_ensure_index(fleet, letter=OCR_FLEET_INDEX,
                             next_button=FLEET_NEXT, prev_button=FLEET_PREV, skip_first_screenshot=True)

    def fleet_equipment_take_on_preset(self, preset_record, enter=FLEET_DETAIL_ENTER_FLAGSHIP,
                                       long_click=False, out=FLEET_DETAIL_CHECK):
        self.ui_click(FLEET_DETAIL, appear_button=page_fleet.check_button,
                      check_button=FLEET_DETAIL_CHECK, skip_first_screenshot=True)
        super().fleet_equipment_take_on_preset(preset_record=preset_record, enter=FLEET_DETAIL_ENTER_FLAGSHIP,
                                               long_click=False, out=FLEET_DETAIL_CHECK)
        self.ui_back(FLEET_CHECK)

    def fleet_equipment_take_off(self, enter=FLEET_DETAIL_ENTER_FLAGSHIP, long_click=False, out=FLEET_DETAIL_CHECK):
        self.ui_click(FLEET_DETAIL, appear_button=page_fleet.check_button,
                      check_button=FLEET_DETAIL_CHECK, skip_first_screenshot=True)
        super().fleet_equipment_take_off(enter=enter, long_click=long_click, out=out)
        self.ui_back(FLEET_CHECK)

    def fleet_enter_ship(self, button):
        self.ui_click(FLEET_DETAIL, appear_button=page_fleet.check_button,
                      check_button=FLEET_DETAIL_CHECK, skip_first_screenshot=True)
        self.ship_info_enter(button, long_click=False)

    def fleet_back(self):
        self.ui_back(FLEET_DETAIL_CHECK)
        self.ui_back(FLEET_CHECK)


class FleetEquipment(DailyEquipment if globals().get("g_current_task", "") == "GemsFarming" else FleetEquipmentNew):
    ...
