import yaml

from module.equipment.assets import *
from module.logger import logger
from module.retire.assets import TEMPLATE_BOGUE, TEMPLATE_HERMES, TEMPLATE_RANGER, TEMPLATE_LANGLEY
from module.storage.assets import EQUIPMENT_FULL
from module.storage.storage import StorageHandler

EMPTY_CODE = "MC8wLzAvMC8wXDA="
EQUIPMENT_PREVIEW = list([
    EQUIPMENT_CODE_EQUIP_0,
    EQUIPMENT_CODE_EQUIP_1,
    EQUIPMENT_CODE_EQUIP_2,
    EQUIPMENT_CODE_EQUIP_3,
    EQUIPMENT_CODE_EQUIP_4,
    EQUIPMENT_CODE_EQUIP_5,
])

class EquipmentCodeHandler(StorageHandler):
    last_code: str = None

    def equipment_code_supported(self):
        if self.device.text_input_supported():
            return True

        logger.warning(
            f"Equipment code input is unavailable with control method "
            f"{self.config.Emulator_ControlMethod}, skip equipment change"
        )
        return False

    def get_code(self, name):
        try:
            config = {}
            for item in yaml.safe_load_all(self.config.EquipmentCode_Config):
                config.update(item)
        except Exception:
            logger.error("Fail to load equipment code config")
            return None
        try:
            name: str = config.pop(name)
            return name
        except Exception:
            logger.error(f"Config does not contain equipment code for {name}")
            return None

    def set_code(self, name, code):
        config = {}
        try:
            for item in yaml.safe_load_all(self.config.EquipmentCode_Config):
                config.update(item)
        except Exception:
            pass
        try:
            config.update({name: code})
            config_yaml = yaml.safe_dump(config)
            self.config.EquipmentCode_Config = config_yaml
        except Exception:
            logger.error("Fail to set equipment code config")

    def current_ship(self):
        """
        Currently, only supports common CV recognization

        Pages:
            in: equipment_code
        """
        for _ in self.loop():
            if not self.appear(EMPTY_SHIP_R):
                break
        if TEMPLATE_BOGUE.match(self.device.image, scaling=1.46):  # image has rotation
            logger.info("Bogue detected")
            return 'bogue'
        elif TEMPLATE_HERMES.match(self.device.image, scaling=124 / 89):
            logger.info("Hermes detected")
            return 'hermes'
        elif TEMPLATE_RANGER.match(self.device.image, scaling=4 / 3):
            logger.info("Ranger detected")
            return 'ranger'
        elif TEMPLATE_LANGLEY.match(self.device.image, scaling=25 / 21):
            logger.info("Langley detected")
            return 'langley'
        else:
            logger.warning("Unknown ship detected, assuming DD")
            return 'DD'

    def _code_enter(self):
        """
        Pages:
            in: ship_detail
            out: equipment_code
        """
        for _ in self.loop():
            if self.appear(EQUIPMENT_CODE_PAGE_CHECK, offset=(5, 5)):
                break

            if self.appear_then_click(EQUIPMENT_CODE_ENTRANCE, offset=(5, 5), interval=1):
                continue

    def _code_exit(self):
        """
        Pages:
            in: equipment_code
            out: ship_detail
        """
        self.ui_back(check_button=EQUIPMENT_CODE_ENTRANCE)

    def is_code_preview_loaded(self):
        if self.appear(EQUIPMENT_CODE_EQUIP_5_LOCKED, offset=(5, 5)):
            max_index = 5
        else:
            max_index = 6
        for index in range(max_index):
            if not self.appear(EQUIPMENT_PREVIEW[index], offset=(5, 5)):
                return True

        return False

    def _code_preview_clear(self):
        for _ in self.loop(timeout=2):
            if not self.is_code_preview_loaded():
                return True

            if self.appear_then_click(EQUIPMENT_CODE_CLEAR, offset=(5, 5), interval=1):
                continue
        else:
            return False

    def _code_input(self, code):
        logger.info(f"Code input: {code}")
        if not self.device.input_text(code, EQUIPMENT_CODE_TEXTBOX):
            logger.warning("Equipment code load failed")
            return False
        for _ in self.loop(timeout=10, skip_first=False):
            if self.device.is_keyboard_shown():
                continue
            if self.is_code_preview_loaded():
                return True
            if self.appear_then_click(EQUIPMENT_CODE_ENTER, offset=(5, 5), interval=3):
                continue
        else:
            logger.warning("Equipment code load failed")
            return False

    def _code_confirm(self):
        logger.info("Code apply")
        for _ in self.loop(timeout=10):
            if self.appear(EQUIPMENT_CODE_ENTRANCE, offset=(5, 5)):
                return True
            if self.appear(EQUIPMENT_FULL, offset=(30, 30)):
                return False
            if self.handle_popup_confirm("EQUIPMENT_CODE"):
                continue
            if self.appear_then_click(EQUIPMENT_CODE_CONFIRM, offset=(5, 5), interval=3):
                continue
        else:
            return False

    def _code_apply(self, code=None):
        for _ in range(5):
            self._code_preview_clear()
            if code is not None and code != EMPTY_CODE:
                success = self._code_input(code)
                if not success:
                    continue
            success = self._code_confirm()
            if success:
                logger.info("Equipment code apply complete.")
                return True
            else:
                self.handle_storage_full()
        else:
            return False

    def _code_export(self):
        self.handle_info_bar()
        if not self.device.ensure_clipboard():
            logger.warning("Equipment code export failed")
            return None
        for _ in self.loop(timeout=10):
            if self.info_bar_count():
                break
            if self.appear_then_click(EQUIPMENT_CODE_EXPORT, offset=(5, 5), interval=3):
                continue
        return self.device.get_clipboard()

    def code_clear(self, name=None):
        if not self.equipment_code_supported():
            return False

        self._code_enter()
        if name is None:
            name = self.current_ship()
        if self.config.EquipmentCode_ExportToConfig and self.get_code(name=name) is None:
            code = self._code_export()
            if code is None:
                return False
            self.last_code = code
            self.set_code(name=name, code=code)
        return self._code_apply(code=None)

    def code_apply(self, name=None):
        if not self.equipment_code_supported():
            return False

        self._code_enter()
        if name is None:
            name = self.current_ship()
        code = self.get_code(name=name)
        if code is None:
            code = self.last_code
        return self._code_apply(code=code)
