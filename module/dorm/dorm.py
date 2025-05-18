import time
import typing as t

from module.base.button import ButtonGrid
from module.base.decorator import Config, cached_property
from module.base.filter import Filter
from module.base.mask import Mask
from module.base.timer import Timer
from module.base.utils import *
from module.dorm.assets import *
from module.dorm.buy_furniture import BuyFurniture
from module.handler.assets import POPUP_CONFIRM
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter
from module.template.assets import TEMPLATE_DORM_COIN, TEMPLATE_DORM_LOVE
from module.ui.assets import DORM_CHECK
from module.ui.page import page_dorm, page_dormmenu
from module.ui.ui import UI

MASK_DORM = Mask(file='./assets/mask/MASK_DORM.png')
DORM_CAMERA_SWIPE = (300, 250)
DORM_CAMERA_RANDOM = (-20, -20, 20, 20)
OCR_SLOT = DigitCounter(OCR_DORM_SLOT, letter=(107, 89, 82), threshold=128, name='OCR_DORM_SLOT')


class OcrDormFood(DigitCounter):
    def pre_process(self, image):
        orange = color_similarity_2d(image, color=(239, 158, 49))
        gray = color_similarity_2d(image, color=(99, 97, 99))
        image = cv2.subtract(255, cv2.max(orange, gray))
        image = cv2.multiply(image, 2)
        return image

    def after_process(self, result):
        result = super().after_process(result)

        if '/' not in result:
            for exp in range(40000, 90001, 1000):
                res = re.match(rf'^(\d+){exp}$', result)
                if res:
                    # 10005800 -> 1000/5800
                    new = f'{res.group(1)}/{exp}'
                    logger.info(f'OcrDormFood result {result} is revised to {new}')
                    result = new
                    break

        return result


OCR_FILL = OcrDormFood(OCR_DORM_FILL, name='OCR_DORM_FILL')


class Food:
    def __init__(self, feed, amount):
        self.feed = feed
        self.amount = amount

    def __str__(self):
        return f'Food_{self.feed}'

    def __eq__(self, other):
        return str(self) == str(other)


FOOD_FEED_AMOUNT = [1000, 2000, 3000, 5000, 10000, 20000]
FOOD_FILTER = Filter(regex=re.compile(r'(\d+)'), attr=['feed'])


class RewardDorm(UI):
    def _dorm_receive_click(self):
        """
        Click coins and loves in dorm.

        Returns:
            int: Receive count.

        Pages:
            in: page_dorm
            out: page_dorm, with info_bar
        """
        image = MASK_DORM.apply(self.device.image)
        loves = TEMPLATE_DORM_LOVE.match_multi(image, name='DORM_LOVE')
        coins = TEMPLATE_DORM_COIN.match_multi(image, name='DORM_COIN')
        logger.info(f'Dorm loves: {len(loves)}, Dorm coins: {len(coins)}')
        # Complicated dorm background
        if len(loves) > 6:
            logger.warning('Too many dorm loves, limited to 6')
            loves = loves[:6]
        if len(coins) > 6:
            logger.warning('Too many dorm coins, limited to 6')
            coins = coins[:6]

        count = 0
        for button in loves:
            count += 1
            # Disable click record check, because may have too many coins or loves.
            self.device.click(button, control_check=False)
            self.device.sleep((0.5, 0.8))
        for button in coins:
            count += 1
            self.device.click(button, control_check=False)
            self.device.sleep((0.5, 0.8))

        return count

    @Config.when(DEVICE_CONTROL_METHOD='minitouch')
    def _dorm_feed_long_tap(self, button, count):
        # Long tap to feed. This requires minitouch.
        timeout = Timer(count // 5 + 5).start()
        x, y = random_rectangle_point(button.button)
        builder = self.device.minitouch_builder
        builder.down(x, y).commit()
        builder.send()

        while 1:
            builder.move(x, y).commit().wait(10)
            builder.send()
            self.device.screenshot()

            if not self._dorm_has_food(button) \
                    or self.handle_info_bar() \
                    or self.appear(POPUP_CONFIRM, offset=self._popup_offset):
                break
            if timeout.reached():
                logger.warning('Wait dorm feed timeout')
                break

        builder.up().commit()
        builder.send()

    @Config.when(DEVICE_CONTROL_METHOD='MaaTouch')
    def _dorm_feed_long_tap(self, button, count):
        timeout = Timer(count // 5 + 5).start()
        x, y = random_rectangle_point(button.button)
        builder = self.device.maatouch_builder
        builder.down(x, y).commit()
        builder.send()

        while 1:
            builder.move(x, y).commit().wait(10)
            builder.send()
            self.device.screenshot()

            if not self._dorm_has_food(button) \
                    or self.handle_info_bar() \
                    or self.appear(POPUP_CONFIRM, offset=self._popup_offset):
                break
            if timeout.reached():
                logger.warning('Wait dorm feed timeout')
                break

        builder.up().commit()
        builder.send()

    @Config.when(DEVICE_CONTROL_METHOD='uiautomator2')
    def _dorm_feed_long_tap(self, button, count):
        timeout = Timer(count // 5 + 5).start()
        x, y = random_rectangle_point(button.button)
        self.device.u2.touch.down(x, y)

        while 1:
            self.device.u2.touch.move(x, y)
            time.sleep(.01)
            self.device.screenshot()

            if not self._dorm_has_food(button) \
                    or self.handle_info_bar() \
                    or self.appear(POPUP_CONFIRM, offset=self._popup_offset):
                break
            if timeout.reached():
                logger.warning('Wait dorm feed timeout')
                break

        self.device.u2.touch.up(x, y)

    @Config.when(DEVICE_CONTROL_METHOD='nemu_ipc')
    def _dorm_feed_long_tap(self, button, count):
        timeout = Timer(count // 5 + 5).start()
        x, y = random_rectangle_point(button.button)

        while 1:
            self.device.nemu_ipc.down(x, y)
            time.sleep(.01)
            self.device.screenshot()

            if not self._dorm_has_food(button) \
                    or self.handle_info_bar() \
                    or self.appear(POPUP_CONFIRM, offset=self._popup_offset):
                break
            if timeout.reached():
                logger.warning('Wait dorm feed timeout')
                break

        self.device.nemu_ipc.up()

    @Config.when(DEVICE_CONTROL_METHOD=None)
    def _dorm_feed_long_tap(self, button, count):
        logger.warning(f'Current control method {self.config.Emulator_ControlMethod} '
                       f'does not support DOWN/UP events, use multi-click instead')
        self.device.multi_click(button, count)

    def dorm_view_reset(self, skip_first_screenshot=True):
        """
        Use Dorm manage and Back to reset dorm view.

        Pages:
            in: page_dorm
            out: page_dorm
        """
        logger.info('Dorm view reset')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(DORM_MANAGE_CHECK, offset=(20, 20)):
                break

            if self.appear_then_click(DORM_MANAGE, offset=(20, 20), interval=3):
                continue
            # Handle all popups
            if self.ui_additional(get_ship=False):
                continue
            if self.appear_then_click(DORM_FURNITURE_CONFIRM, offset=(30, 30), interval=3):
                continue

        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(DORM_MANAGE, offset=(20, 20)):
                break

            if self.appear(DORM_MANAGE_CHECK, offset=(20, 20), interval=3):
                self.device.click(DORM_FURNITURE_SHOP_QUIT)
                continue

    def dorm_collect(self):
        """
        Collect all the coins and loves in the dorm using the one-click collect button.

        Pages:
            in: page_dorm
            out: page_dorm
        """
        logger.hr('Dorm collect')

        self.ensure_no_info_bar()
        skip_first_screenshot = True

        # Set a timer to avoid Alas failing to detect the info_bar by accident.
        timeout = Timer(1.5, count=3).start()

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Handle all popups
            if self.ui_additional(get_ship=False):
                continue

            # Collect coins and loves through the quick collect button
            if self.appear_then_click(DORM_QUICK_COLLECT, offset=(20, 20), interval=1):
                continue

            # Normal end
            if self.info_bar_count() > 0:
                break

            # Timeout end
            if timeout.reached():
                logger.warning('Dorm collect timeout, probably because Alas did not detect the info_bar')
                break

    @cached_property
    def _dorm_food(self):
        return ButtonGrid(origin=(395, 410), delta=(129, 0), button_shape=(105, 70), grid_shape=(6, 1), name='FOOD')

    @cached_property
    def _dorm_food_ocr(self):
        grids = self._dorm_food.crop((54, 41, 101, 66), name='FOOD_AMOUNT')
        return Digit(grids.buttons, letter=(255, 255, 255), threshold=128, name='OCR_DORM_FOOD')

    def _dorm_has_food(self, button):
        return np.min(rgb2gray(self.image_crop(button, copy=False))) < 127

    def _dorm_feed_click(self, button, count):
        """
        Args:
            button (Button): Food button.
            count (int): Food use count.

        Pages:
            in: DORM_FEED_CHECK
        """
        logger.info(f'Dorm feed {button} x {count}')
        if count <= 3:
            for _ in range(count):
                self.device.click(button)
                self.device.sleep((0.5, 0.8))
            skip_first_screenshot = False

        else:
            self._dorm_feed_long_tap(button, count)
            skip_first_screenshot = True

        self.popup_interval_clear()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            # End
            if self.appear(DORM_FEED_CHECK, offset=(20, 20)):
                break
            # Click
            if self.handle_popup_cancel('DORM_FEED'):
                continue

    def dorm_food_get(self):
        """
        Returns:
            list[Food]:
            int: Amount to feed.

        Pages:
            in: DORM_FEED_CHECK
        """
        has_food = [self._dorm_has_food(button) for button in self._dorm_food.buttons]
        amount = self._dorm_food_ocr.ocr(self.device.image)
        amount = [a if hf else 0 for a, hf in zip(amount, has_food)]
        food = [Food(feed=f, amount=a) for f, a in zip(FOOD_FEED_AMOUNT, amount)]
        _, fill, total = OCR_FILL.ocr(self.device.image)
        if total == 0:
            fill = -1
        logger.info(f'Dorm food: {[f.amount for f in food]}, to fill: {fill}')
        return food, fill

    def dorm_feed_once(self):
        """
        Returns:
            bool: If executed.

        Pages:
            in: DORM_FEED_CHECK
        """
        timeout = Timer(1.5, count=3).start()
        food: t.List[Food] = []
        fill: int = 0
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if timeout.reached():
                logger.warning('Get dorm food timeout, probably because food is empty')
                break

            if self.handle_info_bar():
                continue

            # Get
            food, fill = self.dorm_food_get()
            if fill == -1:
                continue
            if sum([f.amount for f in food]) > 0:
                break
        if fill < 0:
            fill = 0

        FOOD_FILTER.load(self.config.Dorm_FeedFilter)
        for selected in FOOD_FILTER.apply(food):
            button = self._dorm_food.buttons[food.index(selected)]
            if selected.amount > 0 and fill > selected.feed:
                count = min(fill // selected.feed, selected.amount)
                self._dorm_feed_click(button=button, count=count)
                return True

        return False

    def dorm_feed(self):
        """
        Returns:
            int: Executed count.

        Pages:
            in: DORM_FEED_CHECK
        """
        logger.hr('Dorm feed')

        for n in range(10):
            if not self.dorm_feed_once():
                logger.info('Dorm feed finished')
                return n

        logger.warning('Dorm feed run count reached')
        return 10

    def dorm_feed_enter(self, skip_first_screenshot=False):
        """
        Pages:
            in: DORM_CHECK
            out: DORM_FEED_CHECK
        """
        self.interval_clear(DORM_CHECK)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(DORM_FEED_CHECK, offset=(20, 20)):
                break

            if self.ui_additional(get_ship=False):
                self.interval_clear(DORM_CHECK)
                continue
            if self.appear(DORM_CHECK, offset=(20, 20), interval=5):
                self.device.click(DORM_FEED_ENTER)
                continue
            if self.appear(DORM_MANAGE_CHECK, offset=(20, 20), interval=5):
                self.device.click(DORM_FURNITURE_SHOP_QUIT)
                logger.info(f'{DORM_MANAGE_CHECK} -> {DORM_FURNITURE_SHOP_QUIT}')
                continue
            if self.appear(DORM_FURNITURE_SHOP_FIRST, offset=(20, 20), interval=5):
                self.device.click(DORM_FURNITURE_SHOP_QUIT)
                logger.info(f'{DORM_FURNITURE_SHOP_FIRST} -> {DORM_FURNITURE_SHOP_QUIT}')
                continue
            if self.appear(DORM_FURNITURE_SHOP_FIRST_SELECTED, offset=(20, 20), interval=5):
                self.device.click(DORM_FURNITURE_SHOP_QUIT)
                logger.info(f'{DORM_FURNITURE_SHOP_FIRST_SELECTED} -> {DORM_FURNITURE_SHOP_QUIT}')
                continue

    def dorm_feed_quit(self, skip_first_screenshot=True):
        """
        Pages:
            in: DORM_FEED_CHECK
            out: DORM_CHECK
        """
        self.interval_clear(DORM_FEED_CHECK)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(DORM_CHECK):
                break

            if self.appear(DORM_FEED_CHECK, offset=(20, 20), interval=5):
                self.device.click(DORM_FEED_ENTER)
                continue
            if self.handle_popup_cancel('DORM_FEED'):
                self.interval_clear(DORM_CHECK)
                continue
            if self.ui_additional(get_ship=False):
                self.interval_clear(DORM_CHECK)
                continue

    def dorm_run(self, feed=True, collect=True, buy_furniture=False):
        """
        Pages:
            in: Any page
            out: page_dorm
        """
        if not feed and not collect and not buy_furniture:
            return

        self.ui_ensure(page_dormmenu)
        self.handle_info_bar()
        if not self.appear(DORM_RED_DOT, offset=(30, 30)):
            logger.info('Nothing to collect. Dorm collecting skipped.')
            collect = False
            if not feed and not buy_furniture:
                return
        self.ui_goto(page_dorm, skip_first_screenshot=True)

        # Feed first to handle DORM_INFO
        # DORM_INFO may cover dorm coins and loves
        if feed:
            logger.hr('Dorm feed', level=1)
            self.dorm_feed_enter()
            self.dorm_feed()
            self.dorm_feed_quit()

        if collect:
            logger.hr('Dorm collect', level=1)
            self.dorm_collect()

        if buy_furniture:
            logger.hr('Dorm buy furniture', level=1)
            BuyFurniture(self.config, self.device).run()

    def get_dorm_ship_amount(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Returns:
            int: Number of ships in dorm

        Pages:
            in: page_dorm
        """
        timeout = Timer(2, count=4).start()
        current = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Handle popups
            if self.appear_then_click(DORM_FURNITURE_CONFIRM, offset=(30, 30), interval=3):
                timeout.reset()
                continue
            if self.ui_additional(get_ship=False):
                timeout.reset()
                continue

            current, _, total = OCR_SLOT.ocr(self.device.image)

            if timeout.reached():
                logger.warning('Get dorm slots timeout')
                break
            if total == 0:
                continue
            elif current not in [0, 1, 2, 3, 4, 5, 6]:
                logger.warning(f'Invalid dorm slot amount: {current}')
                continue
            else:
                break

        return current

    def cal_dorm_delay(self, ships):
        """
        (Task to delay) = 20000 / (Food consumption per 15 second) * 15 / 60

        | Ships in dorm | Food consumption per 15 second | Task to delay |
        | ------------- | ------------------------------ | ------------- |
        | 0             | 0                              | 278           |
        | 1             | 5                              | 1000          |
        | 2             | 9                              | 556           |
        | 3             | 12                             | 417           |
        | 4             | 14                             | 358           |
        | 5             | 16                             | 313           |
        | 6             | 18                             | 278           |

        Args:
            ships (int): Number of ships in dorm

        Returns:
            int: Minutes to delay

        Pages:
            in: page_dorm
        """
        dict_delay = {
            0: self.config.Scheduler_SuccessInterval,
            1: 1000,
            2: 556,
            3: 417,
            4: 358,
            5: 313,
            6: 278,
        }
        delay = dict_delay.get(ships, self.config.Scheduler_SuccessInterval)
        return delay

    def run(self):
        """
        Pages:
            in: Any page
            out: page_dorm
        """
        if not self.config.Dorm_Feed and not self.config.Dorm_Collect \
                and not self.config.BuyFurniture_Enable:
            self.config.Scheduler_Enable = False
            self.config.task_stop()

        self.dorm_run(feed=self.config.Dorm_Feed,
                      collect=self.config.Dorm_Collect,
                      buy_furniture=self.config.BuyFurniture_Enable)

        # Scheduler
        ships = self.get_dorm_ship_amount()
        delay = self.cal_dorm_delay(ships)
        logger.info(f'Ships in dorm: {ships}, task to delay: {delay}')
        self.config.task_delay(minute=delay)
