from dataclasses import dataclass


@dataclass
class Waypoint:
    # Position to goto, (x, y)
    position: tuple
    # Position diff < threshold is considered as arrived
    # `threshold` is used first if it is set
    threshold: int = None
    # If `threshold` is not set, `waypoint_threshold` and `endpoint_threshold` are used
    waypoint_threshold: int = 10
    endpoint_threshold: int = 3
    # Max move speed, '2x_run', 'straight_run', 'run', 'walk'
    # See MapControl._goto() for details of each speed level
    speed: str = '2x_run'

    """
    The following attributes are only be used if this waypoint is the end point of goto()
    """
    # True to enable endpoint optimizations, character will smoothly approach target position
    # False to stop all controls at arrive
    end_point_opt: bool = True
    # Set rotation after arrive, 0~360
    end_point_rotation: int = None
    end_point_rotation_threshold: int = 15

    def __str__(self):
        return f'Waypoint({self.position})'

    __repr__ = __str__

    def get_threshold(self, end):
        """
        Args:
            end: True if this is an end point

        Returns:
            int
        """
        if self.threshold is not None:
            return self.threshold
        if end:
            return self.endpoint_threshold
        else:
            return self.waypoint_threshold


def ensure_waypoint(point) -> Waypoint:
    """
    Args:
        point: Position (x, y) or Waypoint object

    Returns:
        Waypoint:
    """
    if isinstance(point, Waypoint):
        return point
    return Waypoint(point)


@dataclass(repr=False)
class Waypoint2xRun(Waypoint):
    speed: str = '2x_run'


@dataclass(repr=False)
class WaypointStraightRun(Waypoint):
    speed: str = 'straight_run'


@dataclass(repr=False)
class WaypointRun(Waypoint):
    speed: str = 'run'


@dataclass(repr=False)
class WaypointWalk(Waypoint):
    speed: str = 'walk'
