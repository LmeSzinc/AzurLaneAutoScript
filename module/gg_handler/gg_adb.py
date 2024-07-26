# import subprocess
#
# from module.logger import logger
# from module.gg_handler.gg_data import GGData
# from module.config.config import deep_get
# from module.base.base import ModuleBase as Base
# from module.base.utils import point2str, random_rectangle_point
# from module.device.method.adb import Adb
# from module.device.method.utils import (RETRY_TRIES, retry_sleep,
#                                         HierarchyButton, handle_adb_error)
# from module.exception import GameStuckError
#
# class GGADB(Adb):
#
#     def __init__(self, config):
#         super().__init__(config)
#         self.factor = 200
#         self.config = config
#         self.adb_reconnect()
#         self.gg_package_name = deep_get(self.config.data, keys='GameManager.GGHandler.GGPackageName')
#
#     def appear(self, xpath):
#         return bool(HierarchyButton(self.h, xpath))
#
#     def appear_then_click(self, xpath):
#         b = HierarchyButton(self.h, xpath)
#         if b:
#             point = random_rectangle_point(b.button)
#             logger.info(f'Click {point2str(*point)} @ {b}')
#             self.click_adb(*point)
#             return True
#         else:
#             return False
#
#     def exit(self):
#         self.app_stop_adb(f'{self.gg_package_name}')
#         logger.attr('GG', 'Killed')
#
#     def skip_error(self):
#         _skipped = 0
#         self.h = self.dump_hierarchy_adb()
#         if self.appear('//*[@text="重启游戏"]'):
#             _skipped = 1
#             logger.hr('Game died with GG panel')
#         logger.info('No matter GG panel exists or not, Kill GG')
#         self.exit()
#         return _skipped
#
#     def set_on(self, factor=200):
#         self.factor = factor
#         ggdata = GGData(self.config).get_data()
#         for _i in range(1):
#             try:
#                 if ggdata['gg_on']:
#                     logger.attr('GG', 'Enabled')
#                     pass
#                 else:
#                     chosen = False
#                     self.h = self.dump_hierarchy_adb()
#                     if self.appear_then_click(f'//*[@resource-id="com.ucr.tx:id/hot_frame"]'):
#                         logger.info('Open GG panel')
#                         Base.device.sleep(0.5)
#                     else:
#                         self.app_start_adb(self.gg_package_name)
#                         logger.info('Starting GG')
#                         logger.info('In GG overview')
#                         Base.device.sleep(3)
#                     while 1:
#                         Base.device.sleep(0.5)
#                         self.h = self.dump_hierarchy_adb()
#                         if self.appear_then_click('//*[@text="忽略"]'):
#                             logger.info("Click ignore")
#                             continue
#                         if self.appear_then_click(f'//*[@resource-id="{self.gg_package_name}:id/btn_start_usage"]'):
#                             logger.info('Click GG start button')
#                             logger.attr('GG', 'Started')
#                             continue
#                         if self.appear_then_click(f'//*[@resource-id="{self.gg_package_name}:id/hot_point_icon"]'):
#                             logger.info('Open GG panel')
#                             continue
#                         if self.appear(f'//*[@resource-id="{self.gg_package_name}:id/search_tab"]') \
#                                 and not self.appear(f'//*[@resource-id="{self.gg_package_name}:id/search_toolbar"]'):
#                             self.appear_then_click(f'//*[@resource-id="{self.gg_package_name}:id/search_tab"]')
#                             logger.info('Switch to search tab')
#                             continue
#                         if self.appear_then_click(
#                                 f'//*[@package="{self.gg_package_name}" '
#                                 f'and @resource-id="android:id/text1" '
#                                 f'and contains(@text,"碧蓝航线")]'
#                                         ):
#                             logger.info('Choose APP: AzurLane')
#                             chosen = True
#                             continue
#                         if not chosen and self.appear(f'//*[@resource-id="{self.gg_package_name}:id/app_icon"]'):
#                             self.appear_then_click(f'//*[@resource-id="{self.gg_package_name}:id/app_icon"]')
#                             logger.info('Click APP choosing tag')
#                             continue
#                         if self.appear(f'//*[@resource-id="{self.gg_package_name}:id/search_toolbar"]'):
#                             self.appear_then_click(f'//*[@resource-id="{self.gg_package_name}:id/search_toolbar"]/'
#                                                    f'android.widget.ImageView[last()]'
#                                                   )
#                             logger.info('Click run Scripts')
#                             if self._run():
#                                 return 1
#                         if self.appear_then_click('//*[@text="取消"]'):
#                             logger.info("Cancel exists but not running script, click cancel")
#                             continue
#                         if self.appear_then_click('//*[@text="确定"]'):
#                                 # and self.d.xpath('//*[contains(@text,"脚本已结束")]').exists:
#                             logger.info("Confirm exists but script crashed, click confirm")
#                             continue
#                         if self.appear_then_click('//*[@text="重启游戏"]'):
#                             logger.info('GG Panel after game died exists, restart the game')
#                             logger.info('Click Restart')
#                             continue
#             finally:
#                 pass
#
#     def _run(self):
#         _run = 0
#         _set = 0
#         _confirmed = 0
#         while 1:
#             self.h = self.dump_hierarchy_adb()
#             if self.appear(f'//*[@resource-id="{self.gg_package_name}:id/file"]'):
#                 self.adb_shell(['input', 'text', "/sdcard/Notes/Multiplier.lua"])
#                 logger.info('Lua path set')
#                 import os
#                 _pop = os.popen(f'"toolkit/Lib/site-packages/adbutils/binaries/adb.exe" '
#                             f'-s {self.device.serial} shell mkdir /sdcard/Notes')
#                 _pop = os.popen(f'"toolkit/Lib/site-packages/adbutils/binaries/adb.exe" '
#                             f'-s {self.device.serial} shell rm /sdcard/Notes/Multiplier.lua')
#                 _pop = os.popen(f'"toolkit/Lib/site-packages/adbutils/binaries/adb.exe" '
#                             f'-s {self.device.serial} push "Multiplier.lua" /sdcard/Notes/Multiplier.lua')
#             Base.device.sleep(0.5)
#             if self.appear_then_click('//*[@text="执行"]'):
#                 logger.info('Click Run')
#                 Base.device.sleep(0.5)
#             if self.appear_then_click('//*[contains(@text,"修改面板")]'):
#                 logger.info('Click Change Statistic')
#             if self.appear_then_click(f'//*[@resource-id="{self.gg_package_name}:id/edit"]'):
#                 logger.info('Factor Set')
#                 Base.device.sleep(0.5)
#                 _set = 1
#             if _set and self.appear('//*[@text="确定"]'):
#                 self.appear_then_click('//*[@text="确定"]')
#                 logger.info("Click confirm")
#                 Base.device.sleep(0.5)
#                 _confirmed = 1
#
#             from module.base.timer import Timer
#             timeout = Timer(90, count=90).start()
#             if _set and _confirmed:
#                 try:
#                     while 1:
#                         if self.appear_then_click('//*[@text="确定"]'):
#                             GGData(self.config).set_data(target='gg_on', value=True)
#                             break
#                         if timeout.reached():
#                             raise GameStuckError
#                 finally:
#                     pass
#                 GGData(self.config).set_data(target='gg_on', value='True')
#                 logger.attr('GG', 'Enabled')
#                 logger.info("Close the script")
#             if _set and _confirmed:
#                 break
#             else:
#                 return 0
#         logger.hr('GG Enabled', level=2)
#         self.app_stop_adb(self.gg_package_name)
#         return 1
