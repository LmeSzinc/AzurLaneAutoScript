from module.base.decorator import cached_property
from module.device.method.fastinput_ime import FastInputIME
from module.device.method.uiautomator_2 import Uiautomator2


class Input(Uiautomator2):
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
