import itertools

from module.base.timer import Timer
from module.exception import MapWalkError, MapEnemyMoved
from module.handler.ambush import AmbushHandler
from module.logger import logger
from module.map.camera import Camera
from module.map.map_base import SelectedGrids
from module.map.map_base import location2node, location_ensure
from module.map.utils import match_movable


class Fleet(Camera, AmbushHandler):
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
        if self.config.FLEET_2 and self.config.FLEET_BOSS == 2:
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

    @fleet_current.setter
    def fleet_current(self, value):
        if self.fleet_current_index == 2:
            self.fleet_2_location = value
        else:
            self.fleet_1_location = value

    @property
    def fleet_boss(self):
        if self.config.FLEET_BOSS == 2 and self.config.FLEET_2:
            return self.fleet_2
        else:
            return self.fleet_1

    @property
    def fleet_boss_index(self):
        if self.config.FLEET_BOSS == 2 and self.config.FLEET_2:
            return 2
        else:
            return 1

    @property
    def fleet_step(self):
        if not self.config.MAP_HAS_FLEET_STEP:
            return 0
        if self.fleet_current_index == 2:
            return self.config.Fleet_Fleet2Step
        else:
            return self.config.Fleet_Fleet1Step

    def fleet_switch(self):
        self.fleet_switch_click()
        self.fleet_current_index = 1 if self.fleet_current_index == 2 else 2
        self.camera = self.fleet_current
        self.update()
        self.find_path_initial()
        self.map.show_cost()
        self.show_fleet()
        self.hp_get()
        self.lv_get()
        self.handle_strategy(index=self.fleet_current_index)

    def switch_to(self):
        pass

    round = 0
    enemy_round = {}

    def round_next(self):
        """
        Call this method after fleet arrived.
        """
        if not self.config.MAP_HAS_MOVABLE_ENEMY and not self.config.MAP_HAS_MAZE:
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
            if self.config.MAP_HAS_MOVABLE_NORMAL_ENEMY:
                if not self.map.select(is_enemy=True):
                    self.enemy_round = {}
            else:
                self.enemy_round = {}
        try:
            data = self.map.spawn_data[self.battle_count]
        except IndexError:
            data = {}
        enemy = data.get('siren', 0)
        if self.config.MAP_HAS_MOVABLE_NORMAL_ENEMY:
            enemy += data.get('enemy', 0)
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
    def round_enemy_turn(self):
        """
        Returns:
            tuple[int]: Enemy moves once after player move X times.
                        It's a tuple because different enemy may have different X.
        """
        if self.config.MAP_HAS_MOVABLE_ENEMY:
            if self.config.MAP_HAS_MOVABLE_NORMAL_ENEMY:
                return tuple(set((list(self.config.MOVABLE_ENEMY_TURN) + list(self.config.MOVABLE_NORMAL_ENEMY_TURN))))
            else:
                return self.config.MOVABLE_ENEMY_TURN
        else:
            if self.config.MAP_HAS_MOVABLE_NORMAL_ENEMY:
                return self.config.MOVABLE_NORMAL_ENEMY_TURN
            else:
                return tuple()

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
            for turn in self.round_enemy_turn:
                if self.round - enemy > 0 and (self.round - enemy) % turn == 0:
                    return True

        return False

    @property
    def round_wait(self):
        """
        Returns:
            float: Seconds to wait enemies moving.
        """
        second = 0
        if self.config.MAP_HAS_MOVABLE_ENEMY:
            count = 0
            for enemy, c in self.enemy_round.items():
                for turn in self.round_enemy_turn:
                    if self.round + 1 - enemy > 0 and (self.round + 1 - enemy) % turn == 0:
                        count += c
                        break
            second += count * self.config.MAP_SIREN_MOVE_WAIT

        if self.config.MAP_HAS_MAZE:
            if (self.round + 1) % 3 == 0:
                second += 1.0

        return second

    @property
    def round_maze_changed(self):
        """
        Returns:
            bool: If maze changed at the start of this round.
        """
        if not self.config.MAP_HAS_MAZE:
            return False
        return self.round != 0 and self.round % 3 == 0

    def maze_active_on(self, grid):
        """
        Args:
            grid:

        Returns:
            bool: If maze wall is on a the specific grid.
        """
        if not self.config.MAP_HAS_MAZE:
            return False

        grid = self.map[location_ensure(grid)]
        if not grid.is_maze:
            return False
        return self.round % self.map.maze_round in grid.maze_round

    movable_before: SelectedGrids
    movable_before_normal: SelectedGrids

    @property
    def _walk_sight(self):
        sight = self.map.camera_sight
        return (sight[0], 0, sight[2], sight[3])

    def _goto(self, location, expected=''):
        """Goto a grid directly and handle ambush, air raid, mystery picked up, combat.

        Args:
            location (tuple, str, GridInfo): Destination.
            expected (str): Expected result on destination grid, such as 'combat', 'combat_siren', 'mystery'.
                Will give a waring if arrive with unexpected result.
        """
        location = location_ensure(location)
        result_mystery = ''
        self.movable_before = self.map.select(is_siren=True)
        self.movable_before_normal = self.map.select(is_enemy=True)
        if self.hp_retreat_triggered():
            self.withdraw()
        is_portal = self.map[location].is_portal

        while 1:
            self.in_sight(location, sight=self._walk_sight)
            self.focus_to_grid_center()
            grid = self.convert_global_to_local(location)

            self.ambush_color_initial()
            self.enemy_searching_color_initial()
            grid.__str__ = location
            result = 'nothing'

            self.device.click(grid)
            arrived = False
            # Wait to confirm fleet arrived. It does't appear immediately if fleet in combat.
            extra = 0
            if self.config.Submarine_Mode == 'hunt_only':
                extra += 4.5
            if self.config.MAP_HAS_LAND_BASED and grid.is_mechanism_trigger:
                extra += grid.mechanism_wait
            arrive_timer = Timer(0.5 + self.round_wait + extra, count=2)
            arrive_unexpected_timer = Timer(1.5 + self.round_wait + extra, count=6)
            # Wait after ambushed.
            ambushed_retry = Timer(0.5)
            # If nothing happens, click again.
            walk_timeout = Timer(20)
            walk_timeout.start()

            while 1:
                self.device.screenshot()
                self.view.update(image=self.device.image)
                if is_portal:
                    self.update()
                    grid = self.view[self.view.center_loca]

                # Combat
                if self.config.Campaign_UseFleetLock and not self.is_in_map():
                    if self.handle_retirement():
                        self.map_offensive()
                        walk_timeout.reset()
                    if self.handle_combat_low_emotion():
                        walk_timeout.reset()
                if self.combat_appear():
                    self.combat(expected_end=self._expected_combat_end(expected), fleet_index=self.fleet_current_index)
                    self.hp_get()
                    self.lv_get(after_battle=True)
                    arrived = True if not self.config.MAP_HAS_MOVABLE_ENEMY else False
                    result = 'combat'
                    self.battle_count += 1
                    self.fleet_ammo -= 1
                    if 'siren' in expected or (self.config.MAP_HAS_MOVABLE_ENEMY and not expected):
                        self.siren_count += 1
                    elif self.map[location].may_enemy:
                        self.map[location].is_cleared = True

                    self.handle_boss_appear_refocus()
                    if self.config.MAP_FOCUS_ENEMY_AFTER_BATTLE:
                        self.camera = location
                        self.update()
                    grid = self.convert_global_to_local(location)
                    walk_timeout.reset()

                # Ambush
                if self.handle_ambush():
                    self.hp_get()
                    self.lv_get(after_battle=True)
                    walk_timeout.reset()
                    self.view.update(image=self.device.image)
                    if not (grid.predict_fleet() and grid.predict_current_fleet()):
                        ambushed_retry.start()

                # Mystery
                mystery = self.handle_mystery(button=grid)
                if mystery:
                    self.mystery_count += 1
                    result = 'mystery'
                    result_mystery = mystery

                # Cat attack animation
                if self.handle_map_cat_attack():
                    walk_timeout.reset()
                    continue

                if self.handle_walk_out_of_step():
                    raise MapWalkError('walk_out_of_step')

                # Arrive
                if self.is_in_map() and (
                        grid.predict_fleet()
                        or (self.config.MAP_WALK_USE_CURRENT_FLEET and grid.predict_current_fleet())
                        or (walk_timeout.reached() and grid.predict_current_fleet())
                ):
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
                    if is_portal:
                        location = self.map[location].portal_link
                        self.camera = location
                    logger.info(f'Arrive {location2node(location)} confirm. Result: {result}. Expected: {expected}')
                    arrived = True
                    break

                # Story
                if expected == 'story':
                    if self.handle_story_skip():
                        result = 'story'
                        continue

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
        if self.round_maze_changed:
            self.find_path_initial()
            raise MapEnemyMoved
        self.find_path_initial()

    def goto(self, location, optimize=None, expected=''):
        """
        Args:
            location (tuple, str, GridInfo): Destination.
            optimize (bool): Optimize walk path, reducing ambushes.
                If None, loads MAP_WALK_OPTIMIZE
            expected (str): Expected result on destination grid, such as 'combat', 'combat_siren', 'mystery'.
                Will give a waring if arrive with unexpected result.
        """
        location = location_ensure(location)
        if optimize is None:
            optimize = self.config.MAP_WALK_OPTIMIZE

        # self.device.sleep(1000)
        if optimize and (self.config.MAP_HAS_AMBUSH or self.config.MAP_HAS_FLEET_STEP or self.config.MAP_HAS_PORTAL
                         or self.config.MAP_HAS_MAZE):
            nodes = self.map.find_path(location, step=self.fleet_step)
            for node in nodes:
                if self.maze_active_on(node):
                    logger.info(f'Maze is active on {location2node(node)}, bouncing to wait')
                    for _ in range(10):
                        grids = self.map[node].maze_nearby.delete(self.map.select(is_fleet=True))
                        if grids.select(is_enemy=False):
                            grids = grids.select(is_enemy=False)
                        grids = grids.sort('cost')
                        self._goto(grids[0], expected='')
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
        # Release fortress block
        if self.config.MAP_HAS_FORTRESS:
            if not self.map.select(is_fortress=True):
                self.map.select(is_mechanism_block=True).set(is_mechanism_block=False)
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
        if self.config.MAP_HAS_MOVABLE_NORMAL_ENEMY:
            if self.config.MAP_HAS_MOVABLE_ENEMY:
                for grid in self.movable_before:
                    grid.wipe_out()
                for grid in self.movable_before_normal:
                    grid.wipe_out()
                self.full_scan(mode='movable')
                self.track_movable(enemy_cleared=enemy_cleared, siren=True)
                self.track_movable(enemy_cleared=enemy_cleared, siren=False)
            else:
                for grid in self.movable_before_normal:
                    grid.wipe_out()
                self.full_scan(mode='movable')
                self.track_movable(enemy_cleared=enemy_cleared, siren=False)

        elif self.config.MAP_HAS_MOVABLE_ENEMY:
            for grid in self.movable_before:
                grid.wipe_out()
            self.full_scan(queue=None if enemy_cleared else self.movable_before,
                           must_scan=self.movable_before, mode='movable')
            self.track_movable(enemy_cleared=enemy_cleared, siren=True)

    def track_movable(self, enemy_cleared=True, siren=True):
        """
        Track enemy moving and predict missing enemies.

        Args:
            enemy_cleared (bool): True if cleared an enemy and need to scan spawn enemies.
                                  False if just a simple walk and only need to scan movable enemies.
            siren (bool): True if track sirens, false if track normal enemies
        """
        # Track siren moving
        before = self.movable_before if siren else self.movable_before_normal
        after = self.map.select(is_siren=True) if siren else self.map.select(is_enemy=True)
        step = self.config.MOVABLE_ENEMY_FLEET_STEP if siren else 1
        spawn = self.map.select(may_siren=True) if siren else self.map.select(may_enemy=True)
        matched_before, matched_after = match_movable(
            before=before.location,
            spawn=spawn.location,
            after=after.location,
            fleets=[self.fleet_current] if enemy_cleared else [],
            fleet_step=step
        )
        matched_before = self.map.to_selected(matched_before)
        matched_after = self.map.to_selected(matched_after)
        logger.info(f'Movable enemy {before} -> {after}')
        logger.info(f'Tracked enemy {matched_before} -> {matched_after}')

        # Delete wrong prediction
        for grid in after.delete(matched_after):
            if not grid.may_siren:
                logger.warning(f'Wrong detection: {grid}')
                grid.wipe_out()

        # Predict missing siren
        diff = before.delete(matched_before)
        _, missing = self.map.missing_get(
            self.battle_count, self.mystery_count, self.siren_count, self.carrier_count, mode='normal')
        missing = missing['siren'] if siren else missing['enemy']
        if diff and missing != 0:
            logger.warning(f'Movable enemy tracking lost: {diff}')
            covered = self.map.grid_covered(self.map[self.fleet_current], location=[(0, -2)])
            if self.fleet_1_location:
                covered = covered.add(self.map.grid_covered(self.map[self.fleet_1_location], location=[(0, -1)]))
            if self.fleet_2_location:
                covered = covered.add(self.map.grid_covered(self.map[self.fleet_2_location], location=[(0, -1)]))
            if siren:
                for grid in after:
                    covered = covered.add(self.map.grid_covered(grid))
            else:
                for grid in self.map.select(is_siren=True):
                    covered = covered.add(self.map.grid_covered(grid))
            logger.attr('enemy_covered', covered)
            accessible = SelectedGrids([])
            for grid in diff:
                self.map.find_path_initial(grid, has_ambush=False)
                accessible = accessible.add(self.map.select(cost=0)).add(self.map.select(cost=1))
                if siren:
                    accessible = accessible.add(self.map.select(cost=2))
            self.map.find_path_initial(self.fleet_current, has_ambush=self.config.MAP_HAS_AMBUSH)
            logger.attr('enemy_accessible', accessible)
            predict = accessible.intersect(covered).select(is_sea=True, is_fleet=False)
            logger.info(f'Movable enemy predict: {predict}')
            matched_after = matched_after.add(predict)
            for grid in predict:
                if siren:
                    grid.is_siren = True
                grid.is_enemy = True
        elif missing == 0:
            logger.info(f'Movable enemy tracking drop: {diff}')

        for grid in matched_after:
            if grid.location != self.fleet_current:
                grid.is_movable = True

    def find_all_fleets(self):
        logger.hr('Find all fleets')
        queue = self.map.select(is_spawn_point=True)
        while queue:
            queue = queue.sort_by_camera_distance(self.camera)
            self.in_sight(queue[0], sight=(-1, 0, 1, 2))
            grid = self.convert_global_to_local(queue[0])
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
                if self.convert_global_to_local(fleets[0]).predict_current_fleet():
                    self.fleet_1 = fleets[0].location
                    self.fleet_2 = fleets[1].location
                else:
                    self.in_sight(fleets[1], sight=(-1, 0, 1, 2))
                    if self.convert_global_to_local(fleets[1]).predict_current_fleet():
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
        """
        This method should be called after entering a map and before doing any operations.

        Args:
            map_ (CampaignMap):
        """
        logger.hr('Map init')
        self.map_data_init(map_)
        self.map_control_init()

    def map_data_init(self, map_):
        """
        Init map data according to settings and map status.
        Just data processing, no screenshots and clicks.

        Args:
            map_ (CampaignMap):
        """
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
        self.handle_clear_mode_config_cover()
        self.map.poor_map_data = self.config.POOR_MAP_DATA
        self.map.load_map_data(use_loop=self.map_is_clear_mode)
        self.map.load_spawn_data(use_loop=self.map_is_clear_mode)
        self.map.grid_connection_initial(
            wall=self.config.MAP_HAS_WALL,
            portal=self.config.MAP_HAS_PORTAL,
        )
        self.map.load_mechanism(
            land_based=self.config.MAP_HAS_LAND_BASED,
            maze=self.config.MAP_HAS_MAZE,
            fortress=self.config.MAP_HAS_FORTRESS
        )

    def map_control_init(self):
        """
        Preparation before operations.
        Such as select strategy, calculate hp and level, init camera position, do first map scan.
        """
        self.handle_strategy(index=1 if not self.fleets_reversed else 2)
        self.update()
        if self.handle_fleet_reverse():
            self.handle_strategy(index=1)
        self.hp_reset()
        self.hp_get()
        self.lv_reset()
        self.lv_get()
        self.ensure_edge_insight(preset=self.map.in_map_swipe_preset_data)
        self.full_scan(must_scan=self.map.camera_data_spawn_point)
        self.find_current_fleet()
        self.find_path_initial()
        self.map.show_cost()
        self.round_reset()
        self.round_battle()

    def handle_clear_mode_config_cover(self):
        if not self.map_is_clear_mode:
            return False

        if self.config.POOR_MAP_DATA and self.map.is_map_data_poor:
            self.config.POOR_MAP_DATA = False
        self.map.fortress_data = [(), ()]

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
