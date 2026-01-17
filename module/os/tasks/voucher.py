from module.config.utils import get_os_next_reset
from module.logger import logger
from module.os.map import OSMap
from module.os_handler.assets import EXCHANGE_CHECK, EXCHANGE_ENTER
from module.shop.shop_voucher import VoucherShop


class OpsiVoucher(OSMap):
    def _os_voucher_enter(self):
        self.os_map_goto_globe(unpin=False)
        self.ui_click(click_button=EXCHANGE_ENTER, check_button=EXCHANGE_CHECK,
                      offset=(200, 20), retry_wait=3, skip_first_screenshot=True)

    def _os_voucher_exit(self):
        self.ui_back(check_button=EXCHANGE_ENTER, appear_button=EXCHANGE_CHECK,
                     offset=(200, 20), retry_wait=3, skip_first_screenshot=True)
        self.os_globe_goto_map()

    def os_voucher(self):
        logger.hr('OS voucher', level=1)
        self._os_voucher_enter()
        VoucherShop(self.config, self.device).run()
        self._os_voucher_exit()

        next_reset = get_os_next_reset()
        logger.info('OS voucher finished, delay to next reset')
        logger.attr('OpsiNextReset', next_reset)
        self.config.task_delay(target=next_reset)
