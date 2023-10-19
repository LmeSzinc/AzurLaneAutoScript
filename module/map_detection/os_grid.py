from module.base.utils import *
from module.map_detection.grid import Grid, GridInfo, GridPredictor
from module.map_detection.utils_assets import ASSETS
from module.os.assets import *
from module.os.radar import RadarGrid
from module.template.assets import *


class OSGridInfo(GridInfo):
    is_os = True

    is_enemy = False  # Red gun
    is_resource = False  # green box to get items
    is_exclamation = False  # Yellow exclamation mark '!'
    is_meowfficer = False  # Blue meowfficer
    is_question = False  # White question mark '?'
    is_ally = False  # Ally cargo ship in daily mission, yellow '!' on radar
    is_akashi = False  # White question mark '?'
    is_scanning_device = False
    is_logging_tower = False
    is_exploration_reward = False
    is_fleet_mechanism = False

    is_fleet = False

    is_radar_scanned = False

    @property
    def is_interactive_only(self):
        # Fleet can't goto this grid, but can only interact next to it
        return self.is_ally or self.is_akashi

    def encode(self):
        dic = {
            'AL': 'is_ally',
            'AK': 'is_akashi',
            'SD': 'is_scanning_device',
            'LT': 'is_logging_tower',
            'ER': 'is_exploration_reward',
            'FM': 'is_fleet_mechanism',
        }
        for key, value in dic.items():
            if self.__getattribute__(value):
                return key

        if self.is_siren:
            name = self.enemy_genre[6:8].upper() if self.enemy_genre else 'SU'
            return name if name else 'SU'

        if self.is_enemy:
            return '%s%s' % (
                self.enemy_scale if self.enemy_scale else 0,
                self.enemy_genre[0].upper() if self.enemy_genre else 'E')

        dic = {
            'RE': 'is_resource',
            'EX': 'is_exclamation',
            'ME': 'is_meowfficer',
            'QU': 'is_question',
            'FL': 'is_fleet',
            '==': 'is_radar_scanned'
        }
        for key, value in dic.items():
            if self.__getattribute__(value):
                return key

        return '--'

    def merge(self, info, mode='normal'):
        """
        Args:
            info (OSGridInfo, RadarGrid):
            mode (str): Scan mode, must be 'normal' in OS

        Returns:
            bool: If success.
        """
        if isinstance(info, RadarGrid):
            self.is_radar_scanned = True

        if info.is_ally:
            self.is_ally = True
            return True
        if info.is_akashi:
            self.is_akashi = True
            return True
        if info.is_scanning_device:
            self.is_scanning_device = True
            return True
        if info.is_logging_tower:
            self.is_logging_tower = True
            return True
        if info.is_exploration_reward:
            self.is_exploration_reward = True
            return True
        if info.is_fleet_mechanism:
            self.is_fleet_mechanism = True
            return True

        if info.is_question:
            self.is_question = True
            return True
        if info.is_meowfficer:
            self.is_meowfficer = True
            return True
        if info.is_exclamation:
            self.is_exclamation = True
            return True
        if info.is_resource:
            self.is_resource = True
            return True
        if info.is_enemy:
            self.is_enemy = True
            if info.enemy_scale:
                self.enemy_scale = info.enemy_scale
            if info.enemy_genre and not (info.enemy_genre == 'Enemy' and self.enemy_genre):
                self.enemy_genre = info.enemy_genre
            return True

        # if info.is_fleet:
        #     self.is_fleet = True
        #     return True

        return True

    def wipe_out(self):
        """
        Call this method when a fleet step on grid.
        """
        super().wipe_out()

        self.is_enemy = False
        self.is_resource = False
        self.is_exclamation = False
        self.is_meowfficer = False
        self.is_question = False
        self.is_scanning_device = False
        self.is_logging_tower = False
        self.is_exploration_reward = False
        self.is_fleet_mechanism = False

    def reset(self):
        """
        Call this method after entering a map.
        """
        super().reset()

        self.is_radar_scanned = False
        self.is_ally = False
        self.is_akashi = False


class OSGridPredictor(GridPredictor):
    def predict(self):
        self.enemy_genre = self.predict_enemy_genre()
        # self.enemy_scale = self.predict_enemy_scale()
        # self.is_resource = self.predict_resource()
        # self.is_meowfficer = self.predict_meowfficer()  # This will increase the overall time cost about 100ms
        # self.is_ally = self.predict_ally()
        self.is_akashi = self.enemy_genre == 'Akashi'
        self.is_scanning_device = self.enemy_genre == 'ScanningDevice'
        self.is_logging_tower = self.enemy_genre == 'LoggingTower'
        self.is_exploration_reward = self.enemy_genre == 'ExplorationReward'
        self.is_current_fleet = self.predict_current_fleet()
        self.is_fleet = self.is_current_fleet
        self.is_fleet_mechanism = self.predict_fleet_mechanism()

        if self.enemy_genre:
            self.is_enemy = True
        if self.enemy_scale:
            self.is_enemy = True
        # if not self.is_enemy:
        #     self.is_enemy = self.predict_static_red_border()
        if self.is_enemy and not self.enemy_genre:
            self.enemy_genre = 'Enemy'
        if self.config.MAP_HAS_SIREN:
            if self.enemy_genre is not None and self.enemy_genre.startswith('Siren'):
                self.is_siren = True
                self.enemy_scale = 0

    def predict_fleet(self):
        # OS don't have ammo icon
        return super().predict_current_fleet()

    def predict_sea(self):
        color = cv2.mean(self.image_trans)
        if not min(color[1], color[2]) > color[0] + 20:
            return False

        area = area_pad((48, 48, 48 + 46, 48 + 46), pad=5)
        res = cv2.matchTemplate(ASSETS.tile_center_image, crop(self.image_homo, area=area), cv2.TM_CCOEFF_NORMED)
        _, sim, _, _ = cv2.minMaxLoc(res)
        if sim > 0.8:
            return True

        # tile = 135
        # corner = 25
        # corner = [(5, 5, corner, corner), (tile - corner, 5, tile, corner), (5, tile - corner, corner, tile),
        #           (tile - corner, tile - corner, tile, tile)]
        # for area, template in zip(corner[::-1], ASSETS.tile_corner_image_list[::-1]):
        #     res = cv2.matchTemplate(template, crop(self.image_homo, area=area), cv2.TM_CCOEFF_NORMED)
        #     _, sim, _, _ = cv2.minMaxLoc(res)
        #     if sim > 0.8:
        #         return True

        return False

    _os_template_enemy = {
        'Akashi': TEMPLATE_SIREN_Akashi,
        'ScanningDevice': TEMPLATE_ScanningDevice,
        'LoggingTower': TEMPLATE_LoggingTower,
        'ExplorationReward': TEMPLATE_ExplorationReward,
    }
    _os_template_enemy_upper = {
        'ScanningDevice': TEMPLATE_ScanningDeviceUpper,
        'LoggingTower': TEMPLATE_LoggingTowerUpper,
    }

    def predict_enemy_genre(self):
        image = rgb2gray(self.relative_crop((-0.5, -1, 0.5, 0), shape=(60, 60)))
        for name, template in self._os_template_enemy.items():
            if template.match(image):
                return name

        image = rgb2gray(self.relative_crop((-0.5, -2, 0.5, -1), shape=(60, 60)))
        for name, template in self._os_template_enemy_upper.items():
            if template.match(image):
                return name

        return None

    def predict_enemy_scale(self):
        """
        Detect the icon on the upper-left which shows enemy scale: Large, Middle, Small.

        Returns:
            int: 1: Small, 2: Middle, 3: Large, 0: Unknown.
        """
        point = (-0.385, 0.815)
        size = (0.53, 0.53)
        image = self.relative_crop((point[0] - size[0], point[1] - size[1], point[0], point[1]), shape=(50, 50))
        red = color_similarity_2d(image, (255, 130, 132))
        yellow = color_similarity_2d(image, (255, 235, 156))

        if TEMPLATE_ENEMY_L.match(red):
            scale = 3
        elif TEMPLATE_ENEMY_M.match(yellow):
            scale = 2
        # Disable the detection of 1 triangle enemies
        # In OS, light tower on map will detect to be 1 triangle enemy
        # elif TEMPLATE_ENEMY_S.match(yellow):
        #     scale = 1
        else:
            scale = 0

        return scale

    def predict_resource(self):
        image = rgb2gray(self.relative_crop((-0.5, -1, 0.5, 0), shape=(60, 60)))
        return TEMPLATE_OS_Resource.match(image, similarity=0.85)

    def predict_meowfficer(self):
        image = rgb2gray(self.image_trans)
        return TEMPLATE_OS_Meowfficer.match(image, similarity=0.85)

    def predict_ally(self):
        # Ally cargo ship in daily mission
        image = rgb2gray(self.relative_crop((-0.5, -0.5, 0.5, 0.5), shape=(60, 60)))
        return TEMPLATE_OS_AllyCargo.match(image, similarity=0.85)

    def predict_akashi(self):
        image = rgb2gray(self.relative_crop((-0.5, -1, 0.5, 0), shape=(60, 60)))
        return TEMPLATE_SIREN_Akashi.match(image, similarity=0.85)

    def predict_caught_by_siren(self):
        # Detect the red slash background of `In action`.
        return self.relative_rgb_count(
            area=(-1, -0.5, 0, 0.5), color=(255, 109, 91), shape=(50, 50), threshold=221) > 120

    def predict_fleet_mechanism(self):
        # Get the upper border
        area = self.grid2screen(np.array([(0, 0), (1, 0.2)]))
        area = np.rint(area.flatten()).astype(int).tolist()
        # It should in cyan
        h = (185, 195)
        s = (15, 90)
        v = (60, 100)
        image = cv2.cvtColor(crop(self.image, area), cv2.COLOR_RGB2HSV)
        lower = (h[0] / 2, s[0] * 2.55, v[0] * 2.55)
        upper = (h[1] / 2 + 1, s[1] * 2.55 + 1, v[1] * 2.55 + 1)
        image = cv2.inRange(image, lower, upper)
        # Flatten to a horizontal line
        line = np.max(image, axis=0)
        # Line should be continuous
        # If not, a fleet may stand on it
        if np.mean(line) < 180:
            return False
        # Should also have random white rectangles
        area = self.grid2screen(np.array([(0.2, 0.2), (0.8, 0.8)]))
        area = np.rint(area.flatten()).astype(int).tolist()
        image = color_similarity_2d(crop(self.image, area), color=(255, 255, 255))
        count = image[image > 221].shape[0]
        if count < 30:
            return False
        # Shouldn't contain any thing green or yellow
        # Green is island and yellow is belt
        # image = cv2.cvtColor(crop(self.image, area), cv2.COLOR_RGB2HSV)
        # h = (0, 180)
        # s = (30, 90)
        # v = (30, 100)
        # lower = (h[0] / 2, s[0] * 2.55, v[0] * 2.55)
        # upper = (h[1] / 2 + 1, s[1] * 2.55 + 1, v[1] * 2.55 + 1)
        # image_in_range = cv2.inRange(image, lower, upper)
        # if image_in_range[image_in_range > 0].shape[0] > 30:
        #     return False
        # Should match the letter `2`
        image = rgb2gray(self.image_trans)
        sim, button = TEMPLATE_FleetMechanism.match_result(image)
        point = (53, 37)
        distance = np.linalg.norm(np.subtract(button.area[:2], point))
        if distance > 5 or sim < 0.3:
            return False

        return True


class OSGrid(OSGridInfo, OSGridPredictor, Grid):
    pass
