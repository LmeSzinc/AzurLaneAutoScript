from module.logger import logger
from module.gg_handler.assets import *
from module.gg_handler.gg_data import gg_data
from module.base.base import ModuleBase as base

class gg_handler(base):

    def __init__(self,config,device,switch=True,factor=200):
        self.s=switch
        self.f=factor
        self.device=device
        self.config=config
        
    def gg_skip_error(self):
        """
        Page: 
            in: Game down error
            out: restart
        """
        self.device.sleep(3)
        self.device.screenshot()
        if base.appear(self,BUTTON_GG_RESTART_ERROR,offset=30,threshold=0.5):
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
            if base.appear(self,BUTTON_GG_CONFIRM, offset=30,threshold=0.8):
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
            self.device.screenshot()
            self.device.sleep(2)
            if base.appear(self,BUTTON_GG_SEARCH_MODE_CONFIRM,offset=30,threshold=0.8):
                self.device.click(BUTTON_GG_SCRIPT_ENTER_POS)
                logger.info('GG script ready to start')
                break
            elif base.appear_then_click(self,BUTTON_GG_SCRIPT_END, offset=30,threshold=0.8):
                logger.info('Close previous script')
            elif base.appear_then_click(self,BUTTON_GG_SCRIPT_FATAL, offset=30,threshold=0.8):
                logger.info('Stop previous script')
            elif base.appear_then_click(self,BUTTON_GG_APP_CHOOSE, offset=30,threshold=0.8):
                logger.info('APP choose')
            else:
                if base.appear(self,BUTTON_GG_SCRIPT_ENTER_CONFIRM, offset=30,threshold=0.8):
                    break
                self.device.click(BUTTON_GG_TAB_SEARCH_POS)
        while 1:
            self.device.screenshot()
            if base.appear_then_click(self,BUTTON_GG_SCRIPT_START, offset=30,threshold=0.8):
                return 1
        
            
        
    def _gg_mode(self):
        """
        Page:
            in: GG Script Menu
            out: GG GG input panel
        """
        while 1:
            self.device.screenshot()
            if base.appear(self,BUTTON_GG_SCRIPT_MENU_A, offset=30,threshold=0.8):
                method=[BUTTON_GG_SCRIPT_MENU_B,BUTTON_GG_SCRIPT_MENU_A]
                self.device.click(method[int(self.s)])
                break
        self.device.sleep(1)
        
    
    def _gg_handle_factor(self):
        """
        Page:
            in: GG input panel
            out:factor set(Not ensured yet)
        """
        logger.info(f'Factor={self.f}')
        if self.f==200 : 
            logger.info('Skip factor input')
            return 0
        logger.info(self.f)
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
        for i in str(self.f):
            self.device.click(method[int(i)])
            self.device.sleep(0.5)
        logger.info('Input success')


    def _gg_script_run(self):
        """
        Page:
            in: GG factor set
            out: GG Menu
        """
        while 1:
            self.device.screenshot()
            if base.appear_then_click(self,BUTTON_GG_SCRIPT_START_PROCESS, offset=30,threshold=0.8):
                break
        
        logger.info('Waiting for end')
        while 1:
            self.device.screenshot()
            if base.appear_then_click(self,BUTTON_GG_SCRIPT_END, offset=30,threshold=0.8):
                return 1
    
    def _gg_exit(self):
        while 1:
            self.device.screenshot()
            if not base.appear(self,BUTTON_GG_CONFIRM, offset=30,threshold=0.8):
                return 1
            self.device.click(BUTTON_GG_EXIT_POS)
        logger.info(f'GG status: {switch}')
            

    def gg_run(self):
        self._enter_gg()
        self._gg_enter_script()
        self._gg_mode()
        self._gg_handle_factor()
        self._gg_script_run()
        gg_data(self.config,target='gg_on',value=self.s).set_data()
        self._gg_exit()
    
    # def gg_reset(self):
        # self.gg_run(False,)
        # self.