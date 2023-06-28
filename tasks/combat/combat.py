from module.logger import logger
from tasks.base.assets.assets_base_page import CLOSE
from tasks.combat.assets.assets_combat_finish import COMBAT_AGAIN, COMBAT_EXIT
from tasks.combat.assets.assets_combat_prepare import COMBAT_PREPARE
from tasks.combat.assets.assets_combat_team import COMBAT_TEAM_PREPARE
from tasks.combat.interact import CombatInteract
from tasks.combat.prepare import CombatPrepare
from tasks.combat.state import CombatState
from tasks.combat.team import CombatTeam
from tasks.map.control.joystick import MapControlJoystick


class Combat(CombatInteract, CombatPrepare, CombatState, CombatTeam, MapControlJoystick):
    def handle_combat_prepare(self):
        """
        Pages:
            in: COMBAT_PREPARE
        """
        current = self.combat_get_trailblaze_power()
        cost = self.combat_get_wave_cost()
        if cost == 10:
            wave = min(current // self.combat_wave_cost, 6)
            logger.info(f'Current has {current}, combat costs {self.combat_wave_cost}, able to do {wave} waves')
            if wave > 0:
                self.combat_set_wave(wave)
        else:
            logger.info(f'Current has {current}, combat costs {self.combat_wave_cost}, do 1 wave')

    def handle_ascension_dungeon_prepare(self):
        """
        Returns:
            bool: If clicked.
        """
        if self.combat_wave_cost == 30 and self.is_in_main():
            if self.handle_map_A():
                return True

        return False

    def combat_prepare(self, team=1):
        """
        Args:
            team: 1 to 6.

        Returns:
            bool: True if success to enter combat
                False if trialblaze power is not enough

        Pages:
            in: COMBAT_PREPARE
            out: is_combat_executing
        """
        logger.hr('Combat prepare')
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_combat_executing():
                return True

            # Click
            if self.appear(COMBAT_TEAM_PREPARE, interval=2):
                self.team_set(team)
                self.device.click(COMBAT_TEAM_PREPARE)
                self.interval_reset(COMBAT_TEAM_PREPARE)
                continue
            if self.appear(COMBAT_TEAM_PREPARE):
                self.interval_reset(COMBAT_PREPARE)
                self._map_A_timer.reset()
            if self.appear(COMBAT_PREPARE, interval=2):
                self.handle_combat_prepare()
                if self.state.TrailblazePower < self.combat_wave_cost:
                    return False
                self.device.click(COMBAT_PREPARE)
                self.interval_reset(COMBAT_PREPARE)
                continue
            if self.handle_combat_interact():
                continue
            if self.handle_ascension_dungeon_prepare():
                continue

    def combat_execute(self):
        """
        Pages:
            in: is_combat_executing
            out: COMBAT_AGAIN
        """
        logger.hr('Combat execute')
        skip_first_screenshot = True
        is_executing = True
        self.combat_state_reset()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(COMBAT_AGAIN):
                break

            # Daemon
            if self.is_combat_executing():
                if not is_executing:
                    logger.info('Combat continues')
                    self.device.stuck_record_clear()
                is_executing = True
            else:
                is_executing = False
            if self.handle_combat_state():
                continue

    def _combat_can_again(self) -> bool:
        """
        Pages:
            in: COMBAT_AGAIN
        """
        current = self.combat_get_trailblaze_power(expect_reduce=True)
        if self.combat_wave_cost == 10:
            if current >= self.combat_wave_cost * 6:
                logger.info(f'Current has {current}, combat costs {self.combat_wave_cost}, can run again')
                return True
            else:
                logger.info(f'Current has {current}, combat costs {self.combat_wave_cost}, can not run again')
                return False
        else:
            if current >= self.combat_wave_cost:
                logger.info(f'Current has {current}, combat costs {self.combat_wave_cost}, can run again')
                return True
            else:
                logger.info(f'Current has {current}, combat costs {self.combat_wave_cost}, can not run again')
                return False

    def combat_finish(self) -> bool:
        """
        Returns:
            bool: True if exit, False if again

        Pages:
            in: COMBAT_AGAIN
            out: page_main if exit
                is_combat_executing if again
        """
        logger.hr('Combat finish')
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_main():
                logger.info('Combat finishes at page_main')
                return True
            if self.is_combat_executing():
                logger.info('Combat finishes at another combat')
                return False

            # Click
            if self.appear(COMBAT_AGAIN, interval=2):
                if self._combat_can_again():
                    self.device.click(COMBAT_AGAIN)
                else:
                    self.device.click(COMBAT_EXIT)
                self.interval_reset(COMBAT_AGAIN)

    def combat_exit(self, skip_first_screenshot=True):
        """
        Pages:
            in: Any page during combat
            out: page_main
        """
        logger.info('Combat exit')
        self.interval_clear([COMBAT_PREPARE, COMBAT_TEAM_PREPARE, COMBAT_AGAIN])
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_main():
                break

            # Click
            if self.appear(COMBAT_PREPARE, interval=2):
                logger.info(f'{COMBAT_PREPARE} -> {CLOSE}')
                self.device.click(CLOSE)
                continue
            if self.appear(COMBAT_TEAM_PREPARE, interval=2):
                logger.info(f'{COMBAT_TEAM_PREPARE} -> {CLOSE}')
                self.device.click(CLOSE)
                continue
            if self.appear(COMBAT_AGAIN, interval=2):
                logger.info(f'{COMBAT_AGAIN} -> {COMBAT_EXIT}')
                self.device.click(COMBAT_EXIT)
                continue

    def combat(self, team: int = 1, skip_first_screenshot=True):
        """
        Combat until trailblaze power runs out.

        Args:
            team: 1 to 6.
            skip_first_screenshot:

        Pages:
            in: COMBAT_PREPARE
                or page_main with DUNGEON_COMBAT_INTERACT
            out: page_main
        """
        if not skip_first_screenshot:
            self.device.screenshot()

        while 1:
            logger.hr('Combat', level=2)
            # Prepare
            prepare = self.combat_prepare(team)
            if not prepare:
                self.combat_exit()
                break
            # Execute
            self.combat_execute()
            # Finish
            finish = self.combat_finish()
            if self.state.TrailblazePower >= self.combat_wave_cost:
                logger.info('Still having some trailblaze power run with less waves to empty it')
                continue
            if finish:
                break
