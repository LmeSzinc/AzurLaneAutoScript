import re
import shlex

from module.base.timer import Timer
from module.logger import logger


class AdbInput:
    """Type printable ASCII using keyboard events and the device's existing IME."""

    def __init__(self, device):
        self.device = device

    def adb_input_supported(self):
        return True

    def ensure_adb_input(self):
        return True

    def _shell(self, command):
        # adbutils 0.11 uses Windows argument quoting for lists, even on Android.
        command = ' '.join(shlex.quote(str(arg)) for arg in command)
        marker = '__ALAS_INPUT_EXIT__'
        output = self.device.adb_shell(
            command + '; printf "\\n' + marker + '%s" "$?"', timeout=30)
        message, separator, status = output.rpartition('\n' + marker)
        if not separator or status.strip() != '0':
            logger.warning(f'ADB input command failed: {message if separator else output}')
            return False
        return True

    def input_text_adb(self, text, focus, clear=True):
        if any(ord(char) < 32 or ord(char) > 126 for char in text):
            logger.warning('ADB text input supports printable ASCII; use FastInputIME for other text')
            return False
        if not self.ensure_adb_input():
            return False
        focus()
        if clear:
            if not self.device.clear_text_uiautomator2():
                logger.warning('Unable to clear the focused Android text field')
                return False
        elif not self._shell(['input', 'keyevent', 'KEYCODE_MOVE_END']):
            return False
        # Android's input command translates %s to a space. Split that sequence
        # across commands so literal percent signs and spaces remain unchanged.
        for part in re.split(r'(?<=%)(?=s)', text):
            if part and not self._shell(['input', 'text', part]):
                return False
        if not self._shell(['input', 'keyevent', 'KEYCODE_ENTER']):
            return False
        self.device.sleep((0.3, 0.5))
        if self.device.is_keyboard_shown():
            if not self._shell(['input', 'keyevent', 'KEYCODE_BACK']):
                return False
            timeout = Timer(5).start()
            while self.device.is_keyboard_shown():
                if timeout.reached():
                    logger.warning('Timed out dismissing the text input keyboard')
                    return False
                self.device.sleep(0.1)
        return True
