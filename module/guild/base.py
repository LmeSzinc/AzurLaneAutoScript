from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.logger import logger
from module.ui.navbar import Navbar
from module.ui.ui import UI


class GuildBase(UI):
    @cached_property
    def _guild_side_navbar(self):
        """
        leader_sidebar 6 options
            lobby.
            members.
            apply.
            logistics.
            tech.
            operations.

        member_sidebar 5 options
            lobby.
            members.
            logistics.
            tech.
            operations.
        """
        guild_side_navbar = ButtonGrid(
            origin=(21, 118),
            delta=(0, 94.5),
            button_shape=(60, 75),
            grid_shape=(1, 6),
            name="GUILD_SIDE_NAVBAR",
        )

        return Navbar(
            grids=guild_side_navbar,
            active_color=(247, 255, 173),
            inactive_color=(140, 162, 181),
        )

    def guild_side_navbar_ensure(self, upper=None, bottom=None):
        """
        Ensure able to transition to page
        Whether page has completely loaded is handled
        separately and optionally

        Args:
            upper (int):
                leader|member
                1     for lobby.
                2     for members.
                3|N/A for apply.
                4|3   for logistics.
                5|4   for tech.
                6|5   for operations.
            bottom (int):
                leader|member
                6|5   for lobby.
                5|4   for members.
                4|N/A for apply.
                3     for logistics.
                2     for tech.
                1     for operations.

        Returns:
            bool: if side_navbar set ensured
        """
        if self._guild_side_navbar.get_total(main=self) == 6:
            if upper == 3 or bottom == 4:
                logger.warning('Transitions to "apply" is not supported')
                return False

        if self._guild_side_navbar.set(self, upper=upper, bottom=bottom):
            return True
        return False
