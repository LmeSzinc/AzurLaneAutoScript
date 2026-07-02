from module.logger import logger
from module.base.timer import Timer
from module.equipment.assets import *
from module.equipment.equipment_change import EquipmentChange
from module.ocr.ocr import Digit
from module.ui.assets import FLEET_CHECK
from module.ui.page import page_fleet

OCR_FLEET_INDEX = Digit(OCR_FLEET_INDEX, letter=(90, 154, 255), threshold=128, alphabet='123456')


class FleetEquipment(EquipmentChange):
    def fleet_enter(self, fleet):
        self.ui_ensure(page_fleet)

        # ui_ensure_index, set fleet
        letter = OCR_FLEET_INDEX
        next_button = FLEET_NEXT
        prev_button = FLEET_PREV
        interval = (0.2, 0.3)

        retry = Timer(1, count=2)
        for _ in self.loop():
            current = letter.ocr(self.device.image)
            logger.attr("Index", current)

            # ui_ensure_index but ignore default value 0
            # otherwise we would have 1 extra click switching from 1 to 4
            if current == 0:
                continue

            diff = fleet - current
            if diff == 0:
                break

            if retry.reached():
                button = next_button if diff > 0 else prev_button
                self.device.multi_click(button, n=abs(diff), interval=interval)
                retry.reset()

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
