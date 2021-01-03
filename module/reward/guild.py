from re import sub
from datetime import datetime, timedelta
import numpy as np

from module.statistics.item import ItemGrid
from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import *
from module.combat.assets import GET_ITEMS_1
from module.handler.assets import POPUP_CONFIRM
from module.reward.assets import *
from module.logger import logger
from module.ocr.ocr import Digit, Ocr
from module.ui.ui import UI, page_guild

GUILD_RECORD = ('RewardRecord', 'guild')

GUILD_EXCHANGE_LIMIT = Digit(OCR_GUILD_EXCHANGE_LIMIT, threshold=64)
GUILD_EXCHANGE_INFO = Digit(OCR_GUILD_EXCHANGE_INFO, lang='cnocr', letter=(148, 249, 99), threshold=64)

GUILD_SIDEBAR = ButtonGrid(
    origin=(21, 118), delta=(0, 94.5), button_shape=(60, 75), grid_shape=(1, 6), name='GUILD_SIDEBAR')
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

class RewardGuild(UI):
    def _guild_sidebar_click(self, index):
        """
        Performs the calculations necessary
        to determine the index location on
        sidebar and then click at that location

        Args:
            index (int):
                leader sidebar
                6 for lobby.
                5 for members.
                4 apply.
                3 for logistics.
                2 for tech.
                1 for operations.

                member sidebar
                6 for lobby.
                5 for members.
                3/4 for logistics.
                2 for tech
                1 for operations

        Returns:
            bool: if changed.
        """
        if index <= 0 or index > 6:
            logger.warning(f'Sidebar index cannot be clicked, {index}, limit to 1 through 6 only')
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
        elif total == 6:
            current = 7 - current
        else:
            logger.warning('Guild sidebar total count error.')

        if total == 5 and index >= 4:
            index -= 1

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
                leader sidebar
                6 for lobby.
                5 for members.
                4 apply.
                3 for logistics.
                2 for tech.
                1 for operations.

                member sidebar
                6 for lobby.
                5 for members.
                3/4 for logistics.
                2 for tech
                1 for operations

        Returns:
            bool: sidebar click ensured or not
        """
        if index <= 0 or index > 6:
            logger.warning(f'Sidebar index cannot be ensured, {index}, limit 1 through 6 only')
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
        if not self.guild_sidebar_ensure(6):
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

    def guild_logistics(self):
        """
        Execute all actions in logistics

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """

        # Transition to Logistics
        if not self.guild_sidebar_ensure(3):
            logger.info('Ensurance has failed, please join a Guild first')
            return

        # Last screencapture should contain affiliation
        # color in top-right where guild coins is
        # Determine guild affiliation
        color = get_color(self.device.image, GUILD_AFFILIATION_CHECK_IN_LOGISTICS.area)
        if color_similar(color, (115, 146, 206)):
            is_azur_affiliation  = True
        elif color_similar(color, (206, 117, 115)):
            is_azur_affiliation  = False
        else:
            logger.warning(f'Unknown guild affiliation color: {color}')
            return

        # Additional wait time needed to screencapture fully loaded page
        btn_guild_logistics_check = GUILD_LOGISTICS_CHECK_AZUR if is_azur_affiliation  else GUILD_LOGISTICS_CHECK_AXIS
        self.wait_until_appear(btn_guild_logistics_check)

        # Acquire remaining buttons
        btn_guild_mission_rewards = GUILD_MISSION_REWARDS_AZUR if is_azur_affiliation  else GUILD_MISSION_REWARDS_AXIS
        btn_guild_mission_accept = GUILD_MISSION_ACCEPT_AZUR if is_azur_affiliation  else GUILD_MISSION_ACCEPT_AXIS
        btn_guild_supply_rewards = GUILD_SUPPLY_REWARDS_AZUR if is_azur_affiliation  else GUILD_SUPPLY_REWARDS_AXIS

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

    def guild_operations(self):
        pass

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

        if logistics:
            self.guild_logistics()

        if operations:
            self.guild_operations()

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
            do_logistics = True
            do_operations = False

        if not self.guild_run(logistics=do_logistics, operations=do_operations):
            return False

        self.config.record_save(option=('RewardRecord', 'guild'))
        return True