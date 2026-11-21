import base64

from module.base.timer import Timer
from module.device.method.uiautomator_2 import Uiautomator2, retry
from module.logger import logger


class FastInputIME(Uiautomator2):
    """FastInputIME input-method mixin for devices using uiautomator2 control."""

    FASTINPUT_IME = 'com.github.uiautomator/.FastInputIME'

    def _fastinput_ime_prepare_onscreen_keyboard(self):
        """Best-effort Android preparation; emulator keyboard preferences may also be needed."""
        if not self.is_bluestacks_air:
            return
        setting = 'show_ime_with_hard_keyboard'
        try:
            if self.adb_shell(['settings', 'get', 'secure', setting]).strip() == '1':
                return
            self.adb_shell(['settings', 'put', 'secure', setting, '1'])
            if self.adb_shell(['settings', 'get', 'secure', setting]).strip() == '1':
                return
        except Exception as e:
            logger.warning(f'Unable to enable the on-screen keyboard: {e}')
        self._fastinput_ime_log_failure_hint()

    def _fastinput_ime_log_failure_hint(self):
        if self.is_bluestacks_air:
            logger.warning('Enable the on-screen keyboard in BlueStacks Air input settings.')
        elif self.is_mumu_over_version_400:
            logger.warning('MuMu may block changing the default input method. Select FastInputIME in Android settings.')

    def _set_fastinput_ime(self):
        try:
            self.u2.set_fastinput_ime(True)
        except Exception as e:
            logger.warning(f'Unable to set FastInputIME: {e}')
        return self.current_ime()[0] == self.FASTINPUT_IME

    def _enable_fastinput_ime(self):
        if self.is_mumu_over_version_400 or self.sdk_ver >= 35:
            switch_resource_ids = ('com.android.settings:id/switchWidget', 'android:id/switch_widget')
        else:
            switch_resource_ids = ('android:id/switch_widget', 'com.android.settings:id/switchWidget')
        # Keep both layouts usable when emulator and Android versions differ.
        switch_resources = ' or '.join(f'@resource-id="{value}"' for value in switch_resource_ids)
        other_enabled = (
            '//*[@resource-id="android:id/title" and @text!="FastInputIME"]'
            f'/following-sibling::*[({switch_resources}) and @enabled="true" and @checked="true"]'
        )
        logger.info('Enable FastInputIME in Android settings')
        self.stuck_record_clear()
        self.adb_shell(['am', 'start', '-a', 'android.settings.INPUT_METHOD_SETTINGS'])
        timeout = Timer(20).start()
        try:
            while not timeout.reached():
                self.dump_hierarchy()
                button = self.xpath_to_button('//*[@resource-id="android:id/button1"]')
                if button:
                    self.click(button)
                    continue
                for resource_id in switch_resource_ids:
                    button = self.xpath_to_button(
                        '//*[@resource-id="android:id/title" and @text="FastInputIME"]'
                        f'/following-sibling::*[@resource-id="{resource_id}"]')
                    if button:
                        break
                else:
                    continue
                checked = button.attrib.get('checked')
                if checked == 'false':
                    self.click(button)
                    continue
                if checked != 'true':
                    continue
                # Disable one competing IME at a time, then rescan its switch.
                button = self.xpath_to_button(f'({other_enabled})[1]')
                if button:
                    self.click(button)
                    continue
                return
            raise OSError('Timed out enabling FastInputIME in Android settings')
        finally:
            self.adb_shell(['input', 'keyevent', '4'])
            self.stuck_record_clear()

    @retry
    def input_text_fastinput_ime(self, text, button):
        """Replace the focused editor's text and submit it; retries replace it again."""
        self._fastinput_ime_prepare_onscreen_keyboard()
        # mInputShown can remain true without the target textbox being focused.
        self.click(button)
        click_timer = Timer(1, count=3).start()
        timeout = Timer(20).start()
        while not timeout.reached():
            name, shown = self.current_ime()
            if name != self.FASTINPUT_IME:
                if not self._set_fastinput_ime():
                    logger.warning('FastInputIME not enabled by adb shell, trying to enable it in settings')
                    self._enable_fastinput_ime()
                    if not self._set_fastinput_ime():
                        self._fastinput_ime_log_failure_hint()
                        raise OSError('Unable to select FastInputIME')
                self.click(button)
                click_timer.reset()
            elif shown:
                break
            elif click_timer.reached_and_reset():
                self.click(button)
            self.sleep(0.1)
        else:
            self._fastinput_ime_log_failure_hint()
            raise OSError('Timed out waiting for the text input keyboard')

        # uiautomator2's send_keys/send_action repeat its legacy-only IME check.
        payload = base64.b64encode(text.encode('utf-8')).decode('ascii')
        for command in (
            ['am', 'broadcast', '-a', 'ADB_SET_TEXT', '--es', 'text', payload],
            ['am', 'broadcast', '-a', 'ADB_EDITOR_CODE', '--ei', 'code', '6'],
        ):
            result = self.u2.shell(command)
            if getattr(result, 'exit_code', 0):
                raise OSError(f'FastInputIME broadcast failed: {result.output}')
