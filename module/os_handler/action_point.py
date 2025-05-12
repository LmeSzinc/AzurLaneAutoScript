from datetime import datetime

import module.config.server as server
from module.base.button import ButtonGrid
from module.base.timer import Timer
from module.base.utils import *
from module.config.utils import get_server_next_update
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter
from module.os_handler.assets import *
from module.os_handler.map_event import MapEventHandler
from module.statistics.item import Item, ItemGrid
from module.ui.assets import OS_CHECK
from module.ui.ui import UI

OCR_ACTION_POINT_REMAIN = Digit(ACTION_POINT_REMAIN, letter=(255, 219, 66), name='OCR_ACTION_POINT_REMAIN')
OCR_ACTION_POINT_REMAIN_OS = Digit(ACTION_POINT_REMAIN_OS, letter=(239, 239, 239),
                                   threshold=160, name='OCR_SHOP_YELLOW_COINS_OS')

OCR_OS_ADAPTABILITY = Digit([
    OS_ADAPTABILITY_ATTACK,
    OS_ADAPTABILITY_DURABILITY,
    OS_ADAPTABILITY_RECOVER
], letter=(231, 235, 239), lang="cnocr", name='OCR_OS_ADAPTABILITY')


class ActionPointBuyCounter(DigitCounter):
    def after_process(self, result):
        result = super().after_process(result)

        # Possible result: 0/5, 05
        if result == '05':
            result = '0/5'

        return result


if server.server != 'jp':
    # Letters in ACTION_POINT_BUY_REMAIN are not the numeric fonts usually used in azur lane.
    OCR_ACTION_POINT_BUY_REMAIN = ActionPointBuyCounter(
        ACTION_POINT_BUY_REMAIN, letter=(148, 247, 99), lang='cnocr', name='OCR_ACTION_POINT_BUY_REMAIN')
else:
    # The color of the digits ACTION_POINT_BUY_REMAIN is white in JP, which is light green in CN and EN.
    OCR_ACTION_POINT_BUY_REMAIN = ActionPointBuyCounter(
        ACTION_POINT_BUY_REMAIN, letter=(255, 255, 255), lang='cnocr', name='OCR_ACTION_POINT_BUY_REMAIN')


class ActionPointItem(Item):
    def predict_valid(self):
        return True


ACTION_POINT_GRID = ButtonGrid(
    origin=(323, 274), delta=(173, 0), button_shape=(115, 115), grid_shape=(4, 1), name='ACTION_POINT_GRID')
ACTION_POINT_ITEMS = ItemGrid(ACTION_POINT_GRID, templates={}, amount_area=(43, 89, 113, 113))
ACTION_POINT_ITEMS.item_class = ActionPointItem
ACTION_POINTS_COST = {
    1: 5,
    2: 10,
    3: 15,
    4: 20,
    5: 30,
    6: 40,
}
ACTION_POINTS_COST_OBSCURE = {
    1: 10,  # No obscure zones in CL1 actually
    2: 10,
    3: 20,
    4: 20,
    5: 40,
    6: 40,
}
ACTION_POINTS_COST_ABYSSAL = {
    1: 80,
    2: 80,
    3: 80,  # No abyssal zones under CL4 actually
    4: 80,
    5: 100,
    6: 100,
}
ACTION_POINTS_BUY = {
    1: 4000,
    2: 2000,
    3: 2000,
    4: 1000,
    5: 1000,
}
ACTION_POINT_BOX = {
    0: 0,
    1: 20,
    2: 50,
    3: 100,
}


class ActionPointLimit(Exception):
    pass


class ActionPointHandler(UI, MapEventHandler):
    _action_point_box = [0, 0, 0, 0]
    _action_point_current = 0
    _action_point_total = 0

    def _is_in_action_point(self):
        return self.appear(ACTION_POINT_USE, offset=(20, 20))

    def is_current_ap_visible(self):
        return self.match_template_color(CURRENT_AP_CHECK, offset=(40, 5), threshold=15)

    def action_point_use(self, skip_first_screenshot=True):
        prev = self._action_point_current
        self.interval_clear(ACTION_POINT_USE)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(ACTION_POINT_USE, offset=(20, 20), interval=3):
                self.device.sleep(0.3)
                continue

            if self.handle_popup_confirm('ACTION_POINT_USE'):
                continue

            self.action_point_safe_get()
            if self._action_point_current > prev:
                break

    def action_point_update(self):
        """
        Returns:
            int: Total action points, including ap boxes.
        """
        items = ACTION_POINT_ITEMS.predict(self.device.image, name=False, amount=True)
        box = [item.amount for item in items]
        current = OCR_ACTION_POINT_REMAIN.ocr(self.device.image)
        total = current
        if self.config.OS_ACTION_POINT_BOX_USE:
            total += np.sum(np.array(box) * tuple(ACTION_POINT_BOX.values()))
        oil = box[0]

        logger.info(f'Action points: {current}({total}), oil: {oil}')
        self._action_point_current = current
        self._action_point_box = box
        self._action_point_total = total

    def action_point_safe_get(self, skip_first_screenshot=True):
        timeout = Timer(3, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_current_ap_visible():
                break
            if timeout.reached():
                logger.warning('Get action points timeout, wait is_current_ap_visible timeout')
                break
            # Forced map event on the top of action point popup
            if self.handle_map_event():
                timeout.reset()
                continue

        skip_first_screenshot = True
        timeout = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Get action points timeout')
                break
            # Forced map event on the top of action point popup
            if self.handle_map_event():
                timeout.reset()
                continue

            self.action_point_update()

            # Having too many current AP, probably an OCR error
            if self._action_point_current > 600:
                continue

            oil, boxes = self._action_point_box[0], self._action_point_box[1:]
            # Having boxes
            if sum(boxes) > 0:
                if oil > 100:
                    break
                else:
                    # [11, 0, 1, 0]
                    continue
            # Or having oil
            # Might be 0 or 1 when page is not fully loaded
            # [1, 0, 0, 0]
            if oil > 100:
                break

    @staticmethod
    def action_point_get_cost(zone, pinned):
        """
        Args:
            zone (Zone): Zone to enter.
            pinned (str): Zone type. Available types: DANGEROUS, SAFE, OBSCURE, ABYSSAL, STRONGHOLD.

        Returns:
            int: Action points that will cost.
        """
        if pinned == 'DANGEROUS':
            cost = ACTION_POINTS_COST[zone.hazard_level] * 2
        elif pinned == 'SAFE':
            cost = ACTION_POINTS_COST[zone.hazard_level]
        elif pinned == 'OBSCURE':
            cost = ACTION_POINTS_COST_OBSCURE[zone.hazard_level]
        elif pinned == 'ABYSSAL':
            cost = ACTION_POINTS_COST_ABYSSAL[zone.hazard_level]
        elif pinned == 'STRONGHOLD':
            cost = 200
        else:
            logger.warning(f'Unable to get AP cost from zone={zone}, pinned={pinned}, assume it costs 40.')
            cost = 40

        if zone.is_port:
            cost = 0

        return cost

    def action_point_get_active_button(self):
        """
        Returns:
            int: 0 to 3. 0 for oil, 1 for 20 ap box, 2 for 50 ap box, 3 for 100 ap box.
        """
        for index, item in enumerate(ACTION_POINT_GRID.buttons):
            area = item.area
            color = get_color(self.device.image, area=(area[0], area[3] + 5, area[2], area[3] + 10))
            # Active button will turn blue.
            # Active: 196, inactive: 118 ~ 123.
            if color[2] > 160:
                return index

        logger.warning('Unable to find an active action point box button')
        return 1

    def action_point_set_button(self, index, skip_first_screenshot=True):
        """
        Args:
            index (int): 0 to 3. 0 for oil, 1 for 20 ap box, 2 for 50 ap box, 3 for 100 ap box.
            skip_first_screenshot (bool):

        Returns:
            bool: If success.
        """
        for _ in range(3):
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.action_point_get_active_button() == index:
                return True
            else:
                self.device.click(ACTION_POINT_GRID[index, 0])
                self.device.sleep(0.3)

        logger.warning('Failed to set action point button after 3 trial')
        return False

    def action_point_get_buy_remain(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Returns:
            int: Remaining number of purchases of action points

        Pages:
            in: ACTION_POINT_USE
        """
        timeout = Timer(1, count=2).start()
        current = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Get action points buy remain timeout')
                break

            current, _, total = OCR_ACTION_POINT_BUY_REMAIN.ocr(self.device.image)

            # Possible result: 0/5, 05
            if total == 0:
                continue

            break

        return current

    def action_point_buy(self, preserve=1000):
        """
        Use oil to buy action points.

        Args:
            preserve (int): Oil to preserve.

        Returns:
            bool: If bought

        Pages:
            in: ACTION_POINT_USE
        """
        self.action_point_set_button(0)
        current = self.action_point_get_buy_remain()
        buy_max = 5  # In current version of AL, players can buy 5 times of AP in a week.
        buy_count = buy_max - current
        buy_limit = self.config.OpsiGeneral_BuyActionPointLimit
        if buy_count >= buy_limit:
            logger.info('Reach the limit to buy action points this week')
            return False
        cost = ACTION_POINTS_BUY[current]
        oil = self._action_point_box[0]
        logger.info(f'Buy action points will cost {cost}, current oil: {oil}, preserve: {preserve}')
        if oil >= cost + preserve:
            self.action_point_use()
            return True
        else:
            logger.info('Not enough oil to buy')
            return False

    def action_point_quit(self, skip_first_screenshot=True):
        """
        Pages:
            in: ACTION_POINT_USE
            out: page_os
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            # sometimes you have action point popup without black-blurred background
            # ACTION_POINT_CANCEL and OS_CHECK both appears
            if not self.appear(ACTION_POINT_CANCEL, offset=(20, 20)):
                if self.appear(OS_CHECK, offset=(20, 20)):
                    break
            # Click
            if self.appear_then_click(ACTION_POINT_CANCEL, offset=(20, 20), interval=3):
                continue
            # Forced map event on the top of action point popup
            if self.handle_map_event():
                continue

    def handle_action_point(self, zone, pinned, cost=None, keep_current_ap=True, check_rest_ap=False):
        """
        Args:
            zone (Zone): Zone to enter.
            pinned (str): Zone type. Available types: DANGEROUS, SAFE, OBSCURE, ABYSSAL, STRONGHOLD.
            cost (int): Custom action point cost value.
            keep_current_ap (bool): Check action points first to avoid using remaining AP
                when it is not enough for tomorrow's daily.
            check_rest_ap (bool): Skip keep_current_ap if the sum of current action points and rest action points
                that can be obtained today exceeds 200.

        Returns:
            bool: If handled.

        Raises:
            ActionPointLimit: If not having enough action points.

        Pages:
            in: ACTION_POINT_USE
        """
        if not self._is_in_action_point():
            return False

        # AP boxes have an animation to show
        self.action_point_safe_get()
        if cost is None:
            cost = self.action_point_get_cost(zone, pinned)
        buy_checked = False

        # Check the rest action points
        if check_rest_ap:
            diff = get_server_next_update('00:00') - datetime.now()
            today_rest = int(diff.total_seconds() // 600)
            if self._action_point_current + today_rest >= 200:
                logger.info('The sum of the current action points and the rest action points'
                            ' that can be obtained today exceeds 200, skip AP check')
                logger.info(f'Current={self._action_point_current}  Rest={today_rest}')
                keep_current_ap = False

        # Check action points first
        if keep_current_ap:
            if self._action_point_total <= self.config.OS_ACTION_POINT_PRESERVE:
                logger.info(f'Reach the limit of action points, preserve={self.config.OS_ACTION_POINT_PRESERVE}')
                self.action_point_quit()
                raise ActionPointLimit

        for _ in range(12):
            # Having enough action points
            if self._action_point_current >= cost:
                logger.info('Having enough action points')
                self.action_point_quit()
                return True

            # Buy action points
            if self.config.OpsiGeneral_BuyActionPointLimit > 0 and not buy_checked:
                if self.action_point_buy(preserve=self.config.OpsiGeneral_OilLimit):
                    self.action_point_safe_get()
                    continue
                else:
                    buy_checked = True

            # Recheck if total ap is less than cost
            # If it is, skip using boxes
            if self._action_point_total < cost:
                logger.info('Not having enough action points')
                self.action_point_quit()
                raise ActionPointLimit

            # Sort action point boxes
            box = []
            for index in [1, 2, 3]:
                if self._action_point_box[index] > 0:
                    if self._action_point_current + ACTION_POINT_BOX[index] >= 200:
                        box.append(index)
                    else:
                        box.insert(0, index)

            # Use action point boxes
            if len(box):
                if self._action_point_total > self.config.OS_ACTION_POINT_PRESERVE:
                    self.action_point_set_button(box[0])
                    self.action_point_use()
                    continue
                else:
                    logger.info(f'Reach the limit of action points, preserve={self.config.OS_ACTION_POINT_PRESERVE}')
                    self.action_point_quit()
                    raise ActionPointLimit
            else:
                logger.info('No more action point boxes')
                self.action_point_quit()
                raise ActionPointLimit

        logger.warning('Failed to get action points after 12 trial')
        return False

    def action_point_enter(self, skip_first_screenshot=True):
        """
        Pages:
            in: OS_CHECK
            out: ACTION_POINT_USE
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(ACTION_POINT_USE, offset=(20, 20)):
                break

            if self.appear(OS_CHECK, offset=(20, 20), interval=3):
                self.device.click(ACTION_POINT_REMAIN_OS)
                continue
            if self.handle_map_event():
                continue
            if self.appear_then_click(AUTO_SEARCH_REWARD, offset=(50, 50)):
                continue

    def action_point_set(self, zone=None, pinned=None, cost=None, keep_current_ap=True, check_rest_ap=False):
        """
        Args:
            zone (Zone): Zone to enter.
            pinned (str): Zone type. Available types: DANGEROUS, SAFE, OBSCURE, ABYSSAL, STRONGHOLD.
            cost (int): Custom action point cost value.
            keep_current_ap (bool): Check action points first to avoid using remaining AP
                when it not enough for tomorrow's daily
            check_rest_ap (bool): Skip keep_current_ap if the sum of current action points and rest action points
                that can be obtained today exceeds 200.

        Returns:
            bool: If handled.

        Raises:
            ActionPointLimit: If not having enough action points.
        """
        self.action_point_enter()
        if not self.handle_action_point(zone, pinned, cost, keep_current_ap, check_rest_ap):
            return False

        while 1:
            if self.appear(IN_MAP, offset=(200, 5)):
                break
            self.device.screenshot()

        return True

    def action_point_check(self, amount):
        """
        Args:
            amount: Check if having this amount of action points.

        Returns:
            bool: If having enough AP.
        """
        self.action_point_enter()
        self.action_point_safe_get()

        enough = self._action_point_total > amount
        if enough:
            logger.info(f'Having {amount} action points')
        else:
            logger.info(f'Not having {amount} action points')

        self.action_point_quit()
        while 1:
            if self.appear(IN_MAP, offset=(200, 5)):
                break
            self.device.screenshot()

        return enough
