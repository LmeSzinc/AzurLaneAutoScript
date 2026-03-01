from module.config.utils import get_os_reset_remain
from module.logger import logger
from module.os.map import OSMap


class OpsiObscure(OSMap):
    def clear_obscure(self):
        """
        Raises:
            ActionPointLimit:
        """
        logger.hr('OS clear obscure', level=1)
        self.cl1_ap_preserve()
        if self.config.OpsiObscure_ForceRun:
            logger.info('OS obscure finish is under force run')

        result = self.storage_get_next_item('OBSCURE', use_logger=self.config.OpsiGeneral_UseLogger)
        if not result:
            # No obscure coordinates, delay next run to tomorrow.
            if get_os_reset_remain() > 0:
                self.config.task_delay(server_update=True)
            else:
                logger.info('Just less than 1 day to OpSi reset, delay 2.5 hours')
                self.config.task_delay(minute=150, server_update=True)
            self.config.task_stop()

        self.config.override(
            OpsiGeneral_DoRandomMapEvent=False,
            HOMO_EDGE_DETECT=False,
            STORY_OPTION=0,
        )
        self.zone_init()
        self.fleet_set(self.config.OpsiFleet_Fleet)
        self.os_order_execute(
            recon_scan=True,
            submarine_call=self.config.OpsiFleet_Submarine)
        self.run_auto_search(rescan='current')

        self.map_exit()
        self.handle_after_auto_search()

    def os_obscure(self):
        while True:
            self.clear_obscure()
            if self.config.OpsiObscure_ForceRun:
                self.config.check_task_switch()
                continue
            else:
                break
