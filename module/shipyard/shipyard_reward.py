from module.logger import logger
from module.shipyard.ui import ShipyardUI
from module.shop.shop_general import GeneralShop
from module.ui.page import page_main, page_shipyard

PRBP_BUY_PRIZE = {
    (1, 2):               0,
    (3, 4):               150,
    (5, 6, 7):            300,
    (8, 9, 10):           600,
    (11, 12, 13, 14, 15): 1050,
}


class RewardShipyard(ShipyardUI, GeneralShop):
    def _shipyard_calculate(self, start, count, pay=False):
        """
        Calculates the maximum number
        of BPs based on current parameters
        and _shop_gold_coins amount

        Submits payment if 'pay' set to True

        Args:
            start (int): BUY_PRIZE key to resume at
            count (int): Total remaining to buy
            pay (bool): Finalize payment to _shop_gold_coins

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
            cost = [v for k, v in PRBP_BUY_PRIZE.items() if i in k]
            if not len(cost):
                cost = [1500]

            if (total + cost[0]) > self._currency:
                if pay:
                    self._currency -= total
                else:
                    logger.info(f'Can only buy up to {(i - start)} '
                                f'of the {count} BPs')
                return i, i - start
            total += cost[0]

        if pay:
            self._currency -= total
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
        finalize payment to _shop_gold_coins
        """
        return self._shipyard_calculate(start, count, pay=True)

    def _shipyard_buy(self, count):
        """
        Buy up to the configured number of BPs
        Supports buying in both DEV and FATE

        Args:
            count (int): Total to buy
        """
        prev = 1
        start, count = self._shipyard_buy_calc(prev, count)
        while count > 0:
            if not self._shipyard_buy_enter() or \
                    self._shipyard_cannot_strengthen():
                break

            remain = self._shipyard_ensure_index(count)
            if remain is None:
                break
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
        # Gold difficult to Ocr in page_shipyard
        # due to both text and number being
        # right-aligned together
        # Retrieve information from page_main instead
        if not self.ui_page_appear(page_main):
            self.ui_goto_main()
        self.shop_currency()

        self.ui_ensure(page_shipyard)
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
        # Remove this when your server is updated for PR5
        logger.warning('Task "Shipyard" is forced delayed 2 hours before PR5 support. '
                       'Please do research manually and contact server maintainers')
        if self.config.SERVER in ['cn', 'en', 'jp', 'tw']:
            self.config.task_delay(minute=120)
            self.config.task_stop()

        if self.config.Shipyard_BuyAmount <= 0:
            self.config.Scheduler_Enable = False
            self.config.task_stop()

        self.shipyard_run(series=self.config.Shipyard_ResearchSeries,
                          index=self.config.Shipyard_ShipIndex,
                          count=self.config.Shipyard_BuyAmount)
        self.config.task_delay(server_update=True)
