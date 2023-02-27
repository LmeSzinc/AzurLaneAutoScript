from module.logger import logger
from module.gg_handler.gg_data import GGData
from module.config.config import deep_get
from module.base.base import ModuleBase as Base
import uiautomator2 as u2


class GGU2(Base):

    def __init__(self, config, device):
        super().__init__(config, device)
        self.factor = 200
        self.config = config
        self.device = device
        self.d = u2.connect(self.device.serial)
        self.gg_package_name = deep_get(self.config.data, keys='GameManager.GGHandler.GGPackageName')
        self.d.wait_timeout = 10.0

    def exit(self):
        self.d.app_stop(f'{self.gg_package_name}')
        logger.attr('GG', 'Killed')

    def skip_error(self):
        _skipped = 0
        if self.d.xpath('//*[@text="重启游戏"]').exists:
            _skipped = 1
            logger.hr('Game died with GG panel')
        logger.info('No matter GG panel exists or not, Kill GG')
        self.exit()
        return _skipped

    def set_on(self, factor=200):
        _name_dict = {
            'en' : 'Azur Lane',
            'cn' : '碧蓝航线',
            'jp' : 'アズールレーン',
            'tw' : '碧藍航線'
        }
        _server = deep_get(d=self.config.data, keys='GameManager.GGHandler.ServerLocation', default='cn')
        _name = _name_dict[_server]
        self.factor = factor
        ggdata = GGData(self.config).get_data()
        for _i in range(1):
            try:
                if ggdata['gg_on']:
                    logger.attr('GG', 'Enabled')
                    pass
                else:
                    chosen = False
                    if self.d(resourceId=f"{self.gg_package_name}:id/hot_point_icon").exists:
                        self.d(resourceId=f"{self.gg_package_name}:id/hot_point_icon").click()
                        logger.info('Open GG panel')
                        self.device.sleep(0.5)
                    else:
                        self.d.app_start(self.gg_package_name)
                        logger.info('Starting GG')
                        logger.info('In GG overview')
                        self.device.sleep(3)
                    while 1:
                        self.device.sleep(0.5)
                        if self.d.xpath('//*[@text="忽略"]').exists:
                            self.d.xpath('//*[@text="忽略"]').click()
                            logger.info("Click ignore")
                            self.device.sleep(0.3)
                            continue
                        if self.d(resourceId=f"{self.gg_package_name}:id/btn_start_usage").exists:
                            self.d(resourceId=f"{self.gg_package_name}:id/btn_start_usage").click()
                            logger.info('Click GG start button')
                            logger.attr('GG', 'Started')
                            self.device.sleep(0.3)
                            continue
                        if self.d(resourceId=f"{self.gg_package_name}:id/hot_point_icon").exists:
                            self.d(resourceId=f"{self.gg_package_name}:id/hot_point_icon").click()
                            logger.info('Open GG panel')
                            self.device.sleep(0.3)
                            continue
                        if self.d(resourceId=f"{self.gg_package_name}:id/search_tab").exists \
                                and not self.d(resourceId=f"{self.gg_package_name}:id/search_toolbar").exists:
                            self.d(resourceId=f"{self.gg_package_name}:id/search_tab").click()
                            logger.info('Switch to search tab')
                            self.device.sleep(0.3)
                            continue
                        if self.d.xpath(
                                f'//*[@package="{self.gg_package_name}" '
                                f'and @resource-id="android:id/text1" '
                                f'and contains(@text,"{_name}")]'
                        ).exists:
                            self.d.xpath(f'//*[contains(@text,"{_name}")]').click()
                            logger.info('Choose APP: AzurLane')
                            self.device.sleep(0.3)
                            chosen = True
                            continue
                        if not chosen and self.d(resourceId=f"{self.gg_package_name}:id/app_icon").exists:
                            self.d(resourceId=f"{self.gg_package_name}:id/app_icon").click()
                            logger.info('Click APP choosing tag')
                            self.device.sleep(0.3)
                            continue
                        if self.d(resourceId=f"{self.gg_package_name}:id/search_toolbar").exists:
                            self.d.xpath(
                                f'//*[@resource-id="{self.gg_package_name}'
                                f':id/search_toolbar"]/android.widget.ImageView[last()]'
                            ).click()
                            logger.info('Click run Scripts')
                            self.device.sleep(0.3)
                            if self._run():
                                return 1
                        if self.d.xpath('//*[@text="取消"]').exists:
                            self.d.xpath('//*[@text="取消"]').click()
                            logger.info("Cancel exists but not running script, click cancel")
                            self.device.sleep(0.3)
                            continue
                        if self.d.xpath('//*[@text="确定"]').exists:
                            self.d.xpath('//*[@text="确定"]').click()
                            logger.info("Confirm exists but script crashed, click confirm")
                            self.device.sleep(0.3)
                            continue
                        if self.d.xpath('//*[@text="重启游戏"]').exists:
                            self.d.d.xpath('//*[@text="重启游戏"]').click()
                            logger.info('GG Panel after game died exists, restart the game')
                            logger.info('Click Restart')
                            self.device.sleep(0.3)
                            continue
            finally:
                pass

    def _run(self):
        _run = False
        _set = False
        _confirmed = False
        import os
        os.popen(f'"toolkit/Lib/site-packages/adbutils/binaries/adb.exe" -s'
                 f' {self.config.Emulator_Serial} shell mkdir /sdcard/Notes')
        self.device.sleep(0.5)
        os.popen(f'"toolkit/Lib/site-packages/adbutils/binaries/adb.exe" -s'
                 f' {self.config.Emulator_Serial} shell rm /sdcard/Notes/Multiplier.lua')
        self.device.sleep(0.5)
        os.popen(f'"toolkit/Lib/site-packages/adbutils/binaries/adb.exe" -s'
                 f' {self.config.Emulator_Serial} push "bin/Lua/Multiplier.lua" /sdcard/Notes/Multiplier.lua')
        self.device.sleep(0.5)
        logger.info('Lua Pushed')
        while 1:
            self.device.sleep(1)
            if self.d(resourceId=f"{self.gg_package_name}:id/file").exists:
                self.d(resourceId=f"{self.gg_package_name}:id/file").send_keys("/sdcard/Notes/Multiplier.lua")
                logger.info('Lua path set')
            if self.d.xpath('//*[@text="执行"]').exists:
                self.d.xpath('//*[@text="执行"]').click()
                logger.info('Click Run')
                self.device.sleep(0.5)
            if self.d.xpath('//*[contains(@text,"修改面板")]').exists:
                self.d.xpath('//*[contains(@text,"修改面板")]').click()
                logger.info('Click Change Statistic')
                self.device.sleep(0.5)
            if self.d(resourceId=f"{self.gg_package_name}:id/edit").exists:
                self.d(resourceId=f"{self.gg_package_name}:id/edit").send_keys(f"{self.factor}")
                logger.info('Factor Set')
                self.device.sleep(0.5)
                _set = True
            if _set and self.d.xpath('//*[@text="确定"]').exists:
                self.d.xpath('//*[@text="确定"]').click()
                logger.info("Click confirm")
                self.device.sleep(0.5)
                _confirmed = True
            self.d.wait_timeout = 90.0

            if _set and _confirmed:
                try:
                    self.d.xpath('//*[@text="确定"]').click()
                    GGData(self.config).set_data(target='gg_on', value=True)
                finally:
                    pass
                GGData(self.config).set_data(target='gg_on', value='True')
                logger.attr('GG', 'Enabled')
                logger.info("Close the script")
            self.d.wait_timeout = 3
            if _set and _confirmed:
                break
            else:
                return 0
        logger.hr('GG Enabled', level=2)
        self.d.app_stop(self.gg_package_name)
        return 1