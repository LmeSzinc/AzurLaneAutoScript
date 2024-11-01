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
    
    # 点击GG图标，打开界面
    def open_interface(self):
        self.click_template(GG_Logo, '[GG] Open interface success')

    # 选择需要修改的程序
    def select_game(self):
        self.click_template(GG_Game_LOGO, '[GG] Select game success')

    # 脚本中断确定
    def interrupt_check(self):
        self.click_template(GG_Interrupt_Check, '[GG] Interrupt check success')

    # 选择脚本
    def selet_script(self):
        self.click_template(GG_Execute1, '[GG] Execute1 click success')
        self.click_template(GG_Execute2, '[GG] Execute2 click success')

    # 选择模式
    def select_mode(self):
        self.click_template(GG_Select_Mode, '[GG] Select mode success')

    # 点击确定，执行脚本
    def execute_script(self):
        self.click_template(GG_Determine1, '[GG] Open script success')
        self.click_template(GG_Determine2, '[GG] Apply script success')

    def apply(self):
        logger.hr('Open GG', level=0)
        self.open_interface() # 点击图标，打开界面
        self.select_game()  # 选择程序
        self.interrupt_check() # 关闭脚本中止弹窗
        self.selet_script() # 选择运行脚本
        self.select_mode() # 选择脚本模式
        self.execute_script() # 点击确定
        # 检查GG界面是否关闭
        time.sleep(10)
        self.appear_then_click(GG_Close_Interface, offset=(30, 30), interval=5)
        logger.info('Open GG success')


