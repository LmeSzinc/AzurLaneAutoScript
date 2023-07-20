from module.base.timer import Timer
from module.logger import logger
from tasks.dungeon.keywords import KEYWORDS_DUNGEON_LIST
from tasks.forgotten_hall.keywords import KEYWORDS_FORGOTTEN_HALL_STAGE
from tasks.forgotten_hall.ui import ForgottenHallUI
from tasks.map.control.joystick import MapControlJoystick


class UseTechniqueUI(MapControlJoystick, ForgottenHallUI):

    def _use_technique(self, count: int, skip_first_screenshot=True):
        remains = self.map_get_technique_points()
        if count > remains:
            logger.warning(f"Try to use technique {count} times but only have {remains}")
            return

        # Handle technique animation when it's being used
        # INFO │ Click ( 900,  600) @ E_BUTTON
        # INFO │ [TechniquePoints] 4
        # INFO │ [TechniquePoints] 3
        # INFO │ [TechniquePoints] 4
        # INFO │ [TechniquePoints] 3
        # INFO │ [TechniquePoints] 3
        confirm = Timer(0.5, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            remains_after = self.map_get_technique_points()
            if remains - remains_after >= count:
                if confirm.reached():
                    logger.info(f"{remains - remains_after} techniques used")
                    break
            else:
                confirm.reset()

            self.handle_map_E()

    def use_technique(self, count: int = 2, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:
            count: use {count} times

        Examples:
            self = UseTechniquesUI('alas')
            self.device.screenshot()
            self.use_techniques(2)

        Pages:
            in: Any
            out: page_forgotten_hall, FORGOTTEN_HALL_CHECKED
        """
        logger.hr('Use techniques', level=2)
        self.stage_goto(KEYWORDS_DUNGEON_LIST.The_Last_Vestiges_of_Towering_Citadel,
                        KEYWORDS_FORGOTTEN_HALL_STAGE.Stage_1)
        self._choose_first_character()
        self._enter_forgotten_hall_dungeon()
        self._use_technique(count, skip_first_screenshot=skip_first_screenshot)
        self.exit_dungeon()
        self.ui_goto_main()
