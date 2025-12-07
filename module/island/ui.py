from module.base.button import ButtonGrid
from module.base.decorator import cached_property
from module.island.assets import *
from module.ui.navbar import Navbar
from module.ui.scroll import Scroll
from module.ui.ui import UI


ISLAND_SEASON_TASK_SCROLL = Scroll(
    ISLAND_SEASON_TASK_SCROLL_AREA.button,
    color=(128, 128, 128),
    name="ISLAND_SEASON_TASK_SCROLL"
)


class IslandUI(UI):
    def ui_additional(self, get_ship=True):
        return super().ui_additional(get_ship=False)

    @cached_property
    def _island_season_bottom_navbar(self):
        """
        5 options:
            homepage,
            pt_reward,
            season_task,
            season_shop,
            season_rank
        """
        island_season_bottom_navbar = ButtonGrid(
            origin=(54, 677), delta=(246.5, 0),
            button_shape=(186, 33), grid_shape=(5, 1),
            name='ISLAND_SEASON_BOTTOM_NAVBAR'
        )
        return Navbar(grids=island_season_bottom_navbar,
                      active_color=(237, 237, 237),
                      inactive_color=(65, 78, 96),
                      active_count=500,
                      inactive_count=500)

    def island_season_bottom_navbar_ensure(self, left=None, right=None):
        """
        Args:
            left (int):
                1 for homepage,
                2 for pt_reward,
                3 for season_task,
                4 for season_shop,
                5 for season_rank
            right (int):
                1 for season_rank,
                2 for season_shop,
                3 for season_task,
                4 for pt_reward,
                5 for homepage
        """
        if self._island_season_bottom_navbar.set(self, left=left, right=right):
            return True
        return False