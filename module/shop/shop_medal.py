import cv2
import numpy as np
from scipy import signal

import module.config.server as server
from module.base.button import ButtonGrid
from module.base.decorator import cached_property, del_cached_property
from module.base.timer import Timer
from module.base.utils import rgb2gray, load_image
from module.logger import logger
from module.map_detection.utils import Points
from module.ocr.ocr import Digit, DigitYuv, Ocr
from module.shop.assets import *
from module.shop.base import ShopItemGrid_250814
from module.shop.clerk import ShopClerk
from module.shop.shop_status import ShopStatus
from module.ui.scroll import Scroll


class ShopScroll(Scroll):
    def match_color(self, main):
        background_transparency = 0.2
        button_transparency = 0.5
        delta_x = 3
        area = (
            self.area[0] - delta_x,
            self.area[1],
            self.area[2] + delta_x,
            self.area[3]
        )
        image = main.image_crop(area, copy=False).astype(np.float32)
        baseline_color = np.mean(image[:, [0, -1], :], axis=1)
        masked_color = image[:, image.shape[1] // 2, :]
        background_mask = background_transparency * np.array(self.color) + (1 - background_transparency) * baseline_color
        button_mask = button_transparency * np.array(self.color) + (1 - button_transparency) * baseline_color
        err_background = np.sum((masked_color - background_mask) ** 2, axis=1)
        err_button = np.sum((masked_color - button_mask) ** 2, axis=1)
        mask = err_button < err_background
        self.length = np.sum(mask)
        return mask


MEDAL_SHOP_SCROLL_250814 = ShopScroll(
    MEDAL_SHOP_SCROLL_AREA_250814.button,
    color=(44, 48, 56),
    name="MEDAL_SHOP_SCROLL_250814"
)
MEDAL_SHOP_SCROLL_250814.drag_threshold = 0.1
# A little bit larger than 0.1 to handle bottom
MEDAL_SHOP_SCROLL_250814.edge_threshold = 0.12


class ShopPriceOcr(DigitYuv):
    def after_process(self, result):
        result = Ocr.after_process(self, result)
        # '100' detected as '00' on retrofit blueprint
        if result == '00':
            result = '100'
        return Digit.after_process(self, result)


PRICE_OCR = ShopPriceOcr([], letter=(255, 223, 57), threshold=32, name='Price_ocr')
if server.server == 'jp':
    PRICE_OCR_250814 = Digit([], lang='cnocr', letter=(235, 235, 255), threshold=128, name='Price_ocr')
else:
    PRICE_OCR_250814 = Digit([], letter=(255, 255, 255), threshold=128, name='Price_ocr')
TEMPLATE_MEDAL_ICON = Template('./assets/shop/cost/Medal.png')
TEMPLATE_MEDAL_ICON_2 = Template('./assets/shop/cost/Medal_2.png')
TEMPLATE_MEDAL_ICON_3 = Template('./assets/shop/cost/Medal_3.png')

# Universal Bulin (gold) / Elite Bulin (purple).
# module/shop/base.py groups every bulin into the same 'bulin' group, and the
# file name is not a reliable hint either ('BulinT1_2' is gold, 'BulinT1_3' is
# purple), so the type is decided by comparing with these templates.
BULIN_TEMPLATES = {
    'gold': [
        './assets/shop/medal/BulinT1.png',
        './assets/shop/medal/BulinT2.png',
    ],
    'purple': [
        './assets/shop/medal/BulinT1_2.png',
        './assets/shop/medal/BulinT1_3.png',
        './assets/shop/medal/BulinT2_2.png',
    ],
}
BULIN_TEMPLATE_CACHE = {}


def _bulin_feature(image, size=96):
    """
    Turn an item image into a background-free feature vector.

    The shop draws the same item on a slightly different background, and the
    brightness varies between screenshots, so subtract the border colour and
    compare directions only. Images are resized to a fixed size first, because
    the item grid does not always crop to the same shape.

    Args:
        image (np.ndarray): BGR image
        size (int): Side of the fixed square the image is resized to

    Returns:
        np.ndarray: float32, shape (size, size, 3)
    """
    if image.shape[0] != size or image.shape[1] != size:
        image = cv2.resize(image, (size, size))
    image = image.astype(np.int16)
    border = np.concatenate([
        image[:3].reshape(-1, 3), image[-3:].reshape(-1, 3),
        image[:, :3].reshape(-1, 3), image[:, -3:].reshape(-1, 3),
    ])
    background = np.median(border, axis=0)
    return (image - background).astype(np.float32)


def _bulin_template_features(kind):
    """
    Args:
        kind (str): 'gold' or 'purple'

    Returns:
        list[np.ndarray]: feature vectors of the templates of that kind
    """
    if kind not in BULIN_TEMPLATE_CACHE:
        BULIN_TEMPLATE_CACHE[kind] = [
            _bulin_feature(load_image(path))
            for path in BULIN_TEMPLATES[kind]
        ]
    return BULIN_TEMPLATE_CACHE[kind]


def _cosine_similarity(image1, image2):
    a = image1.reshape(-1)
    b = image2.reshape(-1)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


class MedalShop2_250814(ShopClerk, ShopStatus):
    @cached_property
    def shop_filter(self):
        """
        Returns:
            str:
        """
        return self.config.MedalShop2_Filter.strip()

    @cached_property
    def priority_bulin(self):
        """
        Bulin types to buy before anything else, in the order configured.
        Gold (Universal Bulin) first when both are enabled.

        Returns:
            list[str]: e.g. ['gold'], ['purple'], ['gold', 'purple'] or []
        """
        result = []
        if self.config.MedalShop2_PriorityBulinGold:
            result.append('gold')
        if self.config.MedalShop2_PriorityBulinPurple:
            result.append('purple')
        if result:
            logger.attr('Medal shop priority bulin', ' > '.join(result))
        return result

    def bulin_kind(self, item):
        """
        Tell gold bulin (Universal) from purple bulin (Elite).

        ShopItemGrid.predict() groups every bulin as 'bulin', so the type has
        to be decided on the item image itself.

        Args:
            item: Item from MedalShop2 shop grid

        Returns:
            str: 'gold', 'purple' or None if neither is close enough
        """
        image = _bulin_feature(item.image)
        scores = {
            kind: max(_cosine_similarity(image, template)
                      for template in _bulin_template_features(kind))
            for kind in BULIN_TEMPLATES
        }
        kind = max(scores, key=scores.get)
        logger.attr('Bulin type', f'{item.name}: gold={scores["gold"]:.3f} purple={scores["purple"]:.3f}')
        if scores[kind] < 0.75:
            logger.info(f'Bulin type of "{item.name}" is uncertain '
                        f'(similarity={scores[kind]:.2f}), treated as non priority')
            return None
        return kind

    def shop_check_priority_bulin(self, item):
        """
        Whether this item is a bulin that is set as priority.

        Args:
            item:

        Returns:
            bool:
        """
        if not self.priority_bulin:
            return False
        if item.group != 'bulin':
            return False
        if not item.is_known_item:
            return False
        return self.bulin_kind(item) in self.priority_bulin

    def shop_check_custom_item(self, item):
        """
        Override ShopBase.shop_check_custom_item().
        Priority bulin is bought first, regardless of the shop filter.

        Args:
            item: Item to check

        Returns:
            bool:
        """
        if self.shop_check_priority_bulin(item):
            logger.info(f'Priority bulin: {item.name}')
            return True
        return False

    def shop_get_item_to_buy(self, items):
        """
        Override ShopBase.shop_get_item_to_buy().
        Priority bulin is picked by the configured order, not by the order the
        items happen to be on screen, so gold bulin is always bought before
        purple bulin when both are enabled.

        Args:
            items list(Item): acquired from shop_get_items

        Returns:
            Item: Item to buy, or None.
        """
        if self.priority_bulin:
            bulin = {}
            for item in items:
                if item.group != 'bulin' or not item.is_known_item:
                    continue
                kind = self.bulin_kind(item)
                if kind is None:
                    continue
                # Same kind may appear twice on one page, keep them all
                bulin.setdefault(kind, []).append(item)

            for kind in self.priority_bulin:
                for item in bulin.get(kind, ()):
                    if self.shop_check_item(item):
                        logger.info(f'Priority bulin: {item.name} ({kind})')
                        return item

        return super().shop_get_item_to_buy(items)

    # New UI in 2025-08-14
    def _get_medals(self):
        """
        Returns:
            np.array: [[x1, y1], [x2, y2]], location of the medal icon upper-left corner.
        """
        area = (265, 317, 999, 635)
        # copy image because we gonna paint it
        image = self.image_crop(area, copy=True)
        medals = TEMPLATE_MEDAL_ICON_3.match_multi(image, similarity=0.5, threshold=5)
        medals = Points([(0., m.area[1]) for m in medals]).group(threshold=5)
        logger.attr('Medals_icon', len(medals))
        return medals

    def wait_until_medal_appear(self, skip_first_screenshot=True):
        """
        After entering medal shop page,
        items are not loaded that fast,
        wait until any medal icon appears
        """
        timeout = Timer(1, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            medals = self._get_medals()

            if timeout.reached():
                break
            if len(medals):
                break

    @cached_property
    def shop_grid(self):
        return self.shop_medal_grid()

    def shop_medal_grid(self):
        """
        Returns:
            ButtonGrid:
        """
        # (472, 348, 1170, 648)
        medals = self._get_medals()
        count = len(medals)
        if count == 0:
            logger.warning('Unable to find medal icon, assume item list is at top')
            origin_y = 228
            delta_y = 223
            row = 2
        elif count == 1:
            y_list = medals[:, 1]
            # +256, top of the crop area in _get_medals()
            # -125, from the top of medal icon to the top of shop item
            origin_y = y_list[0] + 317 - 126
            delta_y = 223
            row = 1
        elif count == 2:
            y_list = medals[:, 1]
            y1, y2 = y_list[0], y_list[1]
            origin_y = min(y1, y2) + 317 - 126
            delta_y = abs(y1 - y2)
            row = 2
        else:
            logger.warning(f'Unexpected medal icon match result: {[m for m in medals]}')
            origin_y = 228
            delta_y = 223
            row = 2

        # Make up a ButtonGrid
        # Original grid is:
        # shop_grid = ButtonGrid(
        #     origin=(476, 246), delta=(156, 213), button_shape=(98, 98), grid_shape=(5, 2), name='SHOP_GRID')
        shop_grid = ButtonGrid(
            origin=(265, origin_y), delta=(169, delta_y), button_shape=(64, 64), grid_shape=(5, row), name='SHOP_GRID')
        return shop_grid

    shop_template_folder = './assets/shop/medal'

    @cached_property
    def shop_medal_items(self):
        """
        Returns:
            ShopItemGrid_250814:
        """
        shop_grid = self.shop_grid
        shop_medal_items = ShopItemGrid_250814(
            shop_grid,
            templates={},
            amount_area=(60, 74, 96, 95),
            cost_area=(-12, 115, 60, 155),
            price_area=(14, 122, 85, 149),
        )
        shop_medal_items.load_template_folder(self.shop_template_folder)
        shop_medal_items.load_cost_template_folder('./assets/shop/cost')
        shop_medal_items.similarity = 0.85  # Lower the threshold for consistent matches of PR/DRBP
        shop_medal_items.cost_similarity = 0.5
        shop_medal_items.price_ocr = PRICE_OCR_250814
        return shop_medal_items

    def shop_items(self) -> ShopItemGrid_250814:
        """
        Shared alias name for all shops,
        so to use  @Config must define
        a unique alias as cover
        Overriding to add type hint to
        accommodate unique func,
        get_soldout_count in run()

        Returns:
            ShopItemGrid_250814:
        """
        return self.shop_medal_items

    def shop_currency(self):
        """
        Ocr shop medal currency
        Then return medal count

        Returns:
            int: medal amount
        """
        self._currency = self.status_get_medal()
        logger.info(f'Medal: {self._currency}')
        return self._currency

    def shop_has_loaded(self, items):
        """
        If any item parsed with a default
        price of 5000; then shop cannot
        be safely bought from yet

        Returns:
            bool
        """
        for item in items:
            if int(item.price) == 5000:
                return False
        return True

    def shop_interval_clear(self):
        """
        Clear interval on select assets for
        shop_buy_handle
        """
        super().shop_interval_clear()
        self.interval_clear(SHOP_BUY_CONFIRM_SELECT)
        self.interval_clear(SHOP_BUY_CONFIRM_AMOUNT)

    def shop_buy_handle(self, item):
        """
        Handle shop_medal buy interface if detected

        Args:
            item: Item to handle

        Returns:
            bool: whether interface was detected and handled
        """
        if self.appear(SHOP_BUY_CONFIRM_SELECT, offset=(20, 20), interval=3):
            self.shop_buy_select_execute(item)
            self.interval_reset(SHOP_BUY_CONFIRM_SELECT)
            return True
        if self.appear(SHOP_BUY_CONFIRM_AMOUNT, offset=(20, 20), interval=3):
            self.shop_buy_amount_execute(item)
            self.interval_reset(SHOP_BUY_CONFIRM_AMOUNT)
            return True

        return False

    def run(self):
        """
        Run Medal Shop
        """
        # Base case; exit run if filter empty
        import time
        if not self.shop_filter:
            return

        # When called, expected to be in
        # correct Medal Shop interface
        logger.hr('Medal Shop', level=1)
        # Execute buy operations
        MEDAL_SHOP_SCROLL_250814.set_top(main=self)
        time.sleep(0.5)
        while 1:
            # sold items are auto sorted behind
            # if we find any soldout items, no need to check behind
            if self.shop_items().get_soldout_count(self.device.image):
                logger.info('Medal shop early stop')
                break

            self.shop_buy()

            if MEDAL_SHOP_SCROLL_250814.at_bottom(main=self):
                logger.info('Medal shop reach bottom, stop')
                break
            else:
                MEDAL_SHOP_SCROLL_250814.next_page(main=self, page=0.66)
                del_cached_property(self, 'shop_grid')
                del_cached_property(self, 'shop_medal_items')
                continue
