# ALASBaseException
#  ├── ScriptError
#  ├── ScriptEnd
#  ├── EmulatorNotRunningError
#  ├── RequestHumanTakeover
#  ├── CampaignBaseException
#  │    ├── CampaignEnd
#  │    └── CampaignNameError
#  ├── MapBaseException
#  │    ├── MapDetectionError
#  │    ├── MapWalkError
#  │    └── MapEnemyMoved
#  └── GameBaseException
#       ├── GameStuckError
#       ├── GameBugError
#       ├── GameTooManyClickError
#       ├── GameNotRunningError
#       └── GamePageUnknownError


class ALASBaseException(Exception):
    pass


class ScriptError(ALASBaseException):
    # This is likely to be a mistake of developers, but sometimes a random issue
    pass


class ScriptEnd(ALASBaseException):
    pass


class EmulatorNotRunningError(ALASBaseException):
    pass


class RequestHumanTakeover(ALASBaseException):
    # Request human takeover
    # Alas is unable to handle such error, probably because of wrong settings.
    def __init__(self, message='Request human takeover', *args):
        super().__init__(message, *args)


# Campaign
class CampaignBaseException(ALASBaseException):
    pass


class CampaignEnd(CampaignBaseException):
    pass


class CampaignNameError(CampaignBaseException):
    pass


# Map
class MapBaseException(ALASBaseException):
    pass


class MapDetectionError(MapBaseException):
    pass


class MapWalkError(MapBaseException):
    pass


class MapEnemyMoved(MapBaseException):
    pass


# Game
class GameBaseException(ALASBaseException):
    pass


class GameStuckError(GameBaseException):
    pass


class GameBugError(GameBaseException):
    # An error has occurred in Azur Lane game client. Alas is unable to handle.
    # A restart should fix it.
    pass


class GameTooManyClickError(GameBaseException):
    pass


class GameNotRunningError(GameBaseException):
    pass


class GamePageUnknownError(GameBaseException):
    def __init__(self, message='Game page unknown', *args):
        super().__init__(message, *args)
