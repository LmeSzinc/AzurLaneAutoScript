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
