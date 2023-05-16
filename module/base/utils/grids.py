import operator
import typing as t


class SelectedGrids:
    def __init__(self, grids):
        self.grids = grids
        self.indexes: t.Dict[tuple, SelectedGrids] = {}

    def __iter__(self):
        return iter(self.grids)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.grids[item]
        else:
            return SelectedGrids(self.grids[item])

    def __contains__(self, item):
        return item in self.grids

    def __str__(self):
        # return str([str(grid) for grid in self])
        return '[' + ', '.join([str(grid) for grid in self]) + ']'

    def __len__(self):
        return len(self.grids)

    def __bool__(self):
        return self.count > 0

    # def __getattr__(self, item):
    #     return [grid.__getattribute__(item) for grid in self.grids]

    @property
    def location(self):
        """
        Returns:
            list[tuple]:
        """
        return [grid.location for grid in self.grids]

    @property
    def cost(self):
        """
        Returns:
            list[int]:
        """
        return [grid.cost for grid in self.grids]

    @property
    def weight(self):
        """
        Returns:
            list[int]:
        """
        return [grid.weight for grid in self.grids]

    @property
    def count(self):
        """
        Returns:
            int:
        """
        return len(self.grids)

    def select(self, **kwargs):
        """
        Args:
            **kwargs: Attributes of Grid.

        Returns:
            SelectedGrids:
        """
        def matched(obj):
            flag = True
            for k, v in kwargs.items():
                obj_v = obj.__getattribute__(k)
                if type(obj_v) != type(v) or obj_v != v:
                    flag = False
            return flag

        return SelectedGrids([grid for grid in self.grids if matched(grid)])

    def create_index(self, *attrs):
        indexes = {}
        # index_keys = [(grid.__getattribute__(attr) for attr in attrs) for grid in self.grids]
        for grid in self.grids:
            k = tuple(grid.__getattribute__(attr) for attr in attrs)
            try:
                indexes[k].append(grid)
            except KeyError:
                indexes[k] = [grid]

        indexes = {k: SelectedGrids(v) for k, v in indexes.items()}
        self.indexes = indexes
        return indexes

    def indexed_select(self, *values):
        return self.indexes.get(values, SelectedGrids([]))

    def left_join(self, right, on_attr, set_attr, default=None):
        """
        Args:
            right (SelectedGrids): Right table to join
            on_attr:
            set_attr:
            default:

        Returns:
            SelectedGrids:
        """
        right.create_index(*on_attr)
        for grid in self:
            attr_value = tuple([grid.__getattribute__(attr) for attr in on_attr])
            right_grid = right.indexed_select(*attr_value).first_or_none()
            if right_grid is not None:
                for attr in set_attr:
                    grid.__setattr__(attr, right_grid.__getattribute__(attr))
            else:
                for attr in set_attr:
                    grid.__setattr__(attr, default)

        return self

    def filter(self, func):
        """
        Filter grids by a function.

        Args:
            func (callable): Function should receive an grid as argument, and return a bool.

        Returns:
            SelectedGrids:
        """
        return SelectedGrids([grid for grid in self if func(grid)])

    def set(self, **kwargs):
        """
        Set attribute to each grid.

        Args:
            **kwargs:
        """
        for grid in self:
            for key, value in kwargs.items():
                grid.__setattr__(key, value)

    def get(self, attr):
        """
        Get an attribute from each grid.

        Args:
            attr: Attribute name.

        Returns:
            list:
        """
        return [grid.__getattribute__(attr) for grid in self.grids]

    def call(self, func, **kwargs):
        """
        Call a function in reach grid, and get results.

        Args:
            func (str): Function name to call.
            **kwargs:

        Returns:
            list:
        """
        return [grid.__getattribute__(func)(**kwargs) for grid in self]

    def first_or_none(self):
        """
        Returns:

        """
        try:
            return self.grids[0]
        except IndexError:
            return None

    def add(self, grids):
        """
        Args:
            grids(SelectedGrids):

        Returns:
            SelectedGrids:
        """
        return SelectedGrids(list(set(self.grids + grids.grids)))

    def add_by_eq(self, grids):
        """
        Another `add()` method, but de-duplicates with `__eq__` instead of `__hash__`.

        Args:
            grids(SelectedGrids):

        Returns:
            SelectedGrids:
        """
        new = []
        for grid in self.grids + grids.grids:
            if grid not in new:
                new.append(grid)

        return SelectedGrids(new)

    def intersect(self, grids):
        """
        Args:
            grids(SelectedGrids):

        Returns:
            SelectedGrids:
        """
        return SelectedGrids(list(set(self.grids).intersection(set(grids.grids))))

    def intersect_by_eq(self, grids):
        """
        Another `intersect()` method, but de-duplicates with `__eq__` instead of `__hash__`.

        Args:
            grids(SelectedGrids):

        Returns:
            SelectedGrids:
        """
        new = []
        for grid in self.grids:
            if grid in grids.grids:
                new.append(grid)

        return SelectedGrids(new)

    def delete(self, grids):
        """
        Args:
            grids(SelectedGrids):

        Returns:
            SelectedGrids:
        """
        g = [grid for grid in self.grids if grid not in grids]
        return SelectedGrids(g)

    def sort(self, *args):
        """
        Args:
            args (str): Attribute name to sort.

        Returns:
            SelectedGrids:
        """
        if not self:
            return self
        if len(args):
            grids = sorted(self.grids, key=operator.attrgetter(*args))
            return SelectedGrids(grids)
        else:
            return self

    def sort_by_camera_distance(self, camera):
        """
        Args:
            camera (tuple):

        Returns:
            SelectedGrids:
        """
        import numpy as np
        if not self:
            return self
        location = np.array(self.location)
        diff = np.sum(np.abs(location - camera), axis=1)
        # grids = [x for _, x in sorted(zip(diff, self.grids))]
        grids = tuple(np.array(self.grids)[np.argsort(diff)])
        return SelectedGrids(grids)

    def sort_by_clock_degree(self, center=(0, 0), start=(0, 1), clockwise=True):
        """
        Args:
            center (tuple): Origin point.
            start (tuple): Start coordinate, this point will be considered as theta=0.
            clockwise (bool): True for clockwise, false for counterclockwise.

        Returns:
            SelectedGrids:
        """
        import numpy as np
        if not self:
            return self
        vector = np.subtract(self.location, center)
        theta = np.arctan2(vector[:, 1], vector[:, 0]) / np.pi * 180
        vector = np.subtract(start, center)
        theta = theta - np.arctan2(vector[1], vector[0]) / np.pi * 180
        if not clockwise:
            theta = -theta
        theta[theta < 0] += 360
        grids = tuple(np.array(self.grids)[np.argsort(theta)])
        return SelectedGrids(grids)


class RoadGrids:
    def __init__(self, grids):
        """
        Args:
            grids (list):
        """
        self.grids = []
        for grid in grids:
            if isinstance(grid, list):
                self.grids.append(SelectedGrids(grids=grid))
            else:
                self.grids.append(SelectedGrids(grids=[grid]))

    def __str__(self):
        return str(' - '.join([str(grid) for grid in self.grids]))

    def roadblocks(self):
        """
        Returns:
            SelectedGrids:
        """
        grids = []
        for block in self.grids:
            if block.count == block.select(is_enemy=True).count:
                grids += block.grids
        return SelectedGrids(grids)

    def potential_roadblocks(self):
        """
        Returns:
            SelectedGrids:
        """
        grids = []
        for block in self.grids:
            if any([grid.is_fleet for grid in block]):
                continue
            if any([grid.is_cleared for grid in block]):
                continue
            if block.count - block.select(is_enemy=True).count == 1:
                grids += block.select(is_enemy=True).grids
        return SelectedGrids(grids)

    def first_roadblocks(self):
        """
        Returns:
            SelectedGrids:
        """
        grids = []
        for block in self.grids:
            if any([grid.is_fleet for grid in block]):
                continue
            if any([grid.is_cleared for grid in block]):
                continue
            if block.select(is_enemy=True).count >= 1:
                grids += block.select(is_enemy=True).grids
        return SelectedGrids(grids)

    def combine(self, road):
        """
        Args:
            road (RoadGrids):

        Returns:
            RoadGrids:
        """
        out = RoadGrids([])
        for select_1 in self.grids:
            for select_2 in road.grids:
                select = select_1.add(select_2)
                out.grids.append(select)

        return out
