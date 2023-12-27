import re

from module.base.timer import Timer
from module.base.utils import random_rectangle_vector_opted
from module.logger import logger
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_team import *


def button_to_index(button: ButtonWrapper) -> int:
    res = re.search(r'(\d)', button.name)
    if res:
        return int(res.group(1))
    else:
        logger.warning(f'Cannot convert team button to index: {button}')
        return 1


def index_to_button(index: int) -> ButtonWrapper:
    match index:
        case 1:
            return TEAM_1_CLICK
        case 2:
            return TEAM_2_CLICK
        case 3:
            return TEAM_3_CLICK
        case 4:
            return TEAM_4_CLICK
        case 5:
            return TEAM_5_CLICK
        case 6:
            return TEAM_6_CLICK
        case 7:
            return TEAM_7_CLICK
        case 8:
            return TEAM_8_CLICK
        case 9:
            return TEAM_9_CLICK
        case _:
            logger.warning(f'Invalid team index: {index}')
            return TEAM_1_CLICK


class CombatTeam(UI):
    def _get_team(self) -> tuple[list[int], int]:
        """
        Returns:
            list[str]: List of displayed team index.
            int: Current team index, or None if current team is not insight
        """
        list_team = []
        for button in [
            TEAM_1_CLICK, TEAM_2_CLICK, TEAM_3_CLICK, TEAM_4_CLICK, TEAM_5_CLICK,
            TEAM_6_CLICK, TEAM_7_CLICK, TEAM_8_CLICK, TEAM_9_CLICK
        ]:
            button.load_search(TEAM_SEARCH.area)
            if self.appear(button):
                list_team.append(button_to_index(button))
        current_team = None
        for button in [
            TEAM_1_CHECK, TEAM_2_CHECK, TEAM_3_CHECK, TEAM_4_CHECK, TEAM_5_CHECK,
            TEAM_6_CHECK, TEAM_7_CHECK, TEAM_8_CHECK, TEAM_9_CHECK
        ]:
            button.load_search(TEAM_SEARCH.area)
            if self.appear(button):
                current_team = button_to_index(button)
                list_team.append(button_to_index(button))
        list_team = list(sorted(list_team))

        def show(index):
            if index == current_team:
                return f'*0{index}*'
            else:
                return f'0{index}'

        # [Team] 01 02 *03* 04 05 06
        logger.attr('Team', ' '.join([show(i) for i in list_team]))
        return list_team, current_team

    def team_set(self, team: int = 1, skip_first_screenshot=True) -> bool:
        """
        Args:
            team: Team index, 1 to 9.
            skip_first_screenshot:

        Returns:
            bool: If clicked

        Pages:
            in: page_team
        """
        logger.info(f'Team set: {team}')
        # Wait teams show up
        timeout = Timer(1, count=5).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if timeout.reached():
                logger.warning('Wait current team timeout')
                break
            _, current = self._get_team()
            if current:
                if current == team:
                    logger.info(f'Selected to the correct team')
                    return False
                else:
                    break

        # Set team
        click_interval = Timer(2)
        swipe_interval = Timer(2)
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            list_team, current = self._get_team()
            if current and current == team:
                logger.info(f'Selected to the correct team')
                return True

            # Click
            if team in list_team:
                if click_interval.reached():
                    self.device.click(index_to_button(team))
                    click_interval.reset()
                    continue
            # At left
            elif team < min(list_team):
                if swipe_interval.reached():
                    p1, p2 = random_rectangle_vector_opted(
                        (350, 0), box=TEAM_SEARCH.area, random_range=(-20, -10, 20, 10))
                    self.device.drag(p1, p2, name=f'TEAM_DRAG')
                    swipe_interval.reset()
            # At right
            elif team > max(list_team):
                if swipe_interval.reached():
                    p1, p2 = random_rectangle_vector_opted(
                        (-350, 0), box=TEAM_SEARCH.area, random_range=(-20, -10, 20, 10))
                    self.device.drag(p1, p2, name=f'TEAM_DRAG')
                    swipe_interval.reset()

    def handle_combat_team_prepare(self, team: int = 1) -> bool:
        """
        Set team and click prepare before dungeon combat.

        Args:
            team: Team index, 1 to 9.

        Returns:
            int: If clicked
        """
        if self.appear(COMBAT_TEAM_PREPARE, interval=5):
            self.team_set(team)
            self.device.click(COMBAT_TEAM_PREPARE)
            return True

        return False
