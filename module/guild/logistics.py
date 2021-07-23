from module.base.button import ButtonGrid
from module.base.decorator import cached_property, Config
from module.base.timer import Timer
from module.base.utils import *
from module.combat.assets import GET_ITEMS_1
from module.exception import LogisticsRefreshBugHandler
from module.guild.assets import *
from module.guild.base import GuildBase
from module.logger import logger
from module.ocr.ocr import Digit
from module.statistics.item import ItemGrid

RECORD_OPTION_LOGISTICS = ('RewardRecord', 'logistics')
RECORD_SINCE_LOGISTICS = (0,)

EXCHANGE_GRIDS = ButtonGrid(
    origin=(470, 470), delta=(198.5, 0), button_shape=(83, 83), grid_shape=(3, 1), name='EXCHANGE_GRIDS')
EXCHANGE_BUTTONS = ButtonGrid(
    origin=(440, 609), delta=(198.5, 0), button_shape=(144, 31), grid_shape=(3, 1), name='EXCHANGE_BUTTONS')

DEFAULT_ITEM_PRIORITY = [
    't1',
    't2',
    't3',
    'oxycola',
    'coolant',
    'coins',
    'oil',
    'merit'
]

DEFAULT_PLATE_PRIORITY = [
    'torpedo',
    'antiair',
    'plane',
    'gun',
    'general'
]

GRADES = [s for s in DEFAULT_ITEM_PRIORITY if len(s) == 2]


class ExchangeLimitOcr(Digit):
    def pre_process(self, image):
        """
        Args:
            image (np.ndarray): Shape (height, width, channel)

        Returns:
            np.ndarray: Shape (width, height)
        """
        return 255 - color_mapping(rgb2gray(image), max_multiply=2.5)


GUILD_EXCHANGE_LIMIT = ExchangeLimitOcr(OCR_GUILD_EXCHANGE_LIMIT, threshold=64)


class GuildLogistics(GuildBase):
    _guild_logistics_mission_finished = False

    @cached_property
    def exchange_items(self):
        item_grid = ItemGrid(
            EXCHANGE_GRIDS, {}, template_area=(40, 21, 89, 70), amount_area=(60, 71, 91, 92))
        item_grid.load_template_folder('./assets/stats_basic')
        return item_grid

    def _is_in_guild_logistics(self):
        """
        Color sample the GUILD_LOGISTICS_ENSURE_CHECK
        to determine whether is currently
        visible or not

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        # Axis (181, 97, 99) and Azur (148, 178, 255)
        if self.image_color_count(GUILD_LOGISTICS_ENSURE_CHECK, color=(181, 97, 99), threshold=221, count=400) or \
                self.image_color_count(GUILD_LOGISTICS_ENSURE_CHECK, color=(148, 178, 255), threshold=221, count=400):
            return True
        else:
            return False

    def _guild_logistics_ensure(self, skip_first_screenshot=True):
        """
        Ensure guild logistics is loaded
        After entering guild logistics, background loaded first, then St.Louis / Leipzig, then guild logistics

        Args:
            skip_first_screenshot (bool):
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._is_in_guild_logistics():
                break

    @Config.when(SERVER='en')
    def _guild_logistics_mission_available(self):
        """
        Color sample the GUILD_MISSION area to determine
        whether the button is enabled, mission already
        in progress, or no more missions can be accepted

        Used at least twice, 'Collect' and 'Accept'

        Returns:
            bool: If button active

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        r, g, b = get_color(self.device.image, GUILD_MISSION.area)
        if g > max(r, b) - 10:
            # Green tick at the bottom right corner if guild mission finished
            logger.info('Guild mission has finished this week')
            self._guild_logistics_mission_finished = True
            return False
        # 0/300 in EN is bold and pure white, and Collect rewards is blue white, so reverse the if condition
        elif self.image_color_count(GUILD_MISSION, color=(255, 255, 255), threshold=235, count=100):

            logger.info('Guild mission button inactive')
            return False
        elif self.image_color_count(GUILD_MISSION, color=(255, 255, 255), threshold=180, count=50):
            # white pixels less than 50, but has blue-white pixels
            logger.info('Guild mission button active')
            return True
        else:
            # No guild mission counter
            logger.info('No guild mission found, mission of this week may not started')
            return False
            # if self.image_color_count(GUILD_MISSION_CHOOSE, color=(255, 255, 255), threshold=221, count=100):
            #     # Guild mission choose available if user is guild master
            #     logger.info('Guild mission choose found')
            #     return True
            # else:
            #     logger.info('Guild mission choose not found')
            #     return False

    @Config.when(SERVER='jp')
    def _guild_logistics_mission_available(self):
        """
        Color sample the GUILD_MISSION area to determine
        whether the button is enabled, mission already
        in progress, or no more missions can be accepted

        Used at least twice, 'Collect' and 'Accept'

        Returns:
            bool: If button active

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        r, g, b = get_color(self.device.image, GUILD_MISSION.area)
        if g > max(r, b) - 10:
            # Green tick at the bottom right corner if guild mission finished
            logger.info('Guild mission has finished this week')
            self._guild_logistics_mission_finished = True
            return False
        elif self.image_color_count(GUILD_MISSION, color=(255, 255, 255), threshold=254, count=50):
            # 0/300 in JP is (255, 255, 255)
            logger.info('Guild mission button inactive')
            return False
        elif self.image_color_count(GUILD_MISSION, color=(255, 255, 255), threshold=180, count=400):
            # (255, 255, 255) less than 50, but has many blue-white pixels
            logger.info('Guild mission button active')
            return True
        elif not self.image_color_count(GUILD_MISSION, color=(255, 255, 255), threshold=180, count=50):
            # No guild mission counter
            logger.info('No guild mission found, mission of this week may not started')
            # Guild mission choose in JP server disabled until we get the screenshot.
            return False
            # if self.image_color_count(GUILD_MISSION_CHOOSE, color=(255, 255, 255), threshold=221, count=100):
            #     # Guild mission choose available if user is guild master
            #     logger.info('Guild mission choose found')
            #     return True
            # else:
            #     logger.info('Guild mission choose not found')
            #     return False
        else:
            logger.info('Unknown guild mission condition. Skipped.')
            return False

    @Config.when(SERVER=None)
    def _guild_logistics_mission_available(self):
        """
        Color sample the GUILD_MISSION area to determine
        whether the button is enabled, mission already
        in progress, or no more missions can be accepted

        Used at least twice, 'Collect' and 'Accept'

        Returns:
            bool: If button active

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        r, g, b = get_color(self.device.image, GUILD_MISSION.area)
        if g > max(r, b) - 10:
            # Green tick at the bottom right corner if guild mission finished
            logger.info('Guild mission has finished this week')
            self._guild_logistics_mission_finished = True
            return False
        elif self.image_color_count(GUILD_MISSION, color=(255, 255, 255), threshold=180, count=400):
            # Unfinished mission accept/collect range from about 240 to 322
            logger.info('Guild mission button active')
            return True
        elif not self.image_color_count(GUILD_MISSION, color=(255, 255, 255), threshold=180, count=50):
            # No guild mission counter
            logger.info('No guild mission found, mission of this week may not started')
            return False
            # if self.image_color_count(GUILD_MISSION_CHOOSE, color=(255, 255, 255), threshold=221, count=100):
            #     # Guild mission choose available if user is guild master
            #     logger.info('Guild mission choose found')
            #     return True
            # else:
            #     logger.info('Guild mission choose not found')
            #     return False
        else:
            logger.info('Guild mission button inactive')
            return False

    def _guild_logistics_supply_available(self):
        """
        Color sample the GUILD_SUPPLY area to determine
        whether the button is enabled or disabled

        mode determines

        Returns:
            bool: If button active

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        color = get_color(self.device.image, GUILD_SUPPLY.area)
        # Active button has white letters, inactive button have gray letters
        if np.max(color) > np.mean(color) + 25:
            # For members, click to receive supply
            # For leaders, click to buy supply and receive supply
            logger.info('Guild supply button active')
            return True
        else:
            logger.info('Guild supply button inactive')
            return False

    def _guild_logistics_collect(self, skip_first_screenshot=True):
        """
        Execute collect/accept screen transitions within
        logistics

        Args:
            skip_first_screenshot (bool):

        Returns:
            bool: If all guild logistics are check, no need to check them today.

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        logger.hr('Guild logistics')
        confirm_timer = Timer(1.5, count=3).start()
        exchange_interval = Timer(1.5, count=3)
        click_interval = Timer(0.5, count=1)
        supply_checked = False
        mission_checked = False
        exchange_checked = False
        exchange_count = 0

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Handle all popups
            if self.handle_popup_confirm('GUILD_LOGISTICS'):
                confirm_timer.reset()
                exchange_interval.reset()
                continue
            if self.appear_then_click(GET_ITEMS_1, interval=2):
                confirm_timer.reset()
                exchange_interval.reset()
                continue
            if self.appear_then_click(GUILD_MISSION_SELECT, offset=(20, 20), interval=2):
                # Select guild mission for guild leader
                # Hard-coded to select mission: Siren Subjugation III, defeat 300 enemies
                # This mission has the most guild supply and it's the easiest one for members to finish
                confirm_timer.reset()
                continue

            if self._is_in_guild_logistics():
                # Supply
                if not supply_checked and self._guild_logistics_supply_available():
                    if click_interval.reached():
                        self.device.click(GUILD_SUPPLY)
                        click_interval.reset()
                    confirm_timer.reset()
                    continue
                else:
                    supply_checked = True
                # Mission
                if not mission_checked and self._guild_logistics_mission_available():
                    if click_interval.reached():
                        self.device.click(GUILD_MISSION)
                        click_interval.reset()
                    confirm_timer.reset()
                    continue
                else:
                    mission_checked = True
                # Exchange
                if not exchange_checked and exchange_interval.reached():
                    if self._guild_exchange():
                        confirm_timer.reset()
                        exchange_interval.reset()
                        exchange_count += 1
                        continue
                    else:
                        exchange_checked = True
                # End
                if not self.info_bar_count() and confirm_timer.reached():
                    break
                # if supply_checked and mission_checked and exchange_checked:
                #     break
                if exchange_count >= 5:
                    # If you run AL across days, then do guild exchange.
                    # There will show an error, said time is not up.
                    # Restart the game can't fix the problem.
                    # To fix this, you have to enter guild logistics once, then restart.
                    # If exchange for 5 times, this bug is considered to be triggered.
                    logger.warning('Triggered guild logistics refresh bug')
                    raise LogisticsRefreshBugHandler('Triggered guild logistics refresh bug')

            else:
                confirm_timer.reset()

        logger.info(f'supply_checked: {supply_checked}, mission_checked: {mission_checked}, '
                    f'exchange_checked: {exchange_checked}, mission_finished: {self._guild_logistics_mission_finished}')
        return all([supply_checked, mission_checked, exchange_checked, self._guild_logistics_mission_finished])

    @staticmethod
    def _guild_exchange_priorities_helper(title, string_priority, default_priority):
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
        priority_parsed = list(filter(''.__ne__, priority_parsed))
        priority = priority_parsed.copy()
        [priority.remove(s) for s in priority_parsed if s not in default_priority]

        # If after all that processing, result is empty list, then use default
        if len(priority) == 0:
            priority = default_priority

        # logger.info(f'{title:10}: {priority}')
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
        item_priority = self._guild_exchange_priorities_helper(
            'Item', self.config.GUILD_LOGISTICS_ITEM_ORDER_STRING, DEFAULT_ITEM_PRIORITY)

        # T1 Grade Plates
        t1_priority = self._guild_exchange_priorities_helper(
            'T1 Plate', self.config.GUILD_LOGISTICS_PLATE_T1_ORDER_STRING, DEFAULT_PLATE_PRIORITY)

        # T2 Grade Plates
        t2_priority = self._guild_exchange_priorities_helper(
            'T2 Plate', self.config.GUILD_LOGISTICS_PLATE_T2_ORDER_STRING, DEFAULT_PLATE_PRIORITY)

        # T3 Grade Plates
        t3_priority = self._guild_exchange_priorities_helper(
            'T3 Plate', self.config.GUILD_LOGISTICS_PLATE_T3_ORDER_STRING, DEFAULT_PLATE_PRIORITY)

        # Build dictionary
        grade_to_plate_priorities = dict()
        grade_to_plate_priorities['t1'] = t1_priority
        grade_to_plate_priorities['t2'] = t2_priority
        grade_to_plate_priorities['t3'] = t3_priority

        return item_priority, grade_to_plate_priorities

    def _guild_exchange_scan(self):
        """
        Image scan of available options
        to be exchanged. Summarizes matching
        templates and whether red text present
        in a list of tuples

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """

        # Scan the available exchange items that are selectable
        self.exchange_items._load_image(self.device.image)
        name = [self.exchange_items.match_template(item.image) for item in self.exchange_items.items]
        name = [str(item).lower() for item in name]

        # Loop EXCHANGE_GRIDS to detect for red text in bottom right area
        # indicating player lacks inventory for that item
        in_red_list = []
        for button in EXCHANGE_GRIDS.buttons():
            area = area_offset((35, 64, 83, 83), button.area[0:2])
            if self.image_color_count(area, color=(255, 93, 90), threshold=221, count=20):
                in_red_list.append(True)
            else:
                in_red_list.append(False)

        # Zip contents of both lists into tuples
        return zip(name, in_red_list)

    @staticmethod
    def _guild_exchange_check(options, item_priority, grade_to_plate_priorities):
        """
        Sift through all exchangeable options
        Record details on each to determine
        selection order

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        # Contains the details of all options
        choices = dict()

        for i, (option, in_red) in enumerate(options):
            # Options already sorted sequentially
            # Button indexes are in sync
            btn = EXCHANGE_BUTTONS[i, 0]

            # Defaults set absurd values, which tells ALAS to skip option
            item_weight = len(DEFAULT_ITEM_PRIORITY)
            plate_weight = len(DEFAULT_PLATE_PRIORITY)
            can_exchange = False

            # Player lacks inventory of this item
            # so leave this choice under all defaults
            # to skip
            if not in_red:
                # Plate perhaps, extract last
                # 2 characters to ensure
                grade = option[-2:]
                if grade in GRADES:
                    item_weight = item_priority.index(grade)
                    can_exchange = True

                    plate_priority = grade_to_plate_priorities.get(grade)
                    plate_name = option[5:-2]
                    if plate_name in plate_priority:
                        plate_weight = plate_priority.index(plate_name)

                    # Did weight update?
                    # If not, then this choice given less priority
                    # also set to absurd cost to avoid using
                    if plate_weight == len(DEFAULT_PLATE_PRIORITY):
                        item_weight = len(DEFAULT_ITEM_PRIORITY)
                        can_exchange = False

                # Else normal item, check normally
                # Plates are skipped since only grade in priority
                if option in item_priority:
                    item_weight = item_priority.index(option)
                    can_exchange = True

            choices[f'{i + 1}'] = [item_weight, plate_weight, i + 1, can_exchange, btn]
            logger.info(f'Choice #{i + 1} - Name: {option:15}, Weight: {item_weight:3}, Exchangeable: {can_exchange}')

        return choices

    def _guild_exchange_select(self, choices):
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

            # Item is exchangeable and exchange was a success
            if details[3]:
                self.device.click(details[4])
                return True
            else:
                # Remove this choice since inapplicable, then choose again
                choices.pop(key)
        logger.warning('Failed to exchange with any of the 3 available options')
        return False

    def _guild_exchange(self):
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
        if not GUILD_EXCHANGE_LIMIT.ocr(self.device.image) > 0:
            return False

        options = self._guild_exchange_scan()
        choices = self._guild_exchange_check(options, item_priority, grade_to_plate_priorities)
        if self._guild_exchange_select(choices):
            return True
        else:
            return False

    def guild_logistics(self):
        """
        Execute all actions in logistics

        Returns:
            bool: If all guild logistics are check, no need to check them today.

        Pages:
            in: page_guild
            out: page_guild, GUILD_LOGISTICS
        """
        # Transition to Logistics
        if not self.guild_sidebar_ensure(3):
            logger.info('Logistics sidebar not ensured, try again on next reward loop')
            return False
        self._guild_logistics_ensure()

        # Run
        checked = self._guild_logistics_collect()
        if checked:
            logger.info('All guild logistics finished today, skip checking them today')

        return checked
