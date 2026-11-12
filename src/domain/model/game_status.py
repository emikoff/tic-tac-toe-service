from enum import Enum


class GameStatus(Enum):
    DRAW = 0
    USER_WON = 1
    COMPUTER_WON = 2
    GAME_CONTINUES = 3
    GAME_NOT_FOUND = 4
    INVALID_MOVE = 5
    INTERNAL_ERROR = 6
    INVALID_WINNER = 7
