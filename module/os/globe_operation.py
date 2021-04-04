from module.base.timer import Timer
from module.base.utils import *
from module.logger import logger
from module.map_detection.utils import *
from module.os.assets import *
from module.os_handler.map_event import MapEventHandler

ZONE_TYPES = [ZONE_DANGEROUS, ZONE_SAFE, ZONE_OBSCURED, ZONE_LOGGER, ZONE_STRONGHOLD]
ASSETS_PINNED_ZONE = ZONE_TYPES + [ZONE_ENTRANCE, ZONE_SWITCH, ZONE_PINNED]


class GlobeOperation(MapEventHandler):
    def is_in_globe(self):
        return self.appear(IN_GLOBE, offset=(20, 20))

    def get_zone_pinned(self):
        """
        Returns:
            Button:
        """
        for button in ZONE_TYPES:
            if self.appear(button, offset=(20, 20)):
                offset = np.subtract(button.button, button._button)[:2]
                for change in ASSETS_PINNED_ZONE:
                    change._button_offset = area_offset(change._button, offset=offset)

                return button

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
