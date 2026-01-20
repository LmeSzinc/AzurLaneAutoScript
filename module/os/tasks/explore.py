from datetime import timedelta

from module.config.utils import get_os_next_reset, DEFAULT_TIME, get_os_reset_remain
from module.exception import GameStuckError, ScriptError
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.os.globe_operation import OSExploreError
from module.os.map import OSMap


class OpsiExplore(OSMap):
    # List of failed zone id
    _os_explore_failed_zone = []

    def _os_explore_task_delay(self):
        """
        Delay other OpSi tasks during os_explore
        """
        logger.info('Delay other OpSi tasks during OpsiExplore')
        with self.config.multi_set():
            next_run = self.config.Scheduler_NextRun
            for task in ['OpsiObscure', 'OpsiAbyssal', 'OpsiArchive', 'OpsiStronghold', 'OpsiMeowfficerFarming',
                         'OpsiMonthBoss', 'OpsiShop', 'OpsiHazard1Leveling']:
                keys = f'{task}.Scheduler.NextRun'
                current = self.config.cross_get(keys=keys, default=DEFAULT_TIME)
                if current < next_run:
                    logger.info(f'Delay task `{task}` to {next_run}')
                    self.config.cross_set(keys=keys, value=next_run)

    def _os_explore(self):
        """
        Explore all dangerous zones at the beginning of month.
        Failed zone id will be set to _os_explore_failed_zone
        """

        def end():
            logger.info('OS explore finished, delay to next reset')
            next_reset = get_os_next_reset()
            logger.attr('OpsiNextReset', next_reset)
            logger.info('To run again, clear OpsiExplore.Scheduler.NextRun and set OpsiExplore.OpsiExplore.LastZone=0')
            with self.config.multi_set():
                self.config.OpsiExplore_LastZone = 0
                self.config.OpsiExplore_SpecialRadar = False
                self.config.task_delay(target=next_reset)
                self.config.task_call('OpsiDaily', force_call=False)
                self.config.task_call('OpsiShop', force_call=False)
                self.config.task_call('OpsiHazard1Leveling', force_call=False)
            self.config.task_stop()

        logger.hr('OS explore', level=1)
        order = [int(f.strip(' \t\r\n')) for f in self.config.OS_EXPLORE_FILTER.split('>')]
        # Convert user input
        try:
            last_zone = self.name_to_zone(self.config.OpsiExplore_LastZone).zone_id
        except ScriptError:
            logger.warning(f'Invalid OpsiExplore_LastZone={self.config.OpsiExplore_LastZone}, re-explore')
            last_zone = 0
        # Start from last zone
        if last_zone in order:
            order = order[order.index(last_zone) + 1:]
            logger.info(f'Last zone: {self.name_to_zone(last_zone)}, next zone: {order[:1]}')
        elif last_zone == 0:
            logger.info(f'First run, next zone: {order[:1]}')
        else:
            raise ScriptError(f'Invalid last_zone: {last_zone}')
        if not len(order):
            end()

        # Run
        self._os_explore_failed_zone = []
        for zone in order:
            # Check if zone already unlock safe zone
            if not self.globe_goto(zone, stop_if_safe=True):
                logger.info(f'Zone cleared: {self.name_to_zone(zone)}')
                self.config.OpsiExplore_LastZone = zone
                continue

            # Run zone
            logger.hr(f'OS explore {zone}', level=1)
            if not self.config.OpsiExplore_SpecialRadar:
                # Special radar gives 90 turning samples,
                # If no special radar, use the turning samples in storage to acquire stronger fleets.
                self.tuning_sample_use()
            self.fleet_set(self.config.OpsiFleet_Fleet)
            self.os_order_execute(
                recon_scan=not self.config.OpsiExplore_SpecialRadar,
                submarine_call=self.config.OpsiFleet_Submarine)
            self._os_explore_task_delay()

            finished_combat = self.run_auto_search()
            self.config.OpsiExplore_LastZone = zone
            logger.info(f'Zone cleared: {self.name_to_zone(zone)}')
            if finished_combat == 0:
                logger.warning('Zone cleared but did not finish any combat')
                self._os_explore_failed_zone.append(zone)
            self.handle_after_auto_search()
            self.config.check_task_switch()

            # Reached end
            if zone == order[-1]:
                end()

    def os_explore(self):
        for _ in range(2):
            try:
                self._os_explore()
            except OSExploreError:
                logger.info('Go back to NY, explore again')
                self.config.OpsiExplore_LastZone = 0
                self.globe_goto(0)

        failed_zone = [self.name_to_zone(zone) for zone in self._os_explore_failed_zone]
        logger.error(f'OpsiExplore failed at these zones, please check you game settings '
                     f'and check if there is any unfinished event in them: {failed_zone}')
        logger.critical('Failed to solve the locked zone')
        raise GameStuckError
