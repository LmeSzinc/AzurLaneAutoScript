from tasks.map.control.control import MapControl
from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords import MapPlane


class RouteBase(MapControl):
    """
    Base class of `Route`
    Every `Route` class must implement method `route()`
    """
    registered_locked_position = None
    registered_locked_direction = None
    registered_locked_rotation = None

    def route_example(self):
        """
        Pages:
            in: page_main
            out: page_main
                Doesn't matter if in/out are not page_main, just be clear what you're doing
        """
        self.map_init(
            plane=...,
            floor=...,
            position=...,
        )
        self.clear_enemy(
            Waypoint(...).run_2x(),
            Waypoint(...),
        )

    def map_init(
            self,
            plane: MapPlane | str,
            floor: str = 'F1',
            position: tuple[int | float, int | float] = None
    ):
        """
        Args:
            plane (MapPlane, str): Such as Jarilo_AdministrativeDistrict
            floor (str):
            position: Initialize the starter point of minimap tracking
                Leaving None will trigger brute-force starter point finding.
        """
        try:
            if self.device.image is None:
                self.device.screenshot()
        except AttributeError:
            self.device.screenshot()

        self.minimap.set_plane(plane, floor=floor)
        if position is not None:
            self.minimap.init_position(
                position=position,
                locked=self.registered_locked_position is not None
            )
        if self.registered_locked_direction is not None:
            self.minimap.lock_direction(self.registered_locked_direction)
        if self.registered_locked_rotation is not None:
            self.minimap.lock_rotation(self.registered_locked_rotation)

        self.registered_locked_position = None
        self.registered_locked_direction = None
        self.registered_locked_rotation = None

    def before_route(self):
        pass

    def after_route(self):
        pass


def locked_position(function):
    """
    Examples:
        @locked_position
        def Luofu_ScalegorgeWaterscape_F1_X619Y387(self):
            pass  # Search area will be locked
    """

    def wrapper(self: RouteBase, *args, **kwargs):
        self.registered_locked_position = True
        result = function(self, *args, **kwargs)
        return result

    return wrapper


def locked_direction(degree: int | float):
    """
    Examples:
        @locked_direction(270)
        def Luofu_ScalegorgeWaterscape_F1_X619Y387(self):
            pass  # Direction will be locked to 270
    """

    def locker(function):
        def wrapper(self: RouteBase, *args, **kwargs):
            self.registered_locked_direction = degree
            result = function(self, *args, **kwargs)
            return result

        return wrapper

    return locker


def locked_rotation(degree: int | float):
    """
    Examples:
        @locked_rotation(270)
        def Luofu_ScalegorgeWaterscape_F1_X619Y387(self):
            pass  # Rotation will be locked to 270
    """

    def locker(function):
        def wrapper(self: RouteBase, *args, **kwargs):
            self.registered_locked_rotation = degree
            result = function(self, *args, **kwargs)
            return result

        return wrapper

    return locker
