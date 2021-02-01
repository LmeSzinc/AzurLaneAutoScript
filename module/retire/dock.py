from module.base.button import ButtonGrid
from module.equipment.equipment import Equipment
from module.exception import ScriptError
from module.retire.assets import *
from module.ui.switch import Switch

dock_sorting = Switch('Dork_sorting')
dock_sorting.add_status('Ascending', check_button=SORT_ASC, click_button=SORTING_CLICK)
dock_sorting.add_status('Descending', check_button=SORT_DESC, click_button=SORTING_CLICK)

favourite_filter = Switch('Favourite_filter')
favourite_filter.add_status('on', check_button=COMMON_SHIP_FILTER_ENABLE)
favourite_filter.add_status('off', check_button=COMMON_SHIP_FILTER_DISABLE)

filter_extra_enhanceable = Switch('Filter_extra_enhanceable')
filter_extra_enhanceable.add_status('on', check_button=FILTER_EXTRA_ENHANCEABLE_ON)
filter_extra_enhanceable.add_status('off', check_button=FILTER_EXTRA_ENHANCEABLE_OFF)

filter_extra_no_limit = Switch('Filter_extra_no_limit')
filter_extra_no_limit.add_status('on', check_button=FILTER_EXTRA_NO_LIMIT_ON)
filter_extra_no_limit.add_status('off', check_button=FILTER_EXTRA_NO_LIMIT_OFF)

filter_index_all = Switch('Filter_index_all')
filter_index_all.add_status('on', check_button=FILTER_INDEX_ALL_ON)
filter_index_all.add_status('off', check_button=FILTER_INDEX_ALL_OFF)

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

FILTER_SORT_GRIDS = ButtonGrid(
    origin=(284, 109), delta=(157.5, 0), button_shape=(137, 38), grid_shape=(6, 1), name='FILTER_SORT')
FILTER_SORT_TYPES = [['rarity', 'level', 'total', 'join', 'intimacy', 'stat']] # stat has extra grid, not worth pursuing

FILTER_INDEX_GRIDS = ButtonGrid(
    origin=(284, 183), delta=(157.5, 56.5), button_shape=(137, 38), grid_shape=(6, 2), name='FILTER_INDEX')
FILTER_INDEX_TYPES = [['all', 'vanguard', 'main',   'dd', 'cl',     'ca'],
                      ['bb',  'cv',       'repair', 'ss', 'others', 'na']]

FILTER_FACTION_GRIDS = ButtonGrid(
    origin=(284, 316), delta=(157.5, 56.5), button_shape=(137, 38), grid_shape=(6, 2), name='FILTER_FACTION')
FILTER_FACTION_TYPES = [['all',      'eagle',    'royal', 'sakura', 'iron',  'dragon'],
                        ['sardegna', 'northern', 'iris',  'vichya', 'other', 'na'    ]]

FILTER_RARITY_GRIDS = ButtonGrid(
    origin=(284, 449), delta=(157.5, 0), button_shape=(137, 38), grid_shape=(6, 1), name='FILTER_RARITY')
FILTER_RARITY_TYPES = [['all', 'common', 'rare', 'elite', 'super_rare', 'ultra']]

FILTER_EXTRA_GRIDS = ButtonGrid(
    origin=(284, 522), delta=(157.5, 0), button_shape=(137, 38), grid_shape=(6, 1), name='FILTER_EXTRA')
FILTER_EXTRA_TYPES = [['no_limit', 'has_skin', 'can_retrofit', 'enhanceable', 'special', 'na']]


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

    def dock_filter_extra_enhance_set(self, enable):
        filter_extra_enhanceable.set('on' if enable else 'off', main=self)

    def dock_filter_index_all_set(self, enable):
        filter_index_all.set('on' if enable else 'off', main=self)

    def dock_filter_set(self, category, type, enable):
        key = f'filter_{category}_{type}'

        try:
            obj = globals()[key]
            obj.set('on' if enable else 'off', main=self)
        except KeyError:
            raise ScriptError(f'{key} filter switch object does not exist in module/retire/dock.py')

    def dock_filter_set_new(self, category, type, enable):
        # Upper/Lower respectively for keying
        category = category.upper()
        type = type.lower()

        # Build keys
        key_1 = f'FILTER_{category}_GRIDS'
        key_2 = f'FILTER_{category}_TYPES'

        # Try to acquire key from globals()
        try:
            obj_1 = globals()[key_1]
            obj_2 = globals()[key_2]
        except KeyError:
            raise ScriptError(f'Either {key_1} or {key_2} filter grid/type list does not exist in module/retire/dock.py')

        # Internal helper methods
        def get_2d_index(myList, v):
            for i, x in enumerate(myList):
                if v in x:
                    return (x.index(v), i)
            return (None, None)

        def set_filter(button, color_check, skip_first_screenshot=True):
            from module.base.timer import Timer

            confirm_timer = Timer(1.5, count=3).start()
            clicked_timeout = Timer(0.5, count=1)
            clicked_threshold = 3
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()

                if clicked_timeout.reached():
                    if not self.image_color_count(button, color=color_check, threshold=235, count=250) and clicked_threshold > 0:
                        self.device.click(button)
                        confirm_timer.reset()
                        clicked_timeout.reset()
                        clicked_threshold -= 1
                        continue

                if self.appear(DOCK_FILTER_CONFIRM):
                    if confirm_timer.reached():
                        break
                else:
                    confirm_timer.reset()

        # Locate button in grid
        x, y = get_2d_index(obj_2, type)
        if x is None or y is None:
            raise ScriptError(f'Type: {type} is not valid for filter type list {key_2}')
        button = obj_1[x, y]

        # Determine color of resulting button after click based on 'enable'
        # Enable (On)   - Gold/Blue Color depends on category
        # Disable (Off) - Grey regardless of category
        if enable:
            if category in ['SORT', 'INDEX']:
                color_check = (181, 142, 90)
            else:
                color_check = (74, 117, 189)
        else:
            color_check = (115, 130, 148)

        # Set filter of button
        set_filter(button, color_check)
