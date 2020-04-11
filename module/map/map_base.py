import numpy as np

from module.base.utils import location2node, node2location
from module.logger import logger
from module.map.grid_info import GridInfo
from module.map.map_grids import SelectedGrids


def location_ensure(location):
    if isinstance(location, GridInfo):
        return location.location
    elif isinstance(location, str):
        return node2location(location)
    else:
        return location


def camera_1d(shape, sight):
    start, step = abs(sight[0]), sight[1] - sight[0] + 1
    if shape <= start:
        out = shape // 2
    else:
        out = list(range(start, 26, step))
        out.append(shape - sight[1])
        out = [x for x in set(out) if x <= shape - sight[1]]
    return out


def camera_2d(shape, sight):
    x = camera_1d(shape=shape[0], sight=[sight[0], sight[2]])
    y = camera_1d(shape=shape[1], sight=[sight[1], sight[3]])
    out = np.array(np.meshgrid(x, y)).T.reshape(-1, 2)
    return [tuple(c) for c in out]


class CampaignMap:
    def __init__(self, name=None):
        self.name = name
        self.grids = {}
        self._shape = (0, 0)
        self._map_data = ''
        self._weight_data = ''
        self._block_data = []
        self._spawn_data = []
        self._spawn_data_backup = []
        self._camera_data = []
        self.in_map_swipe_preset_data = None

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
                grid = GridInfo()
                grid.location = (x, y)
                self.grids[(x, y)] = grid

        # camera_data can be generate automatically, but it's better to set it manually.
        self.camera_data = [location2node(loca) for loca in camera_2d(self._shape, sight=(-3, -1, 3, 2))]

        # weight_data set to 10.
        for grid in self:
            grid.weight = 10.

    @property
    def map_data(self):
        return self._map_data

    @map_data.setter
    def map_data(self, text):
        self._map_data = text
        for loca, data in self._parse_text(text):
            self.grids[loca].decode(data)

    def show(self):
        # logger.info('Showing grids:')
        logger.info('  ' + ' '.join([' ' + chr(x + 64 + 1) for x in range(self.shape[0] + 1)]))
        for y in range(self.shape[1] + 1):
            text = str(y + 1) + ' ' + ' '.join(
                [self[(x, y)].str if (x, y) in self else '  ' for x in range(self.shape[0] + 1)])
            logger.info(text)

    def update(self, grids, camera):
        """
        Args:
            grids:
            camera (tuple):
        """
        # failure = 0
        offset = np.array(camera) - np.array(grids.center_grid)
        grids.show()
        for grid in grids.grids.values():
            loca = tuple(offset + grid.location)
            if loca in self.grids:
                self.grids[loca].update(grid)
                # flag, fail = self.grids[loca].update(grid)
                # failure += fail

        # return failure
        return True

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
    def spawn_data(self):
        return self._spawn_data

    @spawn_data.setter
    def spawn_data(self, data_list):
        self._spawn_data_backup = data_list
        spawn = {'battle': 0, 'enemy': 0, 'mystery': 0, 'siren': 0, 'boss': 0}
        for data in data_list:
            spawn['battle'] = data['battle']
            spawn['enemy'] += data.get('enemy', 0) + data.get('siren', 0)
            spawn['mystery'] += data.get('mystery', 0)
            spawn['siren'] += data.get('siren', 0)
            spawn['boss'] += data.get('boss', 0)
            self._spawn_data.append(spawn.copy())

    @property
    def weight_data(self):
        return self._weight_data

    @weight_data.setter
    def weight_data(self, text):
        self._weight_data = text
        for loca, data in self._parse_text(text):
            self[loca].weight = float(data)

    def show_cost(self):
        logger.info('  ' + ' '.join(['   ' + chr(x + 64 + 1) for x in range(self.shape[0] + 1)]))
        for y in range(self.shape[1] + 1):
            text = str(y + 1) + ' ' + ' '.join(
                [str(self[(x, y)].cost).rjust(4) if (x, y) in self else '    ' for x in range(self.shape[0] + 1)])
            logger.info(text)

    def show_connection(self):
        logger.info('  ' + ' '.join([' ' + chr(x + 64 + 1) for x in range(self.shape[0] + 1)]))
        for y in range(self.shape[1] + 1):
            text = str(y + 1) + ' ' + ' '.join(
                [location2node(self[(x, y)].connection) if (x, y) in self and self[(x, y)].connection else '  ' for x in
                 range(self.shape[0] + 1)])
            logger.info(text)

    def find_path_initial(self, location, has_ambush=True):
        location = location_ensure(location)

        ambush_cost = 10 if has_ambush else 1
        for grid in self:
            grid.cost = 9999
            grid.connection = None
        self[location].cost = 0
        total = set([grid for grid in self.grids.keys()])
        visited = [location]
        visited = set(visited)

        while 1:
            new = visited.copy()
            for grid in visited:
                for arr in np.array([(0, -1), (0, 1), (-1, 0), (1, 0)]):
                    arr = tuple(arr + grid)
                    if arr not in total or self[arr].is_land:
                        continue
                    cost = 1 if self[arr].is_ambush_save else ambush_cost
                    cost += self[grid].cost

                    if cost < self[arr].cost:
                        self[arr].cost = cost
                        self[arr].connection = grid
                    elif cost == self[arr].cost:
                        if abs(arr[0] - grid[0]) == 1:
                            self[arr].connection = grid
                    if self[arr].is_sea:
                        new.add(arr)
            if len(new) == len(visited):
                break
            visited = new

        # self.show_cost()
        # self.show_connection()

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

    def _find_route_node(self, route):
        """

        Args:
            route (list[tuple]): list of grids.

        Returns:
            list[tuple]: list of walking node.

        Examples:
            MAP_7_2._find_route_node([(2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (6, 1), (7, 1)])
            [(6, 2), (7, 1)]
        """
        res = []
        diff = np.abs(np.diff(route, axis=0))
        turning = np.diff(diff, axis=0)[:, 0]
        indexes = np.where(turning == -1)[0] + 1
        for index in indexes:
            grid = route[index]
            if not self[grid].is_fleet:
                res.append(grid)
            else:
                if (index > 1) and (index + 1 not in indexes):
                    res.append(route[index - 1])
                if (index < len(route) - 2) and (index + 1 not in indexes):
                    res.append(route[index + 1])
        res.append(route[-1])

        return res

    def find_path(self, location):
        location = location_ensure(location)

        path = self._find_path(location)
        if path is None or not len(path):
            logger.warning('No path found. Return destination.')
            return [location]

        logger.info('Path: %s' % '[' + ', ' .join([location2node(grid) for grid in path]) + ']')
        path = self._find_route_node(path)
        logger.info('Path: %s' % '[' + ', ' .join([location2node(grid) for grid in path]) + ']')

        return path

    def missing_get(self, battle_count, mystery_count=0, siren_count=0):
        try:
            missing = self.spawn_data[battle_count].copy()
        except IndexError:
            missing = self.spawn_data[-1].copy()
        may = {'enemy': 0, 'mystery': 0, 'siren': 0, 'boss': 0}
        missing['enemy'] -= battle_count
        missing['mystery'] -= mystery_count
        missing['siren'] -= siren_count
        for grid in self:
            for attr in may.keys():
                if grid.__getattribute__('is_' + attr):
                    missing[attr] -= 1

        for grid in self:
            if not grid.is_fleet and not grid.is_mystery and not grid.is_siren:
                continue

            cover = [(0, -1)]
            if grid.is_current_fleet:
                cover.append((0, -2))

            for upper in cover:
                upper = tuple(np.array(grid.location) + upper)
                if upper in self:
                    upper = self[upper]
                    for attr in may.keys():
                        if upper.__getattribute__('may_' + attr) and not upper.__getattribute__('is_' + attr):
                            may[attr] += 1

        logger.info('missing: %s' % missing)
        logger.info('may: %s' % may)
        return may, missing

    def missing_is_none(self, battle_count, mystery_count=0, siren_count=0):
        may, missing = self.missing_get(battle_count, mystery_count, siren_count)

        for key in may.keys():
            if missing[key] != 0:
                return False

        return True

    def missing_predict(self, battle_count, mystery_count=0, siren_count=0):
        may, missing = self.missing_get(battle_count, mystery_count, siren_count)

        # predict
        for grid in self:
            if not grid.is_fleet and not grid.is_mystery:
                continue

            cover = [(0, -1)]
            if grid.is_current_fleet:
                cover.append((0, -2))

            for upper in cover:
                upper = tuple(np.array(grid.location) + upper)
                if upper in self:
                    upper = self[upper]
                    for attr in may.keys():
                        if upper.__getattribute__('may_' + attr) and missing[attr] > 0 and missing[attr] == may[attr]:
                            logger.info('Predict %s to be %s' % (location2node(upper.location), attr))
                            upper.__setattr__('is_' + attr, True)

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

    def flatten(self):
        """

        Returns:
            list[GridInfo]:
        """
        return self.grids.values()
