from module.equipment.assets import *
from module.equipment.equipment_change import EquipmentChange
from module.ocr.ocr import Digit
from module.ui.assets import FLEET_CHECK
from module.ui.page import page_fleet

OCR_FLEET_INDEX = Digit(OCR_FLEET_INDEX, letter=(90, 154, 255), threshold=128, alphabet='123456')


class FleetEquipment(EquipmentChange):
    def fleet_enter(self, fleet):
        self.ui_ensure(page_fleet)
        self.ui_ensure_index(fleet, letter=OCR_FLEET_INDEX,
                             next_button=FLEET_NEXT, prev_button=FLEET_PREV, skip_first_screenshot=True)

    def fleet_equip_take_on_all_preset(self, preset_record):
        self.ui_click(FLEET_DETAIL, appear_button=page_fleet.check_button,
                      check_button=FLEET_DETAIL_CHECK, skip_first_screenshot=True)
        self.equip_take_on_all_preset(enter=FLEET_DETAIL_ENTER_FLAGSHIP, long_click=False,
                                      out=FLEET_DETAIL_CHECK,
                                      preset_record=preset_record)
        self.ui_back(FLEET_CHECK)

    def fleet_equip_take_off_all(self):
        self.ui_click(FLEET_DETAIL, appear_button=page_fleet.check_button,
                      check_button=FLEET_DETAIL_CHECK, skip_first_screenshot=True)
        self.equip_take_off_all(enter=FLEET_DETAIL_ENTER_FLAGSHIP, long_click=False, out=FLEET_DETAIL_CHECK)
        self.ui_back(FLEET_CHECK)

    def fleet_enter_ship(self, button):
        self.ui_click(FLEET_DETAIL, appear_button=page_fleet.check_button,
                      check_button=FLEET_DETAIL_CHECK, skip_first_screenshot=True)
        self.ship_detail_enter(button, long_click=False)

    def fleet_equip_back(self, button):
        self.ui_back(FLEET_DETAIL_CHECK)
        self.ui_back(button)
