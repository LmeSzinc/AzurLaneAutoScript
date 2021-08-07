import re
from datetime import datetime, timedelta

from PIL import Image

from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.filter import Filter
from module.base.mask import Mask
from module.base.timer import Timer
from module.base.utils import *
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter
from module.reward.assets import *
from module.template.assets import TEMPLATE_DORM_COIN, TEMPLATE_DORM_LOVE
from module.ui.assets import DORM_CHECK, DORM_TROPHY_CONFIRM, DORM_INFO
from module.ui.page import page_dorm, page_dormmenu
from module.ui.ui import UI

MASK_DORM = Mask(file='./assets/mask/MASK_DORM.png')
DORM_CAMERA_SWIPE = (300, 250)
DORM_CAMERA_RANDOM = (-20, -20, 20, 20)
FEED_RECORD = ('RewardRecord', 'dorm_feed')
COLLECT_RECORD = ('RewardRecord', 'dorm_collect')
FOOD = ButtonGrid(origin=(298, 375), delta=(156, 0), button_shape=(112, 66), grid_shape=(6, 1), name='FOOD')
FOOD_AMOUNT = ButtonGrid(
    origin=(343, 411), delta=(156, 0), button_shape=(70, 33), grid_shape=(6, 1), name='FOOD_AMOUNT')
OCR_FOOD = Digit(FOOD_AMOUNT.buttons, letter=(255, 255, 255), threshold=128, name='OCR_DORM_FOOD')
OCR_FILL = DigitCounter(OCR_DORM_FILL, letter=(255, 247, 247), threshold=128, name='OCR_DORM_FILL')


class Food:
    def __init__(self, feed, amount):
        self.feed = feed
        self.amount = amount

    def __str__(self):
        return f'Food_{self.feed}'

    def __eq__(self, other):
        return str(self) == str(other)


FOOD_FEED_AMOUNT = [1000, 2000, 3000, 5000, 10000, 20000]
FOOD_FILTER = Filter(regex=re.compile('(\d+)'), attr=['feed'])


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
        image = MASK_DORM.apply(np.array(self.device.image))
        image = Image.fromarray(image)
        loves = TEMPLATE_DORM_LOVE.match_multi(image, name='DORM_LOVE')
        coins = TEMPLATE_DORM_COIN.match_multi(image, name='DORM_COIN')
        logger.info(f'Dorm loves: {len(loves)}, Dorm coins: {len(coins)}')

        count = 0
        for button in loves:
            count += 1
            # Disable click record check, because may have too many coins or loves.
            self.device.click(button, record_check=False)
            self.device.sleep((0.5, 0.8))
        for button in coins:
            count += 1
            self.device.click(button, record_check=False)
            self.device.sleep((0.5, 0.8))

        return count

    def _dorm_receive(self):
        """
        Click all coins and loves on current screen.
        Zoom-out dorm to detect coins and loves, because swipes in dorm may treat as dragging ships.
        Coordinates here doesn't matter too much.

        Pages:
            in: page_dorm, without info_bar
            out: page_dorm, without info_bar
        """
        for _ in range(2):
            logger.info('Dorm zoom out')
            # Left hand down
            x, y = random_rectangle_point((33, 228, 234, 469))
            self.device.minitouch_builder.down(x, y, contact_id=1).commit()
            self.device.minitouch_send()
            # Right hand swipe
            # Need to avoid drop-down menu in android, which is 38 px.
            p1, p2 = random_rectangle_vector(
                (-700, 450), box=(247, 45, 1045, 594), random_range=(-50, -50, 50, 50), padding=0)
            self.device._drag_minitouch(p1, p2, point_random=(0, 0, 0, 0))
            # Left hand up
            self.device.minitouch_builder.up(contact_id=1).commit()
            self.device.minitouch_send()

        # Collect
        for n in range(3):
            self.device.screenshot()
            # Close trophies info
            if self.appear(DORM_TROPHY_CONFIRM, offset=(30, 30)):
                self.ui_click(DORM_TROPHY_CONFIRM, check_button=DORM_CHECK, skip_first_screenshot=True)
                self.device.screenshot()
            # Close DORM_INFO. Usually, it was handled in ui_ensure(), but sometimes not.
            if self.appear(DORM_INFO, offset=(30, 30)):
                self.ui_click(DORM_INFO, check_button=DORM_CHECK, skip_first_screenshot=True)
                self.device.screenshot()

            if self._dorm_receive_click():
                self.ensure_no_info_bar()
                continue
            else:
                break

    def _dorm_has_food(self, button):
        return np.min(rgb2gray(np.array(self.image_area(button)))) < 127

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
                        or self.handle_popup_cancel('dorm_feed'):
                    break
                if timeout.reached():
                    logger.warning('Wait dorm feed timeout')
                    break

            self.device.minitouch_builder.up().commit()
            self.device.minitouch_send()

        while 1:
            self.device.screenshot()
            if self.handle_popup_cancel('dorm_feed'):
                continue
            # End
            if self.appear(DORM_FEED_CHECK, offset=(20, 20)):
                break

    def _dorm_feed_once(self):
        """
        Returns:
            bool: If executed.

        Pages:
            in: DORM_FEED_CHECK
        """
        self.device.screenshot()
        self.handle_info_bar()

        has_food = [self._dorm_has_food(button) for button in FOOD.buttons]
        amount = OCR_FOOD.ocr(self.device.image)
        amount = [a if hf else 0 for a, hf in zip(amount, has_food)]
        food = [Food(feed=f, amount=a) for f, a in zip(FOOD_FEED_AMOUNT, amount)]
        _, fill, _ = OCR_FILL.ocr(self.device.image)
        logger.info(f'Dorm food: {[f.amount for f in food]}, to fill: {fill}')

        FOOD_FILTER.load(self.config.DORM_FEED_FILTER)
        for selected in FOOD_FILTER.apply(food):
            button = FOOD.buttons[food.index(selected)]
            if selected.amount > 0 and fill > selected.feed:
                count = min(fill // selected.feed, selected.amount)
                self._dorm_feed_click(button=button, count=count)
                return True

        return False

    def _dorm_feed(self):
        """
        Returns:
            int: Executed count.

        Pages:
            in: DORM_FEED_CHECK
        """
        logger.hr('Dorm feed')

        for n in range(10):
            if not self._dorm_feed_once():
                logger.info('Dorm feed finished')
                return n

        logger.warning('Dorm feed run count reached')
        return 10

    def dorm_run(self, feed=True, collect=True):
        """
        Pages:
            in: Any page
            out: page_main
        """
        if not feed and not collect:
            self.ui_goto_main()
            return

        self.ui_ensure(page_dormmenu)
        if not self.appear(DORM_RED_DOT, offset=(30, 30)):
            logger.info('Nothing to collect. Dorm collecting skipped.')
            collect = False
            if not feed:
                self.ui_goto_main()
                return
        self.ui_goto(page_dorm, skip_first_screenshot=True)

        if collect:
            self._dorm_receive()

        if feed:
            self.ui_click(click_button=DORM_FEED_ENTER, appear_button=DORM_CHECK, check_button=DORM_FEED_CHECK,
                          skip_first_screenshot=True)
            self._dorm_feed()
            self.ui_click(click_button=DORM_FEED_ENTER, appear_button=DORM_FEED_CHECK, check_button=DORM_CHECK,
                          skip_first_screenshot=True)

        self.ui_goto_main()

    @cached_property
    def dorm_feed_interval(self):
        return int(ensure_time(self.config.DORM_FEED_INTERVAL, precision=3) * 60)

    def dorm_feed_interval_reset(self):
        """ Call this method after dorm feed executed """
        del self.__dict__['dorm_feed_interval']

    @cached_property
    def dorm_collect_interval(self):
        return int(ensure_time(self.config.DORM_COLLECT_INTERVAL, precision=3) * 60)

    def dorm_collect_interval_reset(self):
        """ Call this method after dorm collect executed """
        del self.__dict__['dorm_collect_interval']

    def handle_dorm(self):
        """
        Returns:
            bool: If executed.
        """
        # Base case check
        if not self.config.ENABLE_DORM_REWARD:
            return False

        # Record check, create configured flags for dorm_run
        now = datetime.now()
        do_collect = False
        collect_record = datetime.strptime(self.config.config.get(*COLLECT_RECORD), self.config.TIME_FORMAT)
        update = collect_record + timedelta(seconds=self.dorm_collect_interval)
        attr = f'{COLLECT_RECORD[0]}_{COLLECT_RECORD[1]}'
        logger.attr(f'{attr}', f'Record time: {collect_record}')
        logger.attr(f'{attr}', f'Next update: {update}')
        if now > update:
            do_collect = True

        do_feed = False
        if self.config.ENABLE_DORM_FEED:
            feed_record = datetime.strptime(self.config.config.get(*FEED_RECORD), self.config.TIME_FORMAT)
            update = feed_record + timedelta(seconds=self.dorm_feed_interval)
            attr = f'{FEED_RECORD[0]}_{FEED_RECORD[1]}'
            logger.attr(f'{attr}', f'Record time: {feed_record}')
            logger.attr(f'{attr}', f'Next update: {update}')

            if now > update:
                do_feed = True

        # Neither, no need to do dorm_run
        if not do_collect and not do_feed:
            return False

        # Execute dorm_run with configured flags
        self.dorm_run(feed=do_feed, collect=do_collect)

        # Record into config if executed
        if do_collect:
            self.dorm_collect_interval_reset()
            self.config.record_save(COLLECT_RECORD)

        if do_feed:
            self.dorm_feed_interval_reset()
            self.config.record_save(FEED_RECORD)

        return True
