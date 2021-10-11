class CampaignEnd(Exception):
    pass


class MapDetectionError(Exception):
    pass


class MapWalkError(Exception):
    pass


class MapEnemyMoved(Exception):
    pass


class CampaignNameError(Exception):
    pass


class ScriptError(Exception):
    # This is likely to be a mistake of developers, but sometimes a random issue
    pass


class ScriptEnd(Exception):
    pass


class GameStuckError(Exception):
    pass


class LogisticsRefreshBugHandler(Exception):
    pass


class GameTooManyClickError(Exception):
    pass


class GameNotRunningError(Exception):
    pass


class RequestHumanTakeover(Exception):
    # Request human takeover
    # Alas is unable to handle such error, probably because of wrong settings.
    pass
