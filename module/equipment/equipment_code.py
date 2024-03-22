import yaml

from module.equipment.assets import *
from module.logger import logger
from module.ui.assets import BACK_ARROW
from module.storage.storage import StorageHandler


class EquipmentCode(StorageHandler):

    @property
    def flagship_equipment_codes(self):
        codes = {
            'langley': None,
            'bogue': None,
            'ranger': None,
            'hermes': None
        }
        try:
            config = {}
            for item in yaml.safe_load_all(self.config.GemsFarming_EquipmentCode):
                config.update(item)
        except Exception:
            logger.error("Fail to load equipment code config, assuming not specified")
            return codes
        for cv in ['langley', 'bogue', 'ranger', 'hermes']:
            try:
                code: str = config.pop(cv, None)
                codes[cv] = code
            except Exception as e:
                logger.exception(e)

        return codes

    def enter_equipment_code_page(self, skip_first_screenshot=False):
        """
        Pages:
            in: ship_detail
            out: equipment_code
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(EQUIPMENT_CODE_ENTRANCE):
                continue

            # End
            if self.appear(EQUIPMENT_CODE_PAGE_CHECK):
                break

    def exit_equipment_code_page(self):
        """
        Pages:
            in: equipment_code
            out: ship_detail
        """
        self.ui_back(check_button=EQUIPMENT_CODE_ENTRANCE)

    def export_equipment_code_to_clipboard(self, skip_first_screenshot=False):
        """
        Use "export" button to export current equipment code to clipboard.
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.info_bar_count():
                break

            if self.appear_then_click(EQUIPMENT_CODE_EXPORT):
                continue

    def clear_all_equipments(self):
        self.appear_then_click(EQUIPMENT_CODE_CLEAR)

    def _enter_equipment_code_input_mode(self, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if not self.appear(EQUIPMENT_CODE_ENTER):
                break

            if self.appear(EQUIPMENT_CODE_ENTER):
                self.device.click(EQUIPMENT_CODE_TEXTBOX)
                continue

    def import_equipment_code(self, text=None):
        """
        Type in equipment code.
        If text is None, use clipboard contents instead to fill in equipment code.
        """
        self._enter_equipment_code_input_mode()
        fail_count = 0
        while 1:
            self.device.screenshot()
            if self.appear_then_click(EQUIPMENT_CODE_ENTER):
                break

            if text:
                # use text input
                logger.info(f"Use equipment code from config: {text}")
                self.device.text_input(text, clear=True)
            else:
                # use clipboard input
                logger.info("Use equipment code from clipboard")
                self.device.u2_clear_text()
                # There is no paste action for u2, using adb input keyevent instead
                self.device.adb_keyevent_input(279)

            try:
                # 6 --> IME_ACTION_DONE
                self.device.u2_send_action(6)
            except EnvironmentError as e:
                fail_count += 1
                logger.exception(str(e) + f" (Retry {fail_count}/3)")
                if fail_count > 3:
                    raise e
                else:
                    self._enter_equipment_code_input_mode()

    def equipment_code_confirm(self, skip_first_screenshot=True):
        """
        Pages:
            in: equipment_code
            out: ship_detail
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(EQUIPMENT_CODE_ENTRANCE):
                return True

            if self.handle_storage_full():
                return False

            if self.handle_popup_confirm('EQUIPMENT_CODE'):
                continue

            if self.appear_then_click(EQUIPMENT_CODE_CONFIRM, interval=5):
                continue
