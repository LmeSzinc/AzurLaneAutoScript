from module.base.button import ButtonGrid
from module.base.switch import Switch
from module.equipment.equipment import Equipment
from module.exception import ScriptError
from module.retire.assets import *

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

filter_index_clear = Switch('Filter_index_clear')
filter_index_clear.add_status('on', check_button=FILTER_INDEX_CLEAR_ON)
filter_index_clear.add_status('off', check_button=FILTER_INDEX_CLEAR_OFF)

filter_index_dd = Switch('Filter_index_dd')
filter_index_dd.add_status('on', check_button=FILTER_INDEX_DD_ON)
filter_index_dd.add_status('off', check_button=FILTER_INDEX_DD_OFF)

filter_index_cl = Switch('Filter_index_cl')
filter_index_cl.add_status('on', check_button=FILTER_INDEX_CL_ON)
filter_index_cl.add_status('off', check_button=FILTER_INDEX_CL_OFF)

filter_index_ca = Switch('Filter_index_ca')
filter_index_ca.add_status('on', check_button=FILTER_INDEX_CA_ON)
filter_index_ca.add_status('off', check_button=FILTER_INDEX_CA_OFF)

filter_index_bb = Switch('Filter_index_bb')
filter_index_bb.add_status('on', check_button=FILTER_INDEX_BB_ON)
filter_index_bb.add_status('off', check_button=FILTER_INDEX_BB_OFF)

filter_index_cv = Switch('Filter_index_cv')
filter_index_cv.add_status('on', check_button=FILTER_INDEX_CV_ON)
filter_index_cv.add_status('off', check_button=FILTER_INDEX_CV_OFF)

filter_index_repair = Switch('Filter_index_repair')
filter_index_repair.add_status('on', check_button=FILTER_INDEX_REPAIR_ON)
filter_index_repair.add_status('off', check_button=FILTER_INDEX_REPAIR_OFF)

filter_index_ss = Switch('Filter_index_ss')
filter_index_ss.add_status('on', check_button=FILTER_INDEX_SS_ON)
filter_index_ss.add_status('off', check_button=FILTER_INDEX_SS_OFF)

filter_index_others = Switch('Filter_index_others')
filter_index_others.add_status('on', check_button=FILTER_INDEX_OTHERS_ON)
filter_index_others.add_status('off', check_button=FILTER_INDEX_OTHERS_OFF)

filter_sort_lvl = Switch('Filter_sort_lvl')
filter_sort_lvl.add_status('on', check_button=FILTER_SORT_LVL_ON)
filter_sort_lvl.add_status('off', check_button=FILTER_SORT_LVL_OFF)

filter_rarity_all = Switch('Filter_rarity_all')
filter_rarity_all.add_status('on', check_button=FILTER_RARITY_ALL_ON)
filter_rarity_all.add_status('off', check_button=FILTER_RARITY_ALL_OFF)

filter_faction_all = Switch('Filter_faction_all')
filter_faction_all.add_status('on', check_button=FILTER_FACTION_ALL_ON)
filter_faction_all.add_status('off', check_button=FILTER_FACTION_ALL_OFF)

CARD_GRIDS = ButtonGrid(
    origin=(93, 76), delta=(164 + 2 / 3, 227), button_shape=(138, 204), grid_shape=(7, 2), name='CARD')
CARD_RARITY_GRIDS = ButtonGrid(
    origin=(93, 76), delta=(164 + 2 / 3, 227), button_shape=(138, 5), grid_shape=(7, 2), name='RARITY')


class Dock(Equipment):
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

    def dock_filter_set(self, category, type, enable):
        key = f'filter_{category}_{type}'

        try:
            obj = globals()[key]
            obj.set('on' if enable else 'off', main=self)
        except:
            raise ScriptError(f'{key} filter switch object does not exist in module/retire/dock.py')
