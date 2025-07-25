from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.shop.ui import ShopUI
from module.ui.navbar import Navbar


class PQShopUI(ShopUI):
    @cached_property
    def _shop_bottom_navbar(self):
        """
        shop_bottom_navbar 4 options
            all.
            gift.
            furniture.
            misc.
        """
        shop_navgrid = ButtonGrid(
            origin=(465, 600), delta=(200, 0), button_shape=(20, 20), grid_shape=(4, 1),
            name='PRIVATE_QUARTERS_BOTTOM_BUTTON_GRID')

        return Navbar(shop_navgrid,
                      active_color=(186, 226, 245), inactive_color=(236, 237, 243),
                      active_count=350, inactive_count=350,
                      active_threshold=221, inactive_threshold=221,
                      name='PRIVATE_QUARTERS_BOTTOM_NAVBAR')

    def shop_bottom_navbar_ensure(self, left=None, right=None):
        """
        Ensure able to transition to page and
        page has loaded to completion
        Use 1 arg or the other, never both

        Args:
            left (int): Depends on ship navs
                        index starts from 1 then
                        increments rightward
            right (int): index stars from 1
                         then increments leftward

        Returns:
            bool: if bottom_navbar set ensured
        """
        if self._shop_bottom_navbar.set(self, left=left, right=right):
            return True
        return False

    @cached_property
    def _shop_left_navbar(self):
        """
        shop_bottom_navbar 4 options
            home.
            sirius.
            noshiro.
            anchorage.
            new_jersey.
        """
        shop_navgrid = ButtonGrid(
            origin=(152, 158), delta=(0, 105), button_shape=(15, 15), grid_shape=(1, 5),
            name='PRIVATE_QUARTERS_LEFT_BUTTON_GRID')

        return Navbar(shop_navgrid,
                      active_color=(255, 255, 255), inactive_color=(176, 245, 250),
                      active_count=200, inactive_count=200,
                      active_threshold=221, inactive_threshold=221,
                      name='PRIVATE_QUARTERS_LEFT_NAVBAR')

    def shop_left_navbar_ensure(self, upper=None, bottom=None):
        """
        Ensure able to transition to page and
        page has loaded to completion
        Use 1 arg or the other, never both

        Args:
            upper (int): Depends on ship navs
                         index starts from 1
                         then increments downward
            bottom (int): index starts from 1
                          then increments upward

        Returns:
            bool: if bottom_navbar set ensured
        """
        if self._shop_left_navbar.set(self, upper=upper, bottom=bottom):
            return True
        return False
