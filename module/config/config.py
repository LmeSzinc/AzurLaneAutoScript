import codecs
import configparser
import copy
import os
from datetime import timezone

import numpy as np

import module.config.server as server
from module.base.timer import *
from module.config.dictionary import *
from module.config.update import get_config
from module.logger import logger


class AzurLaneConfig:
    """
    Basic Config.
    """
    CONFIG_FILE = ''
    config = configparser.ConfigParser(interpolation=None)
    start_time = datetime.now()

    UPDATE_CHECK = True
    ENABLE_NOTIFICATIONS = True
    ENABLE_2X_BOOK = False
    UPDATE_METHOD = 'api'  # web, api
    UPDATE_PROXY = ''
    GITHUB_TOKEN = ''
    SERVER = server.server
    logger.attr('Server', SERVER)

    """
    Fleet
    """
    ENABLE_FLEET_CONTROL = True  # Deprecated, must enable
    ENABLE_MAP_FLEET_LOCK = True
    ENABLE_FLEET_REVERSE_IN_HARD = False
    ENABLE_AUTO_SEARCH = False
    # fleet1_mob_fleet2_boss, fleet1_boss_fleet2_mob, fleet1_all_fleet2_standby, fleet1_standby_fleet2_all
    AUTO_SEARCH_SETTING = 'fleet1_mob_fleet2_boss'
    # Fleet 1-6, if empty use 0.
    FLEET_1 = 1
    FLEET_2 = 2
    # Formation 1-3.
    FLEET_1_FORMATION = 2
    FLEET_2_FORMATION = 2
    # Fleet step 1-6
    FLEET_1_STEP = 3
    FLEET_2_STEP = 2
    # Fleet 1-2, if empty use 0.
    SUBMARINE = 0
    # Combat auto mode: combat_auto, combat_manual, stand_still_in_the_middle, hide_in_bottom_left
    FLEET_1_AUTO_MODE = 'combat_auto'
    FLEET_2_AUTO_MODE = 'combat_auto'

    MOVABLE_ENEMY_FLEET_STEP = 2
    MOVABLE_ENEMY_TURN = (2,)
    MOVABLE_NORMAL_ENEMY_TURN = (1,)

    """
    module.assets
    """
    ASSETS_FOLDER = './assets'

    """
    module.base
    """
    COLOR_SIMILAR_THRESHOLD = 10
    BUTTON_OFFSET = 30
    BUTTON_MATCH_SIMILARITY = 0.85
    SLEEP_AFTER_CLICK = 0
    WAIT_BEFORE_SAVING_SCREEN_SHOT = 1

    """
    module.combat
    """
    ENABLE_SAVE_GET_ITEMS = True
    SUBMARINE_MODE = ''
    SUBMARINE_CALL_AT_BOSS = False
    COMBAT_SCREENSHOT_INTERVAL = 2

    """
    module.combat.hp_balance
    """
    ENABLE_HP_BALANCE = False
    ENABLE_LOW_HP_WITHDRAW = True
    SCOUT_HP_DIFFERENCE_THRESHOLD = 0.2
    SCOUT_HP_WEIGHTS = [1000, 1000, 1000]
    EMERGENCY_REPAIR_SINGLE_THRESHOLD = 0.3
    EMERGENCY_REPAIR_HOLE_THRESHOLD = 0.6
    LOW_HP_WITHDRAW_THRESHOLD = 0.2

    """
    module.combat.level
    """
    LV120_TRIGGERED = False

    """
    module.campaign
    """
    CAMPAIGN_NAME = 'default'
    CAMPAIGN_MODE = 'normal'

    ENABLE_EXCEPTION = True
    ENABLE_GAME_STUCK_HANDLER = True

    ENABLE_STOP_CONDITION = True
    ENABLE_FAST_FORWARD = True
    STOP_IF_OIL_LOWER_THAN = 5000
    STOP_IF_COUNT_GREATER_THAN = 0
    STOP_IF_TIME_REACH = 0
    STOP_IF_TRIGGER_EMOTION_LIMIT = False
    STOP_IF_DOCK_FULL = False
    STOP_IF_REACH_LV120 = False
    STOP_IF_MAP_REACH = 'no'  # no, map_100, map_3_star, map_green_without_3_star, map_green
    STOP_IF_GET_SHIP = False

    MAP_CLEAR_ALL_THIS_TIME = False
    # From chapter_template.lua
    STAR_REQUIRE_1 = 1
    STAR_REQUIRE_2 = 2
    STAR_REQUIRE_3 = 3
    # In Dreamwaker's Butterfly (event_20200917) add new stage entrance icons, called `blue`.
    STAGE_ENTRANCE = ['normal']  # normal, blue, half

    """
    module.event
    """
    EVENT_NAME = ''
    EVENT_STAGE = ''
    EVENT_NAME_AB = ''
    ENABLE_EVENT_AB = False
    ENABLE_EVENT_SP = False
    EVENT_AB_CHAPTER = 'chapter_ab'  # chapter_ab, chapter_abcd, chapter_t, chapter_ht
    EVENT_SP_MOB_FLEET = 1

    """
    module.combat.emotion
    """
    ENABLE_EMOTION_REDUCE = True
    IGNORE_LOW_EMOTION_WARN = False
    EMOTION_LIMIT_TRIGGERED = False
    TIME_FORMAT = '%Y-%m-%d_%H:%M:%S'
    # 20, 30, 40, 50, 60
    FLEET_1_RECOVER_PER_HOUR = 50
    FLEET_1_EMOTION_LIMIT = 120
    FLEET_2_RECOVER_PER_HOUR = 20
    FLEET_2_EMOTION_LIMIT = 50

    """
    module.device
    """
    SERIAL = ''
    PACKAGE_NAME = ''
    COMMAND = ''
    ASCREENCAP_FILEPATH_LOCAL = './bin/ascreencap'
    ASCREENCAP_FILEPATH_REMOTE = '/data/local/tmp/ascreencap'
    MINITOUCH_FILEPATH_REMOTE = '/data/local/tmp/minitouch'
    # Speed: aScreenCap >> uiautomator2 > ADB
    DEVICE_SCREENSHOT_METHOD = 'aScreenCap'  # ADB, uiautomator2, aScreenCap
    # Speed: uiautomator2 >> ADB
    DEVICE_CONTROL_METHOD = 'uiautomator2'  # ADB, uiautomator2, minitouch
    # USE_ADB_SCREENSHOT = True
    # USE_ADB_CONTROL = False
    SCREEN_SHOT_SAVE_FOLDER_BASE = './screenshot'
    SCREEN_SHOT_SAVE_FOLDER = ''
    SCREEN_SHOT_SAVE_INTERVAL = 5  # Seconds between two save. Saves in the interval will be dropped.

    """
    module.daily
    """
    ENABLE_DAILY_MISSION = True
    USE_DAILY_SKIP = True
    # Order of FLEET_DAILY
    # 0 商船护送, 1 海域突进, 2 斩首行动, 3 战术研修, 4 破交作战
    # 0 Escort Mission, 1 Advance Mission, 2 Fierce Assault, 3 Tactical Training, 4 Supply Line Disruption
    FLEET_DAILY = [3, 3, 3, 3, 0]
    FLEET_DAILY_EQUIPMENT = [1, 1, 1, 1, 1, 1]
    DAILY_CHOOSE = {
        4: 1,  # 商船护送, Escort Mission
        5: 1,  # 海域突进, Advance Mission
        1: 2,  # 战术研修, 1航空 2炮击 3雷击. Tactical Training, 1 Aviation, 2 Firepower, 3 Torpedo
        2: 1,  # 斩首行动, Fierce Assault
        3: 1,  # 破交作战, Supply Line Disruption
    }

    """
    module.handler
    """
    AMBUSH_EVADE = True

    """
    module.hard
    """
    ENABLE_HARD_CAMPAIGN = True
    HARD_CAMPAIGN = '10-4'
    FLEET_HARD = 1
    FLEET_HARD_EQUIPMENT = [1, 1, 1, 1, 1, 1]

    """
    module.exercise
    """
    ENABLE_EXERCISE = True
    EXERCISE_CHOOSE_MODE = 'max_exp'  # 'max_exp', 'easiest', 'leftmost', 'easiest_else_exp'
    EXERCISE_PRESERVE = 0
    LOW_HP_THRESHOLD = 0.40
    LOW_HP_CONFIRM_WAIT = 1.0
    OPPONENT_CHALLENGE_TRIAL = 1
    EXERCISE_FLEET_EQUIPMENT = [1, 1, 1, 1, 1, 1]

    """
    module.raid
    """
    RAID_NAME = ''
    RAID_MODE = 'hard'  # hard, normal, easy
    RAID_USE_TICKET = False
    ENABLE_RAID_DAILY = False
    RAID_DAILY_NAME = ''
    RAID_HARD = True
    RAID_NORMAL = True
    RAID_EASY = True

    """
    error_log
    """
    PERSPECTIVE_ERROR_LOG_FOLDER = './log/perspective_error'
    ERROR_LOG_FOLDER = './log/error'
    ENABLE_ERROR_LOG_AND_SCREENSHOT_SAVE = True
    ENABLE_PERSPECTIVE_ERROR_IMAGE_SAVE = False

    """
    module.map.fleet
    """
    MAP_HAS_AMBUSH = True
    MAP_HAS_FLEET_STEP = False
    MAP_HAS_MOVABLE_ENEMY = False
    MAP_HAS_MOVABLE_NORMAL_ENEMY = False
    MAP_HAS_SIREN = False
    MAP_HAS_DYNAMIC_RED_BORDER = False
    MAP_HAS_MAP_STORY = False  # event_20200521_cn(穹顶下的圣咏曲) adds after-combat story.
    MAP_HAS_WALL = False  # event_20200521_cn(穹顶下的圣咏曲) adds wall between grids.
    MAP_HAS_PT_BONUS = False  # 100% PT bonus if success to catch enemy else 50%. Retreat get 0%.
    MAP_IS_ONE_TIME_STAGE = False
    MAP_HAS_PORTAL = False
    MAP_HAS_LAND_BASED = False
    MAP_HAS_MAZE = False  # event_20210422_cn adds maze and maze walls move every 3 rounds.
    MAP_FOCUS_ENEMY_AFTER_BATTLE = False  # Operation siren
    MAP_ENEMY_TEMPLATE = ['Light', 'Main', 'Carrier', 'Treasure']
    MAP_SIREN_TEMPLATE = ['DD', 'CL', 'CA', 'BB', 'CV']
    MAP_ENEMY_GENRE_DETECTION_SCALING = {}  # Key: str, Template name, Value: float, scaling factor
    MAP_SIREN_MOVE_WAIT = 1.5  # The enemy moving takes about 1.2 ~ 1.5s.
    MAP_SIREN_COUNT = 0
    MAP_MYSTERY_HAS_CARRIER = False
    MAP_GRID_CENTER_TOLERANCE = 0.1

    POOR_MAP_DATA = False
    FLEET_BOSS = 2
    # Convert map grid distance to swipe distance
    # Usually range from 1/0.62 to 1/0.61
    # Value may be different in different maps
    MAP_SWIPE_MULTIPLY = 1.626
    # When using minitouch, MAP_SWIPE_MULTIPLY is a fixed value.
    MAP_SWIPE_MULTIPLY_MINITOUCH = 1.572
    # Swipe distance in map grid lower than this will be dropped,
    # because a closing swipe will be treat as a click in game.
    MAP_SWIPE_DROP = 0.15
    MAP_SWIPE_PREDICT = True

    """
    module.retire
    """
    ENABLE_RETIREMENT = True
    USE_ONE_CLICK_RETIREMENT = False
    RETIREMENT_METHOD = 'one_click_retire'  # enhance, old_retire, one_click_retire
    ENHANCE_FAVOURITE = False
    ENHANCE_ORDER_STRING = ''
    ENHANCE_CHECK_PER_CATEGORY = 2
    DOCK_FULL_TRIGGERED = False
    GET_SHIP_TRIGGERED = False
    RETIRE_AMOUNT = 'all'  # all, 10
    RETIRE_N = True
    RETIRE_R = False
    RETIRE_SR = False
    RETIRE_SSR = False

    """
    module.map_detection
    """
    SCREEN_SIZE = (1280, 720)
    DETECTING_AREA = (123, 55, 1280, 720)
    SCREEN_CENTER = (SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 2)
    MID_Y = SCREEN_CENTER[1]
    DETECTION_BACKEND = 'homography'
    # In event_20200723_cn B3D3, Grid have 1.2x width, images on the grid still remain the same.
    GRID_IMAGE_A_MULTIPLY = 1.0

    """
    module.map_detection.homography
    """
    HOMO_TILE = (140, 140)
    HOMO_CENTER_OFFSET = (48, 48)
    # [upper-left, upper-right, bottom-left, bottom-right]
    HOMO_CORNER_OFFSET_LIST = [(-42, -42), (68, -42), (-42, 69), (69, 69)]

    HOMO_CENTER_GOOD_THRESHOLD = 0.9
    HOMO_CENTER_THRESHOLD = 0.8
    HOMO_CORNER_THRESHOLD = 0.8
    HOMO_RECTANGLE_THRESHOLD = 10

    HOMO_EDGE_HOUGHLINES_THRESHOLD = 120
    HOMO_EDGE_COLOR_RANGE = (0, 24)
    # ((x, y), [upper-left, upper-right, bottom-left, bottom-right])
    HOMO_STORAGE = None

    """
    module.map_detection.perspective
    """
    # Parameters for scipy.signal.find_peaks
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (150, 255 - 40),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 24, 255),
        'prominence': 10,
        'distance': 50,
        # 'width': (0, 7),
        'wlen': 1000
    }
    # Parameters for cv2.HoughLines
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 75
    EDGE_LINES_HOUGHLINES_THRESHOLD = 75
    # Parameters for lines pre-cleansing
    HORIZONTAL_LINES_THETA_THRESHOLD = 0.005
    VERTICAL_LINES_THETA_THRESHOLD = 18
    TRUST_EDGE_LINES = False  # True to use edge to crop inner, false to use inner to crop edge
    # Parameters for perspective calculating
    VANISH_POINT_RANGE = ((540, 740), (-3000, -1000))
    DISTANCE_POINT_X_RANGE = ((-3200, -1600),)
    # Parameters for line cleansing
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 3
    ERROR_LINES_TOLERANCE = (-10, 10)
    MID_DIFF_RANGE_H = (129 - 3, 129 + 3)
    MID_DIFF_RANGE_V = (129 - 3, 129 + 3)

    """
    module.daemon
    """
    ENABLE_SEMI_MAP_PREPARATION = True
    ENABLE_SEMI_STORY_SKIP = True

    """
    module.reward
    """
    ENABLE_REWARD = True
    REWARD_INTERVAL = '10, 40'  # str, such as '20', '10, 40'.
    REWARD_STOP_GAME_DURING_INTERVAL = False
    REWARD_LAST_TIME = datetime.now()
    ENABLE_DAILY_REWARD = False
    ENABLE_OIL_REWARD = True
    ENABLE_COIN_REWARD = True
    ENABLE_MISSION_REWARD = True
    ENABLE_COMMISSION_REWARD = True
    ENABLE_TACTICAL_REWARD = True

    COMMISSION_PRIORITY = {
        'major_comm': 0,
        'daily_comm': 100,
        'extra_drill': 20,
        'extra_part': 60,
        'extra_cube': 80,
        'extra_oil': 90,
        'extra_book': 70,
        'urgent_drill': 45,
        'urgent_part': 95,
        'urgent_book': 145,
        'urgent_box': 195,
        'urgent_cube': 165,
        'urgent_gem': 205,
        'urgent_ship': 155,
        'expire_shorter_than_2': 11,
        'expire_longer_than_6': -11,
        'duration_shorter_than_2': 11,
        'duration_longer_than_6': -11,
        'doa_daily': 500,
    }
    COMMISSION_TIME_LIMIT = 0

    TACTICAL_BOOK_TIER_MAX = 3
    TACTICAL_BOOK_TIER_MIN = 2
    TACTICAL_EXP_FIRST = True
    TACTICAL_IF_NO_BOOK_SATISFIED = 'cancel_tactical'  # cancel_tactical, use_the_first_book
    # TACTICAL_BOOK_TIER_NIGHT = 3
    # TACTICAL_EXP_FIRST_NIGHT = False
    # TACTICAL_NIGHT_RANGE = future_time_range('23:30-06:30')  # (Night start, night end), datetime.datetime instance.

    BUY_MEOWFFICER = 0  # 0 to 15.
    ENABLE_TRAIN_MEOWFFICER = False

    ENABLE_DORM_FEED = True
    ENABLE_DORM_REWARD = True
    # When having 6 ships in dorm, to use 6 kind of food, need interval (in minutes) greater than:
    # (14, 28, 42, 70, 139, 278)
    DORM_FEED_INTERVAL = '278, 480'  # str, such as '20', '10, 40'.
    DORM_COLLECT_INTERVAL = '60, 180'  # str, such as '20', '10, 40'.
    DORM_FEED_FILTER = '20000 > 10000 > 5000 > 3000 > 2000 > 1000'

    ENABLE_DATA_KEY_COLLECT = True

    """
    module.guild
    """
    ENABLE_GUILD_LOGISTICS = False
    ENABLE_GUILD_OPERATIONS = False
    GUILD_INTERVAL = '40, 60' # str, such as '20', '10, 40'.
    GUILD_LOGISTICS_ITEM_ORDER_STRING = 't1 > t2 > t3 > oxycola > coolant > coins > oil > merit'
    GUILD_LOGISTICS_PLATE_T1_ORDER_STRING = 'torpedo > antiair > plane > gun > general'
    GUILD_LOGISTICS_PLATE_T2_ORDER_STRING = 'torpedo > antiair > plane > gun > general'
    GUILD_LOGISTICS_PLATE_T3_ORDER_STRING = 'torpedo > antiair > plane > gun > general'
    GUILD_OPERATIONS_JOIN_THRESHOLD = 1
    ENABLE_GUILD_OPERATIONS_BOSS_AUTO = False
    ENABLE_GUILD_OPERATIONS_BOSS_RECOMMEND = False

    """
    module.research
    """
    ENABLE_RESEARCH_REWARD = True
    RESEARCH_FILTER_STRING = ''
    RESEARCH_FILTER_PRESET = 'series_3_than_2'  # customized, series_3, ...
    RESEARCH_USE_CUBE = True
    RESEARCH_USE_COIN = True
    RESEARCH_USE_PART = True

    """
    module.sos
    """
    SOS_FLEETS_CHAPTER_3 = [4, 0]
    SOS_FLEETS_CHAPTER_4 = [4, 0]
    SOS_FLEETS_CHAPTER_5 = [4, 0]
    SOS_FLEETS_CHAPTER_6 = [4, 0]
    SOS_FLEETS_CHAPTER_7 = [4, 6]
    SOS_FLEETS_CHAPTER_8 = [4, 6]
    SOS_FLEETS_CHAPTER_9 = [5, 6, 1]
    SOS_FLEETS_CHAPTER_10 = [4, 6, 1]

    """
    module.os.globe_detection
    """
    OS_GLOBE_HOMO_STORAGE = ((4, 3), ((445, 180), (879, 180), (376, 497), (963, 497)))
    OS_GLOBE_DETECTING_AREA = (0, 0, 1280, 720)
    OS_GLOBE_IMAGE_PAD = 700
    OS_GLOBE_IMAGE_RESIZE = 0.5
    OS_GLOBE_FIND_PEAKS_PARAMETERS = {
        'height': 100,
        # 'width': (0.9, 5),
        'prominence': 20,
        'distance': 35,
        'wlen': 500,
    }
    OS_LOCAL_FIND_PEAKS_PARAMETERS = {
        'height': 50,
        # 'width': (0.9, 5),
        'prominence': 20,
        'distance': 35,
        'wlen': 500,
    }

    """
    module.war_archives
    """
    USE_DATA_KEY = False
    WAR_ARCHIVES_NAME = ''
    WAR_ARCHIVES_STAGE = ''

    """
    module.os_ash
    """
    ENABLE_OS_ASH_ASSIST = True
    OS_ASH_ASSIST_TIER = 15

    """
    C_1_1_affinity_farming
    """
    C11_AFFINITY_BATTLE_COUNT = 0

    """
    C_7_2_mystery_farming
    """
    C72_BOSS_FLEET_STEP_ON_A3 = True

    """
    C_12_2_leveling
    """
    C122_S3_TOLERANCE = 0

    """
    C_12_4_leveling
    """
    C124_NON_S3_ENTER_TOLERANCE = 1
    C124_NON_S3_WITHDRAW_TOLERANCE = 0
    C124_AMMO_PICK_UP = 3

    """
    Os_semi_auto
    """
    ENABLE_OS_SEMI_STORY_SKIP = True

    """
    Os_world_clear
    """
    OS_WORLD_MIN_LEVEL = 1
    OS_WORLD_MAX_LEVEL = 4

    """
    module.os
    """
    DO_OS_IN_DAILY = False
    ENABLE_OS_ASH_ATTACK = True
    ENABLE_OS_MISSION_ACCEPT = True
    ENABLE_OS_SUPPLY_BUY = True
    ENABLE_OS_MISSION_FINISH = True
    ENABLE_OS_OBSCURE_FINISH = True
    ENABLE_OS_MEOWFFICER_FARMING = True

    ENABLE_OS_ACTION_POINT_BUY = False
    OS_ACTION_POINT_PRESERVE = 200
    OS_REPAIR_THRESHOLD = 0.4
    OS_ACTION_POINT_BOX_USE = True
    # 1 to 6. Recommend 3 or 5 for higher meowfficer searching point per action points ratio.
    OS_MEOWFFICER_FARMING_LEVEL = 5
    ENABLE_OS_AKASHI_SHOP_BUY = True
    # ActionPoint, PurpleCoins, RepairPack, TuringSample
    OS_ASKSHI_SHOP_PRIORITY = 'ActionPoint > PurpleCoins'

    """
    module.statistics
    """
    ENABLE_AZURSTAT = False
    AZURSTAT_ID = ''

    def create_folder(self):
        for folder in [self.ASSETS_FOLDER, self.PERSPECTIVE_ERROR_LOG_FOLDER, self.ERROR_LOG_FOLDER]:
            if folder and not os.path.exists(folder):
                os.mkdir(folder)
        self.SCREEN_SHOT_SAVE_FOLDER = self.SCREEN_SHOT_SAVE_FOLDER_BASE + '/' + self.CAMPAIGN_NAME
        if self.ENABLE_SAVE_GET_ITEMS and len(self.SCREEN_SHOT_SAVE_FOLDER_BASE.strip()):
            for folder in [self.SCREEN_SHOT_SAVE_FOLDER_BASE, self.SCREEN_SHOT_SAVE_FOLDER]:
                if folder and not os.path.exists(folder):
                    os.mkdir(folder)

    def merge(self, other):
        """
        Args:
            other (AzurLaneConfig, Config):

        Returns:
            AzurLaneConfig
        """
        config = copy.copy(self)
        for attr in dir(config):
            if attr.endswith('__'):
                continue
            if hasattr(other, attr):
                value = other.__getattribute__(attr)
                if value is not None:
                    config.__setattr__(attr, value)

        return config

    def load_config_file(self, name='alas'):
        self.CONFIG_FILE = f'./config/{name}.ini'
        self.config = get_config(ini_name=name)
        self.load_from_config(self.config)
        self.config_check()

    def config_check(self):
        if self.FLEET_1 == self.FLEET_2:
            logger.warning(f'Mob fleet [{self.FLEET_1}] and boss fleet [{self.FLEET_2}] is the same')
            logger.warning('They should to be set to different fleets')
            exit(1)
        if self.COMMAND.lower() == 'main' and self.CAMPAIGN_NAME.startswith('campaign_'):
            if int(self.CAMPAIGN_NAME.split('_')[1]) >= 7 and self.FLEET_2 == 0:
                logger.warning('You should use 2 fleets from chapter 7 to 13')
                logger.warning(f'Current: mob fleet [{self.FLEET_1}], boss fleet [{self.FLEET_2}]')
                exit(1)

    def save(self):
        self.config.write(codecs.open(self.CONFIG_FILE, "w+", "utf8"))

    def load_from_config(self, config):
        """
        Args:
            config(configparser.ConfigParser):
        """
        self.COMMAND = config.get('Command', 'command')

        # Emulator
        option = config['Emulator']
        self.SERIAL = option['serial']
        self.PACKAGE_NAME = option['package_name'].strip()
        self.ENABLE_ERROR_LOG_AND_SCREENSHOT_SAVE = to_bool(option['enable_error_log_and_screenshot_save'])
        self.ENABLE_PERSPECTIVE_ERROR_IMAGE_SAVE = to_bool(option['enable_perspective_error_image_save'])
        self.DEVICE_SCREENSHOT_METHOD = option['device_screenshot_method']
        self.DEVICE_CONTROL_METHOD = option['device_control_method']
        self.COMBAT_SCREENSHOT_INTERVAL = float(option['combat_screenshot_interval'])
        # UpdateCheck
        self.UPDATE_CHECK = to_bool(option['enable_update_check'])
        self.UPDATE_METHOD = option['update_method']
        self.UPDATE_PROXY = option['update_proxy']
        self.GITHUB_TOKEN = option['github_token']

        option = config['Setting']
        # Stop condition
        self.ENABLE_NOTIFICATIONS = to_bool(option['enable_notifications'])
        self.ENABLE_STOP_CONDITION = to_bool(option['enable_stop_condition'])
        self.ENABLE_EXCEPTION = to_bool(option['enable_exception'])
        self.ENABLE_FAST_FORWARD = to_bool(option['enable_fast_forward'])
        self.ENABLE_2X_BOOK = to_bool(option['enable_2x_book'])
        self.STOP_IF_COUNT_GREATER_THAN = int(option['if_count_greater_than'])
        if not option['if_time_reach'].isdigit():
            self.STOP_IF_TIME_REACH = future_time(option['if_time_reach'])
        else:
            self.STOP_IF_TIME_REACH = 0
        self.STOP_IF_OIL_LOWER_THAN = int(option['if_oil_lower_than'])
        self.STOP_IF_TRIGGER_EMOTION_LIMIT = to_bool(option['if_trigger_emotion_control'])
        self.STOP_IF_DOCK_FULL = to_bool(option['if_dock_full'])
        self.STOP_IF_REACH_LV120 = to_bool(option['if_reach_lv120'])
        self.STOP_IF_MAP_REACH = option['if_map_reach']
        self.STOP_IF_GET_SHIP = to_bool(option['if_get_ship'])
        # Fleet
        self.ENABLE_MAP_FLEET_LOCK = to_bool(option['enable_map_fleet_lock'])
        self.ENABLE_FLEET_REVERSE_IN_HARD = to_bool(option['enable_fleet_reverse_in_hard'])
        self.ENABLE_AUTO_SEARCH = to_bool(option['enable_auto_search'])
        self.AUTO_SEARCH_SETTING = option['auto_search_setting']
        for n in ['1', '2']:
            self.__setattr__(f'FLEET_{n}', int(option[f'fleet_index_{n}']) if to_bool(option[f'fleet_index_{n}']) else 0)
            self.__setattr__(f'FLEET_{n}_FORMATION', int(option[f'fleet_formation_{n}'].split('_')[1]))
            self.__setattr__(f'FLEET_{n}_STEP', int(option[f'fleet_step_{n}']))
            self.__setattr__(f'FLEET_{n}_AUTO_MODE', option[f'fleet_auto_mode_{n}'])
        self.SUBMARINE = int(option['fleet_index_4']) if to_bool(option['fleet_index_4']) else 0
        self.SUBMARINE_MODE = option['submarine_mode']
        self.SUBMARINE_CALL_AT_BOSS = option['submarine_mode'] == 'when_boss_combat_boss_appear'
        # Emotion
        self.ENABLE_EMOTION_REDUCE = to_bool(option['enable_emotion_reduce'])
        self.IGNORE_LOW_EMOTION_WARN = to_bool(option['ignore_low_emotion_warn'])
        for n in ['1', '2']:
            recover = dic_emotion_recover[option[f'emotion_recover_{n}']]
            recover += 10 if to_bool(option[f'hole_fleet_married_{n}']) else 0
            self.__setattr__(f'FLEET_{n}_RECOVER_PER_HOUR', recover)
            self.__setattr__(f'FLEET_{n}_EMOTION_LIMIT', dic_emotion_limit[option[f'emotion_control_{n}']])
        # HP balance, save get items -> combat
        self.ENABLE_HP_BALANCE = to_bool(option['enable_hp_balance'])
        self.ENABLE_LOW_HP_WITHDRAW = to_bool(option['enable_low_hp_withdraw'])
        self.SCOUT_HP_DIFFERENCE_THRESHOLD = float(option['scout_hp_difference_threshold'])
        self.SCOUT_HP_WEIGHTS = to_list(option['scout_hp_weights'])
        self.EMERGENCY_REPAIR_SINGLE_THRESHOLD = float(option['emergency_repair_single_threshold'])
        self.EMERGENCY_REPAIR_HOLE_THRESHOLD = float(option['emergency_repair_hole_threshold'])
        self.LOW_HP_WITHDRAW_THRESHOLD = float(option['low_hp_withdraw_threshold'])
        self.ENABLE_SAVE_GET_ITEMS = to_bool(option['enable_drop_screenshot'])
        self.SCREEN_SHOT_SAVE_FOLDER_BASE = option['drop_screenshot_folder']
        self.ENABLE_AZURSTAT = to_bool(option['enable_azurstat'])
        self.AZURSTAT_ID = option['azurstat_id']
        # Retirement
        self.ENABLE_RETIREMENT = to_bool(option['enable_retirement'])
        self.RETIREMENT_METHOD = option['retire_method']
        self.RETIRE_AMOUNT = option['retire_amount'].split('_')[1]
        self.ENHANCE_FAVOURITE = to_bool(option['enhance_favourite'])
        self.ENHANCE_ORDER_STRING = option['enhance_order_string']
        self.ENHANCE_CHECK_PER_CATEGORY = int(option['enhance_check_per_category'])
        for r in ['n', 'r']:
            self.__setattr__(f'RETIRE_{r.upper()}', to_bool(option[f'retire_{r}']))

        # Reward
        option = config['Reward']
        self.REWARD_INTERVAL = option['reward_interval']
        self.REWARD_STOP_GAME_DURING_INTERVAL = to_bool(option['reward_stop_game_during_interval'])
        for attr in ['enable_reward', 'enable_oil_reward', 'enable_coin_reward', 'enable_mission_reward',
                     'enable_dorm_reward', 'enable_dorm_feed',
                     'enable_commission_reward', 'enable_tactical_reward', 'enable_daily_reward',
                     'enable_research_reward',
                     'enable_data_key_collect', 'enable_train_meowfficer',
                     'enable_guild_logistics', 'enable_guild_operations', 'enable_guild_operations_boss_auto', 'enable_guild_operations_boss_recommend']:
            self.__setattr__(attr.upper(), to_bool(option[attr]))
        if not option['commission_time_limit'].isdigit():
            self.COMMISSION_TIME_LIMIT = future_time(option['commission_time_limit'])
        else:
            self.COMMISSION_TIME_LIMIT = 0
        for attr in self.COMMISSION_PRIORITY.keys():
            self.COMMISSION_PRIORITY[attr] = int(option[attr])
        self.DORM_FEED_INTERVAL = option['dorm_feed_interval']
        self.DORM_COLLECT_INTERVAL = option['dorm_collect_interval']
        self.DORM_FEED_FILTER = option['dorm_feed_filter']
        self.TACTICAL_BOOK_TIER_MAX = int(option['tactical_book_tier_max'])
        self.TACTICAL_BOOK_TIER_MIN = int(option['tactical_book_tier_min'])
        self.TACTICAL_EXP_FIRST = to_bool(option['tactical_exp_first'])
        self.TACTICAL_IF_NO_BOOK_SATISFIED = option['tactical_if_no_book_satisfied']
        # self.TACTICAL_NIGHT_RANGE = future_time_range(option['tactical_night_range'])
        # self.TACTICAL_BOOK_TIER_NIGHT = int(option['tactical_book_tier_night'])
        # self.TACTICAL_EXP_FIRST_NIGHT = to_bool(option['tactical_exp_first_night'])
        for item in ['coin', 'cube', 'part']:
            self.__setattr__(f'RESEARCH_USE_{item}'.upper(), to_bool(option[f'RESEARCH_USE_{item}'.lower()]))
        self.RESEARCH_FILTER_PRESET = option['research_filter_preset']
        self.RESEARCH_FILTER_STRING = option['research_filter_string']
        self.BUY_MEOWFFICER = int(option['buy_meowfficer'])
        self.GUILD_INTERVAL = option['guild_interval']
        self.GUILD_LOGISTICS_ITEM_ORDER_STRING = option['guild_logistics_item_order_string']
        self.GUILD_LOGISTICS_PLATE_T1_ORDER_STRING = option['guild_logistics_plate_t1_order_string']
        self.GUILD_LOGISTICS_PLATE_T2_ORDER_STRING = option['guild_logistics_plate_t2_order_string']
        self.GUILD_LOGISTICS_PLATE_T3_ORDER_STRING = option['guild_logistics_plate_t3_order_string']
        self.GUILD_OPERATIONS_JOIN_THRESHOLD = float(option['guild_operations_join_threshold'])

        option = config['Main']
        self.CAMPAIGN_MODE = option['campaign_mode']
        self.CAMPAIGN_NAME = option['main_stage']
        self.CAMPAIGN_NAME = 'campaign_' + self.CAMPAIGN_NAME.replace('-', '_')

        option = config['Daily']
        for n in ['daily_mission', 'hard_campaign', 'exercise']:
            self.__setattr__(f'ENABLE_{n.upper()}', option[f'enable_{n}'])
        # Daily mission
        self.ENABLE_DAILY_MISSION = to_bool(option['enable_daily_mission'])
        self.USE_DAILY_SKIP = to_bool(option['use_daily_skip'])
        for n in [1, 2, 3, 4, 5]:
            self.DAILY_CHOOSE[n] = dic_daily[option[f'daily_mission_{n}']]
        if option['daily_fleet'].isdigit():
            self.FLEET_DAILY = [int(option['daily_fleet'])] * 4 + [0]
        else:
            self.FLEET_DAILY = to_list(option['daily_fleet']) + [0]
        self.FLEET_DAILY_EQUIPMENT = to_list(option['daily_equipment'])
        # Hard
        self.ENABLE_HARD_CAMPAIGN = to_bool(option['enable_hard_campaign'])
        self.HARD_CAMPAIGN = option['hard_campaign']
        self.FLEET_HARD = int(option['hard_fleet'])
        self.FLEET_HARD_EQUIPMENT = to_list(option['hard_equipment'])
        # Exercise
        self.ENABLE_EXERCISE = to_bool(option['enable_exercise'])
        self.EXERCISE_CHOOSE_MODE = option['exercise_choose_mode']
        self.EXERCISE_PRESERVE = int(option['exercise_preserve'])
        self.OPPONENT_CHALLENGE_TRIAL = int(option['exercise_try'])
        self.LOW_HP_THRESHOLD = float(option['exercise_hp_threshold'])
        self.LOW_HP_CONFIRM_WAIT = float(option['exercise_low_hp_confirm'])
        self.EXERCISE_FLEET_EQUIPMENT = to_list(option['exercise_equipment'])
        # Event bonus
        # option = config['Event_daily_ab']
        self.ENABLE_EVENT_AB = to_bool(option['enable_event_ab'])
        self.ENABLE_EVENT_SP = to_bool(option['enable_event_sp'])
        self.EVENT_NAME_AB = option['event_name_ab']
        self.EVENT_AB_CHAPTER = option['event_ab_chapter']
        self.EVENT_SP_MOB_FLEET = int(option['event_sp_mob_fleet'])
        # Raid daily
        self.ENABLE_RAID_DAILY = to_bool(option['enable_raid_daily'])
        self.RAID_DAILY_NAME = option['raid_daily_name']
        self.RAID_HARD = to_bool(option['raid_hard'])
        self.RAID_NORMAL = to_bool(option['raid_normal'])
        self.RAID_EASY = to_bool(option['raid_easy'])
        # Operation Siren
        self.ENABLE_OS_ASH_ASSIST = to_bool(option['enable_os_ash_assist'])
        self.OS_ASH_ASSIST_TIER = int(option['os_ash_assist_tier'])

        # Event
        option = config['Event']
        self.EVENT_NAME = option['event_name']
        self.EVENT_STAGE = option['event_stage'].lower()

        # Sos
        option = config['Sos']
        for chapter in range(3, 11):
            self.__setattr__(f'SOS_FLEETS_CHAPTER_{chapter}', to_list(option[f'sos_fleets_chapter_{chapter}']))

        # War archives
        option = config['War_archives']
        self.WAR_ARCHIVES_NAME = option['war_archives_name']
        self.WAR_ARCHIVES_STAGE = option['war_archives_stage'].lower()

        # Raid
        option = config['Raid']
        self.RAID_NAME = option['raid_name']
        self.RAID_MODE = option['raid_mode']
        self.RAID_USE_TICKET = to_bool(option['raid_use_ticket'])

        # Event_daily_ab
        # option = config['Event_daily_ab']
        # self.EVENT_NAME_AB = option['event_name_ab']

        # Semi_auto
        option = config['Semi_auto']
        self.ENABLE_SEMI_MAP_PREPARATION = to_bool(option['enable_semi_map_preparation'])
        self.ENABLE_SEMI_STORY_SKIP = to_bool(option['enable_semi_story_skip'])

        # C_1_1_affinity_farming
        option = config['C11_affinity_farming']
        self.C11_AFFINITY_BATTLE_COUNT = int(option['affinity_battle_count'])

        # C_7_2_mystery_farming
        option = config['C72_mystery_farming']
        self.C72_BOSS_FLEET_STEP_ON_A3 = to_bool(option['boss_fleet_step_on_a3'])
        if self.COMMAND.lower() == 'c72_mystery_farming' and not self.C72_BOSS_FLEET_STEP_ON_A3:
            self.FLEET_2 = 0

        # C_12_2_leveling
        option = config['C122_leveling']
        self.C122_S3_TOLERANCE = int(option['s3_enemy_tolerance'])

        # C_12_4_leveling
        option = config['C124_leveling']
        self.C124_NON_S3_ENTER_TOLERANCE = int(option['non_s3_enemy_enter_tolerance'])
        self.C124_NON_S3_WITHDRAW_TOLERANCE = int(option['non_s3_enemy_withdraw_tolerance'])
        self.C124_AMMO_PICK_UP = int(option['ammo_pick_up_124'])

        # OS semi auto
        option = config['Os_semi_auto']
        self.ENABLE_OS_SEMI_STORY_SKIP = to_bool(option['enable_os_semi_story_skip'])

        # OS clear map
        option = config['Os_clear_map']
        self.ENABLE_OS_ASH_ATTACK = to_bool(option['enable_os_ash_attack'])

        # OS clear world
        option = config['Os_world_clear']
        self.OS_WORLD_MIN_LEVEL = int(option['os_world_min_level'])
        self.OS_WORLD_MAX_LEVEL = int(option['os_world_max_level'])

        # OS fully auto
        option = config['Os_fully_auto']
        for attr in ['do_os_in_daily', 'enable_os_mission_accept', 'enable_os_mission_finish', 'enable_os_supply_buy',
                     'enable_os_ash_attack', 'enable_os_obscure_finish', 'enable_os_meowfficer_farming',
                     'enable_os_action_point_buy', 'enable_os_akashi_shop_buy']:
            self.__setattr__(attr.upper(), to_bool(option[attr]))
        self.OS_MEOWFFICER_FARMING_LEVEL = int(option['os_meowfficer_farming_level'])
        self.OS_ACTION_POINT_PRESERVE = int(option['os_action_point_preserve'])
        self.OS_REPAIR_THRESHOLD = float(option['os_repair_threshold'])
        self.OS_ASKSHI_SHOP_PRIORITY = option['os_akashi_shop_priority']

    def get_server_timezone(self):
        if self.SERVER == 'en':
            return -7
        elif self.SERVER == 'cn':
            return 8
        elif self.SERVER == 'jp':
            return 9
        else:
            return 8

    def get_server_last_update(self, since):
        """
        Args:
            since (tuple(int)): Update hour in Azurlane, such as (0, 12, 18,).

        Returns:
            datetime.datetime
        """
        d = datetime.now(timezone.utc).astimezone()
        diff = d.utcoffset() // timedelta(seconds=1) // 3600 - self.get_server_timezone()
        since = np.sort((np.array(since) + diff) % 24)
        update = sorted([past_time(f'{t}:00') for t in since])[-1]
        return update

    def record_executed_since(self, option, since):
        """
        Args:
            option (tuple(str)): (Section, Option), such as ('DailyRecord', 'exercise').
            since (tuple(int)): Update hour in Azurlane, such as (0, 12, 18,).

        Returns:
            bool: If got a record after last game update.
        """
        record = datetime.strptime(self.config.get(*option), self.TIME_FORMAT)
        update = self.get_server_last_update(since)

        logger.attr(f'{option[0]}_{option[1]}', f'Record time: {record}')
        logger.attr(f'{option[0]}_{option[1]}', f'Last update: {update}')
        return record > update

    def triggered_app_restart(self):
        if self.get_server_last_update(since=(0,)) > self.start_time:
            logger.hr('Triggered restart new day')
            return True
        else:
            return False

    def record_save(self, option):
        record = datetime.strftime(datetime.now(), self.TIME_FORMAT)
        self.config.set(option[0], option[1], record)
        self.save()

    def cover(self, **kwargs):
        """
        Cover some settings, and recover later.

        Usage:
        backup = self.config.cover(ENABLE_DAILY_REWARD=False)
        # do_something()
        backup.recover()

        Args:
            **kwargs:

        Returns:
            ConfigBackup:
        """
        backup = ConfigBackup(config=self)
        backup.cover(**kwargs)
        return backup

    def __init__(self, ini_name='alas'):
        """
        Args:
            ini_name (str): Config to load.
        """
        self.load_config_file(ini_name)

        self.create_folder()


class ConfigBackup:
    def __init__(self, config):
        """
        Args:
            config (AzurLaneConfig):
        """
        self.config = config
        self.backup = {}
        self.kwargs = {}

    def cover(self, **kwargs):
        self.kwargs = kwargs
        for key, value in kwargs.items():
            self.backup[key] = self.config.__getattribute__(key)
            self.config.__setattr__(key, value)

    def recover(self):
        for key, value in self.backup.items():
            self.config.__setattr__(key, value)

# cfg = AzurLaneConfig()
