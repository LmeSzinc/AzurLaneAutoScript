import copy

from module.base.utils import location2node, node2location
from module.logger import logger
from module.map.map_grids import SelectedGrids
from module.map.utils import *
from module.map_detection.grid_info import GridInfo


class CampaignMap:
    def __init__(self, name=None):
        self.name = name
        self.grid_class = GridInfo
        self.grids = {}
        self._shape = (0, 0)
        self._map_data = ''
        self._map_data_loop = ''
        self._weight_data = ''
        self._wall_data = ''
        self._portal_data = []
        self._land_based_data = []
        self._maze_data = []
        self.maze_round = 9
        self._fortress_data = [(), ()]
        self._bouncing_enemy_data = []
        self._spawn_data = []
        self._spawn_data_stack = []
        self._spawn_data_loop = []
        self._spawn_data_use_loop = False
        self._camera_data = []
        self._camera_data_spawn_point = []
        self._map_covered = SelectedGrids([])
        self._ignore_prediction = []
        self.in_map_swipe_preset_data = None
        self.poor_map_data = False
        self.camera_sight = (-3, -1, 3, 2)
        self.grid_connection = {}

    def __iter__(self):
        return iter(self.grids.values())

    def __getitem__(self, item):
        """
        Args:
            item:

        Returns:
            GridInfo:
        """
        return self.grids[tuple(item)]

    def __contains__(self, item):
        return tuple(item) in self.grids

    @staticmethod
    def _parse_text(text):
        text = text.strip()
        for y, row in enumerate(text.split('\n')):
            row = row.strip()
            for x, data in enumerate(row.split(' ')):
                yield (x, y), data

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, scale):
        self._shape = node2location(scale.upper())
        for y in range(self._shape[1] + 1):
            for x in range(self._shape[0] + 1):
                grid = self.grid_class()
                grid.location = (x, y)
                self.grids[(x, y)] = grid

        # camera_data can be generate automatically, but it's better to set it manually.
        self.camera_data = [location2node(loca) for loca in camera_2d((0, 0, *self._shape), sight=self.camera_sight)]
        self.camera_data_spawn_point = []
        # weight_data set to 10.
        for grid in self:
            grid.weight = 10.

    @property
    def map_data(self):
        return self._map_data

    @map_data.setter
    def map_data(self, text):
        self._map_data = text
        self._load_map_data(text)

    @property
    def map_data_loop(self):
        return self._map_data_loop

    @map_data_loop.setter
    def map_data_loop(self, text):
        self._map_data_loop = text

    def load_map_data(self, use_loop=False):
        """
        Args:
            use_loop (bool): If at clearing mode.
                             clearing mode (Correct name) == fast forward (in old Alas) == loop (in lua files)
        """
        has_loop = bool(len(self.map_data_loop))
        logger.info(f'Load map_data, has_loop={has_loop}, use_loop={use_loop}')
        if has_loop and use_loop:
            self._load_map_data(self.map_data_loop)
        else:
            self._load_map_data(self.map_data)

    def _load_map_data(self, text):
        if not len(self.grids.keys()):
            grids = np.array([loca for loca, _ in self._parse_text(text)])
            self.shape = location2node(tuple(np.max(grids, axis=0)))

        for loca, data in self._parse_text(text):
            self.grids[loca].decode(data)

    @property
    def wall_data(self):
        return self._wall_data

    @wall_data.setter
    def wall_data(self, text):
        self._wall_data = text

    @property
    def portal_data(self):
        return self._portal_data

    @portal_data.setter
    def portal_data(self, portal_list):
        """
        Args:
            portal_list (list[tuple]): [(start, end),]
        """
        for nodes in portal_list:
            node1, node2 = location_ensure(nodes[0]), location_ensure(nodes[1])
            self._portal_data.append((node1, node2))
            self[node1].is_portal = True

    @property
    def land_based_data(self):
        return self._land_based_data

    @land_based_data.setter
    def land_based_data(self, data):
        self._land_based_data = data

    def _load_land_base_data(self, data):
        """
        land_based_data need to be set after map_data.

        Args:
            data (list[list[str]]): Such as [['H7', 'up'], ['D5', 'left'], ['G3', 'down'], ['C2', 'right']]
        """
        rotation_dict = {
            'up': [(0, -1), (0, -2), (0, -3)],
            'down': [(0, 1), (0, 2), (0, 3)],
            'left': [(-1, 0), (-2, 0), (-3, 0)],
            'right': [(1, 0), (2, 0), (3, 0)],
        }
        self._land_based_data = data
        for land_based in data:
            grid, rotation = land_based
            grid = self.grids[location_ensure(grid)]
            trigger = self.grid_covered(grid=grid, location=[(0, -1), (0, 1), (-1, 0), (1, 0)]).select(is_land=False)
            block = self.grid_covered(grid=grid, location=rotation_dict[rotation]).select(is_land=False)
            trigger.set(is_mechanism_trigger=True, mechanism_trigger=trigger, mechanism_block=block)
            block.set(is_mechanism_block=True)

    @property
    def maze_data(self):
        return self._maze_data

    @maze_data.setter
    def maze_data(self, data):
        self._maze_data = data

    def _load_maze_data(self, data):
        """
        Args:
            data (list): Such as [('D5', 'I4', 'J6'), ('C4', 'E4', 'D8'), ('C2', 'G2', 'G6')]
        """
        self._maze_data = data
        self.maze_round = len(data) * 3
        for index, maze in enumerate(data):
            maze = self.to_selected(maze)
            maze.set(is_maze=True, maze_round=tuple(list(range(index * 3, index * 3 + 3))))
            for grid in maze:
                self.find_path_initial(grid, has_ambush=False)
                grid.maze_nearby = self.select(cost=1).add(self.select(cost=2)).select(is_land=False)

    @property
    def fortress_data(self):
        return self._fortress_data

    @fortress_data.setter
    def fortress_data(self, data):
        enemy, block = data
        if not isinstance(enemy, SelectedGrids):
            enemy = self.to_selected((enemy,) if not isinstance(enemy, (tuple, list)) else enemy)
        if not isinstance(block, SelectedGrids):
            block = self.to_selected((block,) if not isinstance(block, (tuple, list)) else block)
        self._fortress_data = [enemy, block]

    def _load_fortress_data(self, data):
        """
        Args:
            data (list):  [fortress_enemy, fortress_block], they can should be str or a tuple/list of str.
                Such as [('B5', 'E2', 'H5', 'E8'), 'G3'] or ['F5', 'G1']
        """
        self._fortress_data = data
        enemy, block = data
        enemy.set(is_fortress=True)
        block.set(is_mechanism_block=True)

    @property
    def bouncing_enemy_data(self):
        return self._bouncing_enemy_data

    @bouncing_enemy_data.setter
    def bouncing_enemy_data(self, data):
        self._bouncing_enemy_data = [self.to_selected(route) for route in data]

    def _load_bouncing_enemy_data(self, data):
        """
        Args:
            data (list[SelectedGrids]): Grids that enemy is bouncing in.
                [enemy_route, enemy_route, ...], Such as [(C2, C3, C4), ]
        """
        for route in data:
            route.set(may_bouncing_enemy=True)

    def load_mechanism(self, land_based=False, maze=False, fortress=False, bouncing_enemy=False):
        logger.info(f'Load mechanism, land_base={land_based}, maze={maze}, fortress={fortress}, '
                    f'bouncing_enemy={bouncing_enemy}')
        if land_based:
            self._load_land_base_data(self.land_based_data)
        if maze:
            self._load_maze_data(self.maze_data)
        if fortress:
            self._load_fortress_data(self._fortress_data)
        if bouncing_enemy:
            self._load_bouncing_enemy_data(self._bouncing_enemy_data)

    def grid_connection_initial(self, wall=False, portal=False):
        """
        Args:
            wall (bool): If use wall_data
            portal (bool): If use portal_data

        Returns:
            bool: If used wall data.
        """
        logger.info(f'grid_connection: wall={wall}, portal={portal}')

        # Generate grid connection.
        total = set([grid for grid in self.grids.keys()])
        for grid in self:
            connection = set()
            for arr in np.array([(0, -1), (0, 1), (-1, 0), (1, 0)]):
                arr = tuple(arr + grid.location)
                if arr in total:
                    connection.add(arr)
            self.grid_connection[grid.location] = connection

        # Use wall_data to delete connection.
        if wall and self._wall_data:
            wall = []
            for y, line in enumerate([l for l in self._wall_data.split('\n') if l]):
                for x, letter in enumerate(line[4:-2]):
                    if letter != ' ':
                        wall.append((x, y))
            wall = np.array(wall)
            vert = wall[np.all([wall[:, 0] % 4 == 2, wall[:, 1] % 2 == 0], axis=0)]
            hori = wall[np.all([wall[:, 0] % 4 == 0, wall[:, 1] % 2 == 1], axis=0)]
            disconnect = []
            for loca in (vert - (2, 0)) // (4, 2):
                disconnect.append([loca, loca + (1, 0)])
            for loca in (hori - (0, 1)) // (4, 2):
                disconnect.append([loca, loca + (0, 1)])
            for g1, g2 in disconnect:
                g1 = tuple(g1.tolist())
                g2 = tuple(g2.tolist())
                self.grid_connection[g1].remove(g2)
                self.grid_connection[g2].remove(g1)

        # Create portal link
        for start, end in self._portal_data:
            if portal:
                self.grid_connection[start].add(end)
                self[start].is_portal = True
                self[start].portal_link = end
            else:
                if end in self.grid_connection[start]:
                    self.grid_connection[start].remove(end)
                self[start].is_portal = False
                self[start].portal_link = None

        return True

    def show(self):
        # logger.info('Showing grids:')
        logger.info('   ' + ' '.join([' ' + chr(x + 64 + 1) for x in range(self.shape[0] + 1)]))
        for y in range(self.shape[1] + 1):
            text = str(y + 1).rjust(2) + ' ' + ' '.join(
                [self[(x, y)].str if (x, y) in self else '  ' for x in range(self.shape[0] + 1)])
            logger.info(text)

    def update(self, grids, camera, mode='normal'):
        """
        Args:
            grids:
            camera (tuple):
            mode (str): Scan mode, such as 'normal', 'carrier', 'movable'
        """
        offset = np.array(camera) - np.array(grids.center_loca)
        # grids.show()

        failed_count = 0
        for grid in grids.grids.values():
            loca = tuple(offset + grid.location)
            if loca in self.grids:
                if self.ignore_prediction_match(globe=loca, local=grid):
                    continue
                if not copy.copy(self.grids[loca]).merge(grid, mode=mode):
                    logger.warning(f"Wrong Prediction. {self.grids[loca]} = '{grid.str}'")
                    failed_count += 1

        if failed_count < 2:
            for grid in grids.grids.values():
                loca = tuple(offset + grid.location)
                if loca in self.grids:
                    if self.ignore_prediction_match(globe=loca, local=grid):
                        continue
                    self.grids[loca].merge(grid, mode=mode)
            return True
        else:
            logger.warning('Too many wrong prediction')
            return False

    def reset(self):
        for grid in self:
            grid.reset()

    def reset_fleet(self):
        for grid in self:
            grid.is_current_fleet = False

    @property
    def camera_data(self):
        """
        Returns:
            SelectedGrids:
        """
        return self._camera_data

    @camera_data.setter
    def camera_data(self, nodes):
        """
        Args:
            nodes (list): Contains str.
        """
        self._camera_data = SelectedGrids([self[node2location(node)] for node in nodes])

    @property
    def camera_data_spawn_point(self):
        """Additional camera_data to detect fleets at spawn point.

        Returns:
            SelectedGrids:
        """
        return self._camera_data_spawn_point

    @camera_data_spawn_point.setter
    def camera_data_spawn_point(self, nodes):
        """
        Args:
            nodes (list): Contains str.
        """
        self._camera_data_spawn_point = SelectedGrids([self[node2location(node)] for node in nodes])

    @property
    def spawn_data(self):
        """
        Returns:
            [list[dict]]:
        """
        if self._spawn_data_use_loop:
            return self._spawn_data_loop
        else:
            return self._spawn_data

    @spawn_data.setter
    def spawn_data(self, data_list):
        self._spawn_data = data_list

    @property
    def spawn_data_loop(self):
        return self._spawn_data_loop

    @spawn_data_loop.setter
    def spawn_data_loop(self, data_list):
        self._spawn_data_loop = data_list

    @property
    def spawn_data_stack(self):
        return self._spawn_data_stack

    def load_spawn_data(self, use_loop=False):
        has_loop = bool(len(self._spawn_data_loop))
        logger.info(f'Load spawn_data, has_loop={has_loop}, use_loop={use_loop}')
        if has_loop and use_loop:
            self._spawn_data_use_loop = True
            self._load_spawn_data(self._spawn_data_loop)
        else:
            self._spawn_data_use_loop = False
            self._load_spawn_data(self._spawn_data)

    def _load_spawn_data(self, data_list):
        spawn = {'battle': 0, 'enemy': 0, 'mystery': 0, 'siren': 0, 'boss': 0}
        for data in data_list:
            spawn['battle'] = data['battle']
            spawn['enemy'] += data.get('enemy', 0)
            spawn['mystery'] += data.get('mystery', 0)
            spawn['siren'] += data.get('siren', 0)
            spawn['boss'] += data.get('boss', 0)
            self._spawn_data_stack.append(spawn.copy())

    @property
    def weight_data(self):
        return self._weight_data

    @weight_data.setter
    def weight_data(self, text):
        self._weight_data = text
        for loca, data in self._parse_text(text):
            self[loca].weight = float(data)

    @property
    def map_covered(self):
        """
        Returns:
            SelectedGrids:
        """
        covered = []
        for grid in self:
            covered += self.grid_covered(grid).grids
        return SelectedGrids(covered).add(self._map_covered)

    @map_covered.setter
    def map_covered(self, nodes):
        """
        Args:
            nodes (list): Contains str.
        """
        self._map_covered = SelectedGrids([self[node2location(node)] for node in nodes])

    def ignore_prediction(self, globe, **local):
        """
        Args:
            globe (GridInfo, tuple, str): Grid in globe map.
            **local: Any properties in local grid.

        Examples:
            MAP.ignore_prediction(D5, enemy_scale=1, enemy_genre='Enemy')
            will ignore `1E` enemy on D5.
        """
        globe = location_ensure(globe)
        self._ignore_prediction.append((globe, local))

    def ignore_prediction_match(self, globe, local):
        """
        Args:
            globe (tuple):
            local (GridInfo):

        Returns:
            bool: If matched a wrong prediction.
        """
        for wrong_globe, wrong_local in self._ignore_prediction:
            if wrong_globe == globe:
                if all([local.__getattribute__(k) == v for k, v in wrong_local.items()]):
                    return True

        return False

    @property
    def is_map_data_poor(self):
        if not self.select(may_enemy=True) or not self.select(may_boss=True) or not self.select(is_spawn_point=True):
            return False
        if not len(self.spawn_data):
            return False
        return True

    def show_cost(self):
        logger.info('   ' + ' '.join(['   ' + chr(x + 64 + 1) for x in range(self.shape[0] + 1)]))
        for y in range(self.shape[1] + 1):
            text = str(y + 1).rjust(2) + ' ' + ' '.join(
                [str(self[(x, y)].cost).rjust(4) if (x, y) in self else '    ' for x in range(self.shape[0] + 1)])
            logger.info(text)

    def show_connection(self):
        logger.info('   ' + ' '.join([' ' + chr(x + 64 + 1) for x in range(self.shape[0] + 1)]))
        for y in range(self.shape[1] + 1):
            text = str(y + 1).rjust(2) + ' ' + ' '.join(
                [location2node(self[(x, y)].connection) if (x, y) in self and self[(x, y)].connection else '  ' for x in
                 range(self.shape[0] + 1)])
            logger.info(text)

    def find_path_initial(self, location, has_ambush=True, has_enemy=True):
        """
        Args:
            location (tuple(int)): Grid location
            has_ambush (bool): MAP_HAS_AMBUSH
            has_enemy (bool): False if only sea and land are considered
        """
        location = location_ensure(location)
        ambush_cost = 10 if has_ambush else 1
        for grid in self:
            grid.cost = 9999
            grid.connection = None
        start = self[location]
        start.cost = 0
        visited = [start]
        visited = set(visited)

        while 1:
            new = visited.copy()
            for grid in visited:
                for arr in self.grid_connection[grid.location]:
                    arr = self[arr]
                    if arr.is_land or arr.is_mechanism_block:
                        continue
                    cost = ambush_cost if arr.may_ambush else 1
                    cost += grid.cost

                    if cost < arr.cost:
                        arr.cost = cost
                        arr.connection = grid.location
                    elif cost == arr.cost:
                        if abs(arr.location[0] - grid.location[0]) == 1:
                            arr.connection = grid.location
                    if arr.is_sea or not has_enemy:
                        new.add(arr)
            if len(new) == len(visited):
                break
            visited = new

        # self.show_cost()
        # self.show_connection()

    def find_path_initial_multi_fleet(self, location_dict, current, has_ambush):
        """
        Args:
            location_dict (dict): Key: int, fleet index. Value: tuple(int), grid location.
            current (tuple): Current location.
            has_ambush (bool): MAP_HAS_AMBUSH
        """
        location_dict = sorted(location_dict.items(), key=lambda kv: (int(kv[1] == current),))
        for fleet, location in location_dict:
            if location == ():
                continue
            self.find_path_initial(location, has_ambush=has_ambush)
            attr = f'cost_{fleet}'
            for grid in self:
                grid.__setattr__(attr, grid.cost)

    def _find_path(self, location):
        """
        Args:
            location (tuple):

        Returns:
            list[tuple]: walking route.

        Examples:
            MAP_7_2._find_path(node2location('H2'))
            [(2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (6, 1), (7, 1)]  # ['C3', 'D3', 'E3', 'F3', 'G3', 'G2', 'H2']
        """
        if self[location].cost == 0:
            return [location]
        if self[location].connection is None:
            return None
        res = [location]
        while 1:
            location = self[location].connection
            if len(res) > 30:
                logger.warning('Route too long')
                logger.warning(res)
                # exit(1)
            if location is not None:
                res.append(location)
            else:
                break
        res.reverse()

        if len(res) == 0:
            logger.warning('No path found. Destination: %s' % str(location))
            return [location, location]

        return res

    def _find_route_node(self, route, step=0, turning_optimize=False):
        """
        Args:
            route (list[tuple]): list of grids.
            step (int): Fleet step in event map. Default to 0.
            turning_optimize: (bool): True to optimize route to reduce ambushes

        Returns:
            list[tuple]: list of walking node.

        Examples:
            MAP_7_2._find_route_node([(2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (6, 1), (7, 1)])
            [(6, 2), (7, 1)]
        """
        if turning_optimize:
            res = []
            diff = np.abs(np.diff(route, axis=0))
            turning = np.diff(diff, axis=0)[:, 0]
            indexes = np.where(turning == -1)[0] + 1
            for index in indexes:
                if not self[route[index]].is_fleet:
                    res.append(index)
                else:
                    logger.info(f'Path_node_avoid: {self[route[index]]}')
                    if (index > 1) and (index - 1 not in indexes):
                        res.append(index - 1)
                    if (index < len(route) - 2) and (index + 1 not in indexes):
                        res.append(index + 1)
            res.append(len(route) - 1)
            # res = [4, 6]
            if step == 0:
                return [route[index] for index in res]
        else:
            if step == 0:
                return [route[-1]]
            # Index of the last node
            # res = [6]
            res = [max(len(route) - 1, 0)]

        res.insert(0, 0)
        inserted = []
        for left, right in zip(res[:-1], res[1:]):
            for index in list(range(left, right, step))[1:]:
                way_node = self[route[index]]
                if way_node.is_fleet or way_node.is_portal or way_node.is_flare:
                    logger.info(f'Path_node_avoid: {way_node}')
                    if (index > 1) and (index - 1 not in res):
                        inserted.append(index - 1)
                    if (index < len(route) - 2) and (index + 1 not in res):
                        inserted.append(index + 1)
                else:
                    inserted.append(index)
            inserted.append(right)
        res = inserted
        # res = [3, 6, 8]
        return [route[index] for index in res]

    def find_path(self, location, step=0, turning_optimize=False):
        location = location_ensure(location)

        path = self._find_path(location)
        if path is None or not len(path):
            logger.warning('No path found. Return destination.')
            return [location]
        logger.info('Full path: %s' % '[' + ', ' .join([location2node(grid) for grid in path]) + ']')

        portal_path = []
        index = [0]
        for i, loca in enumerate(zip(path[:-1], path[1:])):
            grid = self[loca[0]]
            if grid.is_portal and grid.portal_link == loca[1]:
                index += [i, i + 1]
            if grid.is_maze and i != 0:
                index += [i]
        if len(path) not in index:
            index.append(len(path))
        for start, end in zip(index[:-1], index[1:]):
            if end - start == 1 and self[path[start]].is_portal and self[path[start]].portal_link == path[end]:
                continue
            local_path = path[start:end + 1]
            local_path = self._find_route_node(local_path, step=step, turning_optimize=turning_optimize)
            portal_path += local_path
            logger.info('Path: %s' % '[' + ', ' .join([location2node(grid) for grid in local_path]) + ']')
        path = portal_path

        return path

    def grid_covered(self, grid, location=None):
        """
        Args:
            grid (GridInfo)
            location (list[tuple[int]]): Relative coordinate of the covered grid.

        Returns:
            SelectedGrids:
        """
        if location is None:
            covered = [tuple(np.array(grid.location) + upper) for upper in grid.covered_grid()]
        else:
            covered = [tuple(np.array(grid.location) + upper) for upper in location]
        covered = [self[upper] for upper in covered if upper in self]
        return SelectedGrids(covered)

    def missing_get(self, battle_count, mystery_count=0, siren_count=0, carrier_count=0, mode='normal'):
        try:
            missing = self.spawn_data_stack[battle_count].copy()
        except IndexError:
            missing = self.spawn_data_stack[-1].copy()
        may = {'enemy': 0, 'mystery': 0, 'siren': 0, 'boss': 0, 'carrier': 0}
        missing['enemy'] -= battle_count - siren_count
        missing['mystery'] -= mystery_count
        missing['siren'] -= siren_count
        missing['carrier'] = carrier_count - self.select(is_enemy=True, may_enemy=False).count \
            if mode == 'carrier' else 0
        for grid in self:
            for attr in ['enemy', 'mystery', 'siren', 'boss']:
                if grid.__getattribute__('is_' + attr):
                    missing[attr] -= 1
        missing['enemy'] += len(self.fortress_data[0]) - self.select(is_fortress=True).count
        for route in self.bouncing_enemy_data:
            if not route.select(may_bouncing_enemy=True):
                # bouncing enemy cleared, re-add one enemy
                missing['enemy'] += 1

        for upper in self.map_covered:
            if (upper.may_enemy or mode == 'movable') and not upper.is_enemy:
                may['enemy'] += 1
            if upper.may_mystery and not upper.is_mystery:
                may['mystery'] += 1
            if (upper.may_siren or mode == 'movable') and not upper.is_siren:
                may['siren'] += 1
            if upper.may_boss and not upper.is_boss:
                may['boss'] += 1
            if upper.may_carrier:
                may['carrier'] += 1

        logger.attr('enemy_missing',
                    ', '.join([f'{k[:2].upper()}:{str(v).rjust(2)}' for k, v in missing.items() if k != 'battle']))
        logger.attr('enemy_may____',
                    ', '.join([f'{k[:2].upper()}:{str(v).rjust(2)}' for k, v in may.items()]))
        return may, missing

    def missing_is_none(self, battle_count, mystery_count=0, siren_count=0, carrier_count=0, mode='normal'):
        if self.poor_map_data:
            return False

        may, missing = self.missing_get(battle_count, mystery_count, siren_count, carrier_count, mode)

        for key in may.keys():
            if missing[key] != 0:
                return False

        return True

    def missing_predict(self, battle_count, mystery_count=0, siren_count=0, carrier_count=0, mode='normal'):
        if self.poor_map_data:
            return False

        may, missing = self.missing_get(battle_count, mystery_count, siren_count, carrier_count, mode)

        # predict
        for upper in self.map_covered:
            for attr in ['enemy', 'mystery', 'siren', 'boss']:
                if upper.__getattribute__('may_' + attr) and missing[attr] > 0 and missing[attr] == may[attr]:
                    logger.info('Predict %s to be %s' % (location2node(upper.location), attr))
                    upper.__setattr__('is_' + attr, True)
            if carrier_count:
                if upper.may_carrier and missing['carrier'] > 0 and missing['carrier'] == may['carrier']:
                    logger.info('Predict %s to be enemy' % location2node(upper.location))
                    upper.__setattr__('is_enemy', True)

    def select(self, **kwargs):
        """
        Args:
            **kwargs: Attributes of Grid.

        Returns:
            SelectedGrids:
        """
        result = []
        for grid in self:
            flag = True
            for k, v in kwargs.items():
                if grid.__getattribute__(k) != v:
                    flag = False
            if flag:
                result.append(grid)

        return SelectedGrids(result)

    def to_selected(self, grids):
        """
        Args:
            grids (list):

        Returns:
            SelectedGrids:
        """
        return SelectedGrids([self[location_ensure(loca)] for loca in grids])

    def flatten(self):
        """
        Returns:
            list[GridInfo]:
        """
        return self.grids.values()
