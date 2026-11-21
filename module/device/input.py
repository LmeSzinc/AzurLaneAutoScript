from module.device.app_control import AppControl
from module.device.method.adb_input import AdbInput
from module.device.method.fastinput_ime import FastInputIME


class Input(AdbInput, FastInputIME):
    @property
    def _use_fastinput(self):
        return self.config.Emulator_ControlMethod in AppControl._app_u2_family

    def input_text(self, text, button):
        method = self.input_text_fastinput_ime if self._use_fastinput else self.input_text_adb
        method(text, button)

    def current_ime(self):
        return self.current_ime_adb()

    def is_keyboard_shown(self):
        return self.current_ime()[1]

    def ensure_clipboard(self):
        method = self.ensure_clipboard_uiautomator2 if self._use_fastinput else self.ensure_clipboard_adb
        method()

    def get_clipboard(self):
        try:
            method = self.get_clipboard_uiautomator2 if self._use_fastinput else self.get_clipboard_adb
            return method()
        finally:
            self.stuck_record_clear()
