import numpy as np

from module.combat.assets import GET_ITEMS_1, GET_ITEMS_2, GET_ITEMS_3
from module.exception import MapWalkError
from module.exception import ScriptError
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.os.assets import MAP_EXIT
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

        # UI switching
        self.device.screenshot()
        if self.is_in_map():
            logger.info('Already in os map')
        elif self.is_in_globe():
            self.os_globe_goto_map()
            # Zone header has an animation to show.
            self.device.sleep(0.3)
            self.device.screenshot()
        else:
            if self.ui_page_appear(page_os):
                self.ui_goto_main()
            self.ui_ensure(page_os)
            # Zone header has an animation to show.
            self.device.sleep(0.3)
            self.device.screenshot()

        # Init
        _get_current_zone_success = False
        for _ in range(5):
            try:
                self.get_current_zone()
                _get_current_zone_success = True
                break
            except:
                self.handle_map_event()
            finally:
                self.device.screenshot()
        if not _get_current_zone_success:
            self.get_current_zone()

        # self.map_init()
        self.hp_reset()
        self.handle_fleet_repair(revert=False)

        # Clear current zone
        self.run_auto_search()

        # Exit from special zones types, only SAFE and DANGEROUS are acceptable.
        if self.appear(MAP_EXIT, offset=(20, 20)):
            logger.warning('OS is in a special zone type, while SAFE and DANGEROUS are acceptable')
            self.map_exit()

    def globe_goto(self, zone, types=('SAFE', 'DANGEROUS'), refresh=False, stop_if_safe=False):
        """
        Goto another zone in OS.

        Args:
            zone (str, int, Zone): Name in CN/EN/JP, zone id, or Zone instance.
            types (tuple[str], list[str], str): Zone types, or a list of them.
                Available types: DANGEROUS, SAFE, OBSCURE, LOGGER, STRONGHOLD.
                Try the the first selection in type list, if not available, try the next one.
            refresh (bool): If already at target zone,
                set false to skip zone switching,
                set true to re-enter current zone to refresh.
            stop_if_safe (bool): Return false if zone is SAFE.

        Pages:
            in: IN_MAP or IN_GLOBE
            out: IN_MAP
        """
        zone = self.name_to_zone(zone)
        logger.hr(f'Globe goto: {zone}')
        if self.zone == zone:
            if refresh:
                logger.info('Goto another zone to refresh current zone')
                self.globe_goto(self.zone_nearest_azur_port(self.zone), types=('SAFE', 'DANGEROUS'), refresh=False)
            else:
                logger.info('Already at target zone')
                return False
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
        self.get_current_zone()
        # Fleet repairs before starting if needed
        self.handle_fleet_repair(revert=False)
        # self.map_init()
        return True

    def port_goto2(self):
        """
        Wraps `port_goto2()`, handle walk_out_of_step

        Returns:
            bool: If success
        """
        for _ in range(3):
            try:
                super().port_goto2()
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

        self.port_goto2()
        self.port_enter()
        self.port_dock_repair()
        self.port_quit()

        if revert and prev != self.zone:
            self.globe_goto(prev)

    def handle_fleet_repair(self, revert=True):
        if self.config.OpsiGeneral_RepairThreshold > 0:
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
            self.port_goto2()
            self.port_enter()
            if mission and mission_success:
                mission_success &= self.port_mission_accept()
            if supply and supply_success:
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
            result = self.os_get_next_mission2()
            if not result:
                break

            self.get_current_zone()
            self.run_auto_search()
            self.handle_fleet_repair(revert=False)

        return True

    def os_daily(self):
        while 1:
            mission_success = True
            if self.config.OpsiDaily_DoMission or self.config.OpsiDaily_BuySupply:
                self.os_finish_daily_mission()
                self.config.check_task_switch()
                # If unable to receive more dailies, finish them and try again.
                mission_success, _ = self.os_port_daily(
                    mission=self.config.OpsiDaily_DoMission, supply=self.config.OpsiDaily_BuySupply)

            if self.config.OpsiDaily_DoMission:
                self.os_finish_daily_mission()

            if mission_success:
                break

        self.config.task_delay(server_update=True)

    def os_meowfficer_farming(self):
        """
        Recommend 3 or 5 for higher meowfficer searching point per action points ratio.
        """
        logger.hr(f'OS meowfficer farming, hazard_level={self.config.OpsiMeowfficerFarming_HazardLevel}', level=1)
        while 1:
            if self.config.OpsiGeneral_AshAttack and not self._ash_fully_collected:
                self.config.OS_ACTION_POINT_PRESERVE = 0
            else:
                self.config.OS_ACTION_POINT_PRESERVE = self.config.OpsiMeowfficerFarming_ActionPointPreserve

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
            self.os_order_execute(recon_scan=True, submarine_call=False)
            self.config.task_delay(minute=30)
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

        result = self.os_get_next_obscure(use_logger=self.config.OpsiObscure_UseLogger)
        if not result:
            # No obscure coordinates, delay next run to tomorrow.
            self.config.task_delay(server_update=True)
            self.config.task_stop()

        self.get_current_zone()
        self.os_order_execute(recon_scan=True, submarine_call=self.config.OpsiObscure_CallSubmarine)

        # Delay next run 30min or 60min.
        delta = 60 if self.config.OpsiObscure_CallSubmarine else 30
        if not self.config.OpsiObscure_ForceRun:
            self.config.task_delay(minute=delta)

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
