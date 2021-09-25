import module.config.server as server


class ManualConfig:
    SERVER = server.server

    SCHEDULER_PRIORITY = """
    Restart
    > Research > Commission > Tactical > Dorm > Meowfficer > Guild > Reward
    > Gacha > Shop > Shipyard
    > OpsiObscure > Exercise > Daily > Hard > OpsiAsh
    > Sos > EventSp > EventAb > RaidDaily > WarArchieves
    > OpsiExplore > OpsiDaily > OpsiMeowfficerFarming
    > Event > Raid > Main
    > C11AffinityFarming > C124Leveling > C122Leveling > C72MysteryFarming > GemsFarming
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
    # In Dreamwaker's Butterfly (event_20200917) add new stage entrance icons, called `blue`.
    STAGE_ENTRANCE = ['normal']  # normal, blue, half

    """
    module.combat.level
    """
    LV120_TRIGGERED = False
    LV32_TRIGGERED = False
    STOP_IF_REACH_LV32 = False

    """
    module.device
    """
    SERIAL = ''
    PACKAGE_NAME = ''
    ASCREENCAP_FILEPATH_LOCAL = './bin/ascreencap'
    ASCREENCAP_FILEPATH_REMOTE = '/data/local/tmp/ascreencap'
    MINITOUCH_FILEPATH_REMOTE = '/data/local/tmp/minitouch'

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
    MAP_SWIPE_PREDICT = True
    # Corner to ensure in ensure_edge_insight.
    # Value can be 'upper-left', 'upper-right', 'bottom-left', 'bottom-right', or 'upper', 'bottom', 'left', 'right'
    # Missing axis will be random, and '' for all random
    MAP_ENSURE_EDGE_INSIGHT_CORNER = ''

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
