import numpy as np

from module.exception import MapWalkError, ScriptError, RequestHumanTakeover
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.os.fleet import BossFleet
from module.os.map import OSMap
from module.reward.reward import Reward
from module.ui.ui import page_os


class OperationSiren(Reward, OSMap):
    def os_init(self):
        """
        Call this method before doing any Operation functions.

        Pages:
            in: IN_MAP or IN_GLOBE or page_os or any page
            out: IN_MAP
        """
        logger.hr('OS init', level=1)
        self.config.override(Submarine_Fleet=1, Submarine_Mode='every_combat')

        # UI switching
        if self.is_in_map():
            logger.info('Already in os map')
        elif self.is_in_globe():
            self.os_globe_goto_map()
        else:
            if self.ui_page_appear(page_os):
                self.ui_goto_main()
            self.ui_ensure(page_os)

        # Init
        self.zone_init()

        # self.map_init()
        self.hp_reset()
        self.handle_fleet_repair(revert=False)

        # Exit from special zones types, only SAFE and DANGEROUS are acceptable.
        if self.is_in_special_zone():
            logger.warning('OS is in a special zone type, while SAFE and DANGEROUS are acceptable')
            self.map_exit()

        # Clear current zone
        if self.zone.is_port:
            logger.info('In port, skip running first auto search')
            self.handle_ash_beacon_attack()
        else:
            self.run_auto_search()
            self.handle_fleet_repair(revert=False)

    def get_current_zone_from_globe(self):
        """
        Get current zone from globe map. See OSMapOperation.get_current_zone()
        """
        self.os_map_goto_globe(unpin=False)
        self.globe_update()
        self.zone = self.get_globe_pinned_zone()
        self.os_globe_goto_map()
        return self.zone

    def globe_goto(self, zone, types=('SAFE', 'DANGEROUS'), refresh=False, stop_if_safe=False):
        """
        Goto another zone in OS.

        Args:
            zone (str, int, Zone): Name in CN/EN/JP/TW, zone id, or Zone instance.
            types (tuple[str], list[str], str): Zone types, or a list of them.
                Available types: DANGEROUS, SAFE, OBSCURE, ABYSSAL, STRONGHOLD.
                Try the the first selection in type list, if not available, try the next one.
            refresh (bool): If already at target zone,
                set false to skip zone switching,
                set true to re-enter current zone to refresh.
            stop_if_safe (bool): Return false if zone is SAFE.

        Returns:
            bool: If zone switched.

        Pages:
            in: IN_MAP or IN_GLOBE
            out: IN_MAP
        """
        zone = self.name_to_zone(zone)
        logger.hr(f'Globe goto: {zone}')
        if self.zone == zone:
            if refresh:
                logger.info('Goto another zone to refresh current zone')
                return self.globe_goto(self.zone_nearest_azur_port(self.zone),
                                       types=('SAFE', 'DANGEROUS'), refresh=False)
            else:
                logger.info('Already at target zone')
                return False
        # MAP_EXIT
        if self.is_in_special_zone():
            self.map_exit()
        # IN_MAP
        if self.is_in_map():
            self.os_map_goto_globe()
        # IN_GLOBE
        if not self.is_in_globe():
            logger.warning('Trying to move in globe, but not in os globe map')
            raise ScriptError('Trying to move in globe, but not in os globe map')
        # self.ensure_no_zone_pinned()
        self.globe_update()
        self.globe_focus_to(zone)
        if stop_if_safe:
            if self.zone_has_safe():
                logger.info('Zone is safe, stopped')
                self.ensure_no_zone_pinned()
                return False
        self.zone_type_select(types=types)
        self.globe_enter(zone)
        # IN_MAP
        if hasattr(self, 'zone'):
            del self.zone
        self.zone_init()
        # Fleet repairs before starting if needed
        self.handle_fleet_repair(revert=False)
        # self.map_init()
        return True

    def port_goto(self):
        """
        Wraps `port_goto()`, handle walk_out_of_step

        Returns:
            bool: If success
        """
        for _ in range(3):
            try:
                super().port_goto()
                return True
            except MapWalkError:
                pass

            logger.info('Goto another port then re-enter')
            prev = self.zone
            self.globe_goto(self.zone_nearest_azur_port(self.zone))
            self.globe_goto(prev)

    def fleet_repair(self, revert=True):
        """
        Repair fleets in nearest port.

        Args:
            revert (bool): If go back to previous zone.
        """
        logger.hr('OS fleet repair')
        prev = self.zone
        if self.zone.is_azur_port:
            logger.info('Already in azur port')
        else:
            self.globe_goto(self.zone_nearest_azur_port(self.zone))

        self.port_goto()
        self.port_enter()
        self.port_dock_repair()
        self.port_quit()

        if revert and prev != self.zone:
            self.globe_goto(prev)

    def handle_fleet_repair(self, revert=True):
        """
        Args:
            revert (bool): If go back to previous zone.

        Returns:
            bool: If repaired.
        """
        if self.config.OpsiGeneral_RepairThreshold <= 0:
            return False
        if self.is_in_special_zone():
            logger.info('OS is in a special zone type, skip fleet repair')
            return False

        self.hp_get()
        check = [round(data, 2) <= self.config.OpsiGeneral_RepairThreshold if use else False
                 for data, use in zip(self.hp, self.hp_has_ship)]
        if any(check):
            logger.info('At least one ship is below threshold '
                        f'{str(int(self.config.OpsiGeneral_RepairThreshold * 100))}%, '
                        'retreating to nearest azur port for repairs')
            self.fleet_repair(revert=revert)
        else:
            logger.info('No ship found to be below threshold '
                        f'{str(int(self.config.OpsiGeneral_RepairThreshold * 100))}%, '
                        'continue OS exploration')
        self.hp_reset()
        return True

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
        if np.random.uniform() > 0.5:
            # St. Petersburg => Liverpool => Gibraltar => NY City
            ports = [3, 1, 2, 0]
        else:
            # NY City => Gibraltar => Liverpool => St. Petersburg
            ports = [0, 2, 1, 3]

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

            self.zone_init()
            if result > 1:
                self.globe_goto(self.zone, refresh=True)
            self.fleet_set(self.config.OpsiFleet_Fleet)
            self.os_order_execute(
                recon_scan=False,
                submarine_call=self.config.OpsiFleet_Submarine)
            self.run_auto_search()
            self.handle_fleet_repair(revert=False)
            self.config.check_task_switch()

        return True

    def os_daily(self):
        # Finish existing missions first
        self.os_finish_daily_mission()

        if self.config.OpsiDaily_UseTuningSample:
            self.os_tuning_sample()

        while 1:
            # If unable to receive more dailies, finish them and try again.
            success = self.os_mission_overview_accept()
            self.os_finish_daily_mission()
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
                    self.config.task_stop(message=f'wrong input, task stopped')
                else:
                    logger.hr(f'OS meowfficer farming, zone_id={zone.zone_id}', level=1)
                    self.globe_goto(zone)
                    self.fleet_set(self.config.OpsiFleet_Fleet)
                    self.os_order_execute(
                        recon_scan=False,
                        submarine_call=self.config.OpsiFleet_Submarine)
                    self.run_auto_search()
                    self.handle_fleet_repair(revert=False)
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
                self.handle_fleet_repair(revert=False)
                self.config.check_task_switch()

    def os_explore(self):
        """
        Explore all dangerous zones at the beginning of month.
        """

        def end():
            logger.info('OS explore finished')
            logger.info('To run again, set OpsiExplore.Scheduler.Enable=True, OpsiExplore.OpsiExplore.LastZone=0')
            with self.config.multi_set():
                self.config.Scheduler_Enable = False
                self.config.OpsiExplore_LastZone = 0
                self.config.task_delay(minute=0)
            self.config.task_stop()

        logger.hr('OS explore', level=1)
        order = [int(f.strip(' \t\r\n')) for f in self.config.OS_EXPLORE_FILTER.split('>')]
        if self.config.OpsiExplore_LastZone in order:
            order = order[order.index(self.config.OpsiExplore_LastZone) + 1:]
        elif self.config.OpsiExplore_LastZone == 0:
            # First run
            pass
        else:
            logger.warning(f'Invalid OpsiExplore_LastZone={self.config.OpsiExplore_LastZone}, re-explore')
        if not len(order):
            end()

        for zone in order:
            if not self.globe_goto(zone, stop_if_safe=True):
                logger.info(f'Zone cleared: {self.name_to_zone(zone)}')
                self.config.OpsiExplore_LastZone = zone
                continue

            logger.hr(f'OS explore {zone}', level=1)
            self.fleet_set(self.config.OpsiFleet_Fleet)
            self.os_order_execute(
                recon_scan=not self.config.OpsiExplore_SpecialRadar,
                submarine_call=self.config.OpsiFleet_Submarine)
            self.run_auto_search()
            self.config.OpsiExplore_LastZone = zone
            logger.info(f'Zone cleared: {self.name_to_zone(zone)}')
            self.handle_fleet_repair(revert=False)
            self.config.check_task_switch()
            if zone == order[-1]:
                end()

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
            self.config.task_delay(server_update=True)
            self.config.task_stop()

        self.zone_init()
        self.fleet_set(self.config.OpsiFleet_Fleet)
        self.os_order_execute(
            recon_scan=True,
            submarine_call=self.config.OpsiFleet_Submarine)
        self.run_auto_search()

        self.map_exit()
        self.handle_fleet_repair(revert=False)

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
            self.config.task_delay(server_update=True)
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

    def os_tuning_sample(self):
        """
        Use all tuning samples.
        """
        logger.hr('Using all tuning samples', level=2)
        sample_types = ['OFFENSE', 'SURVIVAL', 'COMBAT', 'QUALITY_OFFENSE', 'QUALITY_SURVIVAL', 'QUALITY_COMBAT']
        for sample_type in sample_types:
            if self.storage_get_next_item(item=sample_type, use_logger=False):
                logger.info(f'Used {sample_type} sample(s)')
            else:
                logger.info(f'No {sample_type} sample')
        return True


# if __name__ == '__main__':
#     self = OperationSiren('alas', task='OpsiStronghold')
#     from module.os.config import OSConfig
#
#     self.config = self.config.merge(OSConfig())
#     self.device.screenshot()
#     self.zone_init()
#     self.run_stronghold()

if __name__ == '__main__':
    self = OperationSiren('alas', task='OpsiTuneSample')
    from module.os.config import OSConfig

    self.config = self.config.merge(OSConfig())
    self.device.screenshot()
    self.zone_init()
    self.os_tuning_sample()
