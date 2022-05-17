import inflection

from module.base.timer import Timer
from module.exception import CampaignEnd, RequestHumanTakeover
from module.logger import logger
from module.map.map import Map
from module.map.map_grids import SelectedGrids
from module.os.fleet import OSFleet
from module.os.globe_camera import GlobeCamera
from module.ui.assets import OS_CHECK


class OSMap(OSFleet, Map, GlobeCamera):
    def clear_all_objects(self, grid=None):
        """Method to clear all objects around specific grid.

        Args:
            grid (GridInfo):

        Returns:
            int: Cleared count
        """
        if grid is not None:
            logger.hr(f'clear_all_objects: {grid}', level=2)
        for count in range(0, 10):
            grids = self.map.select(is_resource=True) \
                .add(self.map.select(is_enemy=True)) \
                .add(self.map.select(is_meowfficer=True)) \
                .add(self.map.select(is_exclamation=True)).delete(self.map.select(is_interactive_only=True))
            if grid is not None:
                grids = SelectedGrids([g for g in grids if self.grid_is_in_sight(g, camera=grid)])

            if not grids:
                logger.info(f'OS object cleared: {count}')
                return count

            grids = grids.sort_by_camera_distance(self.fleet_current)
            logger.hr('Clear all resource')
            logger.info(f'Grids: {grids}')
            logger.info(f'Clear object {grids[0]}')
            self.goto(grids[0], expected=self._get_goto_expected(grids[0]))
            self.handle_meowfficer_searching()

        logger.warning('Too many objects to clear, stopped')
        return 10

    def handle_meowfficer_searching(self):
        """
        Move back and forth to handle meowfficer farming

        Returns:
            bool: If handled
        """
        if not self.is_meowfficer_searching():
            return False

        logger.hr('Meowfficer searching')
        back = self.fleet_current
        sea = self.get_sea_grids()[:4]
        logger.info(f'Sea grids: {sea}')
        forth = sea[0]

        # Meowfficer searching finishes in 8 steps at max
        # If found good items in current step, progress bar doesn't increase
        for grid in [forth, back] * 7:
            self.goto(grid)
            if self.is_meowfficer_searching():
                percent = self.get_meowfficer_searching_percentage()
                logger.attr('Meowfficer_searching', f'{int(percent * 100)}%')
            else:
                logger.hr('Meowfficer searching end')
                return True

        logger.warning('Too many meowfficer searching steps')
        return True

    def clear_remain_grids(self):
        logger.hr('Clear remain grids', level=2)
        self.clear_all_objects()

    def full_clear(self):
        """
        Clear the whole map.
        """
        logger.info(f'Full scan start')
        self.map.reset_fleet()

        queue = self.map.camera_data

        while len(queue) > 0:
            queue = queue.sort_by_camera_distance(self.camera)
            self.focus_to(queue[0])
            self.focus_to_grid_center(0.25)
            self.view.predict()
            self.map.update(grids=self.view, camera=self.camera)
            self.map.show()

            self.clear_all_objects(queue[0])
            queue = queue[1:]

        self.clear_remain_grids()
        self.clear_akashi()
        logger.info('Full clear end')

    def clear_akashi(self):
        """
        Handle Akashi's shop after auto search.
        After auto search, fleet will near akashi.
        This method detect where akashi stands, enter shop, buy items and exit.

        Returns:
            bool: If found and handled.
        """
        if not self.config.OpsiGeneral_DoRandomMapEvent:
            return False
        if self.zone.is_port:
            logger.info('Current zone is a port, do not have akashi')
            return False

        grid = self.radar.predict_akashi(self.device.image)
        if grid is None:
            logger.info('No akashi on this map')
            return False

        logger.info(f'Found Akashi on {grid}')
        self.handle_info_bar()

        self.update_os()
        self.view.predict()
        self.view.show()

        grid = self.convert_radar_to_local(grid)
        self.handle_akashi_supply_buy(grid)
        return True

    def run(self):
        self.device.screenshot()
        self.handle_siren_platform()
        self.map_init(map_=None)
        self.full_clear()

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
                logger.info('Get OS auto search reward')
                self.wait_until_appear(OS_CHECK, offset=(20, 20))
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
            result = self.wait_until_walk_stable(drop=drop, confirm_timer=Timer(1.5, count=4))
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

    def run_auto_search(self, rescan=None):
        """
        Clear current zone by running auto search.
        OpSi story mode must be cleared to unlock auto search.

        Args:
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
                save=self.config.DropRecord_SaveOpsi,
                upload=self.config.DropRecord_UploadOpsi
        ) as drop:
            self.os_auto_search_run(drop)

            # Record current zone, skip this if no rewards from auto search.
            drop.add(self.device.image)

            self._solved_map_event = set()
            self._solved_fleet_mechanism = False
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
                result = self.wait_until_walk_stable(drop=drop)
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
            result = self.wait_until_walk_stable(drop=drop, confirm_timer=Timer(1.5, count=4))
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
            result = self.wait_until_walk_stable(drop=drop, confirm_timer=Timer(1.5, count=4))
            if 'event' in result:
                self._solved_map_event.add('is_logging_tower')
                return True
            else:
                return False

        grids = self.view.select(is_fleet_mechanism=True)
        if self.config.task.command == 'OpsiExplore' \
                and 'is_fleet_mechanism' not in self._solved_map_event \
                and grids \
                and grids[0].is_fleet_mechanism:
            grid = grids[0]
            logger.info(f'Found fleet mechanism on {grid}')
            self.device.click(grid)
            self.wait_until_walk_stable(drop=drop, confirm_timer=Timer(1.5, count=4))

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
            if not self.config.task.command == 'OpsiExplore' and len(self._solved_map_event):
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
