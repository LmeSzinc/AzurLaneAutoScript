from module.config.utils import deep_get
from module.logger import logger
from module.gg_handler.assets import *
from module.base.base import ModuleBase as Base
from module.gg_handler.gg_data import GGData


class GGScreenshot(Base):

    def __init__(self, config, device):
        super().__init__(config, device)
        self.device = device
        self.config = config
        self.gg_panel_confirm_time = 5
        # self.gg_panel_confirm_time = deep_get(self.config.data, 'GameManager.GGHandler.GGPanelConfirmTime')

    def skip_error(self):
        """
        Page: 
            in: Game down error
            out: restart
        """
        skip_first_screenshot = False
        count = 0
        logger.attr('Confirm Time', f'{self.gg_panel_confirm_time}S')
        times = self.gg_panel_confirm_time * 2
        for i in range(times):
            skipped = 0
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.sleep(0.5)
                self.device.screenshot()
            if self.appear(button=BUTTON_GG_RESTART_ERROR, offset=(50, 50)):
                logger.hr('Game died with GG panel')
                logger.info('Close GG restart error')
                self.device.click(BUTTON_GG_RESTART_ERROR)
                skipped = 1
                count += 1
                if count >= 2:
                    break
        skip_first_screenshot = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.sleep(0.3)
                self.device.screenshot()
            if self.appear(button=BUTTON_GG_RESTART_ERROR, offset=(50, 50)):
                logger.hr('Game died with GG panel')
                logger.info('Close GG restart error')
                skipped = 1
                self.device.click(BUTTON_GG_RESTART_ERROR)
            elif self.appear(button=BUTTON_GG_SCRIPT_END, offset=(50, 50)):
                logger.info('Close previous script')
                skipped = 1
                self.device.click(BUTTON_GG_SCRIPT_END)
            elif self.appear(button=BUTTON_GG_SCRIPT_FATAL, offset=(50, 50)):
                logger.info('Restart previous script')
                skipped = 1
                self.device.click(BUTTON_GG_SCRIPT_FATAL)
            elif self.appear(button=BUTTON_GG_APP_CHOOSE, offset=(150, 500)):
                logger.info('APP choose')
                skipped = 1
                self.device.click(BUTTON_GG_APP_CHOOSE)
            elif self.appear(button=BUTTON_GG_SCRIPT_MENU_A, offset=(50, 50)):
                skipped = 1
                logger.info('Close previous script')
                self.device.click(BUTTON_GG_EXIT_POS)
            elif not self.appear(button=BUTTON_GG_CONFIRM, offset=(50, 50)):
                logger.hr('GG Panel Disappearance Confirmed')
                break
            elif self.appear(button=BUTTON_GG_SEARCH_MODE_CONFIRM, offset=(10, 10), threshold=0.999):
                logger.info('At GG main panel, click GG exit')
                skipped = 1
                self.device.click(BUTTON_GG_EXIT_POS)
            elif self.appear(button=BUTTON_GG_CONFIRM, offset=(50, 50)) and \
                    not self.appear(button=BUTTON_GG_CONFIRM, offset=10):
                self.device.click(BUTTON_GG_TAB_SEARCH_POS)
                skipped = 1
                logger.info('Enter search mode')
            elif self.appear(button=BUTTON_GG_CONFIRM, offset=10):
                logger.info('Unexpected GG page, Try GG exit')
                self.device.click(BUTTON_GG_EXIT_POS)
                skipped = 1
        return skipped

    def _enter_gg(self):
        """
        Page:
            in: any
            out: any GG
        """
        self.device.click(BUTTON_GG_ENTER_POS)
        skip_first_screenshot = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.sleep(0.3)
                self.device.screenshot()
            if self.appear(button=BUTTON_GG_CONFIRM, offset=(50, 50)):
                logger.info('Entered GG')
                break
            self.device.click(BUTTON_GG_ENTER_POS)
        skip_first_screenshot = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.sleep(0.3)
                self.device.screenshot()
            if not self.appear(button=BUTTON_GG_APP_CHOOSE, offset=(150, 500)):
                from module.ui.assets import BACK_ARROW
                self.device.click(BACK_ARROW)
                logger.info('Actually APP choosing button')
            else:
                self.appear_then_click(button=BUTTON_GG_APP_CHOOSE, offset=(150, 500))
                logger.info('APP Choose')
                break

    def _gg_enter_script(self):
        """
        Page:
            in: any GG
            out: GG ready to start script
        """
        skip_first_screenshot = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.sleep(0.5)
                self.device.screenshot()
            if self.appear(button=BUTTON_GG_SCRIPT_ENTER_CONFIRM, offset=(50, 50)):
                logger.info('GG script ready to start')
                break
            elif self.appear(button=BUTTON_GG_SCRIPT_END, offset=(50, 50)):
                logger.info('Close previous script')
                self.device.click(BUTTON_GG_SCRIPT_END)
            elif self.appear(button=BUTTON_GG_SCRIPT_FATAL, offset=(50, 50)):
                logger.info('Stop previous script')
                self.device.click(BUTTON_GG_SCRIPT_FATAL)
            elif self.appear(button=BUTTON_GG_APP_CHOOSE, offset=(150, 500)):
                logger.info('APP choose')
                self.device.click(BUTTON_GG_APP_CHOOSE)
            elif self.appear(button=BUTTON_GG_SEARCH_MODE_CONFIRM, offset=(10, 10), threshold=0.95):
                self.device.click(BUTTON_GG_SCRIPT_ENTER_POS)
                logger.info('Enter script choose')
            else:
                self.device.click(BUTTON_GG_TAB_SEARCH_POS)
                logger.info('Enter search mode')
        skip_first_screenshot = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.sleep(0.5)
                self.device.screenshot()
            if self.appear(button=BUTTON_GG_SCRIPT_START, offset=(50, 50)):
                self.device.click(BUTTON_GG_SCRIPT_START)
                return 1

    def _gg_mode(self):
        """
        Page:
            in: GG Script Menu
            out: GG GG input panel
        """
        skip_first_screenshot = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.sleep(0.5)
                self.device.screenshot()
            if self.appear(button=BUTTON_GG_SCRIPT_MENU_A, offset=(50, 50), threshold=0.8):
                method = [BUTTON_GG_SCRIPT_MENU_B, BUTTON_GG_SCRIPT_MENU_A]
                self.device.click(method[int(self._mode)])
                break

    def _gg_handle_factor(self):
        """
        Page:
            in: GG input panel
            out:factor set(Not ensured yet)
        """
        self.wait_until_appear(button=BUTTON_GG_SCRIPT_START_PROCESS, skip_first_screenshot=True)
        logger.info(f'Factor={self._factor}')
        if self._factor == 200:
            logger.info('Skip factor input')
            return 0
        method = [
            BUTTON_GG_SCRIPT_PANEL_NUM0,
            BUTTON_GG_SCRIPT_PANEL_NUM1,
            BUTTON_GG_SCRIPT_PANEL_NUM2,
            BUTTON_GG_SCRIPT_PANEL_NUM3,
            BUTTON_GG_SCRIPT_PANEL_NUM4,
            BUTTON_GG_SCRIPT_PANEL_NUM5,
            BUTTON_GG_SCRIPT_PANEL_NUM6,
            BUTTON_GG_SCRIPT_PANEL_NUM7,
            BUTTON_GG_SCRIPT_PANEL_NUM8,
            BUTTON_GG_SCRIPT_PANEL_NUM9,
        ]
        for i in str(self._factor):
            self.appear_then_click(button=method[int(i)], offset=(50, 50))
            self.device.sleep(0.5)
        logger.info('Input success')

    def _gg_script_run(self):
        """
        Page:
            in: GG factor set
            out: GG Menu
        """
        skip_first_screenshot = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.sleep(0.5)
                self.device.screenshot()
            if self.appear_then_click(button=BUTTON_GG_SCRIPT_START_PROCESS, offset=(50, 50), threshold=0.9):
                break

        logger.info('Waiting for end')
        skip_first_screenshot = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.sleep(0.5)
                self.device.screenshot()
            if self.appear_then_click(button=BUTTON_GG_SCRIPT_END, offset=(50, 50), threshold=0.9):
                return 1

    def gg_set(self, mode=True, factor=200):
        import os
        os.popen(f'"toolkit/Lib/site-packages/adbutils/binaries/adb.exe" -s'
                 f' {self.device.serial} shell mkdir /sdcard/Notes')
        self.device.sleep(0.5)
        os.popen(f'"toolkit/Lib/site-packages/adbutils/binaries/adb.exe" -s'
                 f' {self.device.serial} shell rm /sdcard/Notes/Multiplier.lua')
        self.device.sleep(0.5)
        os.popen(f'"toolkit/Lib/site-packages/adbutils/binaries/adb.exe" -s'
                 f' {self.device.serial} push "bin/Lua/Multiplier.lua" /sdcard/Notes/Multiplier.lua')
        self.device.sleep(0.5)
        logger.info('Lua Pushed')

        # self._gg_package_name = deep_get(self.config.data, keys='GameManager.GGHandler.GGPackageName')
        # if self._gg_package_name != 'com.':
        #     os.popen(f'"toolkit/Lib/site-packages/adbutils/binaries/adb.exe" -s'
        #              f' {self.device.serial} shell am start -n {self._gg_package_name}')
        self._mode = mode
        self._factor = factor
        self._enter_gg()
        self._gg_enter_script()
        self._gg_mode()
        self._gg_handle_factor()
        self._gg_script_run()
        GGData(self.config).set_data(target='gg_on', value=self._mode)
        self.skip_error()
        logger.attr('GG', 'Enabled')