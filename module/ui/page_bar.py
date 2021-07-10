import numpy as np
from module.base.utils import color_similarity_2d
from module.logger import logger


class PageBar:
    def __init__(self, grids, inactive_color, additional=None, is_reversed=False, name=None):
        """
        Args:
            grid (ButtonGrid):
            inactive_color (tuple):
                (r, g, b) button color for options
                that are inactive i.e. not highlighted
            additional (func):
                additional handling for dynamic size bars,
                must accept at least 2 arguments
            is_reversed (bool):
                whether the grid should be scanned in reverse order
            name (str):
        """
        self.grids = grids
        self.inactive_color = inactive_color
        self.additional = additional
        self.is_reversed = is_reversed
        self.name = name if not None else grids._name

        self.grid_shape = self.grids.grid_shape
        self.is_vertical = True if self.grid_shape[1] > self.grid_shape[0] else False
        self.total = self.grid_shape[0] * self.grid_shape[1]

    def _click(self, main, index):
        """
        Scans for current highlighted position within bar
        Then calculate appropriate index of button location
        to click into for page transition

        Args:
            main (ModuleBase):
            index (int):
                Varies on self.grid

        Returns:
            bool: if changed.
        """
        current = 0
        total = 0
        buttons = self.grid.buttons()
        if self.is_reversed:
            buttons.reverse()
        for idx, button in enumerate(buttons):
            image = np.array(main.image_area(button))
            # Roughly translates to whether the image button
            # is highlighted/bright
            if np.sum(image[:, :, 0] > 235) > 100:
                current = idx + 1
                total = idx + 1
                continue
            # Otherwise, verify whether image button is
            # selectable i.e. inactive_color is present
            if np.sum(color_similarity_2d(image, color=self.inactive_color) > 221) > 100:
                total = idx + 1
            # Finally if neither of the above cases then grid
            # is shorter than expected
            else:
                break

        if not current:
            # No current, may appear erroneous but
            # able to recover for some situations
            logger.info('No option in bar found to be active.')

        current_modified = False
        for x in range(2, (self.total + 1)):
            if total == x:
                current = (total + 1) - current
                current_modified = True
                break
        if not current_modified:
            logger.warning(f'{self.name} total count error.')

        if self.additional is not None:
            index = self.additional(total, index)

        logger.attr(f'{self.name}', f'{current}/{total}')
        if current == index:
            return False

        diff = total - index
        if diff >= 0:
            diff = diff if not self.is_reversed else (self.total - 1) - diff
            if self.is_vertical:
                pos = (0, diff)
            else:
                pos = (diff, 0)
            main.device.click(self.grid[pos])
        else:
            logger.warning(f'Target index {index} cannot be clicked')
        return True

    def ensure(self, main, index, skip_first_screenshot=True):
        """
        Performs action to ensure the specified
        index within the bar is transitioned into
        Maximum of 3 attempts

        Args:
            main (ModuleBase):
            index (int):
                Varies on self.grid
            skip_first_screenshot (bool):

        Returns:
            bool: whether transition successful
        """
        counter = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            if counter >= 3:
                logger.warning('Failed to ensure successful '
                               f'transition to index {index} '
                               f'for {self.name}')
                return False

            if self._click(main, index):
                counter += 1
                main.device.sleep((0.5, 0.8))
                continue
            else:
                return True
