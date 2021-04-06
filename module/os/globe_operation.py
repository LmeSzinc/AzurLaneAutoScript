from module.base.timer import Timer
from module.base.utils import *
from module.logger import logger
from module.map_detection.utils import *
from module.os.assets import *
from module.ui.ui import UI

ZONE_TYPES = [ZONE_DANGEROUS, ZONE_SAFE, ZONE_OBSCURED, ZONE_LOGGER, ZONE_STRONGHOLD]
ZONE_SELECT = [SELECT_DANGEROUS, SELECT_SAFE, SELECT_OBSCURE, SELECT_LOGGER, SELECT_STRONGHOLD]
ASSETS_PINNED_ZONE = ZONE_TYPES + [ZONE_ENTRANCE, ZONE_SWITCH, ZONE_PINNED]


class GlobeOperation(UI):
    def is_in_globe(self):
        return self.appear(IN_GLOBE, offset=(20, 20))

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

    def handle_zone_pinned(self):
        """
        CLose pinned zone info.

        Returns:
            bool: If handled.
        """
        if self.is_zone_pinned():
            self.device.click(ZONE_PINNED)
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

        Returns:
            bool: If current zone has switch.
        """
        image = self.image_area(ZONE_SWITCH)
        center = np.array(image.size) / 2
        count = 0
        for corner in area2corner((0, 0, *image.size)):
            area = (min(corner[0], center[0]), min(corner[1], center[1]),
                    max(corner[0], center[0]), max(corner[1], center[1]))
            area = area_pad(area, pad=2)
            color = np.mean(get_color(image, area))
            if color > 235:
                count += 1

        if count == 1:
            return True
        elif count == 0:
            return False
        else:
            logger.warning(f'Unexpected zone switch, white block: {count}')

    _zone_select_offset = (20, 200)

    def get_zone_select(self):
        """
        Returns:
            list[Button]:
        """
        return [select for select in ZONE_SELECT if self.appear(select, offset=self._zone_select_offset)]

    def is_in_zone_select(self):
        """
        Returns:
            bool:
        """
        return len(self.get_zone_select()) > 0

    def zone_type_select(self, types=('SAFE', 'DANGEROUS')):
        """
        Args:
            types (tuple[str], list[str], str): Zone types, or a list of them.
                Available types: DANGEROUS, SAFE, OBSCURE, LOGGER, STRONGHOLD.
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

        for _ in range(3):
            self.ui_click(ZONE_SWITCH, check_button=self.is_in_zone_select, skip_first_screenshot=True)

            selection = self.get_zone_select()
            logger.attr('Zone_selection', selection)
            button = get_button(selection)
            if button is None:
                logger.warning('No such zone type to select, fallback to default')
                types = ('SAFE', 'DANGEROUS')
                button = get_button(selection)

            self.ui_click(button, check_button=self.is_zone_pinned, offset=self._zone_select_offset,
                          skip_first_screenshot=True)
            if button.name.split('_')[1] == self.get_zone_pinned().name.split('_')[1]:
                return True

        logger.warning('Failed to select zone type after 3 trial')
        return False
