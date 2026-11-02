import re
import shlex

from module.base.timer import Timer
from module.device.method.adb import Adb, retry
from module.device.method.adb_clipboard import ClipboardBinderError, decode_clipboard_parcel
from module.exception import RequestHumanTakeover
from module.logger import logger


class AdbInput(Adb):
    """Type printable ASCII using keyboard events and the device's existing IME."""

    _editor_xpath = (
        '//*[@enabled="true" and not(@password="true") and '
        '(@class="android.widget.EditText" or @class="android.widget.AutoCompleteTextView" '
        'or @class="android.widget.MultiAutoCompleteTextView")]'
    )

    def _clear_text_adb(self, editor):
        if not editor or 'text' not in editor.attrib:
            raise OSError('Cannot read the focused Android editor for ADB clearing')
        # Clear both sides of the cursor, including wrapped/multiline text. UTF-16
        # length bounds the number of key events even for surrogate pairs.
        length = len(editor.attrib['text'].encode('utf-16-le')) // 2
        for key in ('KEYCODE_FORWARD_DEL', 'KEYCODE_DEL'):
            for offset in range(0, length, 128):
                self.adb_shell(['input', 'keyevent'] + [key] * min(128, length - offset), timeout=30)

    @retry
    def input_text_adb(self, text, button):
        """Replace the focused editor's text and submit it; retries replace it again."""
        if any(ord(char) < 32 or ord(char) > 126 for char in text):
            logger.critical('ADB text input supports printable ASCII; use FastInputIME for other text')
            raise RequestHumanTakeover
        self.click(button)
        click_timer = Timer(1).start()
        timeout = Timer(10).start()
        while not timeout.reached():
            self.hierarchy = self.dump_hierarchy_adb()
            editor = self.xpath_to_button(self._editor_xpath + '[@focused="true"]')
            if editor:
                break
            if click_timer.reached_and_reset():
                self.click(button)
        else:
            raise OSError('Timed out waiting for the Android text editor')
        self._clear_text_adb(editor)
        # Android's input command translates %s to a space. Split that sequence
        # across commands so literal percent signs and spaces remain unchanged.
        for part in re.split(r'(?<=%)(?=s)', text):
            if part:
                # adbutils 0.11 quotes lists for Windows; quote text for Android's shell.
                self.adb_shell(f'input text {shlex.quote(part)}', timeout=30)
        self.adb_shell(['input', 'keyevent', 'KEYCODE_ENTER'])
        timeout = Timer(5).start()
        back_timer = Timer(1).start()
        while self.current_ime_adb()[1]:
            if timeout.reached():
                raise OSError('Timed out dismissing the text input keyboard')
            if back_timer.reached_and_reset():
                self.adb_shell(['input', 'keyevent', 'KEYCODE_BACK'])
            self.sleep(0.1)

    @retry
    def ensure_clipboard_adb(self):
        if '_clipboard_adb_command' in self.__dict__:
            return
        sdk = self.sdk_ver
        if not 24 <= sdk <= 36:
            logger.critical(f'ADB clipboard reading is unsupported on SDK {sdk}')
            raise RequestHumanTakeover
        # Transaction numbers follow IClipboard.aidl; never probe other methods.
        transaction = 2 if sdk < 28 else 3 if sdk < 31 else 4
        command = ['service', 'call', 'clipboard', str(transaction), 's16', 'com.android.shell']
        if sdk >= 29:
            user = self.adb_shell(['am', 'get-current-user']).strip()
            if not user.isdecimal():
                raise OSError('Cannot identify the current Android user')
            if sdk >= 33:
                command += ['i32', '-1']  # Null attribution tag, not a null Binder.
            command += ['i32', user]
            if sdk >= 34:
                command += ['i32', '0']  # Default device.
        self._clipboard_adb_command = command

    @retry
    def get_clipboard_adb(self):
        """Read the clipboard Binder service without changing the foreground app."""
        self.ensure_clipboard_adb()
        command = self._clipboard_adb_command
        try:
            return decode_clipboard_parcel(self.adb_shell(command), self.sdk_ver)
        except ClipboardBinderError as e:
            # Android 13 QPR2 added attributionTag without changing the SDK.
            if (self.sdk_ver != 33 or command[-4:-2] != ['i32', '-1']
                    or e.code not in (-2, -3)):
                raise
            command = command[:-4] + command[-2:]
            text = decode_clipboard_parcel(self.adb_shell(command), self.sdk_ver)
            self._clipboard_adb_command = command
            return text
