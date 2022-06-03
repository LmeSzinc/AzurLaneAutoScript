from module.base.base import ModuleBase
from module.base.button import ButtonGrid
from module.base.timer import Timer
from module.logger import logger


class Navbar:
    def __init__(
        self,
        grids,
        active_color=(247, 251, 181),
        inactive_color=(140, 162, 181),
        active_threshold=180,
        inactive_threshold=180,
        active_count=100,
        inactive_count=50,
        name=None,
    ):
        """
        Args:
            grids (ButtonGrid):
            active_color (tuple[int, int, int]):
            inactive_color (tuple[int, int, int]):
            active_threshold (int):
            inactive_threshold (int):
            active_count (int):
            inactive_count (int):
            name (str):
        """
        self.grids = grids
        self.active_color = active_color
        self.inactive_color = inactive_color
        self.active_threshold = active_threshold
        self.inactive_threshold = inactive_threshold
        self.active_count = active_count
        self.inactive_count = inactive_count
        self.name = name if name is not None else grids._name

    def get_info(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            int, int, int: Index of the active nav item, leftmost nav item, and rightmost nav item.
        """
        total = []
        active = []
        for index, button in enumerate(self.grids.buttons):
            if main.image_color_count(
                button,
                color=self.active_color,
                threshold=self.active_threshold,
                count=self.active_count,
            ):
                total.append(index)
                active.append(index)
            elif main.image_color_count(
                button,
                color=self.inactive_color,
                threshold=self.inactive_threshold,
                count=self.inactive_count,
            ):
                total.append(index)

        if len(active) == 0:
            # logger.warning(f'No active nav item found in {self.name}')
            active = None
        elif len(active) == 1:
            active = active[0]
        else:
            logger.warning(
                f"Too many active nav items found in {self.name}, items: {active}"
            )
            active = active[0]

        if len(total) < 2:
            logger.warning(f"Too few nav items found in {self.name}, items: {total}")
        if len(total) == 0:
            left, right = None, None
        else:
            left, right = min(total), max(total)

        return active, left, right

    def get_active(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            int: Index of the active nav item.
        """
        return self.get_info(main=main)[0]

    def get_total(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            int: Numbers of nav items that appears
        """
        _, left, right = self.get_info(main=main)
        return right - left + 1

    def set(
        self,
        main,
        left=None,
        right=None,
        upper=None,
        bottom=None,
        skip_first_screenshot=True,
    ):
        """
        Set nav bar from 1 direction.

        Args:
            main (ModuleBase):
            left (int): Index of nav item counted from left. Start from 1.
            right (int): Index of nav item counted from right. Start from 1.
            upper (int): Index of nav item counted from upper. Start from 1.
            bottom (int): Index of nav item counted from bottom. Start from 1.
            skip_first_screenshot (bool):

        Returns:
            bool: If success
        """
        if left is None and right is None and upper is None and bottom is None:
            logger.warning("Invalid index to set, must set an index from 1 direction")
            return False
        text = ""
        if left is None and upper is not None:
            left = upper
        if right is None and bottom is not None:
            right = bottom
        for k in ["left", "right", "upper", "bottom"]:
            if locals().get(k, None) is not None:
                text += f"{k}={locals().get(k, None)} "
        logger.info(f"{self.name} set to {text.strip()}")

        interval = Timer(2, count=4)
        timeout = Timer(10, count=20).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            if timeout.reached():
                logger.warning(f"{self.name} failed to set {text.strip()}")
                return False

            active, minimum, maximum = self.get_info(main=main)
            logger.info(f"Nav item active: {active} from range ({minimum}, {maximum})")
            # if active is None:
            #     continue
            index = minimum + left - 1 if left is not None else maximum - right + 1
            if not minimum <= index <= maximum:
                logger.warning(
                    f"Index to set ({index}) is not within the nav items that appears ({minimum}, {maximum})"
                )
                continue

            # End
            if active == index:
                return True

            if interval.reached():
                main.device.click(self.grids.buttons[index])
                main.device.sleep((0.1, 0.2))
                interval.reset()
