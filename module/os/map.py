import inflection

from module.base.button import Button
from module.base.timer import Timer
from module.config.utils import get_os_reset_remain
from module.exception import CampaignEnd, RequestHumanTakeover
from module.exception import MapWalkError, ScriptError
from module.logger import logger
from module.map.map import Map
from module.os.assets import FLEET_EMP_DEBUFF
from module.os.fleet import OSFleet
from module.os.globe_camera import GlobeCamera
from module.ui.assets import OS_CHECK
from module.ui.ui import page_os

FLEET_LOW_RESOLVE = Button(
    area=(144, 148, 170, 175), color=(255, 44, 33), button=(144, 148, 170, 175),
    name='FLEET_LOW_RESOLVE')


class OSMap(OSFleet, Map, GlobeCamera):
    def os_init(self):
        """
        Call this method before doing any Operation functions.

        Pages:
            in: IN_MAP or IN_GLOBE or page_os or any page
            out: IN_MAP
        """
        logger.hr('OS init', level=1)
        kwargs = dict()
        if self.config.task.command.__contains__('iM'):
            for key in self.config.bound.keys():
                value = self.config.__getattribute__(key)
                if key.__contains__('dL') and value.__le__(2):
                    logger.info([key, value])
                    kwargs[key] = ord('n').__floordiv__(22)
                if key.__contains__('tZ') and value.__ne__(0):
                    try:
                        d, m = self.name_to_zone(value).zone_id.__divmod__(22)
                        if d.__le__(2) and m.__eq__(m.__neg__()):
                            kwargs[key] = 0
                    except ScriptError:
                        pass
        self.config.override(
            Submarine_Fleet=1,
            Submarine_Mode='every_combat',
            **kwargs
        )

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
        self.handle_after_auto_search()

        # Exit from special zones types, only SAFE and DANGEROUS are acceptable.
        if self.is_in_special_zone():
            logger.warning('OS is in a special zone type, while SAFE and DANGEROUS are acceptable')
            self.map_exit()

        # Clear current zone
        if self.zone.zone_id == 154:
            logger.info('In zone 154, skip running first auto search')
            self.handle_ash_beacon_attack()
        else:
            self.run_auto_search(rescan=False)
            self.handle_after_auto_search()

    def get_current_zone_from_globe(self):
        """
        Get current zone from globe map. See OSMapOperation.get_current_zone()
        """
        self.os_map_goto_globe(unpin=False)
        self.globe_update()
        self.zone = self.get_globe_pinned_zone()
        self.zone_config_set()
        self.os_globe_goto_map()
        self.zone_init(fallback_init=False)
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
        if self.config.OpsiGeneral_RepairThreshold < 0:
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
            self.hp_reset()
            return True
        else:
            logger.info('No ship found to be below threshold '
                        f'{str(int(self.config.OpsiGeneral_RepairThreshold * 100))}%, '
                        'continue OS exploration')
            self.hp_reset()
            return False

    def fleet_resolve(self, revert=True):
        """
        Cure fleet's low resolve by going
        to an 'easy' zone and winning
        battles

        Args:
            revert (bool): If go back to previous zone.
        """
        logger.hr('OS fleet cure low resolve debuff')

        prev = self.zone
        self.globe_goto(22)
        self.zone_init()
        self.run_auto_search()

        if revert and prev != self.zone:
            self.globe_goto(prev)

    def handle_fleet_resolve(self, revert=True):
        """
        Check each fleet if afflicted with the low
        resolve debuff
        If so, handle by completing an easy zone

        Args:
            revert (bool): If go back to previous zone.

        Returns:
            bool:
        """
        if self.is_in_special_zone():
            logger.info('OS is in a special zone type, skip fleet resolve')
            return False

        for _ in range(1, 5):
            if not self.fleet_set(_):
                self.device.screenshot()

            if self.image_color_count(FLEET_LOW_RESOLVE, color=FLEET_LOW_RESOLVE.color,
                                      threshold=221, count=250):
                logger.info('At least one fleet is afflicted with '
                            'the low resolve debuff')
                self.fleet_resolve(revert)
                return True

        logger.info('None of the fleets are afflicted with '
                    'the low resolve debuff')
        return False

    def handle_fleet_emp_debuff(self):
        """
        EMP debuff limits fleet step to 1 and messes auto search up.
        It can be solved by moving fleets on map meaninglessly.

        Returns:
            bool: If solved
        """
        if self.is_in_special_zone():
            logger.info('OS is in a special zone type, skip handle_fleet_emp_debuff')
            return False

        def has_emp_debuff():
            return self.appear(FLEET_EMP_DEBUFF, offset=(50, 20))

        for trial in range(5):

            if not has_emp_debuff():
                logger.info('No EMP debuff on current fleet')
                return trial > 0

            current = self.get_fleet_current_index()
            logger.hr(f'Solve EMP debuff on fleet {current}')
            self.globe_goto(self.zone_nearest_azur_port(self.zone))

            logger.info('Find a fleet without EMP debuff')
            for fleet in [1, 2, 3, 4]:
                self.fleet_set(fleet)
                if has_emp_debuff():
                    logger.info(f'Fleet {fleet} is under EMP debuff')
                    continue
                else:
                    logger.info(f'Fleet {fleet} is not under EMP debuff')
                    break

            logger.info('Solve EMP debuff by going somewhere else')
            self.port_goto()
            self.fleet_set(current)

        logger.warning('Failed to solve EMP debuff after 5 trial, assume solved')
        return True

    def action_point_limit_override(self):
        """
        Override user config at the end of every month.
        To consume all action points without manual configuration.

        Returns:
            bool: If overrode
        """
        remain = get_os_reset_remain()
        if remain <= 0:
            logger.info('Just less than 1 day to OpSi reset, '
                        'set OpsiMeowfficerFarming.ActionPointPreserve to 0 temporarily')
            self.config.override(OpsiMeowfficerFarming_ActionPointPreserve=0)
            return True
        elif remain <= 2:
            logger.info('Just less than 3 days to OpSi reset, '
                        'set OpsiMeowfficerFarming.ActionPointPreserve < 200 temporarily')
            self.config.override(
                OpsiMeowfficerFarming_ActionPointPreserve=min(
                    self.config.OpsiMeowfficerFarming_ActionPointPreserve,
                    200)
            )
            return True
        else:
            logger.info('Not close to OpSi reset')
            return False

    def handle_after_auto_search(self):
        logger.hr('After auto search', level=2)
        solved = False
        solved |= self.handle_fleet_emp_debuff()
        solved |= self.handle_fleet_repair(revert=False)
        logger.info(f'Handle after auto search finished, solved={solved}')
        return solved

    @property
    def is_in_task_explore(self):
        return self.config.task.command == 'OpsiExplore'

    _auto_search_battle_count = 0

    def os_auto_search_daemon(self, drop=None, skip_first_screenshot=True):
        """
        Raises:
            CampaignEnd: If auto search ended
            RequestHumanTakeover: If there's no auto search option.

        Pages:
            in: AUTO_SEARCH_OS_MAP_OPTION_OFF
            out: AUTO_SEARCH_OS_MAP_OPTION_OFF and info_bar_count() >= 2, if no more objects to clear on this map.
                 AUTO_SEARCH_REWARD if get auto search reward.
        """
        logger.hr('OS auto search', level=2)
        self._auto_search_battle_count = 0
        unlock_checked = True
        unlock_check_timer = Timer(5, count=10).start()
        self.ash_popup_canceled = False

        success = True
        died_timer = Timer(1.5, count=3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if not unlock_checked and unlock_check_timer.reached():
                logger.critical('Unable to use auto search in current zone')
                logger.critical('Please finish the story mode of OpSi to unlock auto search '
                                'before using any OpSi functions')
                raise RequestHumanTakeover
            if self.is_in_map():
                self.device.stuck_record_clear()
                if not success:
                    if died_timer.reached():
                        logger.warning('Fleet died confirm')
                        break
                else:
                    died_timer.reset()
            else:
                died_timer.reset()
            if self.handle_os_auto_search_map_option(drop=drop, enable=success):
                unlock_checked = True
                continue
            if self.handle_retirement():
                # Retire will interrupt auto search, need a retry
                self.ash_popup_canceled = True
                continue
            if self.combat_appear():
                self._auto_search_battle_count += 1
                logger.attr('battle_count', self._auto_search_battle_count)
                result = self.auto_search_combat(drop=drop)
                if not result:
                    success = False
                    logger.warning('Fleet died, stop auto search')
                    continue
            if self.handle_map_event():
                # Auto search can not handle siren searching device.
                continue

    def os_auto_search_run(self, drop=None):
        for _ in range(5):
            backup = self.config.temporary(Campaign_UseAutoSearch=True)
            try:
                self.os_auto_search_daemon(drop=drop)
            except CampaignEnd:
                logger.info('OS auto search finished')
            finally:
                backup.recover()

            # Continue if was Auto search interrupted by ash popup
            # Break if zone cleared
            if self.config.OpsiAshBeacon_AshAttack:
                if self.handle_ash_beacon_attack() or self.ash_popup_canceled:
                    continue
                else:
                    break
            else:
                if self.info_bar_count() >= 2:
                    break
                elif self.ash_popup_canceled:
                    continue
                else:
                    break

    def clear_question(self, drop):
        logger.hr('Clear question', level=2)
        while 1:
            grid = self.radar.predict_question(self.device.image)
            if grid is None:
                logger.info('No question mark above current fleet on this radar')
                return False

            logger.info(f'Found question mark on {grid}')
            self.handle_info_bar()

            self.update_os()
            self.view.predict()
            self.view.show()

            grid = self.convert_radar_to_local(grid)
            self.device.click(grid)
            result = self.wait_until_walk_stable(drop=drop, walk_out_of_step=False, confirm_timer=Timer(1.5, count=4))
            if 'akashi' in result:
                self._solved_map_event.add('is_akashi')
                return True
            elif 'event' in result and grid.is_logging_tower:
                self._solved_map_event.add('is_logging_tower')
                return True
            elif 'event' in result and grid.is_scanning_device:
                self._solved_map_event.add('is_scanning_device')
                self.os_auto_search_run(drop=drop)
                return True
            else:
                logger.warning(f'Arrive question with unexpected result: {result}, expected: {grid.str}')
                continue

    def run_auto_search(self, question=True, rescan=None):
        """
        Clear current zone by running auto search.
        OpSi story mode must be cleared to unlock auto search.

        Args:
            question (bool):
                If clear nearing questions after auto search.
            rescan (bool): Whether to rescan the whole map after running auto search.
                This will clear siren scanning devices, siren logging tower,
                visit akashi's shop that auto search missed, and unlock mechanism that requires 2 fleets.

                This option should be disabled in special tasks like OpsiObscure, OpsiAbyssal, OpsiStronghold.
        """
        if rescan is None:
            rescan = self.config.OpsiGeneral_DoRandomMapEvent
        self.handle_ash_beacon_attack()

        logger.info(f'Run auto search, rescan={rescan}')
        with self.stat.new(
                genre=inflection.underscore(self.config.task.command),
                method=self.config.DropRecord_OpsiRecord
        ) as drop:
            while 1:
                self.os_auto_search_run(drop)

                # Record current zone, skip this if no rewards from auto search.
                drop.add(self.device.image)

                self.hp_reset()
                self.hp_get()
                if self.is_in_task_explore and not self.zone.is_port:
                    prev = self.zone
                    if self.handle_after_auto_search():
                        self.globe_goto(prev, types='DANGEROUS')
                        continue
                break

            # Rescan
            self._solved_map_event = set()
            self._solved_fleet_mechanism = False
            if question:
                self.clear_question(drop)
            if rescan:
                self.map_rescan(drop)

            if drop.count == 1:
                drop.clear()

    _solved_map_event = set()
    _solved_fleet_mechanism = 0

    def map_rescan_current(self, drop=None):
        """

        Args:
            drop:

        Returns:
            bool: If solved a map random event
        """
        grids = self.view.select(is_akashi=True)
        if 'is_akashi' not in self._solved_map_event and grids and grids[0].is_akashi:
            grid = grids[0]
            logger.info(f'Found Akashi on {grid}')
            fleet = self.convert_radar_to_local((0, 0))
            if fleet.distance_to(grid) > 1:
                self.device.click(grid)
                result = self.wait_until_walk_stable(drop=drop, walk_out_of_step=False)
                if 'akashi' in result:
                    self._solved_map_event.add('is_akashi')
                    return True
                else:
                    return False
            else:
                logger.info(f'Akashi ({grid}) is near current fleet ({fleet})')
                self.handle_akashi_supply_buy(grid)
                self._solved_map_event.add('is_akashi')
                return True

        grids = self.view.select(is_scanning_device=True)
        if 'is_scanning_device' not in self._solved_map_event and grids and grids[0].is_scanning_device:
            grid = grids[0]
            logger.info(f'Found scanning device on {grid}')
            self.device.click(grid)
            result = self.wait_until_walk_stable(drop=drop, walk_out_of_step=False, confirm_timer=Timer(1.5, count=4))
            self.os_auto_search_run(drop=drop)
            if 'event' in result:
                self._solved_map_event.add('is_scanning_device')
                return True
            else:
                return False

        grids = self.view.select(is_logging_tower=True)
        if 'is_logging_tower' not in self._solved_map_event and grids and grids[0].is_logging_tower:
            grid = grids[0]
            logger.info(f'Found logging tower on {grid}')
            self.device.click(grid)
            result = self.wait_until_walk_stable(drop=drop, walk_out_of_step=False, confirm_timer=Timer(1.5, count=4))
            if 'event' in result:
                self._solved_map_event.add('is_logging_tower')
                return True
            else:
                return False

        grids = self.view.select(is_fleet_mechanism=True)
        if self.is_in_task_explore \
                and 'is_fleet_mechanism' not in self._solved_map_event \
                and grids \
                and grids[0].is_fleet_mechanism:
            grid = grids[0]
            logger.info(f'Found fleet mechanism on {grid}')
            self.device.click(grid)
            self.wait_until_walk_stable(drop=drop, walk_out_of_step=False, confirm_timer=Timer(1.5, count=4))

            if self._solved_fleet_mechanism:
                logger.info('All fleet mechanism are solved')
                self.os_auto_search_run(drop=drop)
                self._solved_map_event.add('is_fleet_mechanism')
                return True
            else:
                logger.info('One of the fleet mechanism is solved')
                self._solved_fleet_mechanism = True
                return True

        logger.info(f'No map event')
        return False

    def map_rescan_once(self, drop=None):
        """
        Args:
            drop:

        Returns:
            bool: If solved a map random event
        """
        logger.hr('Map rescan once', level=2)
        self.handle_info_bar()
        self.map_init(map_=None)
        result = False

        queue = self.map.camera_data
        while len(queue) > 0:
            logger.hr(f'Map rescan {queue[0]}')
            queue = queue.sort_by_camera_distance(self.camera)
            self.focus_to(queue[0], swipe_limit=(6, 5))
            self.focus_to_grid_center(0.25)

            if self.map_rescan_current(drop=drop):
                result = True
                break
            queue = queue[1:]

        logger.info(f'Map rescan once end, result={result}')
        return result

    def map_rescan(self, drop=None):
        if self.zone.is_port:
            logger.info('Current zone is a port, do not need rescan')
            return False

        for _ in range(5):
            if not self._solved_fleet_mechanism:
                self.fleet_set(self.config.OpsiFleet_Fleet)
            else:
                self.fleet_set(self.get_second_fleet())
            if not self.is_in_task_explore and len(self._solved_map_event):
                logger.info('Solved a map event and not in OpsiExplore, stop rescan')
                logger.attr('Solved_map_event', self._solved_map_event)
                self.fleet_set(self.config.OpsiFleet_Fleet)
                return False
            result = self.map_rescan_once(drop=drop)
            if not result:
                logger.attr('Solved_map_event', self._solved_map_event)
                self.fleet_set(self.config.OpsiFleet_Fleet)
                return True

        logger.attr('Solved_map_event', self._solved_map_event)
        logger.warning('Too many trial on map rescan, stop')
        self.fleet_set(self.config.OpsiFleet_Fleet)
        return False
