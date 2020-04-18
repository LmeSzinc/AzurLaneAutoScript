from module.logger import logger
from module.map.exception import CampaignEnd
from module.map.fleet import Fleet
from module.map.grid_info import GridInfo
from module.map.map_grids import SelectedGrids, RoadGrids


class Map(Fleet):
    def clear_chosen_enemy(self, grid, expected=''):
        """
        Args:
            grid (GridInfo):
            expected (str):
        """
        logger.info('Clear enemy: %s' % grid)
        expected = f'combat_{expected}' if expected else 'combat'
        self.show_fleet()
        if self.config.ENABLE_EMOTION_REDUCE and self.config.ENABLE_MAP_FLEET_LOCK:
            self.emotion.wait(fleet=self.fleet_current_index)
        self.goto(grid, expected=expected)

        self.full_scan(battle_count=self.battle_count, mystery_count=self.mystery_count, siren_count=self.siren_count,
                       carrier_count=self.carrier_count)
        self.find_path_initial()
        self.map.show_cost()

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
                logger.info('Ammo not found')
                return False
            grid = grid[0]

        if self.ammo_count > 0:
            logger.info('Pick up ammo: %s' % grid)
            self.goto(grid, expected='')
            self.ensure_no_info_bar()

            # self.ammo_count -= 5 - self.battle_count
            recover = 5 - self.fleet_ammo
            recover = 3 if recover > 3 else recover
            logger.attr('Got ammo', recover)

            self.ammo_count -= recover
            self.fleet_ammo += recover

    @staticmethod
    def select_grids(grids, nearby=False, is_accessible=True, scale=(), strongest=False, weakest=False, cost=True,
                     weight=True, ignore=None):
        """
        Args:
            grids (SelectedGrids):
            nearby (bool):
            is_accessible (bool):
            scale (tuple[int]):
            strongest (bool):
            weakest (bool):
            cost (bool):
            weight (bool):
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
            grids = grids.sort(cost=cost, weight=weight)

        return grids

    @staticmethod
    def show_select_grids(grids, **kwargs):
        length = 3
        keys = list(kwargs.keys())
        for index in range(0, len(keys), length):
            text = ''
            for key in keys[index:index + length]:
                text += f'{key}={kwargs[key]}'
            logger.info(text)

        logger.info(f'Grids: {grids}')

    def clear_all_mystery(self, **kwargs):
        """Methods to pick up all mystery.

        Returns:
            bool: False, because didn't clear any enemy.
        """
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

        grids = self.select_grids(grids, **kwargs)

        if grids:
            logger.hr('Avoid potential roadblock')
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
        """Clear BOSS.

        Returns:
            bool:
        """
        grids = self.map.select(is_boss=True, is_accessible=True)
        grids = grids.add(self.map.select(may_boss=True, is_enemy=True, is_accessible=True))
        logger.info('May boss: %s' % self.map.select(may_boss=True))
        logger.info('May boss and is enemy: %s' % self.map.select(may_boss=True, is_enemy=True))
        logger.info('Is boss: %s' % self.map.select(is_boss=True))

        if grids:
            logger.hr('Clear BOSS')
            grids = grids.sort(cost=True, weight=True)
            logger.info('Grids: %s' % str(grids))
            self.clear_chosen_enemy(grids[0], expected='boss')
            raise CampaignEnd('BOSS Clear.')

        logger.warning('BOSS not detected, trying all boss spawn point.')
        self.clear_potential_boss()

        return False

    def clear_potential_boss(self):
        """
        Method to step on all boss spawn point when boss not detected.
        """
        grids = self.map.select(may_boss=True, is_accessible=True)
        logger.info('May boss: %s' % self.map.select(may_boss=True))
        battle_count = self.battle_count

        for grid in grids:
            logger.hr('Clear BOSS')
            grids = grids.sort(cost=True, weight=True)
            logger.info('Grid: %s' % str(grid))
            self.clear_chosen_enemy(grid, expected='boss')
            if self.battle_count - battle_count > 0:
                raise CampaignEnd('BOSS Clear.')
            else:
                logger.info('Boss guessing incorrect.')

    def clear_siren(self, **kwargs):
        """
        Returns:
            bool: True if clear an enemy.
        """
        grids = self.map.select(may_siren=True, is_enemy=True)
        grids = grids.add(self.map.select(may_siren=True, is_siren=True))
        logger.info('May siren: %s' % self.map.select(may_siren=True))
        logger.info('May siren and is enemy: %s' % self.map.select(may_siren=True, is_enemy=True))
        logger.info('Is siren: %s' % self.map.select(is_siren=True))

        grids = self.select_grids(grids, **kwargs)

        if grids:
            logger.hr('Clear siren')
            self.show_select_grids(grids, **kwargs)
            self.clear_chosen_enemy(grids[0], expected='siren')
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
        for grid in grids:
            if self.fleet_at(grid=grid, fleet=2):
                return False

        logger.info('Fleet 2 step on')
        for grid in grids:
            if grid.is_enemy or grid.is_cleared:
                continue
            if self.check_accessibility(grid=grid, fleet=2):
                logger.info('Fleet_2 step on %s' % grid)
                self.fleet_2.goto(grid)
                self.fleet_1.switch_to()
                return False

        logger.info('Fleet_2 step on %s got roadblocks.')
        self.fleet_1.clear_roadblocks(roadblocks)
        self.fleet_1.clear_all_mystery()
        return True
