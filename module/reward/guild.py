from re import sub
from datetime import datetime, timedelta
import numpy as np

from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import color_similarity_2d, ensure_time
from module.combat.assets import GET_ITEMS_1
from module.handler.assets import POPUP_CONFIRM
from module.reward.assets import *
from module.logger import logger
from module.ocr.ocr import Digit, Ocr
from module.ui.ui import UI, page_guild

GUILD_RECORD = ('RewardRecord', 'guild')

GUILD_EXCHANGE_LIMIT = Digit(OCR_GUILD_EXCHANGE_LIMIT, threshold=64)
GUILD_EXCHANGE_INFO_1 = Ocr(OCR_GUILD_EXCHANGE_INFO_1, lang='cnocr', letter=(148, 249, 99), threshold=64,
                            alphabet='0123ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz- ')
GUILD_EXCHANGE_INFO_2 = Digit(OCR_GUILD_EXCHANGE_INFO_2, lang='cnocr', letter=(148, 249, 99), threshold=64)

GUILD_SIDEBAR = ButtonGrid(
    origin=(21, 118), delta=(0, 94.5), button_shape=(60, 75), grid_shape=(1, 5), name='GUILD_SIDEBAR')

DEFAULT_RESOURCE_PRIORITY = [
    't1',
    't2',
    'cola',
    'coolant',
    'coin',
    'oil',
    'merit',
    't3'
]

DEFAULT_PARTS_PRIORITY = [
    'torpedo',
    'anti-air',
    'aircraft',
    'main',
    'general'
]

RESOURCE_TO_COST = {
    't1': 20,
    't2': 10,
    't3': 5,
    'cola': 20,
    'coolant': 10,
    'coin': 600,
    'oil': 200,
    'merit': 450
}

GRADE_TO_PARTS = {
    't1': DEFAULT_PARTS_PRIORITY,
    't2': DEFAULT_PARTS_PRIORITY,
    't3': DEFAULT_PARTS_PRIORITY
}

class RewardGuild(UI):
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
        The order of selection based on resource weight
        If none are applicable, return False

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        logger.info(choices)
        for i in range(3):
            # Pick the choice with the least resource_weight
            # if same resource_weight, min proceeds to next
            # iterable, which is parts_weight
            # if same parts_weight, next iterable
            # then is button_index
            key = min(choices, key=choices.get)
            details = choices.get(key)
            if details[3] <= details[4]:
                self.ui_click(click_button=details[5], check_button=POPUP_CONFIRM,
                              appear_button=btn_guild_logistics_check, skip_first_screenshot=True)
                self.handle_guild_confirm('GUILD_EXCHANGE', btn_guild_logistics_check)
                #self.handle_guild_cancel('GUILD_EXCHANGE', btn_guild_logistics_check)
                return True
            else:
                # Remove this choice since inapplicable, then choose again
                choices.pop(key)
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
        # First Resources
        resource_priority = self._guild_exchange_priorities_helper('Resource', self.config.GUILD_LOGISTICS_RESOURCE_ORDER_STRING, DEFAULT_RESOURCE_PRIORITY)

        # Second T1 Grade Parts
        t1_priority = self._guild_exchange_priorities_helper('T1 Gear', self.config.GUILD_LOGISTICS_GEAR_T1_ORDER_STRING, DEFAULT_PARTS_PRIORITY)

        # Third T2 Grade Parts
        t2_priority = self._guild_exchange_priorities_helper('T2 Gear', self.config.GUILD_LOGISTICS_GEAR_T2_ORDER_STRING, DEFAULT_PARTS_PRIORITY)

        # Fourth T3 Grade Parts
        t3_priority = self._guild_exchange_priorities_helper('T3 Gear', self.config.GUILD_LOGISTICS_GEAR_T3_ORDER_STRING, DEFAULT_PARTS_PRIORITY)

        # Build custom GRADE_TO_PARTS
        grade_to_parts_priorities = GRADE_TO_PARTS.copy()
        grade_to_parts_priorities['t1'] = t1_priority
        grade_to_parts_priorities['t2'] = t2_priority
        grade_to_parts_priorities['t3'] = t3_priority

        return resource_priority, grade_to_parts_priorities


    def _guild_exchange_check(self, resource_priority, grade_to_parts_priorities, btn_guild_logistics_check):
        """
        Sift through all exchangable options
        Record details on each to determine
        selection order

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        # Holds the details of all 3 choice options
        choices = dict()

        # Check all 3 available selections
        # Use Ocr to determine resource, cost, and inventory of that resource
        for index in range(3):
            index += 1
            btn_key = f'GUILD_EXCHANGE_{index}'
            btn = globals()[btn_key]
            self.ui_click(click_button=btn, check_button=POPUP_CONFIRM,
                          appear_button=btn_guild_logistics_check, skip_first_screenshot=True)

            info_text = (GUILD_EXCHANGE_INFO_1.ocr(self.device.image)).lower()

            # Defaults if Ocr were to fail, set absurd values forcing to skip the resource
            resource_weight = len(DEFAULT_RESOURCE_PRIORITY)
            parts_weight = len(DEFAULT_PARTS_PRIORITY)
            resource_cost = 999999999
            resource_inventory = 0

            # First loop by resource priorities
            for i, resource in enumerate(resource_priority):
                # Valid check, update resource_weight and resource_cost
                if resource in info_text:
                    resource_weight = i
                    resource_cost = RESOURCE_TO_COST.get(resource)

                # If a gear plate, then update parts_weight
                # If not found, parts_weight is unchanged therefore
                # reset resource_cost, to make it impossible to exchange
                if resource in ['t1', 't2', 't3']:
                    parts_priority = grade_to_parts_priorities.get(resource)
                    for j, parts in enumerate(parts_priority):
                        if parts in info_text:
                            parts_weight = j
                    if parts_weight == len(DEFAULT_PARTS_PRIORITY):
                        resource_cost = 999999999
            resource_inventory = GUILD_EXCHANGE_INFO_2.ocr(self.device.image)
            choices[f'{index}'] = [resource_weight, parts_weight, index, resource_cost, resource_inventory, btn]

            self.handle_guild_cancel(btn_key, btn_guild_logistics_check)

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
            in: ANY
            out: GUILD_LOBBY
        """
        # Transition to GUILD_LOBBY
        self.guild_sidebar_ensure(5)

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
        resource_priority, grade_to_parts_priorities = self._guild_exchange_priorities()
        for num in range(limit):
            choices = self._guild_exchange_check(resource_priority, grade_to_parts_priorities, btn_guild_logistics_check)
            if not self._guild_exchange_select(choices, btn_guild_logistics_check):
                logger.warning('Failed to exchange with any of the 3 available options')
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
        # 4) Contribute resources if able
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
        is_affiliation_azur = self.guild_affiliation_ensure()

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
            do_logistics = True
            do_operations = False

        if not self.guild_run(logistics=do_logistics, operations=do_operations):
            return False

        self.config.record_save(option=('RewardRecord', 'guild'))
        return True
