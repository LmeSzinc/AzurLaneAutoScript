from dataclasses import dataclass, field

from module.base.timer import Timer


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
    # Max move speed, 'run_2x', 'straight_run', 'run', 'walk'
    # See MapControl._goto() for details of each speed level
    speed: str = 'run'

    """
    The following attributes are only be used if this waypoint is the end point of goto()
    """
    # True to enable endpoint optimizations, character will smoothly approach target position
    # False to stop all controls at arrive
    end_opt: bool = True
    # Set rotation after arrive, 0~360
    end_rotation: int = None
    end_rotation_threshold: int = 15

    """
    Walk
    """
    # A list of expected events, e.g. ['enemy', 'item']
    # - "enemy", finished any combat
    # - "item", destroyed any destructive objects
    # - "interact", have map interact option (interact is not handled)
    # - callable, A function that returns bool, True represents stop
    # Or empty list [] for just walking
    expected_end: list = field(default_factory=lambda: [])
    # If triggered any expected event, consider arrive and stop walking
    early_stop: bool = True
    # Confirm timer if arrived but didn't trigger any expected event
    unexpected_confirm: Timer = field(default_factory=lambda: Timer(2, count=6))

    def __str__(self):
        return f'Waypoint({self.position})'

    __repr__ = __str__

    def run_2x(self) -> "Waypoint":
        """
        Product a Waypoint object with overridden "speed",
        see Waypoint class for args.
        """
        self.speed = 'run_2x'
        return self

    def straight_run(self) -> "Waypoint":
        self.speed = 'straight_run'
        return self

    def run(self) -> "Waypoint":
        self.speed = 'run'
        return self

    def walk(self) -> "Waypoint":
        self.speed = 'walk'
        return self

    def set_threshold(self, threshold) -> "Waypoint":
        self.threshold = threshold
        return self

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

    @staticmethod
    def expected_to_str(results: list) -> list[str]:
        return [result.__name__ if callable(result) else str(result) for result in results]

    def match_results(self, results) -> list[str]:
        """
        Args:
            results:

        Returns:
            list[str]: A list if matched results
        """
        if not results and not self.expected_end:
            return []

        results = set(self.expected_to_str(results))
        expected_end = set(self.expected_to_str(self.expected_end))
        same = results.intersection(expected_end)

        return list(same)


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


def ensure_waypoints(points) -> list[Waypoint]:
    if not isinstance(points, (list, tuple)):
        points = [points]
    return [ensure_waypoint(point) for point in points]
