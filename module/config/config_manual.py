import module.config.server as server


class ManualConfig:
    SERVER = server.server

    SCHEDULER_PRIORITY = """
    Restart
    > Research > Commission > Tactical > Dorm > Task
    > GuildLogistics > GuildOperation
    > Meowfficer > Gacha > Shop
    > OpsiObscure
    > Exercise > Daily > Hard > OpsiAsh
    > Sos > EventDaily > RaidDaily > WarArchieves
    > OpsiShop > OpsiDaily > OpsiFarm
    > Event > Raid > Main > GemsFarming
    """

    """
    module.base
    """
    COLOR_SIMILAR_THRESHOLD = 10
    BUTTON_OFFSET = 30
    BUTTON_MATCH_SIMILARITY = 0.85
    WAIT_BEFORE_SAVING_SCREEN_SHOT = 1

    """
    module.device
    """
    SERIAL = ''
    PACKAGE_NAME = ''
    ASCREENCAP_FILEPATH_LOCAL = './bin/ascreencap'
    ASCREENCAP_FILEPATH_REMOTE = '/data/local/tmp/ascreencap'
    MINITOUCH_FILEPATH_REMOTE = '/data/local/tmp/minitouch'
