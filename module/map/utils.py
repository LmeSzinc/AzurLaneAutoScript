import numpy as np

from module.base.utils import node2location
from module.map_detection.grid_info import GridInfo


def location_ensure(location):
    """
    Args:
        location: Grid.

    Returns:
        tuple(int): Location, such as (4, 3)
    """
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


def combine(before, after, limit):
    after += [limit]
    for b in before:
        for a in after:
            index = b + [a]
            match = [m for m in index if m < limit]
            if len(set(match)) == len(match):
                yield index


def match_movable(before, spawn, after, fleets, fleet_step=2):
    """
    Args:
        before (list(tuple)): List of location. Before and after are equivalent, you can reverse input.
                              Will match the previous element in `before` first.
        spawn (list(tuple)):
        after (list(tuple)):
        fleets (list(tuple)):
        fleet_step (int):

    Returns:
        list(tuple), list(tuple): Matched before, and after.

    Examples:
        > before = [(0, 2), (0, 0), (1, 0), (2, 4), (7, 19)]
        > after = [(7, 9), (0, 3), (0, 1), (1, 1), (2, 5)]
        > match_movable(before, after)
        ([(0, 2), (0, 0), (1, 0), (2, 4)], [(0, 3), (0, 1), (1, 1), (2, 5)])
    """
    base_weight = -10000
    encourage_weight = -100
    before_len = len(before)
    after_len = len(after)
    before = before + spawn
    after = after + fleets
    x = len(after)
    y = len(before)
    distance = np.ones((y, x), dtype=np.int) * base_weight
    for i1, g1 in enumerate(before):
        for i2, g2 in enumerate(after):
            distance[i1, i2] = fleet_step - sum(abs(np.subtract(g1, g2)))

    distance[distance < 0] = base_weight
    distance[before_len:, :] += encourage_weight
    distance[:, after_len:] += encourage_weight
    distance = np.maximum(distance, base_weight)
    # print(distance)
    # [[-100    1    1    0 -100]
    #  [-100 -100    1    0 -100]
    #  [-100 -100    0    1 -100]
    #  [-100 -100 -100 -100    1]
    #  [-100 -100 -100 -100 -100]]

    permutations = [[]]
    for row in distance:
        match = np.where(row >= encourage_weight)[0].tolist()
        permutations = list(combine(permutations, match, limit=x))
        if not len(permutations):
            permutations = [[x]]

    if len(permutations) == 0 or len(permutations[0]) == 0:
        return [], []
    else:
        permutations = np.array(permutations)
        permutations = permutations[np.argsort(np.sum(permutations, axis=1))]
        distance = np.pad(distance, ((0, 0), (0, 1)), mode='constant', constant_values=base_weight)
        index_x = permutations
        index_y = list(range(y)) * int(index_x.shape[0])
        match = distance[index_y, index_x.ravel()].reshape(-1, y)
        match = np.sum(match, axis=1)
        best_match = permutations[int(np.argmax(match))]
        before = [before[index] for index, match in enumerate(best_match) if match < x]
        after = [after[index] for index in best_match if index < x]
        return before, after
