from module.base.utils import location2node
from module.logger import logger


class GridInfo:
    """
    Class that gather basic information of a grid in map_v1.

    Visit 碧蓝航线WIKI(Chinese Simplified) http://wiki.biligame.com/blhx, to get basic info of a map_v1. For example,
    visit http://wiki.biligame.com/blhx/7-2, to know more about campaign 7-2, which includes boss point, enemy spawn point.

    A grid contains these unchangeable properties which can known from WIKI.
    | print_name | property_name  | description             |
    |------------|----------------|-------------------------|
    | ++         | is_land        | fleet can't go to land  |
    | --         | is_sea         | sea                     |
    | __         |                | submarine spawn point   |
    | SP         | is_spawn_point | fleet may spawns here   |
    | ME         | may_enemy      | enemy may spawns here   |
    | MB         | may_boss       | boss may spawns here    |
    | MM         | may_mystery    | mystery may spawns here |
    | MA         | may_ammo       | fleet can get ammo here |
    | MS         | may_siren      | Siren/Elite enemy spawn |
    """

    # is_sea --
    is_land = False  # ++
    is_spawn_point = False  # SP

    may_enemy = False  # ME
    may_boss = False  # MB
    may_mystery = False  # MM
    may_ammo = False  # MA
    may_siren = False  # MS

    is_enemy = False  # example: 0L 1M 2C 3T 3E
    is_boss = False  # BO
    is_mystery = False  # MY
    is_ammo = False  # AM
    is_fleet = False  # FL
    is_current_fleet = False
    is_submarine = False  # SS
    is_siren = False  # SI

    enemy_scale = 0
    enemy_genre = None  # Light, Main, Carrier, Treasure, Enemy(unknown)

    is_cleared = False
    is_ambush_save = False
    is_caught_by_siren = False
    cost = 9999
    cost_1 = 9999
    cost_2 = 9999
    connection = None
    weight = 1

    location = None

    def decode(self, text):
        text = text.upper()
        dic = {
            '++': 'is_land',
            'SP': 'is_spawn_point',
            'ME': 'may_enemy',
            'MB': 'may_boss',
            'MM': 'may_mystery',
            'MA': 'may_ammo',
            'MS': 'may_siren',
        }
        if text in dic:
            self.__setattr__(dic[text], True)
        if self.may_enemy or self.may_boss or self.may_mystery or self.may_mystery:
            self.is_ambush_save = True
        if self.may_siren:
            self.may_enemy = True
        if self.may_boss:
            self.may_enemy = True

    def encode(self):
        dic = {
            '++': 'is_land',
            'BO': 'is_boss',
        }
        for key, value in dic.items():
            if self.__getattribute__(value):
                return key

        if self.is_siren:
            return self.enemy_genre.split('_')[1][:2].upper() if self.enemy_genre else 'SU'

        if self.is_enemy:
            return '%s%s' % (self.enemy_scale, self.enemy_genre[0].upper()) \
                if self.enemy_genre and self.enemy_scale else '0E'

        dic = {
            'FL': 'is_current_fleet',
            'Fl': 'is_fleet',
            'Fc': 'is_caught_by_siren',
            'MY': 'is_mystery',
            'AM': 'is_ammo',
            '==': 'is_cleared'
        }
        for key, value in dic.items():
            if self.__getattribute__(value):
                return key

        return '--'

    def __str__(self):
        return location2node(self.location)

    __repr__ = __str__

    def __hash__(self):
        return hash(self.location)

    @property
    def str(self):
        return self.encode()

    @property
    def is_sea(self):
        return False if self.is_land or self.is_enemy or self.is_boss else True

    @property
    def may_carrier(self):
        return self.is_sea and not self.may_enemy

    @property
    def is_accessible(self):
        return self.cost < 9999

    @property
    def is_accessible_1(self):
        return self.cost_1 < 9999

    @property
    def is_accessible_2(self):
        return self.cost_2 < 9999

    @property
    def is_nearby(self):
        return self.cost < 20

    def update(self, info, is_carrier_scan=False, ignore_may=False, ignore_cleared=False):
        """
        Args:
            info (GridInfo):
            is_carrier_scan (bool): Is a scan for mystery: enemy_searching, which ignore may_enemy spawn point.
            ignore_may (bool): Ignore map_data, force update.
            ignore_cleared (bool): Ignore is_cleared property.
        """
        if info.is_caught_by_siren:
            self.is_caught_by_siren = True

        for item in ['boss', 'siren']:
            if info.enemy_scale or self.enemy_scale:
                break
            if info.__getattribute__('is_' + item):
                if item == 'boss':
                    flag = not info.is_fleet
                else:
                    flag = not info.is_fleet and not self.is_fleet
                if not ignore_may:
                    flag &= self.__getattribute__('may_' + item)
                if not ignore_cleared:
                    flag &= not self.is_cleared
                if flag:
                    self.__setattr__('is_' + item, True)
                    # self.is_enemy = True
                    # self.enemy_scale = 0
                    self.enemy_genre = info.enemy_genre
                    return True
                else:
                    logger.info(f'Wrong Prediction. Grid: {self}, Attr: is_{item}')

        if info.is_enemy:
            flag = not info.is_fleet and not self.is_fleet and not self.is_siren
            if not is_carrier_scan:
                if not ignore_may:
                    flag &= self.may_enemy
                if not ignore_cleared:
                    flag &= not self.is_cleared
            if flag:
                self.is_enemy = True
                self.enemy_scale = info.enemy_scale
                self.enemy_genre = info.enemy_genre
                if self.may_siren:
                    self.is_siren = True
                return True
            else:
                logger.info(f'Wrong Prediction. Grid: {self}, Attr: is_enemy')

        for item in ['mystery', 'ammo']:
            if info.__getattribute__('is_' + item):
                if self.__getattribute__('may_' + item) or ignore_may:
                    self.__setattr__('is_' + item, True)
                    return True
                else:
                    logger.info(f'Wrong Prediction. Grid: {self}, Attr: {item}')
                    # failure += 1

        self.is_fleet = info.is_fleet
        if info.is_current_fleet:
            self.is_current_fleet = True
        return False

    def wipe_out(self):
        """
        Call this method when a fleet step on grid.
        """
        self.is_enemy = False
        self.enemy_scale = 0
        self.enemy_genre = None
        self.is_mystery = False
        self.is_boss = False
        self.is_ammo = False
        self.is_siren = False
        self.is_caught_by_siren = False

    def reset(self):
        """
        Call this method after entering a map.
        """
        self.wipe_out()
        self.is_fleet = False
        self.is_current_fleet = False
        self.is_submarine = False
        self.is_cleared = False

    def covered_grid(self):
        """Relative coordinate of the covered grid.

        Returns:
            list[tuple]:
        """
        if self.is_current_fleet:
            return [(0, -1), (0, -2)]
        if self.is_fleet or self.is_siren or self.is_mystery:
            return [(0, -1)]

        return []
