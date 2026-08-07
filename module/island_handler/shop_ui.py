from module.base.decorator import cached_property
from module.base.button import ButtonGrid
from module.island.ui import IslandUI, NestedNavbar
from module.island_handler.assets import *
from module.ui.assets import ISLAND_GOTO_ISLAND_SHOP
from module.ui.page import page_island, page_island_shop


SHOP_ITEM_NAME_AREA = (12, 142, 134, 163)


class IslandShopUI(IslandUI):
    has_shop_banner = False

    def ui_goto_island_shop(self):
        self.ui_goto(page_island)
        for _ in self.loop():
            if self.ui_page_appear(page_island_shop, offset=(0, 20)):
                return True
            elif self.appear(ISLAND_SHOP_MILL_CHECK, offset=(20, 20)):
                return True
            elif self.appear(ISLAND_SHOP_RECOMMEND, offset=(0, 20)):
                self.has_shop_banner = True
                return True
            if self.appear_then_click(ISLAND_GOTO_ISLAND_SHOP, offset=(20, 20), interval=1):
                continue

    @cached_property
    def _island_shop_side_navbar(self):
        if not self.has_shop_banner:
            return NestedNavbar(
                grids=ButtonGrid(origin=(12, 80), delta=(0, 70), button_shape=(127, 70), grid_shape=(1, 7), name='ISLAND_SHOP_NAVBAR'),
                subgrid_delta=(0, 58), subgrid_button_shape=(127, 58),
                subgrid_shapes=[(1, 1), (1, 2), (1, 1), (1, 1), (1, 2), (1, 0), (1, 2)],
                direction='vertical',
            )
        else:
            return NestedNavbar(
                grids=ButtonGrid(origin=(12, 80), delta=(0, 70), button_shape=(127, 70), grid_shape=(1, 8), name='ISLAND_SHOP_NAVBAR'),
                subgrid_delta=(0, 58), subgrid_button_shape=(127, 58),
                subgrid_shapes=[(1, 0), (1, 1), (1, 2), (1, 1), (1, 1), (1, 2), (1, 0), (1, 2)],
                direction='vertical',
            )

    def island_shop_side_navbar_ensure(self, main_index, sub_index=None, skip_first_screenshot=True):
        if not self.has_shop_banner:
            return self._island_shop_side_navbar.set(self, main_index=main_index, sub_index=sub_index, skip_first_screenshot=skip_first_screenshot)
        else:
            return self._island_shop_side_navbar.set(self, main_index=main_index+1, sub_index=sub_index, skip_first_screenshot=skip_first_screenshot)

    def wait_island_shop_loading(self):
        for _ in self.loop(timeout=5):
            if self.ui_page_appear(page_island_shop, offset=(0, 20)):
                return True
            if self.appear(ISLAND_SHOP_MILL_CHECK, offset=(20, 20)):
                return True
            if self.appear(ISLAND_SHOP_RECOMMEND, offset=(0, 20)):
                self.has_shop_banner = True
                return True
            if self.appear(ISLAND_SHOP_LOADING, offset=(20, 20)):
                continue