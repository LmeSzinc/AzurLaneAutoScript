import yaml

from module.base.timer import Timer
from module.base.utils import random_rectangle_point, point2str
from module.device.method.utils import HierarchyButton
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

    def fastinput_ime_enable(self):
        self.device.adb_shell(['am', 'start', '-a', 'android.settings.INPUT_METHOD_SETTINGS'])
        while 1:
            h = self.device.dump_hierarchy_adb()

            def appear(xpath):
                return bool(HierarchyButton(h, xpath))

            def appear_then_click(xpath):
                b = HierarchyButton(h, xpath)
                if b:
                    point = random_rectangle_point(b.button)
                    logger.info(f'Click {point2str(*point)} @ {b}')
                    self.device.click_adb(*point)
                    return True
                else:
                    return False

            if appear_then_click('//*[@resource-id="android:id/title" and @text="FastInputIME"]/following-sibling::*[@resource-id="android:id/switch_widget" and @checked="false"]'):
                continue
            if appear_then_click('//*[@resource-id="android:id/button1"]'):
                continue
            # Disable one other enabled IME at a time
            if appear_then_click('(//*[@resource-id="android:id/title" and @text!="FastInputIME"]/following-sibling::*[@resource-id="android:id/switch_widget" and @enabled="true" and @checked="true"])[1]'):
                continue
            if appear('//*[@resource-id="android:id/title" and @text="FastInputIME"]/following-sibling::*[@resource-id="android:id/switch_widget" and @checked="true"]') \
                    and not appear('//*[@resource-id="android:id/title" and @text!="FastInputIME"]/following-sibling::*[@resource-id="android:id/switch_widget" and @enabled="true" and @checked="true"]'):
                break

        self.device.adb_shell(['input', 'keyevent', '4'])

    def _code_input(self, code):
        logger.info(f"Code input: {code}")
        d = self.device.u2
        click_timer = Timer(1, count=3)
        for _ in self.loop():
            name, shown = d.current_ime()
            if shown:
                if name != 'com.github.uiautomator/.FastInputIME':
                    try:
                        d.set_fastinput_ime(True)
                        continue
                    except Exception:
                        logger.warning("FastInputIME not enabled, trying to enable it")
                    self.fastinput_ime_enable()
                    continue
                else:
                    break
            if click_timer.reached_and_reset():
                self.device.click(EQUIPMENT_CODE_TEXTBOX)
        else:
            logger.warning("Equipment code load failed")
            return False
        d.send_keys(text=code, clear=True)
        d.send_action(code="done")
        self.device.sleep((0.3, 0.5))
        for _ in self.loop(timeout=10, skip_first=False):
            _, shown = d.current_ime()
            if shown:
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
        d = self.device.u2
        for _ in self.loop(timeout=10):
            if self.info_bar_count():
                break
            if self.appear_then_click(EQUIPMENT_CODE_EXPORT, offset=(5, 5), interval=3):
                continue
        code = d.clipboard
        return code

    def code_clear(self, name=None):
        self._code_enter()
        if name is None:
            name = self.current_ship()
        if self.config.EquipmentCode_ExportToConfig and self.get_code(name=name) is None:
            self.last_code = self._code_export()
            self.set_code(name=name, code=self.last_code)
        self._code_apply(code=None)

    def code_apply(self, name=None):
        self._code_enter()
        if name is None:
            name = self.current_ship()
        code = self.get_code(name=name)
        if code is None:
            code = self.last_code
        self._code_apply(code=code)