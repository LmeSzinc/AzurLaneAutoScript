from module.device.method.adb import Adb
from module.device.method.uiautomator_2 import Uiautomator2

class Input(Adb, Uiautomator2):
    def adb_keyevent_input(self, code=None):
        # 0 -->  "KEYCODE_UNKNOWN"
        # 1 -->  "KEYCODE_MENU"
        # 2 -->  "KEYCODE_SOFT_RIGHT"
        # 3 -->  "KEYCODE_HOME"
        # 4 -->  "KEYCODE_BACK"
        # 5 -->  "KEYCODE_CALL"
        # 6 -->  "KEYCODE_ENDCALL"
        # 66 --> "KEYCODE_ENTER"
        # 279 --> "KEYCODE_PASTE"
        self.adb_shell(['input', 'keyevent', code])

    def text_input(self, text: str=None, clear: bool=False):
        self.u2_set_fastinput_ime(True)
        self.u2_send_keys(text=text, clear=clear)
