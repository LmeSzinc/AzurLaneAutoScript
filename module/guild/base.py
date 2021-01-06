import numpy as np

from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import *
from module.guild.assets import SWIPE_CHECK, SWIPE_AREA
from module.logger import logger
from module.ui.ui import UI

GUILD_RECORD = ('RewardRecord', 'guild')

GUILD_SIDEBAR = ButtonGrid(
    origin=(21, 118), delta=(0, 94.5), button_shape=(60, 75), grid_shape=(1, 6), name='GUILD_SIDEBAR')

SWIPE_DISTANCE = 250
SWIPE_RANDOM_RANGE = (-40, -20, 40, 20)

class GuildBase(UI):
    @cached_property
    def guild_interval(self):
        return int(ensure_time(self.config.GUILD_INTERVAL, precision=3) * 60)

    def guild_interval_reset(self):
        """ Call this method after guild run executed """
        del self.__dict__['guild_interval']

    def _view_swipe(self, distance):
        """
        Perform swipe action, altered specifically
        for Guild Operations map usage
        """
        swipe_count = 0
        swipe_timer = Timer(3, count=6)
        SWIPE_CHECK.load_color(self.device.image)
        while 1:
            if not swipe_timer.started() or swipe_timer.reached():
                swipe_timer.reset()
                self.device.swipe(vector=(distance, 0), box=SWIPE_AREA.area, random_range=SWIPE_RANDOM_RANGE,
                                  padding=0, duration=(0.22, 0.25), name=f'SWIPE_{swipe_count}')
                self.device.sleep((1.8, 2.1)) # No assets to use to ensure whether screen has stabilized after swipe
                swipe_count += 1

            self.device.screenshot()
            if SWIPE_CHECK.match(self.device.image):
                if swipe_count > 2:
                    logger.info('Same view, page end')
                    return False
                continue

            if not SWIPE_CHECK.match(self.device.image):
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

        # This is a member sidebar, decrement
        # the index by 1 if requested 4 or greater
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