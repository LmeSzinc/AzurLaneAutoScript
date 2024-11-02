from module.handler.assets import *
from module.ui.assets import *
from module.ui.ui import UI
from module.base.timer import Timer
from module.logger import logger
from module.base.button import Button

import time

# 直接抄的登陆程序LoginHandler类的_handle_app_login

class GGHandler(UI):
    def click_template(self, button:Button, info:str):
        self.button = button

        confirm_timer = Timer(1.5, count=4).start()
        orientation_timer = Timer(5)
        click_success = False

        while 1:
            # Watch device rotation
            if not click_success and orientation_timer.reached():
                # Screen may rotate after starting an app
                self.device.get_orientation()
                orientation_timer.reset()

            self.device.screenshot()

            # Click
            if self.appear(self.button, offset=(30, 30), interval=5) and self.button.match_appear_on(self.device.image):
                self.device.click(self.button)
                if not click_success:
                    click_success = True

            if click_success:
                if confirm_timer.reached():
                    logger.info(info)
                    break
            else:
                confirm_timer.reset()

        return True

    # 重启时关闭报错弹窗
    def restart_check(self):
        logger.hr('GG Restart Check')
        self.click_template(GG_RestarCheck, 'GG Restart Check Success')

    # 开启GG
    def apply(self):
        logger.hr('Open GG', level=0)
        open_interface = False
        logger.hr('Steps 1', level=2)
        while 1:
            self.device.screenshot() # 截图

            if not open_interface:
                if self.appear_then_click(GG_Logo, offset=(30, 30), interval=5):
                    open_interface = True # 点击图标，打开界面
                    continue

            if self.appear_then_click(GG_Game_LOGO, offset=(30, 30), interval=5):
                continue # 选择程序

            if self.appear_then_click(GG_Interrupt_Check, offset=(30, 30), interval=5):
                continue  # 关闭脚本中止弹窗

            if self.appear_then_click(GG_Execute1, offset=(30, 30), interval=5):
                continue  # 选择运行脚本

            if self.appear_then_click(GG_Execute2, offset=(30, 30), interval=5):
                continue  # 选择运行脚本

            if self.appear_then_click(GG_Select_Mode, offset=(30, 30), interval=5):
                continue  # 选择脚本模式

            if self.appear_then_click(GG_Determine1, offset=(30, 30), interval=5):
                break  # 点击确定

        logger.hr('Steps 2', level=2)
        while 1:
            self.device.screenshot() # 截图
            if self.appear_then_click(GG_Determine2, offset=(30, 30), interval=5):
                break  # 点击确定
        # 检查GG界面是否关闭
        time.sleep(3)
        self.device.screenshot() # 截图
        self.appear_then_click(GG_Close_Interface, offset=(30, 30), interval=5)
        logger.info('Open GG success')


