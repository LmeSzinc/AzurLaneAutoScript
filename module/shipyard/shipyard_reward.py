from datetime import datetime
from module.base.timer import Timer
from module.campaign.assets import OCR_OIL_CHECK
from module.campaign.campaign_status import OCR_COIN

from module.exception import ScriptError
from module.logger import logger
from module.shipyard.ui import ShipyardUI
from module.ui.page import page_reshmenu, page_shipyard
from module.config.utils import get_server_last_update

PRBP_BUY_PRIZE = {
    (1, 2):               0,
    (3, 4):               150,
    (5, 6, 7):            300,
    (8, 9, 10):           600,
    (11, 12, 13, 14, 15): 1050,
}
DRBP_BUY_PRIZE = {
    (1, 2):               0,
    (3, 4, 5, 6):         600,
    (7, 8, 9, 10):        1200,
    (11, 12, 13, 14, 15): 3000,
}


class RewardShipyard(ShipyardUI):
    _shipyard_bp_rarity = 'PR'
    _coin_count = 0

    def _shipyard_get_cost(self, amount, rarity=None):
        """
        Args:
            amount (int): Index of the blueprint to buy
            rarity (str): 'DR', 'PR'

        Returns:
            int: Prize to buy
        """
        if rarity is None:
            rarity = self._shipyard_bp_rarity

        if rarity == 'PR':
            cost = [v for k, v in PRBP_BUY_PRIZE.items() if amount in k]
            if len(cost):
                return cost[0]
            else:
                return 1500
        elif rarity == 'DR':
            cost = [v for k, v in DRBP_BUY_PRIZE.items() if amount in k]
            if len(cost):
                return cost[0]
            else:
                return 6000
        else:
            raise ScriptError(f'Invalid rarity in _shipyard_get_cost: {rarity}')

    def _shipyard_calculate(self, start, count, pay=False):
        """
        Calculates the maximum number
        of BPs based on current parameters
        and _coin_count amount

        Submits payment if 'pay' set to True

        Args:
            start (int): BUY_PRIZE key to resume at
            count (int): Total remaining to buy
            pay (bool): Finalize payment to _coin_count

        Returns:
            int, int
                - BUY_PRIZE for next _shipyard_buy_calc
                  call
                - Total capable of buying currently
        """
        if start <= 0 or count <= 0:
            return start, count

        total = 0
        i = start
        for i in range(start, (start + count)):
            cost = self._shipyard_get_cost(i)

            if (total + cost) > self._coin_count:
                if pay:
                    self._coin_count -= total
                else:
                    logger.info(f'Can only buy up to {(i - start)} '
                                f'of the {count} BPs')
                return i, i - start
            total += cost

        if pay:
            self._coin_count -= total
        else:
            logger.info(f'Can buy all {count} BPs')
        return i + 1, count

    def _shipyard_buy_calc(self, start, count):
        """
        Shorthand for _shipyard_calculate all information
        is relevant
        """
        return self._shipyard_calculate(start, count, pay=False)

    def _shipyard_pay_calc(self, start, count):
        """
        Shorthand for _shipyard_calculate partial
        information is relevant but most importantly
        finalize payment to _coin_count
        """
        return self._shipyard_calculate(start, count, pay=True)

    def _shipyard_buy(self, count):
        """
        Buy up to the configured number of BPs
        Supports buying in both DEV and FATE

        Args:
            count (int): Total to buy
        """
        logger.hr('shipyard_buy')
        prev = 1
        start, count = self._shipyard_buy_calc(prev, count)
        while count > 0:
            if not self._shipyard_buy_enter() or \
                    self._shipyard_cannot_strengthen():
                break

            remain = self._shipyard_ensure_index(count)
            if remain is None:
                break

            if self._shipyard_bp_rarity == 'DR':
                self.config.ShipyardDr_LastRun = datetime.now().replace(microsecond=0)
            else:
                self.config.Shipyard_LastRun = datetime.now().replace(microsecond=0)

            self._shipyard_buy_confirm('BP_BUY')

            # Pay for actual amount bought based on 'remain'
            # which also updates 'start' as a result
            # Save into 'prev' for next _shipyard_pay_calc
            start, _ = self._shipyard_pay_calc(prev, (count - remain))
            prev = start

            start, count = self._shipyard_buy_calc(start, remain)

    def _shipyard_use(self, index):
        """
        Spend all remaining extraneous BPs
        Supports using BPs in both DEV and FATE
        """
        logger.hr('shipyard_use')
        count = self._shipyard_get_bp_count(index)
        while count > 0:
            if not self._shipyard_buy_enter() or \
                    self._shipyard_cannot_strengthen():
                break

            remain = self._shipyard_ensure_index(count)
            if remain is None:
                break
            self._shipyard_buy_confirm('BP_USE')

            count = self._shipyard_get_bp_count(index)

    def shipyard_run(self, series, index, count):
        """
        Runs shop browse operations

        Args:
            series (int): 1-4 inclusively, button location
            index (int): 1-6 inclusively, button location
                         some series are restricted to 1-5
            count (int): number to buy after use

        Returns:
            bool: If shop attempted to run
                  thereby transition to respective
                  pages. If no transition took place,
                  then did not run
        """
        if count <= 0:
            return False

        # Gold difficult to Ocr in page_shipyard
        # due to both text and number being
        # right-aligned together
        # Retrieve information from page_reshmenu instead
        self.ui_ensure(page_reshmenu)
        timeout = Timer(1, count=1).start()
        skip_first_screenshot = True
        while True:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.appear(OCR_OIL_CHECK, offset=(5, 2)):
                break
            if timeout.reached():
                logger.warning('Assumes that OCR_COIN is in the right place')
                break

        self._coin_count = OCR_COIN.ocr(self.device.image)

        self.ui_goto(page_shipyard)
        if not self.shipyard_set_focus(series=series, index=index) \
                or not self._shipyard_buy_enter() \
                or self._shipyard_cannot_strengthen():
            return True

        self._shipyard_use(index=index)
        self._shipyard_buy(count=count)

        return True

    def run(self):
        """
        Pages:
            in: Any page
            out: page_shipyard
        """
        if self.config.Shipyard_BuyAmount <= 0 and self.config.ShipyardDr_BuyAmount <= 0:
            self.config.Scheduler_Enable = False
            self.config.task_stop()

        logger.hr('Shipyard DR', level=1)
        logger.attr('ShipyardDr_LastRun', self.config.ShipyardDr_LastRun)
        if self.config.ShipyardDr_LastRun > get_server_last_update('04:00'):
            logger.warning('Task Shipyard DR has already been run today, skip')
        else:
            self._shipyard_bp_rarity = 'DR'
            self.shipyard_run(series=self.config.ShipyardDr_ResearchSeries,
                              index=self.config.ShipyardDr_ShipIndex,
                              count=self.config.ShipyardDr_BuyAmount)

        logger.hr('Shipyard PR', level=1)
        logger.attr('Shipyard_LastRun', self.config.Shipyard_LastRun)
        if self.config.Shipyard_LastRun > get_server_last_update('04:00'):
            logger.warning('Task Shipyard PR has already been run today, stop')
            self.config.task_delay(server_update=True)
            self.config.task_stop()
        else:
            self._shipyard_bp_rarity = 'PR'
            self.shipyard_run(series=self.config.Shipyard_ResearchSeries,
                              index=self.config.Shipyard_ShipIndex,
                              count=self.config.Shipyard_BuyAmount)

        self.config.task_delay(server_update=True)
