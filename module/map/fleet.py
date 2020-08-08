import itertools

import numpy as np

from module.base.timer import Timer
from module.exception import MapWalkError, MapEnemyMoved
from module.handler.ambush import AmbushHandler
from module.logger import logger
from module.map.camera import Camera
from module.map.map_base import SelectedGrids
from module.map.map_base import location2node, location_ensure
from module.map.utils import match_movable
from module.map.map_operation import MapOperation


class Fleet(Camera, MapOperation, AmbushHandler):
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

    @property
    def fleet_boss(self):
        if self.config.FLEET_BOSS == 2 or self.config.FLEET_2:
            return self.fleet_2
        else:
            return self.fleet_1

    @property
    def fleet_boss_index(self):
        if self.config.FLEET_BOSS == 2 or self.config.FLEET_2:
            return 2
        else:
            return 1

    @property
    def fleet_step(self):
        if not self.config.MAP_HAS_FLEET_STEP:
            return 0
        if self.fleet_current_index == 2:
            return self.config.FLEET_2_STEP
        else:
            return self.config.FLEET_1_STEP

    def fleet_switch(self):
        self.fleet_switch_click()
        self.fleet_current_index = 1 if self.fleet_current_index == 2 else 2
        self.camera = self.fleet_current
        self.update()
        self.find_path_initial()
        self.map.show_cost()
        self.show_fleet()
        self.hp_get()
        self.handle_strategy(index=self.fleet_current_index)

    def switch_to(self):
        pass

    round = 0
    enemy_round = {}

    def round_next(self):
        """
        Call this method after fleet arrived.
        """
        if not self.config.MAP_HAS_MOVABLE_ENEMY:
            return False
        self.round += 1
        logger.info(f'Round: {self.round}, enemy_round: {self.enemy_round}')

    def round_battle(self):
        """
        Call this method after cleared an enemy.
        """
        if not self.config.MAP_HAS_MOVABLE_ENEMY:
            return False
        if not self.map.select(is_siren=True):
            self.enemy_round = {}
        try:
            data = self.map.spawn_data[self.battle_count]
        except IndexError:
            data = {}
        enemy = data.get('siren', 0)
        if enemy > 0:
            r = self.round
            self.enemy_round[r] = self.enemy_round.get(r, 0) + enemy

    def round_reset(self):
        """
        Call this method after entering map.
        """
        self.round = 0
        self.enemy_round = {}

    @property
    def round_is_new(self):
        """
        Usually, MOVABLE_ENEMY_TURN = 2.
        So a walk round is `player - player - enemy`, player moves twice, enemy moves once.

        Different sirens have different MOVABLE_ENEMY_TURN:
            2: Non-siren elite, SIREN_CL
            3: SIREN_CA

        Returns:
            bool: If it's a new walk round, which means enemies have moved.
        """
        if not self.config.MAP_HAS_MOVABLE_ENEMY:
            return False
        for enemy in self.enemy_round.keys():
            for turn in self.config.MOVABLE_ENEMY_TURN:
                if self.round - enemy > 0 and (self.round - enemy) % turn == 0:
                    return True

        return False

    @property
    def round_wait(self):
        """
        Returns:
            float: Seconds to wait enemies moving.
        """
        if not self.config.MAP_HAS_MOVABLE_ENEMY:
            return 0
        count = 0
        for enemy, c in self.enemy_round.items():
            for turn in self.config.MOVABLE_ENEMY_TURN:
                if self.round + 1 - enemy > 0 and (self.round + 1 - enemy) % turn == 0:
                    count += c
                    break

        return count * self.config.MAP_SIREN_MOVE_WAIT

    movable_before: SelectedGrids

    def _goto(self, location, expected=''):
        """Goto a grid directly and handle ambush, air raid, mystery picked up, combat.

        Args:
            location (tuple, str, GridInfo): Destination.
        """
        location = location_ensure(location)
        result_mystery = ''
        self.movable_before = self.map.select(is_siren=True)

        while 1:
            sight = self.map.camera_sight
            self.in_sight(location, sight=(sight[0], 0, sight[2], sight[3]))
            self.focus_to_grid_center()
            grid = self.convert_map_to_grid(location)

            self.ambush_color_initial()
            self.enemy_searching_color_initial()
            grid.__str__ = location
            result = 'nothing'
            self.device.click(grid)
            arrived = False
            # Wait to confirm fleet arrived. It does't appear immediately if fleet in combat .
            arrive_timer = Timer(0.5 + self.round_wait, count=2)
            arrive_unexpected_timer = Timer(1.5 + self.round_wait, count=6)
            # Wait after ambushed.
            ambushed_retry = Timer(0.5)
            # If nothing happens, click again.
            walk_timeout = Timer(20)
            walk_timeout.start()

            while 1:
                self.device.screenshot()
                grid.image = np.array(self.device.image)

                # Ambush
                if self.handle_ambush():
                    ambushed_retry.start()
                    walk_timeout.reset()

                # Mystery
                mystery = self.handle_mystery(button=grid)
                if mystery:
                    self.mystery_count += 1
                    result = 'mystery'
                    result_mystery = mystery

                # Combat
                if self.config.ENABLE_MAP_FLEET_LOCK and not self.is_in_map():
                    if self.handle_retirement():
                        self.map_offensive()
                        walk_timeout.reset()
                    if self.handle_combat_low_emotion():
                        walk_timeout.reset()
                if self.combat_appear():
                    self.combat(expected_end=self._expected_combat_end(expected), fleet_index=self.fleet_current_index)
                    self.hp_get()
                    if self.hp_withdraw_triggered():
                        self.withdraw()
                    arrived = True if not self.config.MAP_HAS_MOVABLE_ENEMY else False
                    result = 'combat'
                    self.battle_count += 1
                    self.fleet_ammo -= 1
                    if 'siren' in expected or (self.config.MAP_HAS_MOVABLE_ENEMY and not expected):
                        self.siren_count += 1
                    elif self.map[location].may_enemy:
                        self.map[location].is_cleared = True

                    self.handle_boss_appear_refocus()
                    grid = self.convert_map_to_grid(location)
                    walk_timeout.reset()

                # Cat attack animation
                if self.handle_map_cat_attack():
                    walk_timeout.reset()
                    continue

                if self.handle_walk_out_of_step():
                    raise MapWalkError('walk_out_of_step')

                # Arrive
                if self.is_in_map() and \
                        (grid.predict_fleet() or
                         (walk_timeout.reached() and grid.predict_current_fleet())):
                    if not arrive_timer.started():
                        logger.info(f'Arrive {location2node(location)}')
                    arrive_timer.start()
                    arrive_unexpected_timer.start()
                    if not arrive_timer.reached():
                        continue
                    if expected and result not in expected:
                        if arrive_unexpected_timer.reached():
                            logger.warning('Arrive with unexpected result')
                        else:
                            continue
                    logger.info(f'Arrive {location2node(location)} confirm. Result: {result}. Expected: {expected}')
                    arrived = True
                    break

                # End
                if ambushed_retry.started() and ambushed_retry.reached():
                    break
                if walk_timeout.reached():
                    logger.warning('Walk timeout. Retrying.')
                    self.ensure_edge_insight()
                    break

            # End
            if arrived:
                # Ammo grid needs to click again, otherwise the next click doesn't work.
                if self.map[location].may_ammo:
                    self.device.click(grid)
                break

        self.map[self.fleet_current].is_fleet = False
        self.map[location].wipe_out()
        self.map[location].is_fleet = True
        self.__setattr__('fleet_%s_location' % self.fleet_current_index, location)
        if result_mystery == 'get_carrier':
            self.full_scan_carrier()
        if result == 'combat':
            self.round_battle()
        self.round_next()
        if self.round_is_new:
            self.full_scan_movable(enemy_cleared=result == 'combat')
            self.find_path_initial()
            raise MapEnemyMoved
        self.find_path_initial()

    def goto(self, location, optimize=True, expected=''):
        # self.device.sleep(1000)
        location = location_ensure(location)
        if (self.config.MAP_HAS_AMBUSH or self.config.MAP_HAS_FLEET_STEP) and optimize:
            nodes = self.map.find_path(location, step=self.fleet_step)
            for node in nodes:
                try:
                    self._goto(node, expected=expected if node == nodes[-1] else '')
                except MapWalkError:
                    logger.warning('Map walk error.')
                    self.ensure_edge_insight()
                    nodes_ = self.map.find_path(node, step=1)
                    for node_ in nodes_:
                        self._goto(node_, expected=expected if node == nodes[-1] else '')
        else:
            self._goto(location, expected=expected)

    def find_path_initial(self):
        """
        Call this method after fleet moved or entered map.
        """
        if self.fleet_1_location:
            self.map[self.fleet_1_location].is_fleet = True
        if self.fleet_2_location:
            self.map[self.fleet_2_location].is_fleet = True
        location_dict = {}
        if self.config.FLEET_2:
            location_dict[2] = self.fleet_2_location
        location_dict[1] = self.fleet_1_location
        self.map.find_path_initial_multi_fleet(
            location_dict, current=self.fleet_current, has_ambush=self.config.MAP_HAS_AMBUSH)

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

    def full_scan(self, queue=None, must_scan=None, mode='normal'):
        super().full_scan(
            queue=queue, must_scan=must_scan, battle_count=self.battle_count, mystery_count=self.mystery_count,
            siren_count=self.siren_count, carrier_count=self.carrier_count, mode=mode)

        if self.config.FLEET_2 and not self.fleet_2_location:
            fleets = self.map.select(is_fleet=True, is_current_fleet=False)
            if fleets.count:
                logger.info(f'Predict fleet_2 to be {fleets[0]}')
                self.fleet_2_location = fleets[0].location

        for loca in [self.fleet_1_location, self.fleet_2_location]:
            if len(loca) and loca in self.map:
                grid = self.map[loca]
                if grid.may_boss and grid.is_caught_by_siren:
                    # Only boss appears on fleet's face
                    pass
                else:
                    self.map[loca].wipe_out()

    def full_scan_carrier(self):
        """
        Call this method if get enemy searching in mystery.
        """
        prev = self.map.select(is_enemy=True)
        self.full_scan(mode='carrier')
        diff = self.map.select(is_enemy=True).delete(prev)
        logger.info(f'Carrier spawn: {diff}')

    def full_scan_movable(self, enemy_cleared=True):
        """
        Call this method if enemy moved.

        Args:
            enemy_cleared (bool): True if cleared an enemy and need to scan spawn enemies.
                                  False if just a simple walk and only need to scan movable enemies.
        """
        before = self.movable_before
        for grid in before:
            grid.wipe_out()

        self.full_scan(queue=None if enemy_cleared else before, must_scan=before, mode='movable')

        after = self.map.select(is_siren=True)
        step = self.config.MOVABLE_ENEMY_FLEET_STEP
        matched_before, matched_after = match_movable(
            before=before.location,
            spawn=self.map.select(may_siren=True).location,
            after=after.location,
            fleets=[self.fleet_current] if enemy_cleared else [],
            fleet_step=step
        )
        matched_before = self.map.to_selected(matched_before)
        matched_after = self.map.to_selected(matched_after)
        logger.info(f'Movable enemy {before} -> {after}')
        logger.info(f'Tracked enemy {matched_before} -> {matched_after}')

        for grid in after.delete(matched_after):
            if not grid.may_siren:
                logger.warning(f'Wrong detection: {grid}')
                grid.wipe_out()

        diff = before.delete(matched_before)
        if diff:
            logger.info(f'Movable enemy tracking lost: {diff}')
            covered = self.map.grid_covered(self.map[self.fleet_current], location=[(0, -2)]) \
                .add(self.map.grid_covered(self.map[self.fleet_1_location], location=[(0, -1)])) \
                .add(self.map.grid_covered(self.map[self.fleet_2_location], location=[(0, -1)]))
            for grid in after:
                covered = covered.add(self.map.grid_covered(grid))
            accessible = SelectedGrids([])
            location = [(x, y) for x in range(step) for y in range(step) if abs(x) + abs(y) <= step]
            for grid in diff:
                accessible = accessible.add(self.map.grid_covered(grid, location=location))
            predict = accessible.intersect(covered).select(is_sea=True)
            logger.info(f'Movable enemy predict: {predict}')
            for grid in predict:
                grid.is_siren = True
                grid.is_enemy = True

        for grid in matched_after:
            if grid.location != self.fleet_current:
                grid.is_movable = True

    def find_all_fleets(self):
        logger.hr('Find all fleets')
        queue = self.map.select(is_spawn_point=True)
        while queue:
            queue = queue.sort_by_camera_distance(self.camera)
            self.in_sight(queue[0], sight=(-1, 0, 1, 2))
            grid = self.convert_map_to_grid(queue[0])
            if grid.predict_fleet():
                if grid.predict_current_fleet():
                    self.fleet_1 = queue[0].location
                else:
                    self.fleet_2 = queue[0].location
            queue = queue[1:]

    def find_current_fleet(self):
        logger.hr('Find current fleet')
        if not self.config.POOR_MAP_DATA:
            fleets = self.map.select(is_fleet=True, is_spawn_point=True)
        else:
            fleets = self.map.select(is_fleet=True)
        logger.info('Fleets: %s' % str(fleets))
        count = fleets.count
        if count == 1:
            if not self.config.FLEET_2:
                self.fleet_1 = fleets[0].location
            else:
                logger.info('Fleet_2 not detected.')
                if self.config.POOR_MAP_DATA and not self.map.select(is_spawn_point=True):
                    self.fleet_1 = fleets[0].location
                elif self.map.select(is_spawn_point=True).count == 2:
                    logger.info('Predict fleet to be spawn point')
                    another = self.map.select(is_spawn_point=True).delete(SelectedGrids([fleets[0]]))[0]
                    if fleets[0].is_current_fleet:
                        self.fleet_1 = fleets[0].location
                        self.fleet_2 = another.location
                    else:
                        self.fleet_1 = another.location
                        self.fleet_2 = fleets[0].location
                else:
                    cover = self.map.grid_covered(fleets[0], location=[(0, -1)])
                    if fleets[0].is_current_fleet and len(cover) and cover[0].is_spawn_point:
                        self.fleet_1 = fleets[0].location
                        self.fleet_2 = cover[0].location
                    else:
                        self.find_all_fleets()
        elif count == 2:
            current = self.map.select(is_current_fleet=True)
            if current.count == 1:
                self.fleet_1 = current[0].location
                self.fleet_2 = fleets.delete(current)[0].location
            else:
                fleets = fleets.sort_by_camera_distance(self.camera)
                self.in_sight(fleets[0], sight=(-1, 0, 1, 2))
                if self.convert_map_to_grid(fleets[0]).predict_current_fleet():
                    self.fleet_1 = fleets[0].location
                    self.fleet_2 = fleets[1].location
                else:
                    self.in_sight(fleets[1], sight=(-1, 0, 1, 2))
                    if self.convert_map_to_grid(fleets[1]).predict_current_fleet():
                        self.fleet_1 = fleets[1].location
                        self.fleet_2 = fleets[0].location
                    else:
                        logger.warning('Current fleet not found')
                        self.fleet_1 = fleets[0].location
                        self.fleet_2 = fleets[1].location
        else:
            if count == 0:
                logger.warning('No fleets detected.')
                fleets = self.map.select(is_current_fleet=True)
                if fleets.count:
                    self.fleet_1 = fleets[0].location
            if count > 2:
                logger.warning('Too many fleets: %s.' % str(fleets))
            self.find_all_fleets()

        self.fleet_current_index = 1
        self.show_fleet()
        return self.fleet_current

    def map_init(self, map_):
        logger.hr('Map init')
        self.fleet_1_location = ()
        self.fleet_2_location = ()
        self.fleet_current_index = 1
        self.battle_count = 0
        self.mystery_count = 0
        self.carrier_count = 0
        self.siren_count = 0
        self.ammo_count = 3
        self.map = map_
        self.map.reset()
        self.handle_map_green_config_cover()
        self.map.poor_map_data = self.config.POOR_MAP_DATA
        self.map.grid_connection_initial(wall=self.config.MAP_HAS_WALL)
        self.hp_init()
        self.handle_strategy(index=self.fleet_current_index)
        self.ensure_edge_insight(preset=self.map.in_map_swipe_preset_data)
        self.full_scan(must_scan=self.map.camera_data_spawn_point)
        self.find_current_fleet()
        self.find_path_initial()
        self.map.show_cost()
        self.round_reset()
        self.round_battle()

    def handle_map_green_config_cover(self):
        if not self.is_map_green:
            return False

        logger.info('Map is green sea.')

        if self.config.ENABLE_FAST_FORWARD:
            self.config.MAP_HAS_AMBUSH = False
            self.config.MAP_HAS_FLEET_STEP = False
            self.config.MAP_HAS_MOVABLE_ENEMY = False
        else:
            # When disable fast forward, MAP_HAS_AMBUSH depends on map settings.
            # self.config.MAP_HAS_AMBUSH = True
            pass
        if self.config.POOR_MAP_DATA and self.map.is_map_data_poor:
            self.config.POOR_MAP_DATA = False

        return True

    def _expected_combat_end(self, expected):
        for data in self.map.spawn_data:
            if data.get('battle') == self.battle_count and 'boss' in expected:
                return 'in_stage'
            if data.get('battle') == self.battle_count + 1:
                if data.get('enemy', 0) + data.get('siren', 0) + data.get('boss', 0) > 0:
                    return 'with_searching'
                else:
                    return 'no_searching'

        if 'boss' in expected:
            return 'in_stage'

        return None

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
            fleet (int, str): 1, 2, 'boss'

        Returns:
            bool: If accessible.
        """
        if fleet is None:
            return grid.is_accessible
        if isinstance(fleet, str) and fleet.isdigit():
            fleet = int(fleet)
        if fleet == 'boss':
            fleet = self.fleet_boss_index

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

    def brute_find_roadblocks(self, grid, fleet=None):
        """
        Args:
            grid (Grid):
            fleet (int): 1, 2. Default to current fleet.

        Returns:
            SelectedGrids:
        """
        if fleet is not None and fleet != self.fleet_current_index:
            backup = self.fleet_current_index
            self.fleet_current_index = fleet
            self.find_path_initial()
        else:
            backup = None

        if grid.is_accessible:
            if backup is not None:
                self.fleet_current_index = backup
                self.find_path_initial()
            return SelectedGrids([])

        enemies = self.map.select(is_enemy=True)
        logger.info(f'Potential enemy roadblocks: {enemies}')
        for repeat in range(1, enemies.count + 1):
            for select in itertools.product(enemies, repeat=repeat):
                for block in select:
                    block.is_enemy = False
                self.find_path_initial()
                for block in select:
                    block.is_enemy = True

                if grid.is_accessible:
                    select = SelectedGrids(list(select))
                    logger.info(f'Enemy roadblock: {select}')
                    if backup is not None:
                        self.fleet_current_index = backup
                        self.find_path_initial()
                    return select

        logger.warning('Enemy roadblock try exhausted.')

    def handle_boss_appear_refocus(self):
        """

        """
        appear = False
        for data in self.map.spawn_data:
            if data.get('battle') == self.battle_count and data.get('boss', 0):
                logger.info('Catch camera re-positioning after boss appear')
                appear = True

        # if self.config.POOR_MAP_DATA:
        #     self.device.screenshot()
        #     grids = Grids(self.device.image, config=self.config)
        #     grids.predict()
        #     grids.show()
        #     for grid in grids:
        #         if grid.is_boss:
        #             logger.info('Catch camera re-positioning after boss appear')
        #             appear = True
        #             for g in self.map:
        #                 g.wipe_out()
        #             break

        if appear:
            camera = self.camera
            self.ensure_edge_insight()
            logger.info('Refocus to previous camera position.')
            self.focus_to(camera)
            return True
        else:
            return False

    def fleet_checked_reset(self):
        self.map_fleet_checked = False
        self.fleet_1_formation_fixed = False
        self.fleet_2_formation_fixed = False
