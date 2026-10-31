import base64

from module.base.timer import Timer
from module.logger import logger


class FastInputIME:
    """FastInputIME helper using its owning device's shared interaction APIs."""

    FASTINPUT_IME = 'com.github.uiautomator/.FastInputIME'
    _fastinput_ime_control_methods = {'uiautomator2', 'minitouch', 'MaaTouch'}

    def __init__(self, device):
        self.device = device

    def fastinput_ime_supported(self):
        return self.device.config.Emulator_ControlMethod in self._fastinput_ime_control_methods

    def _fastinput_ime_prepare_onscreen_keyboard(self):
        """Best-effort Android preparation; emulator keyboard preferences may also be needed."""
        if not self.device.is_bluestacks_air:
            return
        setting = 'show_ime_with_hard_keyboard'
        try:
            if self.device.adb_shell(['settings', 'get', 'secure', setting]).strip() == '1':
                return
            self.device.adb_shell(['settings', 'put', 'secure', setting, '1'])
            if self.device.adb_shell(['settings', 'get', 'secure', setting]).strip() == '1':
                return
        except Exception as e:
            logger.warning(f'Unable to enable the on-screen keyboard: {e}')
        self._fastinput_ime_log_failure_hint()

    def _fastinput_ime_log_failure_hint(self):
        if self.device.is_bluestacks_air:
            logger.warning('Enable the on-screen keyboard in BlueStacks Air input settings.')
        elif self.device.is_mumu_over_version_400:
            logger.warning('MuMu may block changing the default input method. Select FastInputIME in Android settings.')

    def _set_fastinput_ime(self):
        failed = False
        try:
            for command in ('enable', 'set'):
                result = self.device.u2.shell(['ime', command, self.FASTINPUT_IME])
                exit_code = getattr(result, 'exit_code', 0)
                output = getattr(result, 'output', result)
                if exit_code:
                    failed = True
                    logger.warning(f'Unable to {command} FastInputIME: {output.strip()}')
        except Exception as e:
            failed = True
            logger.warning(f'Unable to set FastInputIME: {e}')
        return not failed and self.device.current_ime()[0] == self.FASTINPUT_IME

    def _enable_fastinput_ime(self):
        if self.device.is_mumu_over_version_400 or self.device.sdk_ver >= 35:
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
        self.device.stuck_record_clear()
        self.device.adb_shell(['am', 'start', '-a', 'android.settings.INPUT_METHOD_SETTINGS'])
        timeout = Timer(20).start()
        try:
            while not timeout.reached():
                self.device.dump_hierarchy()
                button = self.device.xpath_to_button('//*[@resource-id="android:id/button1"]')
                if button:
                    self.device.click(button)
                    continue
                for resource_id in switch_resource_ids:
                    button = self.device.xpath_to_button(
                        '//*[@resource-id="android:id/title" and @text="FastInputIME"]'
                        f'/following-sibling::*[@resource-id="{resource_id}"]')
                    if button:
                        break
                else:
                    continue
                checked = button.attrib.get('checked')
                if checked == 'false':
                    self.device.click(button)
                    continue
                if checked != 'true':
                    continue
                # Disable one competing IME at a time, then rescan its switch.
                button = self.device.xpath_to_button(f'({other_enabled})[1]')
                if button:
                    self.device.click(button)
                    continue
                return True
            logger.warning('Timed out enabling FastInputIME in Android settings')
            return False
        finally:
            self.device.adb_shell(['input', 'keyevent', '4'])
            self.device.stuck_record_clear()

    def ensure_fastinput_ime(self):
        """Prepare the device input method without relying on a game page."""
        self._fastinput_ime_prepare_onscreen_keyboard()
        if self.device.current_ime()[0] == self.FASTINPUT_IME:
            return True
        if self._set_fastinput_ime():
            return True
        logger.warning('FastInputIME not enabled by adb shell, trying to enable it in settings')
        if self._enable_fastinput_ime():
            if self.device.current_ime()[0] == self.FASTINPUT_IME or self._set_fastinput_ime():
                return True
        logger.warning('Unable to select FastInputIME')
        self._fastinput_ime_log_failure_hint()
        return False

    def input_text_fastinput_ime(self, text, focus, clear=True):
        """Focus a textbox, replace its text and submit the input method's done action."""
        if not self.ensure_fastinput_ime():
            return False
        # mInputShown can remain true without the target textbox being focused.
        focus()
        click_timer = Timer(1, count=3).start()
        timeout = Timer(20).start()
        while not timeout.reached():
            name, shown = self.device.current_ime()
            if name != self.FASTINPUT_IME:
                if not self.ensure_fastinput_ime():
                    return False
                focus()
                click_timer.reset()
            elif shown:
                # uiautomator2's send_keys/send_action repeat its legacy-only IME check.
                payload = base64.b64encode(text.encode('utf-8')).decode('ascii')
                action = 'ADB_SET_TEXT' if clear else 'ADB_INPUT_TEXT'
                for command in (
                    ['am', 'broadcast', '-a', action, '--es', 'text', payload],
                    ['am', 'broadcast', '-a', 'ADB_EDITOR_CODE', '--ei', 'code', '6'],
                ):
                    result = self.device.u2.shell(command)
                    if getattr(result, 'exit_code', 0):
                        output = getattr(result, 'output', result)
                        logger.warning(f'FastInputIME broadcast failed: {(output or "").strip()}')
                        return False
                self.device.sleep((0.3, 0.5))
                return True
            elif click_timer.reached_and_reset():
                focus()
            self.device.sleep(0.1)
        logger.warning('Timed out waiting for the text input keyboard')
        self._fastinput_ime_log_failure_hint()
        return False

