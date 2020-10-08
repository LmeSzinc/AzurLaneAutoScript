import re
from datetime import datetime, timedelta

from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.filter import Filter
from module.base.mask import Mask
from module.base.timer import Timer
from module.base.utils import *
from module.logger import logger
from module.map_detection.utils import Points
from module.ocr.ocr import Digit, DigitCounter
from module.reward.assets import *
from module.template.assets import TEMPLATE_DORM_COIN, TEMPLATE_DORM_LOVE
from module.ui.assets import DORM_CHECK, DORM_TROPHY_CONFIRM
from module.ui.page import page_dorm
from module.ui.ui import UI

MASK_DORM = Mask(file='./assets/mask/MASK_DORM.png')
DORM_CAMERA_SWIPE = (300, 250)
DORM_CAMERA_RANDOM = (-20, -20, 20, 20)
FEED_RECORD = ('RewardRecord', 'feed')
COLLECT_RECORD = ('RewardRecord', 'collect')
FOOD = ButtonGrid(origin=(298, 375), delta=(156, 0), button_shape=(112, 66), grid_shape=(6, 1), name='FOOD')
FOOD_AMOUNT = ButtonGrid(
    origin=(343, 411), delta=(156, 0), button_shape=(70, 33), grid_shape=(6, 1), name='FOOD_AMOUNT')
OCR_FOOD = Digit(FOOD_AMOUNT.buttons(), letter=(255, 255, 255), threshold=128, name='OCR_DORM_FOOD')
OCR_FILL = DigitCounter(OCR_DORM_FILL, letter=(255, 247, 247), threshold=128, name='OCR_DORM_FILL')


class Food:
    def __init__(self, feed, amount):
        self.feed = feed
        self.amount = amount


FOOD_FEED_AMOUNT = [1000, 2000, 3000, 5000, 10000, 20000]
FOOD_FILTER = Filter(regex=re.compile('(\d+)'), attr=['feed'], preset=[])


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
        love_points = Points(TEMPLATE_DORM_LOVE.match_multi(image), config=self.config).group()
        coin_points = Points(TEMPLATE_DORM_COIN.match_multi(image), config=self.config).group()
        logger.info(f'Dorm loves: {len(love_points)}, Dorm coins: {len(coin_points)}')

        count = 0
        for point in love_points:
            button = tuple(np.append(point, point + TEMPLATE_DORM_LOVE.size))
            button = Button(area=button, color=(), button=button, name='DORM_LOVE')
            count += 1
            self.device.click(button)
            self.device.sleep((0.5, 0.8))
        for point in coin_points:
            button = tuple(np.append(point, point + TEMPLATE_DORM_LOVE.size))
            button = Button(area=button, color=(), button=button, name='DORM_COIN')
            count += 1
            self.device.click(button)
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
            p1, p2 = random_rectangle_vector((-750, 500), box=(247, 26, 1045, 594), padding=0)
            self.device._drag_minitouch(p1, p2, point_random=(-50, -50, 50, 50))
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

    def _dorm_feed_once(self):
        """
        Returns:
            bool: If executed.

        Pages:
            in: DORM_FEED_CHECK
        """
        self.device.screenshot()
        self.handle_info_bar()

        has_food = [self._dorm_has_food(button) for button in FOOD.buttons()]
        amount = OCR_FOOD.ocr(self.device.image)
        amount = [a if hf else 0 for a, hf in zip(amount, has_food)]
        food = [Food(feed=f, amount=a) for f, a in zip(FOOD_FEED_AMOUNT, amount)]
        _, fill, _ = OCR_FILL.ocr(self.device.image)
        logger.info(f'Dorm food: {[f.amount for f in food]}, to fill: {fill}')

        FOOD_FILTER.load(self.config.DORM_FEED_FILTER)
        for index in FOOD_FILTER.apply(food):
            selected = food[index]
            if selected.amount > 0 and fill > selected.feed:
                count = min(fill // selected.feed, selected.amount)
                self._dorm_feed_click(button=FOOD[index, 0], count=count)
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

    def dorm_run(self):
        """
        Pages:
            in: Any page
            out: page_main
        """
        now = datetime.now()

        collect_record = datetime.strptime(self.config.config.get(*COLLECT_RECORD), self.config.TIME_FORMAT)
        update = collect_record + timedelta(seconds=self.collect_interval)
        attr = f'{COLLECT_RECORD[0]}_{COLLECT_RECORD[1]}'
        logger.attr(f'{attr}', f'Record time: {collect_record}')
        logger.attr(f'{attr}', f'Next update: {update}')

        if now > update:
            self.ui_ensure(page_dorm)
            self._dorm_receive()
            self.collect_interval_reset()
            self.config.record_save(COLLECT_RECORD)

        if self.config.ENABLE_DORM_FEED:
            feed_record = datetime.strptime(self.config.config.get(*FEED_RECORD), self.config.TIME_FORMAT)
            update = feed_record + timedelta(seconds=self.feed_interval)
            attr = f'{FEED_RECORD[0]}_{FEED_RECORD[1]}'
            logger.attr(f'{attr}', f'Record time: {feed_record}')
            logger.attr(f'{attr}', f'Next update: {update}')

            if now > update:
                self.ui_ensure(page_dorm)
                self.ui_click(click_button=DORM_FEED_ENTER, appear_button=DORM_CHECK, check_button=DORM_FEED_CHECK,
                            skip_first_screenshot=True)
                self._dorm_feed()
                self.ui_click(click_button=DORM_FEED_ENTER, appear_button=DORM_FEED_CHECK, check_button=DORM_CHECK,
                            skip_first_screenshot=True)
                self.feed_interval_reset()
                self.config.record_save(FEED_RECORD)

        self.ui_goto_main()

    @cached_property
    def feed_interval(self):
        return int(ensure_time(self.config.FEED_INTERVAL, precision=3) * 60)

    def feed_interval_reset(self):
        """ Call this method after dorm feed executed """
        del self.__dict__['feed_interval']

    @cached_property
    def collect_interval(self):
        return int(ensure_time(self.config.COLLECT_INTERVAL, precision=3) * 60)

    def collect_interval_reset(self):
        """ Call this method after dorm collect executed """
        del self.__dict__['collect_interval']

    def handle_dorm(self):
        """
        Returns:
            bool: If executed.
        """
        if not self.config.ENABLE_DORM_REWARD:
            return False

        self.dorm_run()
        return True
