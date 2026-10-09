from module.exception import GameStuckError


class MaaError(GameStuckError):
    """MAA runtime failure that may be recovered by restarting the game."""

    pass
