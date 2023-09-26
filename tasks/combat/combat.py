from module.base.decorator import run_once
from module.logger import logger
from tasks.base.assets.assets_base_page import CLOSE
from tasks.combat.assets.assets_combat_finish import COMBAT_AGAIN, COMBAT_EXIT
from tasks.combat.assets.assets_combat_prepare import COMBAT_PREPARE
from tasks.combat.assets.assets_combat_team import COMBAT_TEAM_PREPARE, COMBAT_TEAM_SUPPORT
from tasks.combat.interact import CombatInteract
from tasks.combat.prepare import CombatPrepare
from tasks.combat.skill import CombatSkill
from tasks.combat.state import CombatState
from tasks.combat.support import CombatSupport
from tasks.combat.team import CombatTeam
from tasks.map.control.joystick import MapControlJoystick


class Combat(CombatInteract, CombatPrepare, CombatState, CombatTeam, CombatSupport, CombatSkill, MapControlJoystick):
    def handle_combat_prepare(self):
        """
        Returns:
            bool: If able to run a combat

        Pages:
            in: COMBAT_PREPARE
        """
        self.combat_waves = 1
        current = self.combat_get_trailblaze_power()
        cost = self.combat_get_wave_cost()
        if cost == 10:
            # Calyx
            self.combat_waves = min(current // self.combat_wave_cost, 6)
            if self.combat_wave_limit:
                self.combat_waves = min(self.combat_waves, self.combat_wave_limit - self.combat_wave_done)
                logger.info(
                    f'Current has {current}, combat costs {self.combat_wave_cost}, '
                    f'wave={self.combat_wave_done}/{self.combat_wave_limit}, '
                    f'able to do {self.combat_waves} waves')
            else:
                logger.info(f'Current has {current}, combat costs {self.combat_wave_cost}, '
                            f'able to do {self.combat_waves} waves')
            if self.combat_waves > 0:
                self.combat_set_wave(self.combat_waves)
        else:
            # Others
            logger.info(f'Current has {current}, combat costs {self.combat_wave_cost}, '
                        f'do {self.combat_waves} wave')

        # Check limits
        if self.config.stored.TrailblazePower.value < self.combat_wave_cost:
            logger.info('Trailblaze power exhausted, cannot continue combat')
            return False
        if self.combat_waves <= 0:
            logger.info('Combat wave limited, cannot continue combat')
            return False

        return True

    def handle_ascension_dungeon_prepare(self):
        """
        Returns:
            bool: If clicked.
        """
        if self.combat_wave_cost == 30 and self.is_in_main():
            if self.handle_map_A():
                return True

        return False

    def combat_prepare(self, team=1, support_character: str = None):
        """
        Args:
            team: 1 to 6.
            support_character: Support character name

        Returns:
            bool: True if success to enter combat
                False if trialblaze power is not enough

        Pages:
            in: COMBAT_PREPARE
            out: is_combat_executing
        """
        logger.hr('Combat prepare')
        skip_first_screenshot = True
        pre_set_team = bool(support_character)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_combat_executing():
                return True

            # Click
            if self.appear(COMBAT_TEAM_SUPPORT) and support_character:
                if pre_set_team:
                    self.team_set(team)
                    pre_set_team = False
                    continue
                self.support_set(support_character)
                continue
            if self.appear(COMBAT_TEAM_PREPARE, interval=2):
                self.team_set(team)
                self.device.click(COMBAT_TEAM_PREPARE)
                self.interval_reset(COMBAT_TEAM_PREPARE)
                continue
            if self.appear(COMBAT_TEAM_PREPARE):
                self.interval_reset(COMBAT_PREPARE)
                self.map_A_timer.reset()
            if self.appear(COMBAT_PREPARE, interval=2):
                if not self.handle_combat_prepare():
                    return False
                self.device.click(COMBAT_PREPARE)
                self.interval_reset(COMBAT_PREPARE)
                continue
            if self.handle_combat_interact():
                continue
            if self.handle_ascension_dungeon_prepare():
                continue
            if self.handle_popup_confirm():
                continue

    def combat_execute(self, expected_end=None):
        """
        Args:
            expected_end: A function returns bool, True represents end.

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
            if callable(expected_end) and expected_end():
                logger.info(f'Combat execute ended at {expected_end.__name__}')
                break
            if self.appear(COMBAT_AGAIN):
                logger.info(f'Combat execute ended at {COMBAT_AGAIN}')
                break
            if self.is_in_main():
                logger.info(f'Combat execute ended at page_main')
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
        current = self.combat_get_trailblaze_power(expect_reduce=self.combat_wave_cost > 0)
        # Wave limit
        if self.combat_wave_limit:
            if self.combat_wave_done + self.combat_waves > self.combat_wave_limit:
                logger.info(f'Combat wave limit: {self.combat_wave_done}/{self.combat_wave_limit}, '
                            f'can not run again')
                return False

        # Cost limit
        if self.combat_wave_cost == 10:
            if current >= self.combat_wave_cost * self.combat_waves:
                logger.info(f'Current has {current}, combat costs {self.combat_wave_cost}, can run again')
                return True
            else:
                logger.info(f'Current has {current}, combat costs {self.combat_wave_cost}, can not run again')
                return False
        elif self.combat_wave_cost <= 0:
            logger.info(f'Free combat, combat costs {self.combat_wave_cost}, can not run again')
            return False
        else:
            if current >= self.combat_wave_cost:
                logger.info(f'Current has {current}, combat costs {self.combat_wave_cost}, can run again')
                return True
            else:
                logger.info(f'Current has {current}, combat costs {self.combat_wave_cost}, can not run again')
                return False

    def _combat_should_reenter(self):
        """
        Returns:
            bool: True to re-enter combat and run with another wave settings
        """
        # Wave limit
        if self.combat_wave_limit:
            if self.combat_wave_done < self.combat_wave_limit:
                logger.info(f'Combat wave limit: {self.combat_wave_done}/{self.combat_wave_limit}, '
                            f'run again with less waves')
                return True
            else:
                return False
        # Cost limit
        if self.config.stored.TrailblazePower.value >= self.combat_wave_cost:
            logger.info('Still having some trailblaze power run with less waves to empty it')
            return True

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

        @run_once
        def add_wave_done():
            self.combat_wave_done += self.combat_waves
            logger.info(f'Done {self.combat_waves} waves at total')

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
            # Game client might slow to response COMBAT_AGAIN clicks
            if self.appear(COMBAT_AGAIN, interval=5):
                add_wave_done()
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

    def is_trailblaze_power_exhausted(self) -> bool:
        flag = self.config.stored.TrailblazePower.value < self.combat_wave_cost
        logger.attr('TrailblazePowerExhausted', flag)
        return flag

    def combat(self, team: int = 1, wave_limit: int = 0, support_character: str = None, skip_first_screenshot=True):
        """
        Combat until trailblaze power runs out.

        Args:
            team: 1 to 6.
            wave_limit: Limit combat runs, 0 means no limit.
            support_character: Support character name
            skip_first_screenshot:

        Returns:
            int: Run count

        Pages:
            in: COMBAT_PREPARE
                or page_main with DUNGEON_COMBAT_INTERACT
            out: page_main
        """
        if not skip_first_screenshot:
            self.device.screenshot()

        self.combat_wave_limit = wave_limit
        self.combat_wave_done = 0
        run_count = 0
        while 1:
            logger.hr('Combat', level=2)
            logger.info(f'Combat, team={team}, wave={self.combat_wave_done}/{self.combat_wave_limit}')
            # Prepare
            prepare = self.combat_prepare(team, support_character)
            if not prepare:
                self.combat_exit()
                break
            # Execute
            self.combat_execute()
            # Finish
            finish = self.combat_finish()
            if self._combat_should_reenter():
                continue
            run_count += 1
            if finish:
                break

        logger.attr('CombatRunCount', run_count)
        return run_count
