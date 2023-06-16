from module.logger import logger
from tasks.base.page import page_main
from tasks.combat.assets.assets_combat_finish import COMBAT_AGAIN, COMBAT_EXIT
from tasks.combat.assets.assets_combat_prepare import COMBAT_PREPARE
from tasks.combat.assets.assets_combat_team import COMBAT_TEAM_PREPARE
from tasks.combat.interact import CombatInteract
from tasks.combat.prepare import CombatPrepare
from tasks.combat.state import CombatState
from tasks.combat.team import CombatTeam


class Combat(CombatInteract, CombatPrepare, CombatState, CombatTeam):
    _combat_has_multi_wave = True

    @property
    def combat_cost(self):
        if self._combat_has_multi_wave:
            return 10
        else:
            return 30

    def handle_combat_prepare(self):
        """
        Pages:
            in: COMBAT_PREPARE
        """
        current = self.combat_get_trailblaze_power()
        self._combat_has_multi_wave = self.combat_has_multi_wave()
        if self._combat_has_multi_wave:
            wave = min(current // self.combat_cost, 6)
            logger.info(f'Current has {current}, combat costs {self.combat_cost}, able to do {wave} waves')
            self.combat_set_wave(wave)
        else:
            logger.info(f'Current has {current}, combat costs {self.combat_cost}, do 1 wave')

    def combat_prepare(self, team=1):
        """
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
                break

            # Click
            if self.appear(COMBAT_PREPARE, interval=2):
                self.handle_combat_prepare()
                self.device.click(COMBAT_PREPARE)
                self.interval_reset(COMBAT_PREPARE)
                continue
            if self.appear(COMBAT_TEAM_PREPARE, interval=2):
                self.team_set(team)
                self.device.click(COMBAT_TEAM_PREPARE)
                self.interval_reset(COMBAT_TEAM_PREPARE)
                continue
            if self.handle_combat_interact():
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
        if self._combat_has_multi_wave:
            if current >= self.combat_cost * 6:
                logger.info(f'Current has {current}, combat costs {self.combat_cost}, can run again')
                return True
            else:
                logger.info(f'Current has {current}, combat costs {self.combat_cost}, can not run again')
                return False
        else:
            logger.info(f'Current has {current}, combat costs {self.combat_cost}, no again')
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
            if self.appear(page_main.check_button):
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
            self.combat_prepare(team)
            self.combat_execute()
            finish = self.combat_finish()
            if self.state.TrailblazePower >= self.combat_cost:
                logger.info('Still having some trailblaze power run with less waves to empty it')
                continue
            if finish:
                break
