from module.logger import logger
from module.gg_handler.assets import *
from module.base.base import ModuleBase as base

class gg_handler:
        
    def gg_skip_error(self):
        """
        Page: 
            in: Game down error
            out: restart
        """
        self.device.sleep(3)
        if base.appear(self,BUTTON_GG_RESTART_ERROR,threshold=10):
            logger.info('Game died with GG panel')
            self.device.click(BUTTON_GG_RESTART_ERROR)
            self.device.sleep(1)
            
        else:
            logger.info('Game died with no GG panel')
            
        

    
    def _enter_gg(self):
        '''
        Page:
            in: any
            out: any GG
        '''
        self.device.click(BUTTON_GG_ENTER_POS)
        skip_first_screenshot=False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if base.appear(self,BUTTON_GG_CONFIRM, offset=1,threshold=0.5):
                logger.info('Entered GG')
                break
        self.device.sleep(1)
        
        
    def _gg_enter_script(self):
        """
        Page:
            in: any GG
            out: GG ready to start script
        """
        while 1:
            self.device.sleep(0.5)
            if base.appear(self,BUTTON_GG_SEARCH_MODE_CONFIRM,threshold=10):
                self.device.click(BUTTON_GG_SCRIPT_ENTER_POS,threshold=10)
                logger.info('GG script ready to start')
                break
            elif base.appear_then_click(self,BUTTON_GG_SCRIPT_END,threshold=10):
                logger.info('Close previous script')
            elif base.appear_then_click(self,BUTTON_GG_SCRIPT_FATAL,threshold=10):
                logger.info('Stop previous script')
            elif base.appear_then_click(self,BUTTON_GG_APP_CHOOSE,threshold=10):
                logger.info('APP choose')
            else:
                if base.appear(self,BUTTON_GG_SCRIPT_ENTER_CONFIRM,threshold=10):
                    break
                self.device.click(BUTTON_GG_TAB_SEARCH_POS)
       
        base.appear_then_click(self,BUTTON_GG_SCRIPT_START,threshold=10)    
        
            
        
    def _gg_mode(self,switch=True):
        """
        Page:
            in: GG Script Menu
            out: GG GG input panel
        """
        while 1:
            if base.appear(self,BUTTON_GG_SCRIPT_MENU_A,threshold=10):
                method=[BUTTON_GG_SCRIPT_MENU_B,BUTTON_GG_SCRIPT_MENU_A]
                self.device.click(method[int(switch)])
        self.device.sleep(1)
        
    
    def _gg_handle_factor(self,factor=200):
        """
        Page:
            in: GG input panel
            out:factor set(Not ensured yet)
        """
        if factor==200 : return 0
        method=[
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
        for i in str(factor):
            self.device.click(method[int(i)])
            self.device.sleep(1)



    def _gg_script_run(self):
        """
        Page:
            in: GG factor set
            out: GG Menu
        """
        self.device.sleep(1)
        base.appear_then_click(self,BUTTON_GG_SCRIPT_START_PROCESS)
        self.device.sleep(1)
        base.wait_until_appear_then_click(self,BUTTON_GG_SCRIPT_END)
    
    def _gg_exit(self):
        while base.appear(self,BUTTON_GG_CONFIRM, threshold=0.5):
            base.appear_then_click(self,BUTTON_GG_EXIT_POS, threshold=105)

    def gg_run(self,switch=True,factor=200):
        self._enter_gg()
        self._gg_enter_script()
        self._gg_mode(switch)
        self._gg_handle_factor(factor)
        self._gg_script_run()
        self._gg_exit()
    