from module.base.button import ButtonWrapper
from module.base.timer import Timer
from module.logger import logger
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_team import (
    COMBAT_TEAM_PREPARE,
    TEAM_1,
    TEAM_2,
    TEAM_3,
    TEAM_4,
    TEAM_5,
    TEAM_6
)

TEAM_BUTTONS = {
    1: TEAM_1,
    2: TEAM_2,
    3: TEAM_3,
    4: TEAM_4,
    5: TEAM_5,
    6: TEAM_6,
}


class CombatTeam(UI):
    @staticmethod
    def _team_index_to_button(index: int) -> ButtonWrapper:
        try:
            return TEAM_BUTTONS[index]
        except KeyError:
            logger.warning(f'Invalid team index: {index}, return team 1 instead')
            return TEAM_1

    def _get_team_selected(self) -> int:
        for index, button in TEAM_BUTTONS.items():
            if self.image_color_count(button, color=(255, 234, 191), threshold=221, count=50):
                return index

        # logger.warning(f'No team selected')
        return 0

    def team_set(self, team: int = 1, skip_first_screenshot=True) -> bool:
        """
        Args:
            team: Team index, 1 to 6.
            skip_first_screenshot:

        Returns:
            bool: If clicked

        Pages:
            in: page_team
        """
        logger.info(f'Team set: {team}')
        # Wait teams show up
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            current = self._get_team_selected()
            if current:
                if current == team:
                    logger.info(f'Selected to the correct team')
                    return False
                else:
                    break

        # Set team
        interval = Timer(2)
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            current = self._get_team_selected()
            logger.attr('Team', current)
            if current and current == team:
                logger.info(f'Selected to the correct team')
                return True

            # Click
            if interval.reached():
                self.device.click(self._team_index_to_button(team))
                interval.reset()
                continue

    def handle_combat_team_prepare(self, team: int = 1) -> bool:
        """
        Set team and click prepare before dungeon combat.

        Returns:
            int: If clicked
        """
        if self.appear(COMBAT_TEAM_PREPARE, interval=5):
            self.team_set(team)
            self.device.click(COMBAT_TEAM_PREPARE)
            return True

        return False
