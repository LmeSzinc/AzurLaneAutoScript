import itertools
import re

from module.base.filter import Filter
from module.exception import MapEnemyMoved
from module.logger import logger
from module.map.fleet import Fleet
from module.map.map_grids import RoadGrids, SelectedGrids
from module.map_detection.grid_info import GridInfo

ENEMY_FILTER = Filter(regex=re.compile('^(.*?)$'), attr=('str',))


class Map(Fleet):
    def clear_chosen_enemy(self, grid, expected=''):
        """
        Args:
            grid (GridInfo):
            expected (str):

        Returns:
            int: If cleared an enemy.
        """
        logger.info('targetEnemyScale:%s' % (self.config.EnemyPriority_EnemyScaleBalanceWeight))
        logger.info('Clear enemy: %s' % grid)
        expected = f'combat_{expected}' if expected else 'combat'
        battle_count = self.battle_count
        self.show_fleet()
        if self.emotion.is_calculate and self.config.Campaign_UseFleetLock:
            self.emotion.wait(fleet_index=self.fleet_current_index)
        self.goto(grid, expected=expected)

        self.full_scan()
        self.find_path_initial()
        self.map.show_cost()
        return self.battle_count >= battle_count

    def clear_chosen_mystery(self, grid):
        """
        Args:
            grid (GridInfo):
        """
        logger.info('Clear mystery: %s' % grid)
        self.show_fleet()
        self.goto(grid, expected='mystery')
        # self.mystery_count += 1
        self.map.show_cost()

    def pick_up_ammo(self, grid=None):
        """
        Args:
            grid (GridInfo):
        """
        if grid is None:
            grid = self.map.select(may_ammo=True)
            if not grid:
                logger.info('Map has no ammo.')
                return False
            grid = grid[0]

        if self.ammo_count > 0 and grid.is_accessible:
            logger.info('Pick up ammo: %s' % grid)
            self.goto(grid, expected='')
            self.ensure_no_info_bar()

            # self.ammo_count -= 5 - self.battle_count
            recover = 5 - self.fleet_ammo
            recover = 3 if recover > 3 else recover
            logger.attr('Got ammo', recover)

            self.ammo_count -= recover
            self.fleet_ammo += recover

    def clear_mechanism(self, grids=None):
        """
        Args:
            grids (SelectedGrids): Grids that triggers mechanism. If None, select all mechanism triggers.

        Returns:
            bool: False, because didn't clear any enemy.
        """
        if not self.config.MAP_HAS_LAND_BASED:
            return False

        if not grids:
            grids = self.map.select(is_mechanism_trigger=True, is_mechanism_block=False)
        else:
            grids = grids.select(is_mechanism_trigger=True, is_mechanism_block=False)
        grids = self.select_grids(grids, is_accessible=True, sort=('weight', 'cost'))

        for grid in grids:
            logger.info(f'Clear mechanism: {grid}')
            self.goto(grid)
            self.map.show_cost()
            logger.info(f'Mechanism trigger release: {grid.mechanism_trigger}')
            logger.info(f'Mechanism block release: {grid.mechanism_block}')
            raise MapEnemyMoved

        logger.info('Mechanism all cleared')
        return False

    @staticmethod
    def select_grids(grids, nearby=False, is_accessible=True, scale=(), genre=(), strongest=False, weakest=False,
                     sort=('weight', 'cost'), ignore=None):
        """
        Args:
            grids (SelectedGrids):
            nearby (bool):
            is_accessible (bool):
            scale (tuple[int], list[int]): Tuple: select out of order, list: select in order.
            genre (tuple[str], list[str]): light, main, carrier, treasure. (Case insensitive).
            strongest (bool):
            weakest (bool):
            sort (tuple(str)):
            ignore (SelectedGrids):

        Returns:
            SelectedGrids:
        """
        if nearby:
            grids = grids.select(is_nearby=True)
        if is_accessible:
            grids = grids.select(is_accessible=True)
        if ignore is not None:
            grids = grids.delete(grids=ignore)
        if len(scale):
            enemy = SelectedGrids([])
            for enemy_scale in scale:
                enemy = enemy.add(grids.select(enemy_scale=enemy_scale))
                if isinstance(scale, list) and enemy:
                    break
            grids = enemy
        if len(genre):
            enemy = SelectedGrids([])
            for enemy_genre in genre:
                # enemy_genre should be camel case
                enemy_genre = enemy_genre[0].upper() + enemy_genre[1:] if enemy_genre[0].islower() else enemy_genre
                enemy = enemy.add(grids.select(enemy_genre=enemy_genre))
                if isinstance(genre, list) and enemy:
                    break
            grids = enemy
        if strongest:
            for scale in [3, 2, 1, 0]:
                enemy = grids.select(enemy_scale=scale)
                if enemy:
                    grids = enemy
                    break
        if weakest:
            for scale in [1, 2, 3, 0]:
                enemy = grids.select(enemy_scale=scale)
                if enemy:
                    grids = enemy
                    break

        if grids:
            grids = grids.sort(*sort)

        return grids

    @staticmethod
    def show_select_grids(grids, **kwargs):
        length = 3
        keys = list(kwargs.keys())
        for index in range(0, len(keys), length):
            text = [f'{key}={kwargs[key]}' for key in keys[index:index + length]]
            text = ', '.join(text)
            logger.info(text)

        logger.info(f'Grids: {grids}')

    def clear_all_mystery(self, **kwargs):
        """Methods to pick up all mystery.

        Returns:
            bool: False, because didn't clear any enemy.
        """
        kwargs['sort'] = ('cost',)
        while 1:
            grids = self.map.select(is_mystery=True)
            grids = self.select_grids(grids, **kwargs)

            if not grids:
                break

            logger.hr('Clear all mystery')
            self.show_select_grids(grids, **kwargs)
            self.clear_chosen_mystery(grids[0])

        return False

    def clear_enemy(self, **kwargs):
        """Methods to clear a enemy. May not do anything if no suitable enemy.

        Returns:
            bool: True if clear an enemy.
        """
        grids = self.map.select(is_enemy=True, is_boss=False)

        target = self.config.EnemyPriority_EnemyScaleBalanceWeight
        if target == 'S3_enemy_first':
            kwargs['strongest'] = True
        elif target == 'S1_enemy_first':
            kwargs['weakest'] = True
        elif self.config.MAP_CLEAR_ALL_THIS_TIME:
            kwargs['strongest'] = True
        grids = self.select_grids(grids, **kwargs)

        if grids:
            logger.hr('Clear enemy')
            self.show_select_grids(grids, **kwargs)
            self.clear_chosen_enemy(grids[0])
            return True

        return False

    def clear_roadblocks(self, roads, **kwargs):
        """Clear roadblocks.

        Args:
            roads(list[RoadGrids]):

        Returns:
            bool: True if clear an enemy.
        """
        grids = SelectedGrids([])
        for road in roads:
            grids = grids.add(road.roadblocks())

        target = self.config.EnemyPriority_EnemyScaleBalanceWeight
        if target == 'S3_enemy_first':
            kwargs['strongest'] = True
        elif target == 'S1_enemy_first':
            kwargs['weakest'] = True
        elif self.config.MAP_CLEAR_ALL_THIS_TIME:
            kwargs['strongest'] = True
        grids = self.select_grids(grids, **kwargs)

        if grids:
            logger.hr('Clear roadblock')
            self.show_select_grids(grids, **kwargs)
            self.clear_chosen_enemy(grids[0])
            return True

        return False

    def clear_potential_roadblocks(self, roads, **kwargs):
        """Avoid roadblock that only has one grid empty.

        Args:
            roads(list[RoadGrids]):

        Returns:
            bool: True if clear an enemy.
        """
        grids = SelectedGrids([])
        for road in roads:
            grids = grids.add(road.potential_roadblocks())

        target = self.config.EnemyPriority_EnemyScaleBalanceWeight
        if target == 'S3_enemy_first':
            kwargs['strongest'] = True
        elif target == 'S1_enemy_first':
            kwargs['weakest'] = True
        elif self.config.MAP_CLEAR_ALL_THIS_TIME:
            kwargs['strongest'] = True
        grids = self.select_grids(grids, **kwargs)

        if grids:
            logger.hr('Avoid potential roadblock')
            self.show_select_grids(grids, **kwargs)
            self.clear_chosen_enemy(grids[0])
            return True

        return False

    def clear_first_roadblocks(self, roads, **kwargs):
        """Ensure every roadblocks have one grid with is_cleared=True.

        Args:
            roads(list[RoadGrids]):

        Returns:
            bool: True if clear an enemy.
        """
        grids = SelectedGrids([])
        for road in roads:
            grids = grids.add(road.first_roadblocks())

        grids = self.select_grids(grids, **kwargs)

        if grids:
            logger.hr('Clear first roadblock')
            self.show_select_grids(grids, **kwargs)
            self.clear_chosen_enemy(grids[0])
            return True

        return False

    def clear_grids_for_faster(self, grids, **kwargs):
        """Clear some grids to walk a shorter distance.

        Args:
            grids(SelectedGrids):

        Returns:
            bool: True if clear an enemy.
        """

        grids = grids.select(is_enemy=True)
        grids = self.select_grids(grids, **kwargs)

        if grids:
            logger.hr('Clear grids for faster')
            self.show_select_grids(grids, **kwargs)
            self.clear_chosen_enemy(grids[0])
            return True

        return False

    def clear_boss(self):
        """This method is deprecated, although it works well in simple map.
        In a complex map, brute_clear_boss is recommended.

        Returns:
            bool:
        """
        grids = self.map.select(is_boss=True, is_accessible=True)
        grids = grids.add(self.map.select(may_boss=True, is_caught_by_siren=True))
        logger.info('Is boss: %s' % grids)
        if not grids.count:
            grids = grids.add(self.map.select(may_boss=True, is_enemy=True, is_accessible=True))
            logger.warning('Boss not detected, using may_boss grids.')
            logger.info('May boss: %s' % self.map.select(may_boss=True))
            logger.info('May boss and is enemy: %s' % self.map.select(may_boss=True, is_enemy=True))

        if grids:
            self.submarine_move_near_boss(grids[0])
            logger.hr('Clear BOSS')
            grids = grids.sort('weight', 'cost')
            logger.info('Grids: %s' % str(grids))
            self.clear_chosen_enemy(grids[0], expected='boss')

        logger.warning('BOSS not detected, trying all boss spawn point.')
        return self.clear_potential_boss()

    def capture_clear_boss(self):
        """This method is deprecated, although it works well in simple map.
        In a complex map, brute_clear_boss is recommended.
        Note: Lazy method to handle with grand capture map

        Returns:
            bool:
        """

        grids = self.map.select(is_boss=True, is_accessible=True)
        grids = grids.add(self.map.select(may_boss=True, is_caught_by_siren=True))
        logger.info('Is boss: %s' % grids)
        if not grids.count:
            grids = grids.add(self.map.select(may_boss=True, is_enemy=True, is_accessible=True))
            logger.warning('Boss not detected, using may_boss grids.')
            logger.info('May boss: %s' % self.map.select(may_boss=True))
            logger.info('May boss and is enemy: %s' % self.map.select(may_boss=True, is_enemy=True))

        if grids:
            logger.hr('Clear BOSS')
            grids = grids.sort('weight', 'cost')
            logger.info('Grids: %s' % str(grids))
            self.clear_chosen_enemy(grids[0])

        logger.warning('Grand Capture detected, Withdrawing.')
        self.withdraw()

    def clear_potential_boss(self):
        """
        Method to step on all boss spawn point when boss not detected.
        """
        grids = self.map.select(may_boss=True, is_accessible=True).sort('weight', 'cost')
        logger.info('May boss: %s' % grids)
        battle_count = self.battle_count

        for grid in grids:
            logger.hr('Clear potential BOSS')
            grids = grids.sort('weight', 'cost')
            logger.info('Grid: %s' % str(grid))
            self.fleet_boss.clear_chosen_enemy(grid)
            if self.battle_count > battle_count:
                logger.info('Boss guessing correct.')
                return True
            else:
                logger.info('Boss guessing incorrect.')

        grids = self.map.select(may_boss=True, is_accessible=False).sort('weight', 'cost')
        logger.info('May boss: %s' % grids)

        for grid in grids:
            logger.hr('Clear potential BOSS roadblocks')
            roadblocks = self.brute_find_roadblocks(grid, fleet=self.fleet_boss_index)
            roadblocks = roadblocks.sort('weight', 'cost')
            logger.info('Grids: %s' % str(roadblocks))
            self.fleet_1.clear_chosen_enemy(roadblocks[0])
            return True

        return False

    def brute_clear_boss(self):
        """
        Method to clear boss, using brute-force to find roadblocks.
        Note: This method will use 2 fleets.
        """
        boss = self.map.select(is_boss=True)
        if boss:
            logger.info('Brute clear BOSS')
            grids = self.brute_find_roadblocks(boss[0], fleet=self.fleet_boss_index)
            if grids:
                if self.brute_fleet_meet():
                    return True
                logger.info('Brute clear BOSS roadblocks')
                grids = grids.sort('weight', 'cost')
                logger.info('Grids: %s' % str(grids))
                self.clear_chosen_enemy(grids[0])
                return True
            else:
                return self.fleet_boss.clear_boss()
        elif self.map.select(may_boss=True, is_caught_by_siren=True):
            logger.info('BOSS appear on fleet grid')
            self.fleet_2.switch_to()
            return self.clear_chosen_enemy(self.map.select(may_boss=True, is_caught_by_siren=True)[0])
        else:
            logger.warning('BOSS not detected, trying all boss spawn point.')
            return self.clear_potential_boss()

    def brute_fleet_meet(self):
        """
        Method to clear roadblocks between fleets, using brute-force to find roadblocks.
        """
        if self.fleet_boss_index != 2 or not self.fleet_2_location:
            return False
        grids = self.brute_find_roadblocks(self.map[self.fleet_2_location], fleet=1)
        if grids:
            logger.info('Brute clear roadblocks between fleets.')
            grids = grids.sort('weight', 'cost')
            logger.info('Grids: %s' % str(grids))
            self.clear_chosen_enemy(grids[0])
            return True
        else:
            return False

    def clear_siren(self, **kwargs):
        """
        Returns:
            bool: True if clear an enemy.
        """
        if not self.config.MAP_HAS_SIREN and not self.config.MAP_HAS_FORTRESS:
            return False

        if self.config.FLEET_2:
            kwargs['sort'] = ('weight', 'cost_2')
        grids = self.map.select(is_siren=True)
        if self.config.MAP_HAS_FORTRESS:
            grids = grids.add(self.map.select(is_fortress=True))
        grids = self.select_grids(grids, **kwargs)

        if grids:
            logger.hr('Clear siren')
            self.show_select_grids(grids, **kwargs)
            if grids[0].is_fortress:
                expected = 'fortress'
            else:
                expected = 'siren'
            self.clear_chosen_enemy(grids[0], expected=expected)
            return True

        return False

    def clear_any_enemy(self, **kwargs):
        """
        Returns:
            bool: True if clear an enemy.
        """
        grids = self.map.select(is_enemy=True, is_boss=False)

        if self.config.MAP_HAS_SIREN:
            grids = grids.add(self.map.select(is_siren=True))
        if self.config.MAP_HAS_FORTRESS:
            grids = grids.add(self.map.select(is_fortress=True))

        grids = self.select_grids(grids, **kwargs)

        if grids:
            logger.hr('Clear enemy')
            self.show_select_grids(grids, **kwargs)
            grid = grids[0]
            if grid.is_fortress:
                expected = 'fortress'
            elif grid.is_siren:
                expected = 'siren'
            else:
                expected = ''
            self.clear_chosen_enemy(grid, expected=expected)
            return True

        return False

    def fleet_2_step_on(self, grids, roadblocks):
        """Fleet step on a grid which can reduce the ambush frequency another fleet.
        Of course, you can simply use 'self.fleet_2.goto(grid)' and do the same thing.
        However, roads can be block by enemy and this method can handle that.

        Args:
            grids (SelectedGrids):
            roadblocks (list[RoadGrids]):

        Returns:
            bool: if clear an enemy.
        """
        if not self.config.FLEET_2:
            return False
        for grid in grids:
            if self.fleet_at(grid=grid, fleet=2):
                return False
        # if grids.count == len([grid for grid in grids if grid.is_enemy or grid.is_cleared]):
        #     logger.info('Fleet 2 step on, no need')
        #     return False
        all_cleared = grids.select(is_cleared=True).count == grids.count

        logger.info('Fleet 2 step on')
        for grid in grids:
            if grid.is_enemy or (not all_cleared and grid.is_cleared):
                continue
            if self.check_accessibility(grid=grid, fleet=2):
                logger.info('Fleet_2 step on %s' % grid)
                self.fleet_2.goto(grid)
                self.fleet_1.switch_to()
                return False

        logger.info('Fleet_2 step on got roadblocks.')
        clear = self.fleet_1.clear_roadblocks(roadblocks)
        self.fleet_1.clear_all_mystery()
        return clear

    def fleet_2_break_siren_caught(self):
        if self.fleet_boss_index != 2:
            return False
        if not self.config.MAP_HAS_SIREN or not self.config.MAP_HAS_MOVABLE_ENEMY:
            return False
        if not self.map.select(is_caught_by_siren=True):
            logger.info('No fleet caught by siren.')
            return False
        if not self.fleet_2_location or not self.map[self.fleet_2_location].is_caught_by_siren:
            logger.warning('Appear caught by siren, but not fleet_2.')
            for grid in self.map:
                grid.is_caught_by_siren = False
            return False

        logger.info(f'Break siren caught, fleet_2: {self.fleet_2_location}')
        self.fleet_2.switch_to()
        self.ensure_edge_insight()
        self.clear_chosen_enemy(self.map[self.fleet_2_location])
        self.fleet_1.switch_to()
        for grid in self.map:
            grid.is_caught_by_siren = False
        return True

    def fleet_2_push_forward(self):
        """Move fleet 2 to the grid with lower grid.weight
        This will reduce the possibility of Boss fleet get stuck by enemies, especially for those one-way-road map
        from chapter 7 to chapter 9.

        Know more (in Chinese simplified):
        9章道中战最小化路线规划 (Route Planning for battle minimization in chapter 9)
        https://wiki.biligame.com/blhx/9%E7%AB%A0%E9%81%93%E4%B8%AD%E6%88%98%E6%9C%80%E5%B0%8F%E5%8C%96%E8%B7%AF%E7%BA%BF%E8%A7%84%E5%88%92

        Returns:
            bool: If pushed forward.
        """
        if self.fleet_boss_index != 2:
            return False

        logger.info('Fleet_2 push forward')
        grids = self.map.select(is_land=False).sort('weight', 'cost')
        if self.map[self.fleet_2_location].weight <= grids[0].weight:
            logger.info('Fleet_2 pushed to destination')
            self.fleet_1.switch_to()
            return False

        fleets = SelectedGrids([self.map[self.fleet_1_location], self.map[self.fleet_2_location]])
        grids = grids.select(is_accessible_2=True, is_sea=True).delete(fleets)
        if not grids:
            logger.info('Fleet_2 has no where to push')
            return False
        if self.map[self.fleet_2_location].weight <= grids[0].weight:
            logger.info('Fleet_2 pushed to closest grid')
            return False

        logger.info(f'Grids: {grids}')
        logger.info(f'Push forward: {grids[0]}')
        self.fleet_2.goto(grids[0])
        self.fleet_1.switch_to()
        return True

    def fleet_2_rescue(self, grid):
        """Use mob fleet to rescue boss fleet.

        Args:
            grid (GridInfo): Destination. Usually to be boss spawn grid.

        Returns:
            bool: If clear an enemy.
        """
        if self.fleet_boss_index != 2:
            return False

        grids = self.brute_find_roadblocks(grid, fleet=2)
        if not grids:
            return False
        logger.info('Fleet_2 rescue')
        grids = self.select_grids(grids)
        if not grids:
            return False

        self.clear_chosen_enemy(grids[0])
        return True

    def fleet_2_protect(self):
        """
        Mob fleet moves around boss fleet, clear any approaching sirens.

        Returns:
            bool: If clear an enemy.
        """
        if not self.config.FLEET_2 or not self.config.MAP_HAS_MOVABLE_ENEMY:
            return False

        # When having 2 fleet
        for n in range(20):
            if not self.map.select(is_siren=True):
                return False

            nearby = self.map.select(cost_2=1).add(self.map.select(cost_2=2))
            approaching = nearby.select(is_siren=True)
            if approaching:
                grids = self.select_grids(approaching, sort=('cost_2', 'cost_1'))
                self.clear_chosen_enemy(grids[0], expected='siren')
                return True
            else:
                grids = nearby.delete(self.map.select(is_fleet=True))
                grids = self.select_grids(grids, sort=('cost_2', 'cost_1'))
                self.goto(grids[0])
                continue

        logger.warning('fleet_2_protect no siren approaching')
        return False

    def clear_filter_enemy(self, string, preserve=0):
        """
        If EnemyPriority_EnemyScaleBalanceWeight != default_mode, enemy filter is ignored
        If MAP_HAS_MOVABLE_NORMAL_ENEMY, enemy filter is ignored

        Args:
            string (str): Filter to select enemies, from easy to hard
            preserve (int): Preserve several easiest enemies for battle without ammo.
                When run out of ammo, use 0 to clear those preserved enemies.

        Returns:
            bool: If clear an enemy.
        """
        if self.config.MAP_HAS_MOVABLE_NORMAL_ENEMY:
            if self.clear_any_enemy(sort=('cost_2',)):
                return True
            return False

        if self.config.EnemyPriority_EnemyScaleBalanceWeight == 'S3_enemy_first':
            string = '3L > 3M > 3E > 3C > 2L > 2M > 2E > 2C > 1L > 1M > 1E > 1C'
            preserve = 0
        elif self.config.EnemyPriority_EnemyScaleBalanceWeight == 'S1_enemy_first':
            string = '1L > 1M > 1E > 1C > 2L > 2M > 2E > 2C > 3L > 3M > 3E > 3C'

        ENEMY_FILTER.load(string)
        grids = self.map.select(is_enemy=True, is_accessible=True)
        if not grids:
            return False

        grids = ENEMY_FILTER.apply(grids.sort('weight', 'cost').grids)
        logger.info(f'Filter enemy: {grids}, preserve={preserve}')
        if preserve:
            grids = grids[preserve:]

        if grids:
            logger.hr('Clear filter enemy')
            self.clear_chosen_enemy(grids[0])
            return True

        return False

    def clear_bouncing_enemy(self):
        """
        Clear enemies which are bouncing in a fixed route.
        This method will be disabled once it cleared an enemy, since there's only one bouncing enemy on the map.

        Args:
            route (tuple[GridInfo]):

        Returns:
            bool: If cleared an enemy.
        """
        if not self.config.MAP_HAS_BOUNCING_ENEMY:
            return False

        route = None
        for a_route in self.map.bouncing_enemy_data:
            if a_route.select(may_bouncing_enemy=True, is_accessible=True):
                route = a_route
                break
        if route is None:
            return False

        logger.hr('Clear bouncing enemy')
        logger.info(f'Clear bouncing enemy: {route}')
        self.show_fleet()
        prev = self.battle_count
        for n, grid in enumerate(itertools.cycle(route)):
            if self.emotion.is_calculate and self.config.Campaign_UseFleetLock:
                self.emotion.wait(fleet_index=self.fleet_current_index)
            self.goto(grid, expected='combat_nothing')

            if self.battle_count > prev:
                logger.info('Cleared an bouncing enemy')
                route.select(may_bouncing_enemy=True).set(may_bouncing_enemy=False)
                self.full_scan()
                self.find_path_initial()
                self.map.show_cost()
                return True
            if n >= 12:
                logger.warning('Failed to clear bouncing enemy after 12 trial')
                return False

        return False
