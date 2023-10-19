from module.logger import logger
from module.config.config import deep_get
from module.base.base import ModuleBase
import uiautomator2 as u2

class ChangeAttribute(ModuleBase):

    def __init__(self, config, device):
        super().__init__(config, device)
        self.d = u2.connect(self.device.serial)
        self.gg_package_name = deep_get(self.config.data, keys='GameManager.GGHandler.GGPackageName')

    def GetShipData(self):
        DataList: str = deep_get(self.config.data, "GameManager.ChangeAttribute.ShipData").split("\n")
        DataString = "|".join(DataList)
        return DataString

    def PushLua(self):
        IsPush = deep_get(self.config.data, keys='GameManager.ChangeAttribute.PushLua')
        if IsPush:
            self.device.adb_shell("mkdir /sdcard/Notes")
            self.device.sleep(0.5)
            self.device.adb_shell("rm /sdcard/Notes/ShipFucker.lua")
            self.device.sleep(0.5)
            self.device.adb_push("bin/Lua/ShipFucker.lua", "/sdcard/Notes/ShipFucker.lua")
            self.device.sleep(0.5)
            logger.info('Lua Pushed')

    def ChangeAttribute(self):
        if not deep_get(self.config.data, "GameManager.ChangeAttribute.Enable"):
            return 0
        _set = False
        _confirmed = False
        while 1:
            if self.d(resourceId=f"{self.gg_package_name}:id/search_toolbar").exists:
                self.d.xpath(
                    f'//*[@resource-id="{self.gg_package_name}'
                    f':id/search_toolbar"]/android.widget.ImageView[last()]'
                ).click()
            self.device.sleep(1)
            if self.d(resourceId=f"{self.gg_package_name}:id/file").exists:
                self.d(resourceId=f"{self.gg_package_name}:id/file").send_keys("/sdcard/Notes/ShipFucker.lua")
                logger.info('Lua path set')
            if self.d.xpath('//*[@text="执行"]').exists:
                self.d.xpath('//*[@text="执行"]').click()
                logger.info('Click Run')
                self.device.sleep(0.5)
            if self.d.xpath('//*[contains(@text,"改属性")]').exists:
                self.d.xpath('//*[contains(@text,"改属性")]').click()
                logger.info('Click Change Statistic')
                self.device.sleep(0.5)
            if self.d(resourceId=f"{self.gg_package_name}:id/edit").exists:
                ShipDataString = self.GetShipData()
                self.d(resourceId=f"{self.gg_package_name}:id/edit")[0].send_keys(ShipDataString)
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
                    self.device.sleep(0.5)
                    self.d.xpath('//*[@text="确定"]').click()
                finally:
                    pass
            self.d.wait_timeout = 3
            if _set and _confirmed:
                break
            else:
                return 0