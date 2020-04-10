import codecs
import configparser
import copy
import os
from datetime import datetime

import cv2
import numpy as np
from PIL import Image

from module.base.timer import future_time
from module.config.dictionary import *
from module.logger import logger


class AzurLaneConfig:
    """
    Basic Config.
    """
    CONFIG_FILE = ''
    config = configparser.ConfigParser(interpolation=None)

    """
    Fleet
    """
    ENABLE_FLEET_CONTROL = True
    # Fleet 1-6, if empty use 0.
    _FLEET_1 = 1
    FLEET_2 = 2
    FLEET_3 = 3
    # Formation 1-3.
    _FLEET_1_FORMATION = 2
    FLEET_2_FORMATION = 2
    FLEET_3_FORMATION = 2
    # Fleet 1-2, if empty use 0.
    SUBMARINE = 0
    FLEET_CHECKED = False

    USING_SPARE_FLEET = False

    @property
    def FLEET_1(self):
        return self.FLEET_3 if self.USING_SPARE_FLEET else self._FLEET_1

    @FLEET_1.setter
    def FLEET_1(self, value):
        self._FLEET_1 = value

    @property
    def FLEET_1_FORMATION(self):
        return self.FLEET_3_FORMATION if self.USING_SPARE_FLEET else self._FLEET_1_FORMATION

    @FLEET_1_FORMATION.setter
    def FLEET_1_FORMATION(self, value):
        self._FLEET_1_FORMATION = value

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
    ENABLE_MAP_FLEET_LOCK = True
    SUBMARINE_MODE = ''
    SUBMARINE_CALL_AT_BOSS = False

    """
    module.combat.hp_balance
    """
    ENABLE_HP_BALANCE = False
    ENABLE_LOW_HP_WITHDRAW = True
    SCOUT_HP_DIFFERENCE_THRESHOLD = 0.2
    LOW_HP_WITHDRAW_THRESHOLD = 0.2

    """
    module.campaign
    """
    CAMPAIGN_NAME = 'default'
    CAMPAIGN_MODE = 'normal'

    ENABLE_STOP_CONDITION = True
    ENABLE_FAST_FORWARD = True
    STOP_IF_OIL_LOWER_THAN = 5000
    STOP_IF_COUNT_GREATER_THAN = 0
    STOP_IF_TIME_REACH = 0
    STOP_IF_TRIGGER_EMOTION_LIMIT = False
    STOP_IF_DOCK_FULL = False

    """
    module.event
    """
    EVENT_NAME = ''
    CAMPAIGN_EVENT = ''
    EVENT_NAME_AB = ''

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
    FLEET_3_RECOVER_PER_HOUR = 20
    FLEET_3_EMOTION_LIMIT = 50

    """
    module.device
    """
    SERIAL = '127.0.0.1:62001'
    PACKAGE_NAME = 'com.bilibili.azurlane'
    COMMAND = ''
    USE_ADB_SCREENSHOT = False
    USE_ADB_CONTROL = False
    SCREEN_SHOT_SAVE_FOLDER_BASE = './screenshot'
    SCREEN_SHOT_SAVE_FOLDER = ''
    SCREEN_SHOT_SAVE_INTERVAL = 5  # Seconds between two save. Saves in the interval will be dropped.

    """
    module.daily
    """
    ENABLE_DAILY_MISSION = True
    FLEET_DAILY = 3
    FLEET_DAILY_EQUIPMENT = [1, 1, 1, 1, 1, 1]
    DAILY_CHOOSE = {
        4: 1,  # 商船护送
        5: 1,  # 海域突进
        1: 2,  # 战术研修, 1航空 2炮击 3雷击
        2: 1,  # 斩首行动
        3: 1,  # 破交作战
    }

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
    EXERCISE_CHOOSE_MODE = 'max_exp'
    EXERCISE_PRESERVE = 0
    LOW_HP_THRESHOLD = 0.40
    LOW_HP_CONFIRM_WAIT = 1.0
    OPPONENT_CHALLENGE_TRIAL = 1
    EXERCISE_FLEET_EQUIPMENT = [1, 1, 1, 1, 1, 1]

    """
    error_log
    """
    ERROR_LOG_FOLDER = './log/error'

    """
    module.map.fleet
    """
    MAP_HAS_AMBUSH = True

    """
    module.retire
    """
    ENABLE_RETIREMENT = True
    DOCK_FULL_TRIGGERED = False
    RETIRE_MODE = '10'  # all, 10
    RETIRE_N = True
    RETIRE_R = False
    RETIRE_SR = False
    RETIRE_SSR = False

    """
    module.map.perspective
    """
    # Screen
    SCREEN_SIZE = (1280, 720)
    DETECTING_AREA = (123, 55, 1280, 720)
    SCREEN_CENTER = (SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 2)
    MID_Y = SCREEN_CENTER[1]
    # UI mask
    UI_MASK_FILE = './module/map/ui_mask.png'
    UI_MASK = np.array(Image.open(UI_MASK_FILE).convert('L'))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    UI_MASK_STROKE = cv2.erode(UI_MASK, kernel).astype('uint8')

    # Parameters for scipy.signal.find_peaks
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (150, 255 - 40),
        'width': 2,
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
    # Parameters for perspective calculating
    VANISH_POINT_RANGE = ((540, 740), (-3000, -1000))
    DISTANCE_POINT_X_RANGE = ((-3200, -1600),)
    # Parameters for line cleansing
    ERROR_LINES_TOLERANCE = (-10, 10)
    MID_DIFF_RANGE = (129 - 3, 129 + 3)
    COINCIDENT_POINT_RANGE = (
        (
            -abs(ERROR_LINES_TOLERANCE[0]) * MID_DIFF_RANGE[1],
            # SCREEN_SIZE[0] + ERROR_LINES_TOLERANCE[1] * MID_DIFF_RANGE[1]
            200
        ),
        MID_DIFF_RANGE
    )
    """
    module.daemon
    """
    ENABLE_SEMI_MAP_PREPARATION = True
    ENABLE_SEMI_STORY_SKIP = True

    """
    module.reward
    """
    ENABLE_REWARD = True
    REWARD_INTERVAL = 20
    REWARD_LAST_TIME = datetime.now()
    ENABLE_OIL_REWARD = True
    ENABLE_COIN_REWARD = True
    ENABLE_MISSION_REWARD = True
    ENABLE_COMMISSION_REWARD = True
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
    }
    COMMISSION_TIME_LIMIT = 0

    """
    C_7_2_mystery_farming
    """
    C72_BOSS_FLEET_STEP_ON_A3 = True

    """
    C_12_4_leveling
    """
    C124_NON_S3_ENTER_TOLERANCE = 1
    C124_NON_S3_WITHDRAW_TOLERANCE = 0
    C124_AMMO_PICK_UP = 3

    def create_folder(self):
        self.SCREEN_SHOT_SAVE_FOLDER = self.SCREEN_SHOT_SAVE_FOLDER_BASE + '/' + self.CAMPAIGN_NAME
        for folder in [self.SCREEN_SHOT_SAVE_FOLDER_BASE, self.ASSETS_FOLDER, self.SCREEN_SHOT_SAVE_FOLDER, self.ERROR_LOG_FOLDER]:
            if not os.path.exists(folder):
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

    def load_config_file(self, name='main'):
        self.CONFIG_FILE = f'./config/{name}.ini'
        self.config.read_file(codecs.open(self.CONFIG_FILE, "r", "utf8"))
        self.load_from_config(self.config)

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

        option = config['Setting']
        # Stop condition
        self.ENABLE_STOP_CONDITION = to_bool(option['enable_stop_condition'])
        self.ENABLE_FAST_FORWARD = to_bool(option['enable_fast_forward'])
        self.STOP_IF_COUNT_GREATER_THAN = int(option['if_count_greater_than'])
        if not option['if_time_reach'].isdigit():
            self.STOP_IF_TIME_REACH = future_time(option['if_time_reach'])
        else:
            self.STOP_IF_TIME_REACH = 0
        self.STOP_IF_OIL_LOWER_THAN = int(option['if_oil_lower_than'])
        self.STOP_IF_TRIGGER_EMOTION_LIMIT = to_bool(option['if_trigger_emotion_control'])
        self.STOP_IF_DOCK_FULL = to_bool(option['if_dock_full'])
        # Fleet
        self.ENABLE_FLEET_CONTROL = to_bool(option['enable_fleet_control'])
        self.ENABLE_MAP_FLEET_LOCK = to_bool(option['enable_map_fleet_lock'])
        for n in ['1', '2', '3']:
            self.__setattr__(f'FLEET_{n}', int(option[f'fleet_index_{n}']))
            self.__setattr__(f'FLEET_{n}_FORMATION', int(option[f'fleet_formation_{n}'].split('_')[1]))
        self.SUBMARINE = int(option['fleet_index_4']) if to_bool(option['fleet_index_4']) else 0
        self.SUBMARINE_MODE = option['submarine_mode']
        self.SUBMARINE_CALL_AT_BOSS = option['submarine_mode'] == 'when_boss_combat_boss_appear'
        # Emotion
        self.ENABLE_EMOTION_REDUCE = to_bool(option['enable_emotion_reduce'])
        self.IGNORE_LOW_EMOTION_WARN = to_bool(option['ignore_low_emotion_warn'])
        for n in ['1', '2', '3']:
            recover = dic_emotion_recover[option[f'emotion_recover_{n}']]
            recover += 10 if to_bool(option[f'hole_fleet_married_{n}']) else 0
            self.__setattr__(f'FLEET_{n}_RECOVER_PER_HOUR', recover)
            self.__setattr__(f'FLEET_{n}_EMOTION_LIMIT', dic_emotion_limit[option[f'emotion_control_{n}']])
        # HP balance, save get items -> combat
        self.ENABLE_HP_BALANCE = to_bool(option['enable_hp_balance'])
        self.ENABLE_LOW_HP_WITHDRAW = to_bool(option['enable_low_hp_withdraw'])
        self.SCOUT_HP_DIFFERENCE_THRESHOLD = float(option['scout_hp_difference_threshold'])
        self.LOW_HP_WITHDRAW_THRESHOLD = float(option['low_hp_withdraw_threshold'])
        self.ENABLE_SAVE_GET_ITEMS = to_bool(option['enable_drop_screenshot'])
        self.SCREEN_SHOT_SAVE_FOLDER_BASE = option['drop_screenshot_folder']
        # Retirement
        self.ENABLE_RETIREMENT = to_bool(option['enable_retirement'])
        self.RETIRE_MODE = option['retire_mode'].split('_')[1]
        for r in ['n', 'r', 'sr', 'ssr']:
            self.__setattr__(f'RETIRE_{r.upper()}', to_bool(option[f'retire_{r}']))

        # Reward
        option = config['Reward']
        self.REWARD_INTERVAL = int(option['reward_interval'])
        for attr in ['enable_reward', 'enable_oil_reward', 'enable_coin_reward', 'enable_mission_reward', 'enable_commission_reward']:
            self.__setattr__(attr.upper(), to_bool(option[attr]))
        self.COMMISSION_TIME_LIMIT = future_time(option['commission_time_limit'])
        for attr in self.COMMISSION_PRIORITY.keys():
            self.COMMISSION_PRIORITY[attr] = int(option[attr])

        option = config['Main']
        self.CAMPAIGN_NAME = option['main_stage']
        self.CAMPAIGN_NAME = 'campaign_' + self.CAMPAIGN_NAME.replace('-', '_')

        option = config['Daily']
        for n in ['daily_mission', 'hard_campaign', 'exercise']:
            self.__setattr__(f'ENABLE_{n.upper()}', option[f'enable_{n}'])
        # Daily mission
        self.ENABLE_DAILY_MISSION = to_bool(option['enable_daily_mission'])
        for n in [1, 2, 4, 5]:
            self.DAILY_CHOOSE[n] = dic_daily[option[f'daily_mission_{n}']]
        self.FLEET_DAILY = int(option['daily_fleet'])
        self.FLEET_DAILY_EQUIPMENT = equip(option['daily_equipment'])
        # Hard
        self.ENABLE_HARD_CAMPAIGN = to_bool(option['enable_hard_campaign'])
        self.HARD_CAMPAIGN = option['hard_campaign']
        self.FLEET_HARD = int(option['hard_fleet'])
        self.FLEET_HARD_EQUIPMENT = equip(option['hard_equipment'])
        # Exercise
        self.ENABLE_EXERCISE = to_bool(option['enable_exercise'])
        self.EXERCISE_CHOOSE_MODE = option['exercise_choose_mode']
        self.EXERCISE_PRESERVE = int(option['exercise_preserve'])
        self.OPPONENT_CHALLENGE_TRIAL = int(option['exercise_try'])
        self.LOW_HP_THRESHOLD = float(option['exercise_hp_threshold'])
        self.LOW_HP_CONFIRM_WAIT = float(option['exercise_low_hp_confirm'])
        self.EXERCISE_FLEET_EQUIPMENT = equip(option['exercise_equipment'])

        # Event
        option = config['Event']
        self.EVENT_NAME = option['event_name']
        if 'sp' in ''.join(os.listdir(f'./campaign/{self.EVENT_NAME}')):
            self.CAMPAIGN_EVENT = option['sp_stage']
        else:
            self.CAMPAIGN_EVENT = option['event_stage']

        # Event_daily_ab
        option = config['Event_daily_ab']
        self.EVENT_NAME_AB = option['event_name_ab']

        # Semi_auto
        option = config['Semi_auto']
        self.ENABLE_SEMI_MAP_PREPARATION = to_bool(option['enable_semi_map_preparation'])
        self.ENABLE_SEMI_STORY_SKIP = to_bool(option['enable_semi_story_skip'])

        # C_7_2_mystery_farming
        option = config['C72_mystery_farming']
        self.C72_BOSS_FLEET_STEP_ON_A3 = to_bool(option['boss_fleet_step_on_a3'])
        if self.COMMAND.lower() == 'c72_mystery_farming' and not self.C72_BOSS_FLEET_STEP_ON_A3:
            self.FLEET_2 = 0

        # C_12_4_leveling
        option = config['C124_leveling']
        self.C124_NON_S3_ENTER_TOLERANCE = int(option['non_s3_enemy_enter_tolerance'])
        self.C124_NON_S3_WITHDRAW_TOLERANCE = int(option['non_s3_enemy_withdraw_tolerance'])
        self.C124_AMMO_PICK_UP = int(option['ammo_pick_up_124'])

    def record_executed_since(self, option, since):
        """
        Args:
            option (tuple(str)): (Section, Option), such as ('DailyRecord', 'exercise').
            since (tuple(int)): Update hour in Azurlane, such as (0, 12, 18,).

        Returns:
            bool: If got a record after last game update.
        """
        record = datetime.strptime(self.config.get(*option), self.TIME_FORMAT)
        since = np.array(since)

        hour = since[since <= datetime.now().hour][-1]
        update = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)

        logger.attr(f'{option[0]}_{option[1]}', f'Record time: {record}')
        logger.attr(f'{option[0]}_{option[1]}', f'Last update: {update}')
        return record > update

    def record_save(self, option):
        record = datetime.strftime(datetime.now(), self.TIME_FORMAT)
        self.config.set(option[0], option[1], record)
        self.save()

    def __init__(self, ini_name='alas'):
        """
        Args:
            ini_name (str): Config to load.
        """
        self.load_config_file(ini_name)

        self.create_folder()

# cfg = AzurLaneConfig()
