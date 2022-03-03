import inflection

from module.base.timer import Timer
from module.exception import CampaignEnd
from module.exception import RequestHumanTakeover
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
        if not self.config.OpsiGeneral_BuyAkashiShop:
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

    def run_auto_search(self):
        """
        Clear current zone by running auto search.
        OpSi story mode must be cleared to unlock auto search.
        """
        self.handle_ash_beacon_attack()

        with self.stat.new(
                genre=inflection.underscore(self.config.task.command),
                save=self.config.DropRecord_SaveOpsi,
                upload=self.config.DropRecord_UploadOpsi
        ) as drop:
            for _ in range(3):
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

            # Record current zone, skip this if no rewards from auto search.
            if drop.count:
                drop.add(self.device.image)

        self.clear_akashi()
