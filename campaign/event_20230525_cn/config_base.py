class ConfigBase:
    STAGE_ENTRANCE = ['green']

    MAP_HAS_MOVABLE_NORMAL_ENEMY = True
    MOVABLE_NORMAL_ENEMY_TURN = (2,)
    MAP_SIREN_MOVE_WAIT = 1.0
    MAP_WALK_USE_CURRENT_FLEET = True

    INTERNAL_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (80, 255 - 24),
        'width': (1.5, 10),
        'prominence': 10,
        'distance': 35,
    }
    EDGE_LINES_FIND_PEAKS_PARAMETERS = {
        'height': (255 - 24, 255),
        'prominence': 10,
        'distance': 50,
        'wlen': 1000
    }
    HOMO_EDGE_HOUGHLINES_THRESHOLD = 120
    HOMO_EDGE_COLOR_RANGE = (0, 12)
    INTERNAL_LINES_HOUGHLINES_THRESHOLD = 40
    EDGE_LINES_HOUGHLINES_THRESHOLD = 40
    MAP_ENSURE_EDGE_INSIGHT_CORNER = 'bottom'
    MAP_ENEMY_GENRE_DETECTION_SCALING = {
        'DD': 1.111,
        'CL': 1.111,
        'CA': 1.111,
        'CV': 1.111,
        'BB': 1.111,
        'CAred': 1.111,
        'BBred': 1.111,
    }
