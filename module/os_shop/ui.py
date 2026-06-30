from typing import Tuple
from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import random_rectangle_vector
from module.exception import GameStuckError
from module.os_shop.assets import OS_SHOP_CHECK, OS_SHOP_SAFE_AREA, OS_SHOP_SCROLL_AREA
from module.logger import logger
from module.ui.navbar import Navbar
from module.ui.scroll import AdaptiveScroll
from module.ui.ui import UI

OS_SHOP_SCROLL = AdaptiveScroll(
    OS_SHOP_SCROLL_AREA.button,
    parameters={
        'height': 255 - 99,
        'prominence': 40,
    },
    name="OS_SHOP_SCROLL"
)
OS_SHOP_SCROLL.drag_threshold = 0.1
OS_SHOP_SCROLL.edge_threshold = 0.1


class OSShopUI(UI):
    def os_shop_load_ensure(self, skip_first_screenshot=True):
        """
        Switching between sidebar clicks for some
        takes a bit of processing before fully loading
        like guild logistics

        Args:
            skip_first_screenshot (bool):

        Returns:
            bool: Whether expected assets loaded completely
        """
        ensure_timeout = Timer(3, count=6).start()
        while True:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(OS_SHOP_CHECK):
                return True
            else:
                logger.warning('OpsiShop is not appear, retrying.')

            # Exception
            if ensure_timeout.reached():
                raise GameStuckError('Waiting too long for OpsiShop to appear.')

    @cached_property
    def _os_shop_side_navbar(self):
        """
        limited_sidebar 4 options
            NY
            Liverpool
            Gibraltar
            St. Petersburg
        """
        os_shop_side_navbar = ButtonGrid(
            origin=(44, 266), delta=(0, 87),
            button_shape=(231, 46), grid_shape=(1, 4),
            name='OS_SHOP_SIDE_NAVBAR')

        return Navbar(grids=os_shop_side_navbar,
                      active_color=(43, 94, 248), active_threshold=221,
                      inactive_color=(12, 58, 86), inactive_threshold=221)

    def os_shop_side_navbar_ensure(self, upper=None, bottom=None):
        """
        Ensure able to transition to page and
        page has loaded to completion

        Args:
            upper (int):
            limited|regular
                1     NY
                2     Liverpool
                3     Gibraltar
                4     St. Petersburg
            bottom (int):
            limited|regular
                4     NY
                3     Liverpool
                2     Gibraltar
                1     St. Petersburg

        Returns:
            bool: if side_navbar set ensured

        Pages:
            in: PORT_SUPPLY_CHECK
            out: PORT_SUPPLY_CHECK
        """
        logger.info(f'OpsiShop side navbar set to {upper or bottom}')
        self.os_shop_load_ensure()
        self._os_shop_side_navbar.set(self, upper=upper, bottom=bottom)

    def init_slider(self) -> Tuple[float, float]:
        """Initialize the slider

        Returns:
            Tuple[float, float]: (pre_pos, cur_pos)
        """
        if not OS_SHOP_SCROLL.appear(main=self):
            logger.warning('Scroll does not appear, try to rescue slider')
            self.rescue_slider()
        retry = Timer(0, count=3)
        retry.start()
        while not OS_SHOP_SCROLL.at_top(main=self):
            logger.info('Scroll does not at top, try to scroll')
            OS_SHOP_SCROLL.set_top(main=self)
            if retry.reached():
                raise GameStuckError('Scroll drag page error.')
        return -1.0, 0.0

    def rescue_slider(self, distance=200):
        detection_area = (1130, 230, 1170, 710)
        direction_vector = (0, distance)
        p1, p2 = random_rectangle_vector(
            direction_vector, box=detection_area, random_range=(-10, -40, 10, 40), padding=10)
        self.device.drag(p1, p2, segments=2, shake=(25, 0), point_random=(0, 0, 0, 0), shake_random=(-5, 0, 5, 0))
        self.device.click(OS_SHOP_SAFE_AREA)
        self.device.screenshot()

    def pre_scroll(self, pre_pos, cur_pos) -> float:
        """Pretreatment Sliding

        Args:
            pre_pos: Previous position
            cur_pos: Current position

        Raise:
            ScriptError: Slide Page Error

        Returns:
            cur_pos: Current position
        """
        if pre_pos == cur_pos:
            logger.warning('Scroll drag page failed')
            if not OS_SHOP_SCROLL.appear(main=self):
                logger.warning('Scroll does not appear, try to rescue slider')
                self.rescue_slider()
                OS_SHOP_SCROLL.set(cur_pos, main=self)
            retry = Timer(0, count=3)
            retry.start()
            while True:
                logger.warning('Scroll does not drag success, retrying scroll')
                OS_SHOP_SCROLL.next_page(main=self, page=0.5, skip_first_screenshot=False)
                cur_pos = OS_SHOP_SCROLL.cal_position(main=self)
                if pre_pos != cur_pos:
                    logger.info(f'Scroll success drag page to {cur_pos}')
                    return cur_pos
                if retry.reached():
                    raise GameStuckError('Scroll drag page error.')
        else:
            return cur_pos
