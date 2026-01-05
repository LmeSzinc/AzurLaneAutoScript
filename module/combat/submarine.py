from module.base.base import ModuleBase
from module.base.timer import Timer
from module.combat.assets import *
from module.logger import logger


class SubmarineCall(ModuleBase):
    submarine_call_flag = False
    submarine_call_timer = Timer(5)
    submarine_call_click_timer = Timer(1)
    submarine_call_delay_timer = None

    def submarine_call_reset(self, call_delay=0):
        """
        Call this method after in battle_execute.
        
        Args:
            call_delay (float): Delay time before calling submarine, in seconds.
        """
        self.submarine_call_timer.reset()
        self.submarine_call_flag = False
        if call_delay > 0:
            self.submarine_call_delay_timer = Timer(call_delay)
            self.submarine_call_delay_timer.start()
        else:
            self.submarine_call_delay_timer = None

    def handle_submarine_call(self, submarine='do_not_use'):
        """
        Returns:
            str: If call.
        """
        if self.submarine_call_flag:
            return False
        if submarine in ['do_not_use', 'hunt_only', 'hunt_and_boss']:
            self.submarine_call_flag = True
            return False
        
        # Check if delay timer is active, and if it hasn't reached yet
        if self.submarine_call_delay_timer is not None:
            if not self.submarine_call_delay_timer.reached():
                return False
            # Delay reached, disable the timer
            self.submarine_call_delay_timer = None
        
        if self.submarine_call_timer.reached():
            logger.info('Submarine call timer reached')
            self.submarine_call_flag = True
            return False

        if not self.appear(SUBMARINE_AVAILABLE_CHECK_1) or not self.appear(SUBMARINE_AVAILABLE_CHECK_2):
            return False

        if self.appear(SUBMARINE_CALLED):
            logger.info('Submarine called')
            self.submarine_call_flag = True
            return False
        elif self.submarine_call_click_timer.reached():
            if not self.appear_then_click(SUBMARINE_READY):
                logger.info('Incorrect submarine icon')
                self.device.click(SUBMARINE_READY)
            logger.info('Call submarine')
            self.submarine_call_click_timer.reset()
            return True
