from module.base.timer import Timer
from module.handler.ambush import AmbushHandler
from module.handler.mystery import MysteryHandler
from module.logger import logger
from module.map.camera import Camera
from module.map.map_base import location2node, location_ensure
from module.map.map_operation import MapOperation


class Fleet(Camera, AmbushHandler, MysteryHandler, MapOperation):
    fleet_1_location = ()
    fleet_2_location = ()
    fleet_current_index = 1
    battle_count = 0
    mystery_count = 0
    siren_count = 0
    fleet_ammo = 5
    ammo_count = 3

    @property
    def fleet_1(self):
        if self.fleet_current_index != 1:
            self.fleet_switch()
        return self

    @fleet_1.setter
    def fleet_1(self, value):
        self.fleet_1_location = value

    @property
    def fleet_2(self):
        if self.fleet_current_index != 2:
            self.fleet_switch()
        return self

    @fleet_2.setter
    def fleet_2(self, value):
        self.fleet_2_location = value

    @property
    def fleet_current(self):
        if self.fleet_current_index == 2:
            return self.fleet_2_location
        else:
            return self.fleet_1_location

    def fleet_switch(self):
        self.fleet_switch_click()
        self.fleet_current_index = 1 if self.fleet_current_index == 2 else 2
        self.camera = self.fleet_current
        self.update()
        self.find_path_initial()
        self.show_fleet()

    def switch_to(self):
        pass

    def _goto(self, location, expected=''):
        """Goto a grid directly and handle ambush, air raid, mystery picked up, combat.

        Args:
            location (tuple, str, GridInfo): Destination.
        """
        location = location_ensure(location)
        self.in_sight(location, sight=(-3, 0, 3, 2))
        grid = self.convert_map_to_grid(location)

        while 1:
            self.ambush_color_initial()
            grid.__str__ = location
            result = ''
            self.device.click(grid)
            arrived = False
            # Wait to confirm fleet arrived. It does't appear immediately if fleet in combat .
            arrive_timer = Timer(0.3)
            arrive_unexpected_timer = Timer(1.5)
            # Wait after ambushed.
            ambushed_retry = Timer(0.5)
            # If nothing happens, click again.
            walk_timeout = Timer(10)
            walk_timeout.start()

            while 1:
                self.device.screenshot()
                grid.image = self.device.image

                if self.handle_ambush():
                    ambushed_retry.start()
                    # 这个虽然到了之后还会原地再点一次, 但还是先用着, 问题不大
                    # arrived = False
                    # 这个可能会误以为已经到达
                    # arrived = grid.predict_fleet()
                    # 把break去掉就搞定了
                    # break

                if self.handle_mystery(button=grid):
                    # arrived = True
                    self.mystery_count += 1
                    result = 'mystery'
                    # break

                if self.combat_appear():
                    self.combat(expected_end=self._expected_combat_end)
                    arrived = True
                    result = 'combat'
                    self.battle_count += 1
                    if 'siren' in expected:
                        self.siren_count += 1
                    self.fleet_ammo -= 1
                    self.map[location_ensure(location)].is_cleared = True
                    self.handle_boss_appear_refocus()
                    grid = self.convert_map_to_grid(location)
                    # break

                if self.handle_map_cat_attack():
                    continue

                if grid.predict_fleet():
                    arrive_timer.start()
                    arrive_unexpected_timer.start()
                    if not arrive_timer.reached():
                        continue
                    if expected and result not in expected:
                        if arrive_unexpected_timer.reached():
                            logger.warning('Arrive with unexpected result')
                        else:
                            continue
                    logger.info('Arrive confirm')
                    arrived = True
                    break

                # End
                if ambushed_retry.started() and ambushed_retry.reached():
                    break
                if not arrived and walk_timeout.reached():
                    logger.warning('Walk timeout. Retrying.')
                    break

            # End
            if arrived:
                break

        self.map[self.fleet_current].is_fleet = False
        self.map[location].wipe_out()
        self.map[location].is_fleet = True
        self.__setattr__('fleet_%s_location' % self.fleet_current_index, location)

        self.find_path_initial()

    def goto(self, location, optimize=True, expected=''):
        # self.device.sleep(1000)
        location = location_ensure(location)
        if self.config.MAP_HAS_AMBUSH and optimize:
            nodes = self.map.find_path(location)
            for node in nodes:
                self._goto(node, expected=expected)
        else:
            self._goto(location, expected=expected)

    def find_path_initial(self):
        self.map.find_path_initial(self.fleet_current)

    def show_fleet(self):
        fleets = []
        for n in [1, 2]:
            fleet = self.__getattribute__('fleet_%s_location' % n)
            if len(fleet):
                text = 'Fleet_%s: %s' % (n, location2node(fleet))
                if self.fleet_current_index == n:
                    text = '[%s]' % text
                fleets.append(text)
        logger.info(' '.join(fleets))

    def find_current_fleet(self):
        fleets = self.map.select(is_fleet=True, is_spawn_point=True)
        logger.info('Fleets: %s' % str(fleets))
        count = fleets.count
        if count == 1:
            self.fleet_1 = fleets[0].location
        elif count == 2:
            fleets = fleets.sort_by_camera_distance(self.camera)
            self.in_sight(fleets[0], sight=(-1, 0, 1, 2))
            if self.convert_map_to_grid(fleets[0]).predict_current_fleet():
                self.fleet_1 = fleets[0].location
                self.fleet_2 = fleets[1].location
            else:
                self.fleet_1 = fleets[1].location
                self.fleet_2 = fleets[0].location
        else:
            if count == 0:
                logger.warning('No fleets detected. Checking fleet spawn points.')
            if count > 2:
                logger.warning('Too many fleets: %s. Re-checking all spawn points.' % str(fleets))
            queue = self.map.select(is_spawn_point=True)
            while queue:
                queue = queue.sort_by_camera_distance(self.camera)
                self.in_sight(queue[0], sight=(-1, 0, 1, 2))
                grid = self.convert_map_to_grid(queue[0])
                if grid.predict_current_fleet():
                    self.fleet_1 = grid.location
                elif grid.predict_fleet():
                    self.fleet_2 = grid.location
                queue = queue[1:]

        self.fleet_current_index = 1
        self.show_fleet()
        return self.fleet_current

    def map_init(self, map_):
        logger.hr('Map init')
        self.battle_count = 0
        self.mystery_count = 0
        self.siren_count = 0
        self.ammo_count = 3
        self.map = map_
        self.map.reset()
        self.ensure_edge_insight(preset=self.map.in_map_swipe_preset_data)
        self.full_scan(battle_count=self.battle_count, mystery_count=self.mystery_count, siren_count=self.siren_count)
        self.find_current_fleet()
        self.find_path_initial()

    @property
    def _expected_combat_end(self):
        for data in self.map.spawn_data:
            if data.get('battle') == self.battle_count and data.get('boss', 0):
                return 'in_stage'
            if data.get('battle') == self.battle_count + 1:
                if data.get('enemy', 0) > 0:
                    return 'with_searching'
                else:
                    return 'no_searching'

    def fleet_at(self, grid, fleet=None):
        """
        Args:
            grid (Grid):
            fleet (int): 1, 2

        Returns:
            bool: If fleet is at grid.
        """
        if fleet is None:
            return self.fleet_current == grid.location
        if fleet == 1:
            return self.fleet_1_location == grid.location
        else:
            return self.fleet_2_location == grid.location

    def check_accessibility(self, grid, fleet=None):
        """
        Args:
            grid (Grid):
            fleet (int): 1, 2

        Returns:
            bool: If accessible.
        """
        if fleet is None:
            return grid.is_accessible
        if fleet == self.fleet_current_index:
            return grid.is_accessible
        else:
            backup = self.fleet_current_index
            self.fleet_current_index = fleet
            self.find_path_initial()
            result = grid.is_accessible

            self.fleet_current_index = backup
            self.find_path_initial()
            return result

    def handle_boss_appear_refocus(self):
        """

        """
        appear = False
        for data in self.map.spawn_data:
            if data.get('battle') == self.battle_count and data.get('boss', 0):
                appear = True

        if appear:
            logger.info('Catch camera re-positioning after boss appear')
            camera = self.camera
            self.ensure_edge_insight()
            logger.info('Refocus to previous camera position.')
            self.focus_to(camera)
            return True
        else:
            return False
