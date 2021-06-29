from module.base.button import ButtonGrid
from module.base.utils import *
from module.logger import logger
from module.ui.ui import UI

GUILD_SIDEBAR = ButtonGrid(
    origin=(21, 118), delta=(0, 94.5), button_shape=(60, 75), grid_shape=(1, 6), name='GUILD_SIDEBAR')


class GuildBase(UI):
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

        for idx, button in enumerate(GUILD_SIDEBAR.buttons):
            image = np.array(self.image_area(button))
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
            skip_first_screenshot (bool):

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
