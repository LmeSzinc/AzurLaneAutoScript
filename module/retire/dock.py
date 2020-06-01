from module.base.button import ButtonGrid
from module.base.switch import Switch
from module.equipment.equipment import Equipment
from module.retire.assets import *
from module.ui.ui import UI

dock_sorting = Switch('Dork_sorting')
dock_sorting.add_status('Ascending', check_button=SORT_ASC, click_button=SORTING_CLICK)
dock_sorting.add_status('Descending', check_button=SORT_DESC, click_button=SORTING_CLICK)

favourite_filter = Switch('Favourite_filter')
favourite_filter.add_status('on', check_button=COMMON_SHIP_FILTER_ENABLE)
favourite_filter.add_status('off', check_button=COMMON_SHIP_FILTER_DISABLE)

filter_index_enhanceable = Switch('Filter_index_enhanceable')
filter_index_enhanceable.add_status('on', check_button=FILTER_INDEX_ENHANCEMENT_ON)
filter_index_enhanceable.add_status('off', check_button=FILTER_INDEX_ENHANCEMENT_OFF)

filter_index_all = Switch('Filter_index_all')
filter_index_all.add_status('on', check_button=FILTER_INDEX_ALL_ON)
filter_index_all.add_status('off', check_button=FILTER_INDEX_ALL_OFF)


CARD_GRIDS = ButtonGrid(
    origin=(93, 76), delta=(164 + 2 / 3, 227), button_shape=(138, 204), grid_shape=(7, 2), name='CARD')
CARD_RARITY_GRIDS = ButtonGrid(
    origin=(93, 76), delta=(164 + 2 / 3, 227), button_shape=(138, 5), grid_shape=(7, 2), name='RARITY')


class Dock(UI, Equipment):
    def handle_dock_cards_loading(self):
        self.device.sleep((1, 1.5))

    def dock_favourite_set(self, enable=False):
        if favourite_filter.set('on' if enable else 'off', main=self):
            self.handle_dock_cards_loading()

    def _dock_quit_check_func(self):
        return not self.appear(DOCK_CHECK, offset=(20, 20))

    def dock_quit(self):
        self.ui_back(check_button=self._dock_quit_check_func, skip_first_screenshot=True)

    def dock_sort_method_dsc_set(self, enable=True):
        if dock_sorting.set('on' if enable else 'off', main=self):
            self.handle_dock_cards_loading()

    def dock_filter_enter(self):
        self.ui_click(DOCK_FILTER, check_button=DOCK_FILTER_CONFIRM, skip_first_screenshot=True)

    def dock_filter_confirm(self):
        self.ui_click(DOCK_FILTER_CONFIRM, check_button=DOCK_FILTER, skip_first_screenshot=True)
        self.handle_dock_cards_loading()

    def dock_filter_index_enhance_set(self, enable):
        filter_index_enhanceable.set('on' if enable else 'off', main=self)

    def dock_filter_index_all_set(self, enable):
        filter_index_all.set('on' if enable else 'off', main=self)
