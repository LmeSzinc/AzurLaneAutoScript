import time
import typing as t

from module.base.button import ButtonGrid
from module.base.decorator import Config, cached_property
from module.base.filter import Filter
from module.base.mask import Mask
from module.base.timer import Timer
from module.base.utils import *
from module.dorm.assets import *
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter
from module.template.assets import TEMPLATE_DORM_COIN, TEMPLATE_DORM_LOVE
from module.ui.assets import DORM_CHECK
from module.ui.page import page_dorm, page_dormmenu
from module.ui.ui import UI

MASK_DORM = Mask(file='./assets/mask/MASK_DORM.png')
DORM_CAMERA_SWIPE = (300, 250)
DORM_CAMERA_RANDOM = (-20, -20, 20, 20)
OCR_FILL = DigitCounter(OCR_DORM_FILL, letter=(255, 247, 247), threshold=128, name='OCR_DORM_FILL')
OCR_SLOT = DigitCounter(OCR_DORM_SLOT, letter=(107, 89, 82), threshold=128, name='OCR_DORM_SLOT')


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
        self.device.minitouch_builder.down(x, y).commit()
        self.device.minitouch_send()

        while 1:
            self.device.minitouch_builder.move(x, y).commit().wait(10)
            self.device.minitouch_send()
            self.device.screenshot()

            if not self._dorm_has_food(button) \
                    or self.handle_info_bar() \
                    or self.handle_popup_cancel('DORM_FEED'):
                break
            if timeout.reached():
                logger.warning('Wait dorm feed timeout')
                break

        self.device.minitouch_builder.up().commit()
        self.device.minitouch_send()

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
                    or self.handle_popup_cancel('DORM_FEED'):
                break
            if timeout.reached():
                logger.warning('Wait dorm feed timeout')
                break

        self.device.u2.touch.up(x, y)

    @Config.when(DEVICE_CONTROL_METHOD=None)
    def _dorm_feed_long_tap(self, button, count):
        logger.warning(f'Current control method {self.config.Emulator_ControlMethod} '
                       f'does not support DOWN/UP events, use multi-click instead')
        self.device.multi_click(button, count)

    def dorm_collect(self):
        """
        Click all coins and loves on current screen.
        Zoom-out dorm to detect coins and loves, because swipes in dorm may treat as dragging ships.
        Coordinates here doesn't matter too much.

        Pages:
            in: page_dorm, without info_bar
            out: page_dorm, without info_bar
        """
        logger.hr('Dorm collect')
        # if self.config.Emulator_ControlMethod not in ['uiautomator2', 'minitouch']:
        #     logger.warning(f'Current control method {self.config.Emulator_ControlMethod} '
        #                    f'does not support 2 finger zoom out, skip dorm collect')
        #     return

        # Already at a high camera view now, no need to zoom-out.
        # for _ in range(2):
        #     logger.info('Dorm zoom out')
        #     # Left hand down
        #     x, y = random_rectangle_point((33, 228, 234, 469))
        #     self.device.minitouch_builder.down(x, y, contact_id=1).commit()
        #     self.device.minitouch_send()
        #     # Right hand swipe
        #     # Need to avoid drop-down menu in android, which is 38 px.
        #     p1, p2 = random_rectangle_vector(
        #         (-700, 450), box=(247, 45, 1045, 594), random_range=(-50, -50, 50, 50), padding=0)
        #     self.device.drag_minitouch(p1, p2, point_random=(0, 0, 0, 0))
        #     # Left hand up
        #     self.device.minitouch_builder.up(contact_id=1).commit()
        #     self.device.minitouch_send()

        # Collect
        _dorm_receive_attempt = 0
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Handle all popups
            if self.ui_additional():
                continue
            if self.appear_then_click(DORM_FURNITURE_CONFIRM, offset=(30, 30), interval=3):
                continue

            # DORM_CHECK on screen before attempt
            # Stacked popup may fail detection as
            # may be in progress of appearing
            if not self.appear(DORM_CHECK):
                continue

            # End
            # - If max _dorm_receive_attempt (3+) reached
            # - If _dorm_receive_click returns 0 (no coins/loves clicked)
            if _dorm_receive_attempt < 3 and self._dorm_receive_click():
                self.ensure_no_info_bar()
                _dorm_receive_attempt += 1
            else:
                break

    @cached_property
    @Config.when(SERVER='en')
    def _dorm_food(self):
        # 14px lower
        return ButtonGrid(origin=(279, 375), delta=(159, 0), button_shape=(134, 96), grid_shape=(6, 1), name='FOOD')

    @cached_property
    @Config.when(SERVER=None)
    def _dorm_food(self):
        return ButtonGrid(origin=(279, 375), delta=(159, 0), button_shape=(134, 96), grid_shape=(6, 1), name='FOOD')

    @cached_property
    def _dorm_food_ocr(self):
        grids = self._dorm_food.crop((65, 66, 128, 91), name='FOOD_AMOUNT')
        return Digit(grids.buttons, letter=(255, 255, 255), threshold=128, name='OCR_DORM_FOOD')

    def _dorm_has_food(self, button):
        return np.min(rgb2gray(self.image_crop(button))) < 127

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

        else:
            self._dorm_feed_long_tap(button, count)

        while 1:
            self.device.screenshot()
            if self.handle_popup_cancel('DORM_FEED'):
                continue
            # End
            if self.appear(DORM_FEED_CHECK, offset=(20, 20)):
                break

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

            if self.ui_additional():
                self.interval_clear(DORM_CHECK)
                continue
            if self.appear(DORM_CHECK, offset=(20, 20), interval=5):
                self.device.click(DORM_FEED_ENTER)
                continue

    def dorm_feed_quit(self, skip_first_screenshot=False):
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
            if self.appear(DORM_CHECK, offset=(20, 20)):
                break

            if self.appear(DORM_FEED_CHECK, offset=(20, 20), interval=5):
                self.device.click(DORM_FEED_ENTER)
                continue
            if self.handle_popup_cancel('DORM_FEED'):
                self.interval_clear(DORM_CHECK)
                continue
            if self.ui_additional():
                self.interval_clear(DORM_CHECK)
                continue

    def dorm_run(self, feed=True, collect=True):
        """
        Pages:
            in: Any page
            out: page_dorm
        """
        if not feed and not collect:
            return

        self.ui_ensure(page_dormmenu)
        if not self.appear(DORM_RED_DOT, offset=(30, 30)):
            logger.info('Nothing to collect. Dorm collecting skipped.')
            collect = False
            if not feed:
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
            if self.ui_additional():
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
        if not self.config.Dorm_Feed and not self.config.Dorm_Collect:
            self.config.Scheduler_Enable = False
            self.config.task_stop()

        self.dorm_run(feed=self.config.Dorm_Feed, collect=self.config.Dorm_Collect)

        # Scheduler
        ships = self.get_dorm_ship_amount()
        delay = self.cal_dorm_delay(ships)
        logger.info(f'Ships in dorm: {ships}, task to delay: {delay}')
        self.config.task_delay(minute=delay)
