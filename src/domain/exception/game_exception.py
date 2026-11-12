class GameError(Exception):
    pass


class GameNotFoundError(GameError):
    pass


class GameNotAvailableError(GameError):
    pass


class CannotJoinOwnGameError(GameError):
    pass


class NotGameParticipantError(GameError):
    pass


class NotPlayerTurnError(GameError):
    pass


class GameNotStartedError(GameError):
    pass


class GameAlreadyFinishedError(GameError):
    pass


class InvalidGameMoveError(GameError):
    pass
