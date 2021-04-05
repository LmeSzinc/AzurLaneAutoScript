import numpy as np

from module.exception import ScriptError
from module.logger import logger
from module.os.map_data import DIC_OS_MAP


class Zone:
    zone_id: int
    # Map shape, such as J10
    shape: str
    # Corrosion level, from 1 to 7
    hazard_level: int
    # Name in different servers
    cn: str
    en: str
    jp: str
    # Position where information bar is pinned on
    area_pos: tuple
    # area_pos + offset_pos is where mission pinned on
    offset_pos: tuple
    # 1 for upper-left, 2 for upper-right, 3 for bottom-left, 4 for bottom-right, 5 for center
    region: int

    def __init__(self, data):
        self.__dict__.update(data)
        self.location = self.point_convert(self.area_pos)
        self.mission = self.point_convert(np.add(self.area_pos, self.offset_pos))

    @staticmethod
    def point_convert(point):
        """
        Convert coordinates in world_chapter_colormask.lua to os_globe_map.png
        """
        point = np.multiply(point, 1.25)
        point = np.array((point[0], 1694 - point[1]))  # 1694 is the height of os_globe_map.png
        return point

    def __str__(self):
        """

        Returns:
            str: Such as `[3|圣彼得伯格|St. Petersburg|ペテルブルク]`
        """
        return f'[{self.zone_id}|{self.cn}|{self.en}|{self.jp}]'

    __repr__ = __str__

    def __eq__(self, other):
        return self.zone_id == other.zone_id


class ZoneManager:
    _zone_loaded = False
    _list_azur_lane_port = [0, 1, 2, 3]
    zones = {}

    def _load_zone_info(self):
        if self._zone_loaded:
            return False

        self.zones = {}
        for index, info in DIC_OS_MAP.items():
            info['zone_id'] = index
            self.zones[index] = Zone(info)

        self._zone_loaded = True
        return True

    def camera_to_zone(self, camera, region=None):
        """
        Args:
            camera (tuple): Point in os_globe_map.png
            region (int): Limit zone in specific region.

        Returns:
            Zone:
        """
        self._load_zone_info()
        if region is None:
            zones = list(self.zones.values())
        else:
            zones = [z for z in self.zones.values() if z.region == region]
        distance = np.linalg.norm(np.subtract([z.location for z in zones], camera), axis=1)
        return zones[int(np.argmin(distance))]

    def name_to_zone(self, name):
        """
        Args:
            name (str, int, Zone): Name in CN/EN/JP, zone id, or Zone instance.

        Returns:
            Zone:
        """
        self._load_zone_info()
        if isinstance(name, Zone):
            return name
        elif isinstance(name, int):
            return self.zones[name]
        elif isinstance(name, str) and name.isdigit():
            return self.zones[name]
        else:
            def parse_name(n):
                n = str(n).replace(' ', '').lower()
                return n

            name = parse_name(name)
            for zone in self.zones.values():
                if name == parse_name(zone.cn) or name == parse_name(zone.en) or name == parse_name(zone.jp):
                    return zone
            logger.warning(f'Unable to find OS globe zone: {name}')
            raise ScriptError(f'Unable to find OS globe zone: {name}')

    def zone_is_azur_lane_port(self, zone):
        """
        Args:
            zone (str, int, Zone): Name in CN/EN/JP, zone id, or Zone instance.

        Returns:
            bool:
        """
        zone = self.name_to_zone(zone)
        return zone.zone_id in self._list_azur_lane_port

    def zone_nearest_azur_lane_port(self, zone):
        """
        Args:
            zone (str, int, Zone): Name in CN/EN/JP, zone id, or Zone instance.

        Returns:
            Zone:
        """
        zone = self.name_to_zone(zone)
        ports = [self.name_to_zone(port) for port in self._list_azur_lane_port]
        # In same region
        for port in ports:
            if zone.region == port.region:
                return port
        # In different region
        distance = np.linalg.norm(np.subtract([port.location for port in ports], zone.location), axis=1)
        port = ports[int(np.argmin(distance))]
        return port
