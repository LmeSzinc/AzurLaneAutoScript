from module.base.timer import Timer
from module.base.utils import *
from module.exception import GameTooManyClickError
from module.logger import logger
from module.os.assets import *
from module.os_handler.action_point import ActionPointHandler
from module.os_handler.assets import AUTO_SEARCH_REWARD
from module.os_handler.map_event import MapEventHandler

ZONE_TYPES = [ZONE_DANGEROUS, ZONE_SAFE, ZONE_OBSCURE, ZONE_ABYSSAL, ZONE_STRONGHOLD, ZONE_ARCHIVE]
ZONE_SELECT = [SELECT_DANGEROUS, SELECT_SAFE, SELECT_OBSCURE, SELECT_ABYSSAL, SELECT_STRONGHOLD, SELECT_ARCHIVE]
ASSETS_PINNED_ZONE = ZONE_TYPES + [ZONE_ENTRANCE, ZONE_SWITCH, ZONE_PINNED]


class OSExploreError(Exception):
    pass


class GlobeOperation(ActionPointHandler, MapEventHandler):
    def is_in_globe(self):
        return self.appear(GLOBE_GOTO_MAP, offset=(20, 20))

    def get_zone_pinned(self):
        """
        Returns:
            Button:
        """
        for zone in ZONE_TYPES:
            if self.appear(zone, offset=(20, 20)):
                for button in ASSETS_PINNED_ZONE:
                    button.load_offset(zone)

                return zone

        return None

    def is_zone_pinned(self):
        """
        Returns:
            bool:
        """
        return self.get_zone_pinned() is not None

    @staticmethod
    def pinned_to_name(button):
        """
        Args:
            button (Button):

        Returns:
            str: DANGEROUS, SAFE, OBSCURE, ABYSSAL, STRONGHOLD, ARCHIVE.
        """
        return button.name.split('_')[1]

    def get_zone_pinned_name(self):
        """
        Returns:
            str: DANGEROUS, SAFE, OBSCURE, ABYSSAL, STRONGHOLD, ARCHIVE, or ''.
        """
        pinned = self.get_zone_pinned()
        if pinned is not None:
            return self.pinned_to_name(pinned)
        else:
            return ''

    def handle_zone_pinned(self):
        """
        CLose pinned zone info.

        Returns:
            bool: If handled.
        """
        if self.is_zone_pinned():
            # A click does not disable pinned zone, a swipe does.
            self.device.swipe_vector(
                (50, -50), box=area_pad(ZONE_PINNED.area, pad=-80), random_range=(-10, -10, 10, 10),
                padding=0, name='PINNED_DISABLE')
            return True

        return False

    def ensure_no_zone_pinned(self, skip_first_screenshot=True):
        confirm_timer = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_zone_pinned():
                confirm_timer.reset()
            else:
                if confirm_timer.reached():
                    break

    def zone_has_switch(self):
        """
        Switch is an icon of 4 block, one block in white. White block keeps rotating.
        If detected one white block, consider this is a zone switch.

        2021.07.15 ZONE_SWITCH was downscaled and added text "Change Zone".
            So ZONE_SWITCH changed to detect "Change Zone"

        Returns:
            bool: If current zone has switch.
        """
        # image = self.image_crop(ZONE_SWITCH)
        # center = np.array(image.size) / 2
        # count = 0
        # for corner in area2corner((0, 0, *image.size)):
        #     area = (min(corner[0], center[0]), min(corner[1], center[1]),
        #             max(corner[0], center[0]), max(corner[1], center[1]))
        #     area = area_pad(area, pad=2)
        #     color = np.mean(get_color(image, area))
        #     if color > 235:
        #         count += 1
        #
        # if count == 1:
        #     return True
        # elif count == 0:
        #     return False
        # else:
        #     logger.warning(f'Unexpected zone switch, white block: {count}')

        return self.appear(ZONE_SWITCH, offset=(5, 5))

    _zone_select_offset = (20, 200)
    _zone_select_similarity = 0.75

    def get_zone_select(self):
        """
        Returns:
            list[Button]:
        """
        # Lower threshold to 0.75
        # Don't know why buy but fonts are different sometimes
        return [select for select in ZONE_SELECT if
                self.appear(select, offset=self._zone_select_offset, threshold=self._zone_select_similarity)]

    def is_in_zone_select(self):
        """
        Returns:
            bool:
        """
        return len(self.get_zone_select()) > 0

    def ensure_zone_select_expanded(self):
        """
        Returns:
            list[Button]:
        """
        record = 0
        for _ in range(5):
            selection = self.get_zone_select()
            if len(selection) == record and record > 0:
                return selection

            record = len(selection)
            self.device.screenshot()

        logger.warning('Failed to ensure zone selection expanded, assume expanded')
        return self.get_zone_select()

    def zone_select_enter(self):
        """
        Pages:
            in: is_zone_pinned
            out: is_in_zone_select
        """
        self.ui_click(ZONE_SWITCH, appear_button=self.is_zone_pinned, check_button=self.is_in_zone_select,
                      skip_first_screenshot=True)

    def zone_select_execute(self, button):
        """
        Args:
            button (Button): Button to select, one of the SELECT_* buttons

        Pages:
            in: is_in_zone_select
            out: is_zone_pinned
        """

        def appear():
            return self.appear(button, offset=self._zone_select_offset, threshold=self._zone_select_similarity)

        self.ui_click(button, appear_button=appear, check_button=self.is_zone_pinned,
                      skip_first_screenshot=True)

    def zone_type_select(self, types=('SAFE', 'DANGEROUS')):
        """
        Args:
            types (tuple[str], list[str], str): Zone types, or a list of them.
                Available types: DANGEROUS, SAFE, OBSCURE, ABYSSAL, STRONGHOLD, ARCHIVE.
                Try the the first selection in type list, if not available, try the next one.
                Do nothing if no selection satisfied input.

        Returns:
            bool: If success.

        Pages:
            in: is_zone_pinned
            out: is_zone_pinned
        """
        if not self.zone_has_switch():
            logger.info('Zone has no type to select, skip')
            return True

        if isinstance(types, str):
            types = [types]

        def get_button(selection_):
            for typ in types:
                typ = 'SELECT_' + typ
                for sele in selection_:
                    if typ == sele.name:
                        return sele
            return None

        pinned = self.get_zone_pinned_name()
        if pinned in types:
            logger.info(f'Already selected at {pinned}')
            return True

        for _ in range(3):
            self.zone_select_enter()
            selection = self.ensure_zone_select_expanded()
            logger.attr('Zone_selection', selection)

            button = get_button(selection)
            if button is None:
                logger.warning('No such zone type to select, fallback to default')
                types = ('SAFE', 'DANGEROUS')
                button = get_button(selection)

            self.zone_select_execute(button)
            if self.pinned_to_name(button) == self.get_zone_pinned_name():
                return True

        logger.warning('Failed to select zone type after 3 trial')
        return False

    def zone_has_safe(self):
        """
        Checks and selects if zone has SAFE otherwise selects DANGEROUS
        which is guaranteed to be present in every zone

        Returns:
            bool: If SAFE is present.

        Pages:
            in: is_zone_pinned
            out: is_zone_pinned
        """
        if self.get_zone_pinned_name() == 'SAFE':
            return True
        elif self.zone_has_switch():
            self.zone_select_enter()
            flag = SELECT_SAFE in self.ensure_zone_select_expanded()
            button = SELECT_SAFE if flag else SELECT_DANGEROUS
            self.zone_select_execute(button)
            return flag
        else:
            # No zone_switch, already on DANGEROUS
            return False

    def os_globe_goto_map(self, skip_first_screenshot=True):
        """
        Pages:
            in: is_in_globe
            out: is_in_map
        """
        return self.ui_click(GLOBE_GOTO_MAP, check_button=self.is_in_map, offset=(20, 20),
                             retry_wait=3, skip_first_screenshot=skip_first_screenshot)

    def os_map_goto_globe(self, unpin=True, skip_first_screenshot=True):
        """
        Args:
            unpin (bool):
            skip_first_screenshot (bool):

        Pages:
            in: is_in_map
            out: is_in_globe
        """
        click_count = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(MAP_GOTO_GLOBE, offset=(200, 5), interval=5):
                click_count += 1
                if click_count >= 5:
                    # When there's zone exploration reward, AL just don't let you go.
                    logger.warning('Unable to goto globe, '
                                   'there might be uncollected zone exploration rewards preventing exit')
                    raise GameTooManyClickError(f'Too many click for a button: {MAP_GOTO_GLOBE}')
                continue
            if self.handle_map_event():
                continue
            # Popup: AUTO_SEARCH_REWARD appears slowly
            if self.appear_then_click(AUTO_SEARCH_REWARD, offset=(50, 50), interval=5):
                continue
            # Popup: Leaving current zone will terminate meowfficer searching.
            # Popup: Leaving current zone will retreat submarines
            # Searching reward will be shown after entering another zone.
            if self.handle_popup_confirm('GOTO_GLOBE'):
                continue

            # End
            if self.is_in_globe():
                break

        skip_first_screenshot = True
        confirm_timer = Timer(1, count=2).start()
        unpinned = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if unpin:
                if self.handle_zone_pinned():
                    unpinned += 1
                    confirm_timer.reset()
                else:
                    if unpinned and confirm_timer.reached():
                        break
            else:
                if self.is_zone_pinned():
                    break

    def globe_enter(self, zone, skip_first_screenshot=True):
        """
        Args:
            zone (Zone): Zone to enter.
            skip_first_screenshot (bool):

        Raises:
            OSExploreError: If zone locked.

        Pages:
            in: is_zone_pinned
            out: is_in_map
        """
        click_timer = Timer(10)
        click_count = 0
        pinned = None
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if pinned is None:
                pinned = self.get_zone_pinned_name()

            # End
            if self.is_in_map():
                break

            if self.is_zone_pinned():
                if self.appear(ZONE_LOCKED, offset=(20, 20)):
                    logger.warning(f'Zone {zone} locked, neighbouring zones may not have been explored')
                    raise OSExploreError
                if click_count > 5:
                    logger.warning(f'Unable to enter zone {zone}, neighbouring zones may not have been explored')
                    raise OSExploreError
                if click_timer.reached():
                    self.device.click(ZONE_ENTRANCE)
                    click_count += 1
                    click_timer.reset()
                    continue
            if self.handle_action_point(zone=zone, pinned=pinned):
                click_timer.clear()
                continue
            if self.handle_map_event():
                continue
            if self.handle_popup_confirm('GLOBE_ENTER'):
                continue
