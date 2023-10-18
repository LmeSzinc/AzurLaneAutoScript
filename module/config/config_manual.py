from pywebio.io_ctrl import Output

import module.config.server as server


class ManualConfig:
    @property
    def LANG(self):
        return server.lang

    SCHEDULER_PRIORITY = """
    Restart
    > BattlePass > DailyQuest > Assignment
    > Freebies > DataUpdate
    > Weekly > Dungeon
    > Rogue
    """

    """
    module.assets
    """
    ASSETS_FOLDER = './assets'
    ASSETS_MODULE = './tasks'
    ASSETS_RESOLUTION = (1280, 720)

    """
    module.base
    """
    COLOR_SIMILAR_THRESHOLD = 10
    BUTTON_OFFSET = (20, 20)
    BUTTON_MATCH_SIMILARITY = 0.85
    WAIT_BEFORE_SAVING_SCREEN_SHOT = 1

    """
    module.device
    """
    DEVICE_OVER_HTTP = False
    FORWARD_PORT_RANGE = (20000, 21000)
    REVERSE_SERVER_PORT = 7903

    ASCREENCAP_FILEPATH_LOCAL = './bin/ascreencap'
    ASCREENCAP_FILEPATH_REMOTE = '/data/local/tmp/ascreencap'

    # 'DroidCast', 'DroidCast_raw'
    DROIDCAST_VERSION = 'DroidCast'
    DROIDCAST_FILEPATH_LOCAL = './bin/DroidCast/DroidCast-debug-1.1.0.apk'
    DROIDCAST_FILEPATH_REMOTE = '/data/local/tmp/DroidCast.apk'
    DROIDCAST_RAW_FILEPATH_LOCAL = './bin/DroidCast/DroidCastS-release-1.1.5.apk'
    DROIDCAST_RAW_FILEPATH_REMOTE = '/data/local/tmp/DroidCastS.apk'

    MINITOUCH_FILEPATH_REMOTE = '/data/local/tmp/minitouch'

    HERMIT_FILEPATH_LOCAL = './bin/hermit/hermit.apk'

    SCRCPY_FILEPATH_LOCAL = './bin/scrcpy/scrcpy-server-v1.20.jar'
    SCRCPY_FILEPATH_REMOTE = '/data/local/tmp/scrcpy-server-v1.20.jar'

    MAATOUCH_FILEPATH_LOCAL = './bin/MaaTouch/maatouch'
    MAATOUCH_FILEPATH_REMOTE = '/data/local/tmp/maatouch'

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
    83
    > 82 > 67 > 32 > 105 > 115 > 32 > 97 > 32 > 102
    > 114 > 101 > 101 > 32 > 111 > 112 > 101 > 110 > 32 > 115
    > 111 > 117 > 114 > 99 > 101 > 32 > 115 > 111 > 102 > 116
    > 119 > 97 > 114 > 101 > 44 > 32 > 105 > 102 > 32 > 121
    > 111 > 117 > 32 > 112 > 97 > 105 > 100 > 32 > 102 > 111
    > 114 > 32 > 83 > 82 > 67 > 32 > 102 > 114 > 111 > 109
    > 32 > 97 > 110 > 121 > 32 > 99 > 104 > 97 > 110 > 110
    > 101 > 108 > 44 > 32 > 112 > 108 > 101 > 97 > 115 > 101
    > 32 > 114 > 101 > 102 > 117 > 110 > 100 > 46 > 10 > 83
    > 82 > 67 > 32 > 26159 > 19968 > 27454 > 20813 > 36153 > 24320 > 28304
    > 36719 > 20214 > 65292 > 22914 > 26524 > 20320 > 22312 > 20219 > 20309 > 28192
    > 36947 > 20184 > 36153 > 36141 > 20080 > 20102 > 83 > 82 > 67 > 65292
    > 35831 > 36864 > 27454 > 12290 > 10 > 80 > 114 > 111 > 106 > 101
    > 99 > 116 > 32 > 114 > 101 > 112 > 111 > 115 > 105 > 116
    > 111 > 114 > 121 > 32 > 39033 > 30446 > 22320 > 22336 > 65306 > 96
    > 104 > 116 > 116 > 112 > 115 > 58 > 47 > 47 > 103 > 105
    > 116 > 104 > 117 > 98 > 46 > 99 > 111 > 109 > 47 > 76
    > 109 > 101 > 83 > 122 > 105 > 110 > 99 > 47 > 83 > 116
    > 97 > 114 > 82 > 97 > 105 > 108 > 67 > 111 > 112 > 105
    > 108 > 111 > 116 > 96
    """
    OS_ACTION_POINT_BOX_USE = True
    OS_ACTION_POINT_PRESERVE = 0
    OS_CL1_YELLOW_COINS_PRESERVE = 100000


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
