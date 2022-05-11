import numpy as np

from module.config.utils import (deep_get, get_os_next_reset,
                                 get_os_reset_remain,
                                 DEFAULT_TIME)
from module.exception import RequestHumanTakeover, ScriptError
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.os.fleet import BossFleet
from module.os.globe import OSGlobe
from module.os.globe_operation import OSExploreError


class OperationSiren(OSGlobe):
    def os_port_daily(self, mission=True, supply=True):
        """
        Accept all missions and buy all supplies in all ports.
        If reach the maximum number of missions, skip accept missions in next port.
        If not having enough yellow coins or purple coins, skip buying supplies in next port.

        Args:
            mission (bool): If needs to accept missions.
            supply (bool): If needs to buy supplies.

        Returns:
            bool: True if all mission received.
            bool: True if all supplies bought.
        """
        logger.hr('OS port daily', level=1)
        ports = ['NY City', 'Gibraltar', 'Liverpool', 'St. Petersburg']
        if np.random.uniform() > 0.5:
            ports.reverse()

        mission_success = True
        supply_success = True
        for port in ports:
            port = self.name_to_zone(port)
            logger.hr(f'OS port daily in {port}', level=2)
            self.globe_goto(port)
            self.port_goto()
            self.port_enter()
            # Deprecated since 2022.01.13, missions are shown only in overview, no longer to be shown at ports.
            # if mission and mission_success:
            #     mission_success &= self.port_mission_accept()
            if supply:
                supply_success &= self.port_supply_buy()
            self.port_quit()

        return mission_success, supply_success

    def os_port_mission(self):
        """
        Visit all ports and do the daily mission in it.
        """
        logger.hr('OS port mission', level=1)
        ports = ['NY City', 'Dakar', 'Taranto', 'Gibraltar', 'Brest', 'Liverpool', 'Kiel', 'St. Petersburg']
        if np.random.uniform() > 0.5:
            ports.reverse()

        for port in ports:
            port = self.name_to_zone(port)
            logger.hr(f'OS port daily in {port}', level=2)
            self.globe_goto(port)

            self.run_auto_search()
            self.handle_after_auto_search()

    def os_finish_daily_mission(self):
        """
        Finish all daily mission in Operation Siren.
        Suggest to run os_port_daily to accept missions first.

        Returns:
            bool: True if all finished.
        """
        logger.hr('OS finish daily mission', level=1)
        while 1:
            result = self.os_get_next_mission()
            if not result:
                break

            if result != 'pinned_at_archive_zone':
                # The name of archive zone is "archive zone", which is not an existing zone.
                # After archive zone, it go back to previous zone automatically.
                self.zone_init()
            if result == 'already_at_mission_zone':
                self.globe_goto(self.zone, refresh=True)
            self.fleet_set(self.config.OpsiFleet_Fleet)
            self.os_order_execute(
                recon_scan=False,
                submarine_call=self.config.OpsiFleet_Submarine and result != 'pinned_at_archive_zone')
            self.run_auto_search()
            self.handle_after_auto_search()
            self.config.check_task_switch()

        return True

    def os_daily(self):
        # Finish existing missions first
        # No need anymore, os_mission_overview_accept() is able to handle
        # self.os_finish_daily_mission()

        # Clear tuning samples daily
        if self.config.OpsiDaily_UseTuningSample:
            self.tuning_sample_use()

        while 1:
            # If unable to receive more dailies, finish them and try again.
            success = self.os_mission_overview_accept()
            # Re-init zone name
            # MISSION_ENTER appear from the right,
            # need to confirm that the animation has ended,
            # or it will click on MAP_GOTO_GLOBE
            self.zone_init()
            self.os_finish_daily_mission()
            if self.is_in_opsi_explore():
                self.os_port_mission()
                break
            if success:
                break

        self.config.task_delay(server_update=True)

    def os_shop(self):
        self.os_port_daily(mission=False, supply=self.config.OpsiShop_BuySupply)
        self.config.task_delay(server_update=True)

    def os_meowfficer_farming(self):
        """
        Recommend 3 or 5 for higher meowfficer searching point per action points ratio.
        """
        logger.hr(f'OS meowfficer farming, hazard_level={self.config.OpsiMeowfficerFarming_HazardLevel}', level=1)
        self.action_point_limit_override()
        while 1:
            self.config.OS_ACTION_POINT_PRESERVE = self.config.OpsiMeowfficerFarming_ActionPointPreserve
            if self.config.OpsiAshBeacon_AshAttack \
                    and not self._ash_fully_collected \
                    and self.config.OpsiAshBeacon_EnsureFullyCollected:
                logger.info('Ash beacon not fully collected, ignore action point limit temporarily')
                self.config.OS_ACTION_POINT_PRESERVE = 0
            logger.attr('OS_ACTION_POINT_PRESERVE', self.config.OS_ACTION_POINT_PRESERVE)

            # (1252, 1012) is the coordinate of zone 134 (the center zone) in os_globe_map.png
            if self.config.OpsiMeowfficerFarming_TargetZone != 0:
                try:
                    zone = self.name_to_zone(self.config.OpsiMeowfficerFarming_TargetZone)
                except ScriptError:
                    logger.warning(f'wrong zone_id input:{self.config.OpsiMeowfficerFarming_TargetZone}')
                    raise RequestHumanTakeover('wrong input, task stopped')
                else:
                    logger.hr(f'OS meowfficer farming, zone_id={zone.zone_id}', level=1)
                    self.globe_goto(zone)
                    self.fleet_set(self.config.OpsiFleet_Fleet)
                    self.os_order_execute(
                        recon_scan=False,
                        submarine_call=self.config.OpsiFleet_Submarine)
                    self.run_auto_search()
                    if not self.handle_after_auto_search():
                        self.globe_goto(self.zone_nearest_azur_port(zone=zone))
                    self.config.check_task_switch()
            else:
                zones = self.zone_select(hazard_level=self.config.OpsiMeowfficerFarming_HazardLevel) \
                    .delete(SelectedGrids([self.zone])) \
                    .delete(SelectedGrids(self.zones.select(is_port=True))) \
                    .sort_by_clock_degree(center=(1252, 1012), start=self.zone.location)

                logger.hr(f'OS meowfficer farming, zone_id={zones[0].zone_id}', level=1)
                self.globe_goto(zones[0])
                self.fleet_set(self.config.OpsiFleet_Fleet)
                self.os_order_execute(
                    recon_scan=False,
                    submarine_call=self.config.OpsiFleet_Submarine)
                self.run_auto_search()
                self.handle_after_auto_search()
                self.config.check_task_switch()

    def _os_explore_task_delay(self):
        """
        Delay other OpSi tasks during os_explore
        """
        logger.info('Delay other OpSi tasks during OpsiExplore')
        next_run = self.config.Scheduler_NextRun
        for task in ['OpsiObscure', 'OpsiAbyssal', 'OpsiStronghold', 'OpsiMeowfficerFarming']:
            keys = f'{task}.Scheduler.NextRun'
            current = deep_get(self.config.data, keys=keys, default=DEFAULT_TIME)
            if current < next_run:
                logger.info(f'Delay task `{task}` to {next_run}')
                self.config.modified[keys] = next_run

        # ResetActionPointPreserve
        # Unbound attribute, default to 500
        preserve = self.config.OpsiMeowfficerFarming_ActionPointPreserve
        logger.info(f'Set OpsiMeowfficerFarming.ActionPointPreserve to {preserve}')
        self.config.modified['OpsiMeowfficerFarming.OpsiMeowfficerFarming.ActionPointPreserve'] = preserve

        self.config.update()

    def _os_explore(self):
        """
        Explore all dangerous zones at the beginning of month.
        """

        def end():
            logger.info('OS explore finished, delay to next reset')
            next_reset = get_os_next_reset()
            logger.attr('OpsiNextReset', next_reset)
            logger.info('To run again, clear OpsiExplore.Scheduler.NextRun and set OpsiExplore.OpsiExplore.LastZone=0')
            with self.config.multi_set():
                self.config.OpsiExplore_LastZone = 0
                self.config.task_delay(target=next_reset)
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
        for zone in order:
            if not self.globe_goto(zone, stop_if_safe=True):
                logger.info(f'Zone cleared: {self.name_to_zone(zone)}')
                self.config.OpsiExplore_LastZone = zone
                continue

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
            self.run_auto_search()
            self.config.OpsiExplore_LastZone = zone
            logger.info(f'Zone cleared: {self.name_to_zone(zone)}')
            self.handle_after_auto_search()
            self.config.check_task_switch()
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

        logger.critical('Failed to solve the locked zone')
        raise RequestHumanTakeover

    def clear_obscure(self):
        """
        Raises:
            ActionPointLimit:
        """
        logger.hr('OS clear obscure', level=1)
        if self.config.OpsiObscure_ForceRun:
            logger.info('OS obscure finish is under force run')

        result = self.storage_get_next_item('OBSCURE', use_logger=self.config.OpsiGeneral_UseLogger)
        if not result:
            # No obscure coordinates, delay next run to tomorrow.
            if get_os_reset_remain() > 0:
                self.config.task_delay(server_update=True)
            else:
                logger.info('Just less than 1 day to OpSi reset, delay 2.5 hours')
                self.config.task_delay(minute=150, server_update=True)
            self.config.task_stop()

        self.zone_init()
        self.fleet_set(self.config.OpsiFleet_Fleet)
        self.os_order_execute(
            recon_scan=True,
            submarine_call=self.config.OpsiFleet_Submarine)
        self.run_auto_search()

        self.map_exit()
        self.handle_after_auto_search()

    def os_obscure(self):
        while 1:
            self.clear_obscure()
            if self.config.OpsiObscure_ForceRun:
                self.config.check_task_switch()
                continue
            else:
                break

    def clear_abyssal(self):
        """
        Get one abyssal logger in storage,
        attack abyssal boss,
        repair fleets in port.

        Raises:
            ActionPointLimit:
            TaskEnd: If no more abyssal loggers.
            RequestHumanTakeover: If unable to clear boss, fleets exhausted.
        """
        logger.hr('OS clear abyssal', level=1)
        result = self.storage_get_next_item('ABYSSAL', use_logger=self.config.OpsiGeneral_UseLogger)
        if not result:
            # No obscure coordinates, delay next run to tomorrow.
            if get_os_reset_remain() > 0:
                self.config.task_delay(server_update=True)
            else:
                logger.info('Just less than 1 day to OpSi reset, delay 2.5 hours')
                self.config.task_delay(minute=150, server_update=True)
            self.config.task_stop()

        self.zone_init()
        result = self.run_abyssal()
        if not result:
            raise RequestHumanTakeover

        self.fleet_repair(revert=False)

    def os_abyssal(self):
        while 1:
            self.clear_abyssal()
            self.config.check_task_switch()

    def clear_stronghold(self):
        """
        Find a siren stronghold on globe map,
        clear stronghold,
        repair fleets in port.

        Raises:
            ActionPointLimit:
            TaskEnd: If no more strongholds.
            RequestHumanTakeover: If unable to clear boss, fleets exhausted.
        """
        logger.hr('OS clear stronghold', level=1)
        self.os_map_goto_globe()
        self.globe_update()
        zone = self.find_siren_stronghold()
        if zone is None:
            # No siren stronghold, delay next run to tomorrow.
            self.config.task_delay(server_update=True)
            self.config.task_stop()

        self.globe_enter(zone)
        self.zone_init()
        self.os_order_execute(recon_scan=True, submarine_call=False)
        self.run_stronghold()

        self.fleet_repair(revert=False)
        self.handle_fleet_resolve(revert=False)

    def os_stronghold(self):
        while 1:
            self.clear_stronghold()
            self.config.check_task_switch()

    def run_stronghold_one_fleet(self, fleet):
        """
        Args
            fleet (BossFleet):

        Returns:
            bool: If all cleared.
        """
        self.config.override(
            OpsiGeneral_BuyAkashiShop=False,
            OpsiGeneral_RepairThreshold=0
        )
        # Try 3 times, because fleet may stuck in fog.
        for _ in range(3):
            # Attack
            self.fleet_set(fleet.fleet_index)
            self.run_auto_search()
            self.hp_reset()
            self.hp_get()

            # End
            if self.get_stronghold_percentage() == '0':
                logger.info('BOSS clear')
                return True
            elif any(self.need_repair):
                logger.info('Auto search stopped, because fleet died')
                # Re-enter to reset fleet position
                prev = self.zone
                self.globe_goto(self.zone_nearest_azur_port(self.zone))
                self.globe_goto(prev, types='STRONGHOLD')
                return False
            else:
                logger.info('Auto search stopped, because fleet stuck')
                # Re-enter to reset fleet position
                prev = self.zone
                self.globe_goto(self.zone_nearest_azur_port(self.zone))
                self.globe_goto(prev, types='STRONGHOLD')
                continue

    def run_stronghold(self):
        """
        All fleets take turns in attacking siren stronghold.

        Returns:
            bool: If success to clear.

        Pages:
            in: Siren logger (abyssal), boss appeared.
            out: If success, dangerous or safe zone.
                If failed, still in abyssal.
        """
        logger.hr(f'Stronghold clear', level=1)
        fleets = self.parse_fleet_filter()
        for fleet in fleets:
            logger.hr(f'Turn: {fleet}', level=2)
            if not isinstance(fleet, BossFleet):
                self.os_order_execute(recon_scan=False, submarine_call=True)
                continue

            result = self.run_stronghold_one_fleet(fleet)
            if result:
                return True
            else:
                continue

        logger.critical('Unable to clear boss, fleets exhausted')
        return False


if __name__ == '__main__':
    self = OperationSiren('alas', task='OpsiStronghold')
    from module.os.config import OSConfig

    self.config = self.config.merge(OSConfig())
    self.device.screenshot()
    self.zone_init()
    self.run_stronghold()
