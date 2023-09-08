import module.config.server as server


class ManualConfig:
    @property
    def LANG(self):
        return server.lang

    SCHEDULER_PRIORITY = """
    Restart
    > BattlePass > DailyQuest > Dungeon > Assignment
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
