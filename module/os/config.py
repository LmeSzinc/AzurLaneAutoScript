class OSConfig:
    """
    Configs for Operation Siren
    """
    STORY_OPTION = -2

    MAP_FOCUS_ENEMY_AFTER_BATTLE = True
    MAP_HAS_SIREN = True
    MAP_HAS_FLEET_STEP = True
    IGNORE_LOW_EMOTION_WARN = False

    MAP_GRID_CENTER_TOLERANCE = 0.2
    MAP_SWIPE_MULTIPLY = (1.320, 1.009)
    MAP_SWIPE_MULTIPLY_MINITOUCH = (1.276, 0.974)

    DETECTION_BACKEND = 'perspective'
    MID_DIFF_RANGE_H = (103 - 3, 103 + 3)
    MID_DIFF_RANGE_V = (103 - 3, 103 + 3)
    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 40),
        'width': (1.5, 10),
        'prominence': 35,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 40, 255),
        'prominence': 10,
        'distance': 50,
        'wlen': 1000
    }
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 75
    EDGE_LINES_HOUGHLINES_THRESHOLD = 75

    HOMO_EDGE_DETECT = True
    HOMO_CANNY_THRESHOLD = (40, 60)
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 300

    MAP_ENEMY_GENRE_DETECTION_SCALING = {
        'DD': 0.8,
        'CL': 0.8,
        'CA': 0.8,
        'CV': 0.8,
        'BB': 0.8,
    }
    MAP_SWIPE_PREDICT = False
