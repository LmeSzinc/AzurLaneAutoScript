from re import sub
from datetime import datetime, timedelta
import numpy as np

from module.statistics.item import ItemGrid
from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.mask import Mask
from module.base.timer import Timer
from module.base.utils import *
from module.combat.assets import GET_ITEMS_1
from module.handler.assets import POPUP_CONFIRM
from module.reward.assets import *
from module.template.assets import TEMPLATE_OPERATIONS_RED_DOT, TEMPLATE_OPERATIONS_ADD
from module.ui.assets import GUILD_CHECK
from module.logger import logger
from module.ocr.ocr import Digit, Ocr
from module.ui.ui import UI, page_guild

GUILD_RECORD = ('RewardRecord', 'guild')

GUILD_EXCHANGE_LIMIT = Digit(OCR_GUILD_EXCHANGE_LIMIT, threshold=64)
GUILD_EXCHANGE_INFO = Digit(OCR_GUILD_EXCHANGE_INFO, lang='cnocr', letter=(148, 249, 99), threshold=64)

GUILD_SIDEBAR = ButtonGrid(
    origin=(21, 118), delta=(0, 94.5), button_shape=(60, 75), grid_shape=(1, 5), name='GUILD_SIDEBAR')
EXCHANGE_GRIDS = ButtonGrid(origin=(470, 470), delta=(198.5, 0), button_shape=(83, 83), grid_shape=(3, 1))
EXCHANGE_ITEMS = ItemGrid(EXCHANGE_GRIDS, {}, template_area=(40, 21, 89, 70), amount_area=(60, 71, 91, 92))

ITEM_TO_COST = {
    't1': 20,
    't2': 10,
    't3': 5,
    'oxycola': 20,
    'coolant': 10,
    'coins': 600,
    'oil': 200,
    'merit': 450
}

DEFAULT_PLATE_PRIORITY = [
    'torpedo',
    'antiair',
    'plane',
    'gun',
    'general'
]

DEFAULT_ITEM_PRIORITY = ITEM_TO_COST.keys()
GRADES = [s for s in DEFAULT_ITEM_PRIORITY if len(s) == 2]

SWIPE_DISTANCE = 250
SWIPE_RANDOM_RANGE = (-40, -20, 40, 20)

MASK_OPERATIONS = Mask(file='./assets/mask/MASK_OPERATIONS.png')

class RewardGuild(UI):
    def _view_swipe(self, distance):
        """
        Perform swipe action, altered specifically
        for Guild Operations map usage
        """
        swipe_count = 0
        swipe_timer = Timer(3, count=6)
        SWIPE_AREA.load_color(self.device.image)
        while 1:
            if not swipe_timer.started() or swipe_timer.reached():
                swipe_timer.reset()
                self.device.swipe(vector=(distance, 0), box=SWIPE_AREA.area, random_range=SWIPE_RANDOM_RANGE,
                                  padding=0, duration=(0.15, 0.25), name='SWIPE')
                self.device.sleep((1.8, 2.1)) # No assets to use to ensure whether screen has stabilized after swipe
                swipe_count += 1

            self.device.screenshot()
            if SWIPE_AREA.match(self.device.image):
                if swipe_count > 2:
                    logger.info('Same view, page end')
                    return False
                continue

            if not SWIPE_AREA.match(self.device.image):
                logger.info('Different view, page continues')
                return True

    def view_forward(self):
        """
        Performs swipe forward
        """
        return self._view_swipe(distance=-SWIPE_DISTANCE)

    def view_backward(self):
        """
        Performs swipe backward
        """
        return self._view_swipe(distance=SWIPE_DISTANCE)

    def _guild_operations_ensure(self):
        """
        Specific helper to ensure operation has
        been opened. This occurs due to expansion,
        this may shift the map far from how it was
        originally

        Pages:
            in: GUILD_OPERATIONS_MAP
            out: GUILD_OPERATIONS_MAP
        """
        confirm_timer = Timer(1.5, count=3).start()
        verify_timeout = Timer(3, count=6).start()
        while 1:
            self.device.screenshot()

            # End
            if self.appear(GUILD_DISPATCH_QUICK):
                if confirm_timer.reached():
                    return True
            else:
                confirm_timer.reset()
                if verify_timeout.reached():
                    logger.info('Map shift detected, will commence rescan for operation')
                    return False

    def _guild_operations_enter(self):
        """
        Mask and then scan the current image to look
        for active operations, noted by a red dot icon
            0 - Red dot not found at all
            1 - Red dot found and entered into operation successfully
            2 - Red dot found however due to map shift, operation could
                not be entered, allow re-try next loop

        Pages:
            in: GUILD_OPERATIONS_MAP
            out: GUILD_OPERATIONS_DISPATCH
        """
        # Apply mask to cover potential RED_DOTs that are not operations
        image = MASK_OPERATIONS.apply(np.array(self.device.image))

        # Scan image and must have similarity greater than 0.85
        sim, point = TEMPLATE_OPERATIONS_RED_DOT.match_result(image)
        if sim < 0.85:
            logger.info('No active operations found in this area')
            return 0

        # Target RED_DOT found, adjust the found point location
        # for 2 separate clicks
        # First, Expand operation for details click area
        # Second, Open operation enter into dispatch GUI
        expand_point = tuple(sum(x) for x in zip(point, (0, 25)))
        open_point = tuple(sum(x) for x in zip(point, (-55, -55)))

        # Use small area to reduce random click point
        expand_button = area_offset(area=(-4, -4, 4, 4), offset=expand_point)
        open_button = area_offset(area=(-4, -4, 4, 4), offset=open_point)

        expand = Button(area=expand_button, color=(), button=expand_button, name='EXPAND_OPERATION')
        open = Button(area=open_button, color=(), button=open_button, name='OPEN_OPERATION')

        logger.info('Active operation found in this area, attempting to enter')
        self.device.click(expand)
        self.device.sleep((0.5, 0.8))
        self.device.click(open)

        if self._guild_operations_ensure():
            return 1
        else:
            return 2

    def _guild_operations_dispatch_deprecated(self):
        """
        Executes the dispatch sequence

        Pages:
            in: GUILD_OPERATIONS_DISPATCH
            out: GUILD_OPERATIONS_MAP
        """
        # Shorten retry_wait, often not clickable as soon as dispatch window is up
        self.ui_click(click_button=GUILD_DISPATCH_QUICK, check_button=GUILD_DISPATCH_RECOMMEND,
                      retry_wait=3)

        # Already a dispatched fleet?
        # If so, scan image to find point
        # to transition to empty dispatch
        diff_exit = False
        if not self.appear(GUILD_DISPATCH_EMPTY):
            diff_exit = True
            sim, point = TEMPLATE_OPERATIONS_ADD.match_result(self.device.image)
            # Use small area to reduce random click point
            button = area_offset(area=(-2, -2, 24, 12), offset=point)
            dispatch_add = Button(area=button, color=(), button=button, name='GUILD_DISPATCH_ADD')
            self.ui_click(click_button=dispatch_add, check_button=GUILD_DISPATCH_EMPTY,
                          appear_button=GUILD_DISPATCH_RECOMMEND, skip_first_screenshot=True)

        # Currently at an empty fleet window, not entirely sure why need offset=False for this specific click
        self.ui_click(click_button=GUILD_DISPATCH_RECOMMEND, check_button=GUILD_DISPATCH_FLEET,
                      offset=False, skip_first_screenshot=True)

        # Dispatch the fleet, depending on prior actions may need to handle confirm
        # else close once and return to map
        self.device.click(GUILD_DISPATCH_FLEET)
        if diff_exit:
            # GUI self closes the window in this scenario
            self.handle_guild_confirm('GUILD_DISPATCH', GUILD_DISPATCH_IN_PROGRESS)
        else:
            # GUI does not self close the window in this scenario
            # so have to click twice
            self.handle_guild_confirm('GUILD_DISPATCH', GUILD_DISPATCH_RECOMMEND)
        self.ui_click(click_button=GUILD_DISPATCH_CLOSE, check_button=GUILD_OPERATIONS_ACTIVE_CHECK,
                      retry_wait=2, skip_first_screenshot=True)
        self.ensure_no_info_bar()

    def _guild_operations_dispatch(self, skip_first_screenshot=True):
        """
        Executes the dispatch sequence

        Pages:
            in: GUILD_OPERATIONS_DISPATCH
            out: GUILD_OPERATIONS_MAP
        """
        confirm_timer = Timer(1.5, count=3).start()
        close_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(GUILD_DISPATCH_QUICK, interval=3):
                confirm_timer.reset()
                close_timer.reset()
                continue

            sim, point = TEMPLATE_OPERATIONS_ADD.match_result(self.device.image)
            if sim > 0.85:
                # Use small area to reduce random click point
                button = area_offset(area=(-2, -2, 24, 12), offset=point)
                dispatch_add = Button(area=button, color=(), button=button, name='GUILD_DISPATCH_ADD')
                self.device.click(dispatch_add)
                confirm_timer.reset()
                close_timer.reset()
                continue

            if self.appear(GUILD_DISPATCH_EMPTY, interval=3):
                self.device.click(GUILD_DISPATCH_RECOMMEND)
                self.device.sleep((0.5, 0.8))
                self.device.click(GUILD_DISPATCH_FLEET)
                confirm_timer.reset()
                close_timer.reset()

            if self.handle_popup_confirm('GUILD_DISPATCH'):
                self.device.sleep((0.5, 0.8))
                self.device.click(GUILD_DISPATCH_CLOSE)
                confirm_timer.reset()
                close_timer.reset()
                continue

            if self.appear(GUILD_DISPATCH_IN_PROGRESS):
                # Independent timer used instead of interval
                # Since can appear if at least 1 fleet already
                # dispatched, don't want to exit prematurely
                if close_timer.reached_and_reset():
                    self.device.click(GUILD_DISPATCH_CLOSE)
                confirm_timer.reset()
                continue

            # End
            if self.appear(GUILD_OPERATIONS_ACTIVE_CHECK):
                if confirm_timer.reached():
                    self.ensure_no_info_bar()
                    break
            else:
                confirm_timer.reset()
                close_timer.reset()

    def _guild_operations_scan(self, skip_first_screenshot=True):
        """
        Executes the scan operations map sequence
        and additional events
        Scanning for active operations
        if found enters and dispatch fleet
        otherwise swipes forward until
        reached end of map

        Pages:
            in: GUILD_OPERATIONS_MAP
            out: GUILD_OPERATIONS_MAP
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Scan location for any active operations
            entered = self._guild_operations_enter()
            if entered:
                if entered == 1:
                    self._guild_operations_dispatch()
                continue

            if not self.view_forward():
                break

    def _guild_operations_boss_enter(self, skip_first_screenshot=True):
        """
        Execute enter guild raid boss

        Pages:
            in: GUILD_OPERATIONS_BOSS
            out: IN_BATTLE
        """
        is_loading = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(GUILD_BOSS_ENTER, interval=3):
                continue

            if self.appear(GUILD_DISPATCH_RECOMMEND_2, interval=3):
                # TODO: Make this conditional configurable indicating whether
                # player has chosen to auto build the fleet from own dock
                if False:
                    self.device.click(GUILD_DISPATCH_RECOMMEND_2)
                elif self.appear(GUILD_DISPATCH_EMPTY_2):
                    logger.warning('Cannot continue, instructed to not auto-recommend')
                    return False
                continue

            if self.appear_then_click(GUILD_DISPATCH_FLEET, interval=3):
                continue

            # Only print once when detected
            if not is_loading:
                if self.is_combat_loading():
                    is_loading = True
                continue

            # End
            if self.is_combat_executing():
                return True

    def _guild_operations_boss(self):
        """
        Battle against boss on auto

        Pages:
            in: GUILD_OPERATIONS_BOSS
            out: GUILD_OPERATIONS_BOSS
        """
        if not self._guild_operations_boss_enter():
            return
        # TODO: Not as easily overridable, as can affect
        # children classes, uses different BATTLE_STATUS
        # EXP_INFO assets
        # Perhaps have to instantiate independent object
        # Combat class for this
        self.combat_execute(auto='combat_auto')
        self.combat_status(expected_end='in_ui')
        logger.info('Guild Raid Boss has been repelled')

    def _guild_sidebar_click(self, index):
        """
        Performs the calculations necessary
        to determine the index location on
        sidebar and then click at that location

        Args:
            index (int):
                5 for lobby.
                4 for members.
                3 for logistics.
                2 for tech.
                1 for operations.

        Returns:
            bool: if changed.
        """
        if index <= 0 or index > 5:
            logger.warning(f'Sidebar index cannot be clicked, {index}, limit to 1 through 5 only')
            return False

        current = 0
        total = 0

        for idx, button in enumerate(GUILD_SIDEBAR.buttons()):
            image = np.array(self.device.image.crop(button.area))
            if np.sum(image[:, :, 0] > 235) > 100:
                current = idx + 1
                total = idx + 1
                continue
            if np.sum(color_similarity_2d(image, color=(140, 162, 181)) > 221) > 100:
                total = idx + 1
            else:
                break
        if not current:
            logger.warning('No guild sidebar active.')
        if total == 3:
            current = 4 - current
        elif total == 4:
            current = 5 - current
        elif total == 5:
            current = 6 - current
        else:
            logger.warning('Guild sidebar total count error.')

        logger.attr('Guild_sidebar', f'{current}/{total}')
        if current == index:
            return False

        diff = total - index
        if diff >= 0:
            self.device.click(GUILD_SIDEBAR[0, diff])
        else:
            logger.warning(f'Target index {index} cannot be clicked')
        return True

    def _guild_exchange_select(self, choices, btn_guild_logistics_check):
        """
        Execute exchange action on choices
        The order of selection based on item weight
        If none are applicable, return False

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        while len(choices):
            # Select minimum by order of details
            # First, item_weight then plate_weight then button_index
            key = min(choices, key=choices.get)
            details = choices.get(key)

            # Open window for OCR check inventory of target item
            self.ui_click(click_button=details[4], check_button=POPUP_CONFIRM,
                          appear_button=btn_guild_logistics_check, skip_first_screenshot=True)
            item_inventory = GUILD_EXCHANGE_INFO.ocr(self.device.image)

            # Able to make the exchange?
            if details[3] <= item_inventory:
                # Confirm window, return True as exchange was successful
                self.handle_guild_confirm('GUILD_EXCHANGE', btn_guild_logistics_check)
                return True
            else:
                # Cancel window, remove this choice since inapplicable, then choose again
                self.handle_guild_cancel('GUILD_EXCHANGE', btn_guild_logistics_check)
                choices.pop(key)
        logger.warning('Failed to exchange with any of the 3 available options')
        return False

    def _guild_exchange_priorities_helper(self, title, string_priority, default_priority):
        """
        Helper for _guild_exchange_priorities for repeated usage

        Use defaults if configurations are found
        invalid in any manner

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        # Parse the string to a list, perform any special processing when applicable
        priority_parsed = [s.strip().lower() for s in string_priority.split('>')]
        priority_parsed = list(filter(('').__ne__, priority_parsed))
        priority = priority_parsed.copy()
        [priority.remove(s) for s in priority_parsed if s not in default_priority]

        # If after all that processing, result is empty list, then use default
        if len(priority) == 0:
            priority = default_priority

        logger.info(f'{title:10}: {priority}')
        return priority

    def _guild_exchange_priorities(self):
        """
        Set up priorities lists and dictionaries
        based on configurations

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        # Items
        item_priority = self._guild_exchange_priorities_helper('Item', self.config.GUILD_LOGISTICS_ITEM_ORDER_STRING, DEFAULT_ITEM_PRIORITY)

        # T1 Grade Plates
        t1_priority = self._guild_exchange_priorities_helper('T1 Plate', self.config.GUILD_LOGISTICS_PLATE_T1_ORDER_STRING, DEFAULT_PLATE_PRIORITY)

        # T2 Grade Plates
        t2_priority = self._guild_exchange_priorities_helper('T2 Plate', self.config.GUILD_LOGISTICS_PLATE_T2_ORDER_STRING, DEFAULT_PLATE_PRIORITY)

        # T3 Grade Plates
        t3_priority = self._guild_exchange_priorities_helper('T3 Plate', self.config.GUILD_LOGISTICS_PLATE_T3_ORDER_STRING, DEFAULT_PLATE_PRIORITY)

        # Build dictionary
        grade_to_plate_priorities = dict()
        grade_to_plate_priorities['t1'] = t1_priority
        grade_to_plate_priorities['t2'] = t2_priority
        grade_to_plate_priorities['t3'] = t3_priority

        return item_priority, grade_to_plate_priorities

    def _guild_exchange_scan(self):
        """
        Single image scan of available options
        to be exchanged. Summarizes matching
        templates in a 1-D list

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """

        # Scan the available exchange items that are selectable
        EXCHANGE_ITEMS.load_template_folder('./assets/stats_basic')
        EXCHANGE_ITEMS._load_image(self.device.image)
        name = [EXCHANGE_ITEMS.match_template(item.image) for item in EXCHANGE_ITEMS.items]

        # Turn all elements into str and lowercase them
        return [str(item).lower() for item in name]

    def _guild_exchange_check(self, options, item_priority, grade_to_plate_priorities):
        """
        Sift through all exchangable options
        Record details on each to determine
        selection order

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        # Contains the details of all options
        choices = dict()

        for i, option in enumerate(options):
            # Options already sorted sequentially
            # Button indexes are in sync
            btn_key = f'GUILD_EXCHANGE_{i + 1}'
            btn = globals()[btn_key]

            # Defaults set absurd values, which tells ALAS to skip option
            item_weight = len(DEFAULT_ITEM_PRIORITY)
            plate_weight = len(DEFAULT_PLATE_PRIORITY)
            item_cost = 999999999

            # Plate perhaps, extract last
            # 2 characters to ensure
            grade = option[-2:]
            if grade in GRADES:
                item_weight = item_priority.index(grade)
                item_cost = ITEM_TO_COST.get(grade)

                plate_priority = grade_to_plate_priorities.get(grade)
                plate_name = option[5:-2]
                if plate_name in plate_priority:
                    plate_weight = plate_priority.index(plate_name)

                # Did weight update?
                # If not, then this choice given less priority
                # also set to absurd cost to avoid using
                if plate_weight == len(DEFAULT_PLATE_PRIORITY):
                    item_weight = len(DEFAULT_ITEM_PRIORITY)
                    item_cost = 999999999

            # Else normal item, check normally
            # Plates are skipped since only grade in priority
            if option in item_priority:
                item_weight = item_priority.index(option)
                item_cost = ITEM_TO_COST.get(option)

            choices[f'{i + 1}'] = [item_weight, plate_weight, i + 1, item_cost, btn]
            logger.info(f'Choice #{i + 1} - Name: {option:15}, Weight: {item_weight}')

        return choices

    def guild_sidebar_ensure(self, index, skip_first_screenshot=True):
        """
        Performs action to ensure the specified
        index sidebar is transitioned into
        Maximum of 3 attempts

        Args:
            index (int):
                5 for lobby.
                4 for members.
                3 for logistics.
                2 for tech.
                1 for operations.

        Returns:
            bool: sidebar click ensured or not
        """
        if index <= 0 or index > 5:
            logger.warning(f'Sidebar index cannot be ensured, {index}, limit 1 through 5 only')
            return False

        counter = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._guild_sidebar_click(index):
                if counter >= 2:
                    logger.warning('Sidebar could not be ensured')
                    return False
                counter += 1
                self.device.sleep((0.3, 0.5))
                continue
            else:
                return True

    def guild_affiliation_ensure(self, skip_first_screenshot=True):
        """
        Determine player's Guild affiliation

        Pages:
            in: GUILD_ANY
            out: GUILD_LOBBY
        """
        # Transition to GUILD_LOBBY
        if not self.guild_sidebar_ensure(5):
            logger.info('Ensurance has failed, please join a Guild first')
            return

        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(GUILD_AFFILIATION_CHECK_AZUR) or self.appear(GUILD_AFFILIATION_CHECK_AXIS):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

        if self.appear(GUILD_AFFILIATION_CHECK_AZUR):
            return True
        else:
            return False

    def guild_operations_ensure(self, skip_first_screenshot=True):
        """
        Determine which operations menu has loaded
            0 - No ongoing operations, Officers/Elites/Leader must select one to begin
            1 - Operations available, displaying a state diagram/web of operations
            2 - Guild Raid Boss active
            Otherwise None if unable to ensure or determine the menu at all

        Pages:
            in: GUILD_OPERATIONS_ANY
            out: GUILD_OPERATIONS_ANY
        """
        if not self.guild_sidebar_ensure(1):
            logger.info('Ensurance has failed, please join a Guild first')
            return None

        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(GUILD_BOSS_CHECK) or self.appear(GUILD_OPERATIONS_ACTIVE_CHECK):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

        if self.appear(GUILD_OPERATIONS_INACTIVE_CHECK) and self.appear(GUILD_OPERATIONS_ACTIVE_CHECK):
            logger.info('Operations are inactive, please contact your Elite/Officer/Leader seniors to begin an operation')
            return 0
        elif self.appear(GUILD_OPERATIONS_ACTIVE_CHECK):
            logger.info('Operations are active, proceed to scan for open missions and dispatching fleets')
            return 1
        elif self.appear(GUILD_BOSS_CHECK):
            logger.info('Guild Raid Boss is active')
            return 2
        else:
            logger.warning('Operations interface is unrecognized')
            return None

    def handle_guild_confirm(self, confirm_text, appear_button, skip_first_screenshot=True):
        """
        Execute confirm screen transitions

        Pages:
            in: ANY
            out: ANY
        """
        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_popup_confirm(confirm_text):
                confirm_timer.reset()
                continue

            if self.appear_then_click(GET_ITEMS_1, offset=(30, 30), interval=1):
                confirm_timer.reset()
                continue

            # End
            if self.appear(appear_button):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

    def handle_guild_cancel(self, cancel_text, appear_button, skip_first_screenshot=True):
        """
        Execute cancel screen transitions

        Pages:
            in: ANY
            out: ANY
        """
        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_popup_cancel(cancel_text):
                confirm_timer.reset()
                continue

            # End
            if self.appear(appear_button):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

    def guild_lobby_collect(self, skip_first_screenshot=True):
        """
        Performs collect actions if report rewards
        are present in lobby
        If already in page_guild but not lobby,
        this will timeout check and collect next time
        These rewards are queued and do not need to be
        collected immediately

        Pages:
            in: ANY
            out: ANY
        """
        confirm_timer = Timer(1.5, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(GUILD_REPORT_REWARDS, interval=2):
                confirm_timer.reset()
                continue

            if self.appear_then_click(GUILD_REPORT_CLAIM, interval=2):
                confirm_timer.reset()
                continue

            if self.appear_then_click(GET_ITEMS_1, offset=(30, 30), interval=1):
                confirm_timer.reset()
                continue

            if self.appear(GUILD_REPORT_CLAIMED, interval=2):
                self.device.click(GUILD_REPORT_CLOSE)
                confirm_timer.reset()
                continue

            # End
            if self.appear(GUILD_CHECK):
                if confirm_timer.reached():
                    break
            else:
                confirm_timer.reset()

    def guild_exchange(self, limit, btn_guild_logistics_check):
        """
        Performs sift check and executes the applicable
        exchanges, number performed based on limit
        If unable to exchange at all, loop terminates
        prematurely

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        item_priority, grade_to_plate_priorities = self._guild_exchange_priorities()
        for num in range(limit):
            options = self._guild_exchange_scan()
            choices = self._guild_exchange_check(options, item_priority, grade_to_plate_priorities)
            if not self._guild_exchange_select(choices, btn_guild_logistics_check):
                break
            self.ensure_no_info_bar()

    def guild_logistics(self, is_affiliation_azur=True):
        """
        Execute all actions in logistics

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """

        # Transition to Logistics
        # Additional wait time needed
        # as ensure does not wait for
        # page to load
        btn_guild_logistics_check = GUILD_LOGISTICS_CHECK_AZUR if is_affiliation_azur else GUILD_LOGISTICS_CHECK_AXIS
        if not self.guild_sidebar_ensure(3):
            logger.info('Ensurance has failed, please join a Guild first')
            return
        self.wait_until_appear(btn_guild_logistics_check)

        # Acquire remaining buttons
        btn_guild_mission_rewards = GUILD_MISSION_REWARDS_AZUR if is_affiliation_azur else GUILD_MISSION_REWARDS_AXIS
        btn_guild_mission_accept = GUILD_MISSION_ACCEPT_AZUR if is_affiliation_azur else GUILD_MISSION_ACCEPT_AXIS
        btn_guild_supply_rewards = GUILD_SUPPLY_REWARDS_AZUR if is_affiliation_azur else GUILD_SUPPLY_REWARDS_AXIS

        # Execute all logistics actions
        # 1) Collect Mission Rewards if available
        # 2) Accept Mission if available
        # 3) Collect Supply Rewards if available
        # 4) Contribute items if able
        if self.appear_then_click(btn_guild_mission_rewards, offset=(20, 20)):
            self.handle_guild_confirm('GUILD_MISSION_REWARDS', btn_guild_logistics_check)
            self.ensure_no_info_bar()

        if self.appear_then_click(btn_guild_mission_accept, offset=(20, 20)):
            self.handle_guild_confirm('GUILD_MISSION_ACCEPT', btn_guild_logistics_check)
            self.ensure_no_info_bar()

        if self.appear_then_click(btn_guild_supply_rewards, offset=(20, 20)):
            self.handle_guild_confirm('GUILD_SUPPLY_REWARDS', btn_guild_logistics_check)
            self.ensure_no_info_bar()

        GUILD_EXCHANGE_LIMIT.letter = (173, 182, 206) if is_affiliation_azur else (214, 113, 115)
        limit = GUILD_EXCHANGE_LIMIT.ocr(self.device.image)
        if limit > 0:
            self.guild_exchange(limit, btn_guild_logistics_check)

    def guild_operations(self, is_affiliation_azur=True):
        # Determine the mode of operations, currently 3 are available
        operations_mode = self.guild_operations_ensure()
        if operations_mode is None:
            return

        # Deprecated, using self.guild_lobby_collect() instead for this part
        # Execute all operations actions
        # 1) Collect Report Rewards if available
        # 2) Based on mode:
        #    - Operations inactive, nothing to do
        #    - Operations active, scan, select, and then dispatch a fleet
        #    - Guild Raid Boss active, nothing to do tentative
        #btn_guild_report_enter = GUILD_REPORT_ENTER_OPERATIONS if operations_mode < 2 else GUILD_REPORT_ENTER_BOSS
        #btn_guild_report_exit_check = GUILD_OPERATIONS_ACTIVE_CHECK if operations_mode < 2 else GUILD_BOSS_CHECK
        #self.ui_click(click_button=btn_guild_report_enter, check_button=GUILD_REPORT_CLOSE,
        #              skip_first_screenshot=True)
        #if self.appear_then_click(GUILD_REPORT_CLAIM):
        #    self.handle_guild_confirm('GUILD_REPORT_REWARDS', GUILD_REPORT_CLAIMED)
        #    self.ensure_no_info_bar()
        #self.ui_click(click_button=GUILD_REPORT_CLOSE, check_button=btn_guild_report_exit_check,
        #              appear_button=GUILD_REPORT_CLAIMED, skip_first_screenshot=True)

        if operations_mode == 0:
            return
        elif operations_mode == 1:
            self._guild_operations_scan()
        else:
            # TODO: Make this conditional configurable to player to enable check
            if True:
                if self.appear(GUILD_BOSS_AVAILABLE):
                    # self._guild_operations_boss()
                    logger.info('Check TODO for _guild_operations_boss')
                else:
                    logger.info('Guild Raid Boss is already done')
            else:
                logger.info('Play manually to contribute higher score')


    def guild_run(self, logistics=True, operations=True):
        """
        Execute logistics and operations actions
        if enabled by arguments

        Pages:
            in: Any page
            out: page_main
        """
        if not logistics and not operations:
            return False

        # By default, going to page_guild always
        # opens in GUILD_LOBBY
        # If already in page_guild will ensure
        # correct sidebar
        self.ui_ensure(page_guild)
        is_affiliation_azur = self.guild_affiliation_ensure()
        if is_affiliation_azur is None:
            return False

        self.guild_lobby_collect()

        # TODO May have reconsider using these assets
        # as these red dots can move based on whether
        # leader or not
        # Logistics checking is short but if it isn't
        # lit up, we can skip it to save on time
        if not self.appear(GUILD_LOGISTICS_RED_DOT, offset=(30, 30)):
            logistics = False

        # Operations checking is a longer process, if not
        # up then don't bother with it
        if not self.appear(GUILD_OPERATIONS_RED_DOT, offset=(30, 30)):
            operations = False

        if logistics:
            self.guild_logistics(is_affiliation_azur)

        if operations:
            self.guild_operations(is_affiliation_azur)

        self.ui_goto_main()
        return True

    @cached_property
    def guild_interval(self):
        return int(ensure_time(self.config.GUILD_INTERVAL, precision=3) * 60)

    def guild_interval_reset(self):
        """ Call this method after guild run executed """
        del self.__dict__['guild_interval']

    def handle_guild(self):
        """
        Returns:
            bool: If executed
        """
        # Both disabled, do not run
        if not self.config.ENABLE_GUILD_LOGISTICS and not self.config.ENABLE_GUILD_OPERATIONS:
            return False

        # Determine if interval has elapsed
        # If not, assumed to already be in page_main
        # so can check for GUILD_RED_DOT
        now = datetime.now()
        do_logistics = False
        do_operations = False
        guild_record = datetime.strptime(self.config.config.get(*GUILD_RECORD), self.config.TIME_FORMAT)
        update = guild_record + timedelta(seconds=self.guild_interval)
        attr = f'{GUILD_RECORD[0]}_{GUILD_RECORD[1]}'
        logger.attr(f'{attr}', f'Record time: {guild_record}')
        logger.attr(f'{attr}', f'Next update: {update}')
        if now > update or self.appear(GUILD_RED_DOT, offset=(30, 30)):
            do_logistics = self.config.ENABLE_GUILD_LOGISTICS
            do_operations = self.config.ENABLE_GUILD_OPERATIONS

        if not self.guild_run(logistics=do_logistics, operations=do_operations):
            return False

        self.config.record_save(option=('RewardRecord', 'guild'))
        return True