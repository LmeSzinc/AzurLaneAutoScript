from module.base.button import ButtonGrid
from module.base.utils import get_color, color_similar
from module.combat.assets import GET_ITEMS_1
from module.handler.info_bar import InfoBarHandler
from module.logger import logger
from module.retire.assets import *
from module.ui.ui import UI, BACK_ARROW

CARD_GRIDS = ButtonGrid(origin=(93, 76), delta=(164 + 2 / 3, 227), button_shape=(138, 204), grid_shape=(7, 2), name='CARD')
CARD_RARITY_GRIDS = ButtonGrid(origin=(93, 76), delta=(164 + 2 / 3, 227), button_shape=(138, 5), grid_shape=(7, 2), name='RARITY')

CARD_RARITY_COLORS = {
    'N': (174, 176, 187),
    'R': (106, 195, 248),
    'SR': (151, 134, 254),
    'SSR': (248, 223, 107)
    # Not support marriage cards.
}

class Retirement(UI, InfoBarHandler):
    def _handle_retirement_cards_loading(self):
        self.device.sleep((1, 1.5))

    def _retirement_choose(self, amount=10, target_rarity=('N',)):
        """
        Args:
            amount (int): Amount of cards retire. 0 to 10.
            target_rarity (tuple(str)): Card rarity. N, R, SR, SSR.

        Returns:
            int: Amount of cards have retired.
        """
        cards = []
        rarity = []
        for x, y, button in CARD_RARITY_GRIDS.generate():
            card_color = get_color(image=self.device.image, area=button.area)
            f = False
            for r, rarity_color in CARD_RARITY_COLORS.items():

                if color_similar(card_color, rarity_color, threshold=15):
                    cards.append([x, y])
                    rarity.append(r)
                    f = True

            if not f:
                logger.warning(f'Unknown rarity color. Grid: ({x}, {y}). Color: {card_color}')

        logger.info(' '.join([r.rjust(3) for r in rarity[:7]]))
        logger.info(' '.join([r.rjust(3) for r in rarity[7:]]))

        selected = 0
        for card, r in zip(cards, rarity):
            if r in target_rarity:
                self.device.click(CARD_GRIDS[card])
                self.device.sleep((0.1, 0.15))
                selected += 1
            if selected >= amount:
                break
        return selected

    def _retirement_set_sort_method(self, method):
        """
        Args:
            method (str): ASC for ascending, DESC for descending.

        Returns:
            bool: If method change.
        """
        current = 'UNKNOWN'
        self.device.screenshot()
        if self.appear(SORT_ASC):
            current = 'ASC'
        if self.appear(SORT_DESC):
            current = 'DESC'

        logger.info(f'Current sorting: {current}')
        if current != method:
            logger.info(f'Sorting set to {method}')
            self.device.click(SORTNG_CLICK)
            self._handle_retirement_cards_loading()
            self.device.screenshot()
            return True
        else:
            return False

    def _retirement_confirm(self):
        executed = False
        while 1:
            self.device.screenshot()
            if self.appear_then_click(SHIP_CONFIRM, offset=30, interval=2):
                continue
            if self.appear_then_click(SHIP_CONFIRM_2, offset=30, interval=2):
                continue
            if self.appear_then_click(EQUIP_CONFIRM, offset=30, interval=2):
                continue
            if self.appear_then_click(EQUIP_CONFIRM_2, offset=30, interval=2):
                executed = True
                continue
            if self.appear(GET_ITEMS_1, interval=2):
                self.device.click(GET_ITEMS_1_RETIREMENT_SAVE)
                self.interval_reset(SHIP_CONFIRM)
                continue

            # End
            if executed and self.appear(IN_RETIREMENT_CHECK):
                # self._handle_retirement_cards_loading()
                # self.device.screenshot()
                self.handle_info_bar()
                self.device.screenshot()
                break

    def retirement_appear(self):
        return self.appear(RETIRE_APPEAR_1, offset=30) \
            and self.appear(RETIRE_APPEAR_2, offset=30) \
            and self.appear(RETIRE_APPEAR_3, offset=30)

    def _retirement_quit(self):
        skip = True
        while 1:
            if skip:
                skip = False
            else:
                self.device.screenshot()

            # End
            if not self.appear(IN_RETIREMENT_CHECK):
                break

            if self.appear_then_click(BACK_ARROW, offset=(20, 20)):
                continue

    @property
    def _retire_amount(self):
        if self.config.RETIRE_MODE == 'all':
            return 2000
        if self.config.RETIRE_MODE == '10':
            return 10
        return 10

    @property
    def _retire_rarity(self):
        rarity = set()
        if self.config.RETIRE_N:
            rarity.add('N')
        if self.config.RETIRE_R:
            rarity.add('R')
        if self.config.RETIRE_SR:
            rarity.add('SR')
        if self.config.RETIRE_SSR:
            rarity.add('SSR')
        return rarity

    def retire_ships(self, amount=None, rarity=None):
        """
        Args:
            amount (int): Amount of cards retire. 0 to 2000.
            rarity (tuple(str)): Card rarity. N, R, SR, SSR.
        """
        if amount is None:
            amount = self._retire_amount
        if rarity is None:
            rarity = self._retire_rarity
        logger.hr('Retirement')
        logger.info(f'Amount={amount}. Rarity={rarity}')
        self._retirement_set_sort_method('ASC')
        total = 0

        while amount:
            selected = self._retirement_choose(amount=10 if amount > 10 else amount, target_rarity=rarity)
            total += selected
            if selected == 0:
                break

            self._retirement_confirm()

            amount -= selected
            if amount <= 0:
                break

        self._retirement_set_sort_method('DESC')
        logger.info(f'Total retired: {total}')

    def handle_retirement(self, amount=None, rarity=None):
        if not self.config.ENABLE_RETIREMENT:
            return False
        if not self.retirement_appear():
            return False

        self.ui_click(RETIRE_APPEAR_1, check_button=IN_RETIREMENT_CHECK, skip_first_screenshot=True)
        self._handle_retirement_cards_loading()

        self.retire_ships(amount=amount, rarity=rarity)

        self._retirement_quit()
        return True
