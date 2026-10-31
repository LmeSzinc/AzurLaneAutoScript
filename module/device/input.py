import os
import tempfile

from filelock import FileLock, Timeout

from module.base.decorator import cached_property
from module.device.method.adb_input import AdbInput
from module.device.method.fastinput_ime import FastInputIME
from module.device.method.uiautomator_2 import Uiautomator2
from module.logger import logger


# Independent of the device serial and checkout, since emulators may share a host clipboard.
_CLIPBOARD_LOCK_FILE = os.path.join(tempfile.gettempdir(), 'alas-clipboard.lock')


class Input(Uiautomator2):
    @cached_property
    def adb_input(self):
        return AdbInput(self)

    @cached_property
    def fastinput_ime(self):
        return FastInputIME(self)

    @cached_property
    def input_methods(self):
        fastinput = {
            'supported': self.fastinput_ime.fastinput_ime_supported,
            'prepare': self.fastinput_ime.ensure_fastinput_ime,
            'input': self.fastinput_ime.input_text_fastinput_ime,
        }
        return {
            'ADB': {
                'supported': self.adb_input.adb_input_supported,
                'prepare': self.adb_input.ensure_adb_input,
                'input': self.adb_input.input_text_adb,
            },
            'FastInputIME': fastinput,
            'uiautomator2': fastinput,
        }

    @cached_property
    def input_method_override(self) -> str:
        return ''

    def _input_method(self, operation):
        if self.input_method_override:
            method = self.input_method_override
        else:
            method = 'uiautomator2'
        methods = self.input_methods.get(method, self.input_methods['uiautomator2'])
        return methods[operation]

    def text_input_supported(self):
        return self._input_method('supported')()

    def ensure_text_input(self):
        return self._input_method('prepare')()

    def input_text(self, text, button, clear=True):
        method = self._input_method('input')
        return method(text, focus=lambda: self.click(button), clear=clear)

    def is_keyboard_shown(self):
        return self.is_keyboard_shown_uiautomator2()

    def current_ime(self):
        return self.current_ime_uiautomator2()

    def ensure_clipboard(self):
        # The uiautomator2 app needs default-IME access when reading a game app's
        # clipboard in the background on Android 10 and newer.
        if self.sdk_ver < 29:
            return True
        return self.fastinput_ime.ensure_fastinput_ime()

    def get_clipboard(self):
        return self.get_clipboard_uiautomator2()

    def clipboard_copy(self, copy, timeout=30):
        """Run a UI copy action and read its result under a shared process lock.

        The callback returns True after copying completes. Return None if clipboard
        preparation, lock acquisition or the copy action fails.
        """
        if not self.ensure_clipboard():
            return None
        # Use a fresh lock object per operation: reentrancy must not let another
        # device or thread enter an existing copy/read transaction.
        lock = FileLock(_CLIPBOARD_LOCK_FILE)
        try:
            lock.acquire(timeout=timeout)
        except Timeout:
            logger.warning('Timed out waiting for another Alas clipboard operation')
            return None
        try:
            if not copy():
                return None
            return self.get_clipboard()
        finally:
            lock.release()
