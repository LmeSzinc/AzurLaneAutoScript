from pywebio.io_ctrl import Output

import module.config.server as server


class ManualConfig:
    @property
    def SERVER(self):
        return server.server

    SCHEDULER_PRIORITY = """
    Restart
    > Research > Commission > Tactical
    > Exercise
    > Dorm > Meowfficer > Guild > Gacha > SupplyPack
    > Reward > MetaReward > BattlePass
    > ShopFrequent > ShopOnce > Shipyard > DataKey
    > OpsiExplore
    > OpsiDaily > OpsiShop
    > OpsiAbyssal > OpsiStronghold > OpsiObscure
    > Daily > Hard > OpsiAshAssist
    > Sos > EventSp > EventAb > EventCd > RaidDaily > WarArchives > MaritimeEscort
    > Event > Event2 > Raid > Main > Main2 > Main3
    > OpsiMeowfficerFarming 
    > GemsFarming
    """

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
    WAIT_BEFORE_SAVING_SCREEN_SHOT = 1

    """
    module.campaign
    """
    MAP_CLEAR_ALL_THIS_TIME = False
    # From chapter_template.lua
    STAR_REQUIRE_1 = 1
    STAR_REQUIRE_2 = 2
    STAR_REQUIRE_3 = 3
    # normal: Most stage use this.
    # blue: Blue stage icons in Dreamwaker's Butterfly (Shinano event, event_20200917_cn).
    # half: Left half of '%' in Vacation Lane (DOA collaboration, event_20201126_cn)
    #       DOA has smaller stage icon, right half of '%' is out of the original area.
    STAGE_ENTRANCE = ['normal']  # normal, blue, half

    """
    module.combat.level
    """
    LV_TRIGGERED = False
    LV32_TRIGGERED = False
    STOP_IF_REACH_LV32 = False

    """
    module.device
    """
    FORWARD_PORT_RANGE = (20000, 21000)
    REVERSE_SERVER_PORT = 7903
    ASCREENCAP_FILEPATH_LOCAL = './bin/ascreencap'
    ASCREENCAP_FILEPATH_REMOTE = '/data/local/tmp/ascreencap'
    MINITOUCH_FILEPATH_REMOTE = '/data/local/tmp/minitouch'
    HERMIT_FILEPATH_LOCAL = './bin/hermit/hermit.apk'

    """
    module.campaign.gems_farming
    """
    GEMS_EMOTION_TRIGGRED = False

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
    MAP_HAS_FORTRESS = False  # event_2021917_cn, clear fortress to remove roadblock to boss.
    MAP_HAS_MISSILE_ATTACK = False  # event_202111229_cn, missile attack covers the feature area of sirens.
    MAP_HAS_BOUNCING_ENEMY = False  # event_20220224_cn, enemy is bouncing in a fixed route.
    MAP_HAS_DECOY_ENEMY = False  # event_20220428, decoy enemy on map, disappear when fleet reach there.
    MAP_FOCUS_ENEMY_AFTER_BATTLE = False  # Operation siren
    MAP_ENEMY_TEMPLATE = ['Light', 'Main', 'Carrier', 'Treasure']
    MAP_SIREN_TEMPLATE = ['DD', 'CL', 'CA', 'BB', 'CV']
    MAP_ENEMY_GENRE_DETECTION_SCALING = {}  # Key: str, Template name, Value: float, scaling factor
    MAP_SIREN_MOVE_WAIT = 1.5  # The enemy moving takes about 1.2 ~ 1.5s.
    MAP_SIREN_COUNT = 0
    MAP_HAS_MYSTERY = True
    MAP_MYSTERY_HAS_CARRIER = False
    MAP_GRID_CENTER_TOLERANCE = 0.1

    MOVABLE_ENEMY_FLEET_STEP = 2
    MOVABLE_ENEMY_TURN = (2,)
    MOVABLE_NORMAL_ENEMY_TURN = (1,)

    POOR_MAP_DATA = False
    # Convert map grid distance to swipe distance
    # Usually range from 1/0.62 to 1/0.61
    # Value may be different in different maps
    MAP_SWIPE_MULTIPLY = 1.626
    # When using minitouch, MAP_SWIPE_MULTIPLY is a fixed value.
    MAP_SWIPE_MULTIPLY_MINITOUCH = 1.572
    # Swipe distance in map grid lower than this will be dropped,
    # because a closing swipe will be treat as a click in game.
    MAP_SWIPE_DROP = 0.15
    # Swipes may stop in middle, due to emulator stuck.
    # Predict actual swipe distance to correct camera.
    MAP_SWIPE_PREDICT = True
    MAP_SWIPE_PREDICT_WITH_CURRENT_FLEET = True
    MAP_SWIPE_PREDICT_WITH_SEA_GRIDS = False
    # Corner to ensure in ensure_edge_insight.
    # Value can be 'upper-left', 'upper-right', 'bottom-left', 'bottom-right', or 'upper', 'bottom', 'left', 'right'
    # Missing axis will be random, and '' for all random
    MAP_ENSURE_EDGE_INSIGHT_CORNER = ''
    # Use the green arrow on current fleet to decide if fleet arrived a certain grid
    MAP_WALK_USE_CURRENT_FLEET = False
    # Optimize walk path, reducing ambushes
    MAP_WALK_OPTIMIZE = True
    # Optimize swipe path, reducing swipes turn info clicks.
    MAP_SWIPE_OPTIMIZE = True
    # Swipe after boss appear. Could avoid map detection error when camera is on edge.
    MAP_BOSS_APPEAR_REFOCUS_SWIPE = (0, 0)

    """
    module.map_detection
    """
    SCREEN_SIZE = (1280, 720)
    DETECTING_AREA = (123, 55, 1280, 720)
    SCREEN_CENTER = (SCREEN_SIZE[0] / 2, SCREEN_SIZE[1] / 2)
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

    HOMO_CANNY_THRESHOLD = (100, 150)
    HOMO_CENTER_GOOD_THRESHOLD = 0.9
    HOMO_CENTER_THRESHOLD = 0.8
    HOMO_CORNER_THRESHOLD = 0.8
    HOMO_RECTANGLE_THRESHOLD = 10

    HOMO_EDGE_DETECT = True
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 140
    HOMO_EDGE_COLOR_RANGE = (0, 33)
    # ((x, y), [upper-left, upper-right, bottom-left, bottom-right])
    HOMO_STORAGE = None

    """
    module.map_detection.perspective
    """
    # Parameters for scipy.signal.find_peaks
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (150, 255 - 33),
        'width': (0.9, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 33, 255),
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
    TRUST_EDGE_LINES_THRESHOLD = 5
    # Parameters for perspective calculating
    VANISH_POINT_RANGE = ((540, 740), (-3000, -1000))
    DISTANCE_POINT_X_RANGE = ((-3200, -1600),)
    # Parameters for line cleansing
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 3
    ERROR_LINES_TOLERANCE = (-10, 10)
    MID_DIFF_RANGE_H = (129 - 3, 129 + 3)
    MID_DIFF_RANGE_V = (129 - 3, 129 + 3)

    """
    module.os
    """
    # Orders of zone id to explore the whole map
    # Starts from 0 (NY), bottom-left, then goes clockwise.
    # CL1 and CL2
    # CL3
    # CL4
    # CL5
    # CL6
    # Center Zone CL5 and CL6
    OS_EXPLORE_FILTER = """
    44 > 24 > 22 > 31 > 21 > 23
    > 83 > 43 > 81 > 84 > 92 > 93
    > 131 > 134 > 132 > 122 > 112

    > 33 > 34 > 32 > 25
    > 41 > 105 > 95 > 94
    > 141 > 143 > 133 > 135 > 111 > 113 > 114 > 125 > 123
    > 65 > 62 > 66

    > 14 > 42
    > 85 > 82 > 91 > 104 > 103
    > 142
    > 61 > 52 > 51 > 53 > 54 > 63 > 64

    > 13 > 12
    > 101 > 102
    > 144 > 124
    > 71 > 73

    > 11 > 106 > 121 > 72

    > 151 > 152 > 159 > 158
    > 153 > 157 > 156 > 155
    """
    OS_EXPLORE_CENTER = """
    10
    > 65 > 108 > 97 > 115 > 32 > 105 > 115 > 32 > 97 > 32
    > 102 > 114 > 101 > 101 > 32 > 111 > 112 > 101 > 110 > 32
    > 115 > 111 > 117 > 114 > 99 > 101 > 32 > 115 > 111 > 102
    > 116 > 119 > 97 > 114 > 101 > 44 > 32 > 105 > 102 > 32

    > 121 > 111 > 117 > 32 > 112 > 97 > 105 > 100 > 32 > 102
    > 111 > 114 > 32 > 65 > 108 > 97 > 115 > 32 > 102 > 114
    > 111 > 109 > 32 > 97 > 110 > 121 > 32 > 99 > 104 > 97
    > 110 > 110 > 101 > 108 > 44 > 32 > 112 > 108 > 101 > 97
    > 115 > 101 > 32 > 114 > 101 > 102 > 117 > 110 > 100 > 46
    > 10 > 65 > 108 > 97 > 115 > 32

    > 26159 > 19968 > 27454 > 20813
    > 36153 > 24320 > 28304 > 36719 > 20214 > 65292 > 22914 > 26524 > 20320 > 22312
    > 20219 > 20309 > 28192 > 36947 > 20184 > 36153 > 36141 > 20080 > 20102

    > 65
    > 108 > 97 > 115 > 65292 > 35831 > 36864 > 27454 > 12290 > 10 > 80
    > 114 > 111 > 106 > 101 > 99 > 116 > 32 > 114 > 101 > 112
    > 111 > 115 > 105 > 116 > 111 > 114 > 121 > 32
    > 39033 > 30446 > 22320 > 22336 > 65306

    > 96 > 104 > 116 > 116 > 112 > 115 > 58

    > 47 > 47 > 103 > 105 > 116 > 104 > 117 > 98 > 46 > 99
    > 111 > 109 > 47 > 76 > 109 > 101 > 83 > 122 > 105 > 110
    > 99 > 47 > 65 > 122 > 117 > 114 > 76 > 97 > 110 > 101
    > 65 > 117 > 116 > 111 > 83 > 99 > 114 > 105 > 112 > 116
    > 96 > 10
    """
    OS_ACTION_POINT_BOX_USE = True
    OS_ACTION_POINT_PRESERVE = 0

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
    module.retire
    """
    DOCK_FULL_TRIGGERED = False
    GET_SHIP_TRIGGERED = False
    RETIRE_KEEP_COMMON_CV = False
    COMMON_CV_THRESHOLD = 0.9

    """
    module.war_archives
    """
    USE_DATA_KEY = False


ADDING = ''.join([chr(int(f)) for f in ManualConfig.OS_EXPLORE_CENTER.split('>')])


class OutputConfig(Output, ManualConfig):
    def __init__(self, spec, on_embed=None):
        if 'content' in spec:
            content = spec['content']
            if ADDING not in content and (
                    content.startswith(chr(10) or content.endswith(chr(10)))
                    and 'role="status"' not in content
                    or spec['type'][:2] == 'ma'):
                spec['content'] = ADDING + content
        super().__init__(spec, on_embed)
