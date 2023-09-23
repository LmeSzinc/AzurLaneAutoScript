from module.logger import logger
from tasks.base.assets.assets_base_popup import POPUP_SINGLE
from tasks.dungeon.keywords import KEYWORDS_DUNGEON_LIST
from tasks.forgotten_hall.keywords import KEYWORDS_FORGOTTEN_HALL_STAGE
from tasks.forgotten_hall.ui import ForgottenHallUI
from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_BackwaterPass
from tasks.map.route.base import RouteBase


class Route(RouteBase, ForgottenHallUI):
    def combat_execute(self, expected_end=None):
        # Challenge completed, return button appears
        def combat_ended():
            return self.appear(POPUP_SINGLE)

        return super().combat_execute(expected_end=combat_ended)

    def route(self):
        """
        Pages:
            in: Any
            out: page_forgotten_hall
        """
        logger.hr('Forgotten hall stage 1')
        self.stage_goto(KEYWORDS_DUNGEON_LIST.The_Last_Vestiges_of_Towering_Citadel,
                        KEYWORDS_FORGOTTEN_HALL_STAGE.Stage_1)
        self.team_choose_first_4()
        self.enter_forgotten_hall_dungeon()

        self.map_init(plane=Jarilo_BackwaterPass, position=(369.4, 643.4))
        self.clear_enemy(
            Waypoint((313.4, 643.4)).run_2x()
        )
        self.exit_dungeon()
