class ALASBaseError(Exception):
    pass


class CampaignEnd(ALASBaseError):
    pass


class MapDetectionError(ALASBaseError):
    pass


class MapWalkError(ALASBaseError):
    pass


class MapEnemyMoved(ALASBaseError):
    pass


class CampaignNameError(ALASBaseError):
    pass


class ScriptError(ALASBaseError):
    # This is likely to be a mistake of developers, but sometimes a random issue
    pass


class ScriptEnd(ALASBaseError):
    pass


class GameStuckError(ALASBaseError):
    pass


class GameBugError(ALASBaseError):
    # An error has occurred in Azur Lane game client. Alas is unable to handle.
    # A restart should fix it.
    pass


class GameTooManyClickError(ALASBaseError):
    pass


class EmulatorNotRunningError(ALASBaseError):
    pass


class GameNotRunningError(ALASBaseError):
    pass


class GamePageUnknownError(ALASBaseError):
    def __init__(self, message='Game page unknown', *args):
        super().__init__(message, *args)

class RequestHumanTakeover(ALASBaseError):
    # Request human takeover
    # Alas is unable to handle such error, probably because of wrong settings.
    def __init__(self, message='Request human takeover', *args):
        super().__init__(message, *args)
