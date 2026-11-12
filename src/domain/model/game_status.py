from enum import Enum


class GameStatus(Enum):
    DRAW = 0
    USER_WON = 1
    COMPUTER_WON = 2
    GAME_CONTINUES = 3
