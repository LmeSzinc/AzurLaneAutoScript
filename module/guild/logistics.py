import re

from module.base.button import ButtonGrid
from module.base.decorator import Config, cached_property
from module.base.filter import Filter
from module.base.timer import Timer
from module.base.utils import *
from module.combat.assets import GET_ITEMS_1
from module.exception import GameBugError
from module.guild.assets import *
from module.guild.base import GuildBase
from module.logger import logger
from module.ocr.ocr import Digit
from module.statistics.item import ItemGrid

EXCHANGE_GRIDS = ButtonGrid(
    origin=(470, 470), delta=(198.5, 0), button_shape=(83, 83), grid_shape=(3, 1), name='EXCHANGE_GRIDS')
EXCHANGE_BUTTONS = ButtonGrid(
    origin=(440, 609), delta=(198.5, 0), button_shape=(144, 31), grid_shape=(3, 1), name='EXCHANGE_BUTTONS')
EXCHANGE_FILTER = Filter(regex=re.compile('^(.*?)$'), attr=('name',))


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

    def _handle_guild_fleet_mission_start(self):
        """
        Select new weekly fleet mission.
        Current account must be a guild master or officer.

        Returns:
            bool: If clicked
        """
        if not self.config.GuildLogistics_SelectNewMission:
            return False

        if self.appear_then_click(GUILD_MISSION_NEW, offset=(20, 20), interval=2):
            return True
        if self.appear_then_click(GUILD_MISSION_SELECT, offset=(20, 20), interval=2):
            # Select guild mission for guild leader
            # Hard-coded to select mission: Siren Subjugation III, defeat 300 enemies
            # This mission has the most guild supply and it's the easiest one for members to finish
            return True

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
        logger.attr('Guild master/official', self.config.GuildOperation_SelectNewOperation)
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
            if self._handle_guild_fleet_mission_start():
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
                    logger.warning(
                        'Unable to do guild exchange, probably because the timer in game was bugged')
                    raise GameBugError('Triggered guild logistics refresh bug')

            else:
                confirm_timer.reset()

        logger.info(f'supply_checked: {supply_checked}, mission_checked: {mission_checked}, '
                    f'exchange_checked: {exchange_checked}, mission_finished: {self._guild_logistics_mission_finished}')
        # Azur Lane receives new guild missions now
        # No longer consider `self._guild_logistics_mission_finished` as a check
        return all([supply_checked, mission_checked, exchange_checked])

    def _guild_exchange_scan(self):
        """
        Image scan of available options.
        Not exchangeable items are tagged enough=False.

        Returns:
            list[Item]:

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        # Scan the available exchange items that are selectable
        items = self.exchange_items.predict(self.device.image, name=True, amount=False)

        # Loop EXCHANGE_GRIDS to detect for red text in bottom right area
        # indicating player lacks inventory for that item
        for item, button in zip(items, EXCHANGE_GRIDS.buttons):
            area = area_offset((35, 64, 83, 83), button.area[0:2])
            if self.image_color_count(area, color=(255, 93, 90), threshold=221, count=20):
                item.enough = False
            else:
                item.enough = True

        text = [str(item.name) if item.enough else str(item.name) + ' (not enough)' for item in items]
        logger.info(f'Exchange items: {", ".join(text)}')
        return items

    def _guild_exchange(self):
        """
        Performs sift check and executes the applicable
        exchanges, number performed based on limit
        If unable to exchange at all, loop terminates
        prematurely

        Returns:
            bool: If clicked.

        Pages:
            in: GUILD_LOGISTICS
            out: GUILD_LOGISTICS
        """
        if not GUILD_EXCHANGE_LIMIT.ocr(self.device.image) > 0:
            return False

        items = self._guild_exchange_scan()
        EXCHANGE_FILTER.load(self.config.GuildLogistics_ExchangeFilter)
        selected = EXCHANGE_FILTER.apply(items, func=lambda item: item.enough)
        logger.attr('Exchange_sort', ' > '.join([str(item.name) for item in selected]))

        if len(selected):
            button = EXCHANGE_BUTTONS.buttons[items.index(selected[0])]
            # Just bored click, will retry in self._guild_logistics_collect
            self.device.click(button)
            return True
        else:
            logger.warning('No guild exchange items satisfy current filter, or not having enough resources')
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
        logger.hr('Guild logistics', level=1)
        self.guild_side_navbar_ensure(bottom=3)
        self._guild_logistics_ensure()

        result = self._guild_logistics_collect()
        logger.info(f'Guild logistics run success: {result}')
        return result
