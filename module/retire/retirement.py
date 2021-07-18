from module.base.button import ButtonGrid
from module.base.decorator import Config
from module.base.utils import get_color, color_similar
from module.combat.assets import GET_ITEMS_1
from module.exception import ScriptError
from module.logger import logger
from module.retire.assets import *
from module.retire.enhancement import Enhancement

CARD_GRIDS = ButtonGrid(
    origin=(93, 76), delta=(164 + 2 / 3, 227), button_shape=(138, 204), grid_shape=(7, 2), name='CARD')
CARD_RARITY_GRIDS = ButtonGrid(
    origin=(93, 76), delta=(164 + 2 / 3, 227), button_shape=(138, 5), grid_shape=(7, 2), name='RARITY')

CARD_RARITY_COLORS = {
    'N': (174, 176, 187),
    'R': (106, 195, 248),
    'SR': (151, 134, 254),
    'SSR': (248, 223, 107)
    # Not support marriage cards.
}


class Retirement(Enhancement):
    _unable_to_enhance = False

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
            self.device.click(SORTING_CLICK)
            self.handle_dock_cards_loading()
            self.device.screenshot()
            return True
        else:
            return False

    def _retirement_set_common_ship_filter(self, enable=False):
        """
        Args:
            enable (bool): If enable common_ship_filter

        Returns:
            bool: If changed.
        """
        self.device.screenshot()
        if self.appear(COMMON_SHIP_FILTER_ENABLE):
            current = True
        elif self.appear(COMMON_SHIP_FILTER_DISABLE):
            current = False
        else:
            logger.warning('Common ship filter not detected, skipped')
            return False

        if current != enable:
            logger.info(f'Common ship filter set to {enable}')
            self.device.click(COMMON_SHIP_FILTER_ENABLE)
            self.handle_dock_cards_loading()
            self.device.screenshot()
            return True
        else:
            return False

    def _retirement_confirm(self):
        executed = False
        while 1:
            self.device.screenshot()
            if self.config.RETIRE_SR or self.config.RETIRE_SSR or self.config.RETIREMENT_METHOD == 'one_click_retire':
                if self.appear_then_click(SR_SSR_CONFIRM, offset=(10, 50), interval=2):
                    continue
            if self.appear_then_click(SHIP_CONFIRM, offset=(30, 30), interval=2):
                continue
            if self.appear_then_click(SHIP_CONFIRM_2, offset=(30, 30), interval=2):
                continue
            if self.appear_then_click(EQUIP_CONFIRM, offset=(30, 30), interval=2):
                continue
            if self.appear_then_click(EQUIP_CONFIRM_2, offset=(30, 30), interval=2):
                executed = True
                continue
            if self.appear(GET_ITEMS_1, offset=(30, 30)):
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

    def _retirement_quit_check_func(self):
        return not self.appear(IN_RETIREMENT_CHECK)

    def _retirement_quit(self):
        self.ui_back(check_button=self._retirement_quit_check_func, skip_first_screenshot=True)

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

    @Config.when(RETIREMENT_METHOD='one_click_retire')
    def retire_ships(self, amount=None, rarity=None):
        logger.hr('Retirement')
        logger.info('Using one click retirement.')
        self._retirement_set_common_ship_filter()
        if amount is None:
            amount = self._retire_amount
        end = False
        total = 0

        while 1:
            self.handle_info_bar()

            while 1:
                self.device.screenshot()
                if self.appear(SHIP_CONFIRM_2):
                    break
                if self.info_bar_count():
                    logger.info('No more ships to retire.')
                    end = True
                    break
                if self.appear_then_click(ONE_CLICK_RETIREMENT, interval=2):
                    continue

            if end:
                break
            self._retirement_confirm()
            total += 10
            if total >= amount:
                break

        logger.info(f'Total retired round: {total // 10}')
        return total

    @Config.when(RETIREMENT_METHOD='old_retire')
    def retire_ships(self, amount=None, rarity=None):
        """
        Args:
            amount (int): Amount of cards retire. 0 to 2000.
            rarity (tuple(str)): Card rarity. N, R, SR, SSR.

        Returns:
            int: Total retired.
        """
        if amount is None:
            amount = self._retire_amount
        if rarity is None:
            rarity = self._retire_rarity
        logger.hr('Retirement')
        logger.info(f'Amount={amount}. Rarity={rarity}')
        self._retirement_set_sort_method('ASC')
        self._retirement_set_common_ship_filter()
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
        return total

    def handle_retirement(self):
        if not self.config.ENABLE_RETIREMENT:
            return False
        if not self.retirement_appear():
            return False

        if self._unable_to_enhance:
            self.config.RETIREMENT_METHOD = 'one_click_retire'
            total = self._retire_handler()
            self.config.RETIREMENT_METHOD = 'enhance'
            self._unable_to_enhance = False
            if not total:
                logger.warning('No ship retired, exit')
                logger.info('This may happens because wrong options of one click retirement in game')
                exit(1)
        elif 'retire' in self.config.RETIREMENT_METHOD or self._unable_to_enhance:
            total = self._retire_handler()
            self._unable_to_enhance = False
            if not total:
                logger.warning('No ship retired, exit')
                logger.info('This may happens because some filters are set in dock')
                exit(1)
        else:
            total = self._enhance_handler()
            if not total:
                logger.info('No ship to enhance, but dock full, will try retire')
                self._unable_to_enhance = True

        return True

    def _retire_handler(self):
        self.ui_click(RETIRE_APPEAR_1, check_button=IN_RETIREMENT_CHECK, skip_first_screenshot=True)
        self.handle_dock_cards_loading()

        total = self.retire_ships()
        if not total:
            logger.warning('No ship retired, trying to reset dock filter and disable favourite, then retire again')
            self.dock_filter_set_faster()
            self.dock_favourite_set(enable=False)
            total = self.retire_ships()

        self._retirement_quit()
        self.config.DOCK_FULL_TRIGGERED = True

        return total
