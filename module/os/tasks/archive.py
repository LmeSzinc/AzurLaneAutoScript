from module.config.utils import get_nearest_weekday_date
from module.logger import logger
from module.os.map import OSMap
from module.os_handler.assets import EXCHANGE_CHECK, EXCHANGE_ENTER
from module.shop.shop_voucher import VoucherShop


class OpsiArchive(OSMap):
    def _os_voucher_enter(self):
        self.os_map_goto_globe(unpin=False)
        self.ui_click(click_button=EXCHANGE_ENTER, check_button=EXCHANGE_CHECK,
                      offset=(200, 20), retry_wait=3, skip_first_screenshot=True)

    def _os_voucher_exit(self):
        self.ui_back(check_button=EXCHANGE_ENTER, appear_button=EXCHANGE_CHECK,
                     offset=(200, 20), retry_wait=3, skip_first_screenshot=True)
        self.os_globe_goto_map()

    def os_archive(self):
        """
        Complete active archive zone in daily mission
        Purchase next available logger archive then repeat
        until exhausted

        Run on weekly basis, AL devs seemingly add new logger
        archives after random scheduled maintenances
        """
        if self.is_in_opsi_explore():
            logger.info('OpsiExplore is under scheduling, stop OpsiArchive')
            self.config.task_delay(server_update=True)
            self.config.task_stop()

        shop = VoucherShop(self.config, self.device)
        while True:
            # In case logger bought manually,
            # finish pre-existing archive zone
            self.os_finish_daily_mission(question=False, rescan=False)

            logger.hr('OS voucher', level=1)
            self._os_voucher_enter()
            bought = shop.run_once()
            self._os_voucher_exit()
            if not bought:
                break

        # Reset to nearest 'Wednesday' date
        next_reset = get_nearest_weekday_date(target=2)
        logger.info('All archive zones finished, delay to next reset')
        logger.attr('OpsiNextReset', next_reset)
        self.config.task_delay(target=next_reset)
