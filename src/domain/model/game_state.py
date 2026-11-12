from enum import Enum


class GameState(str, Enum):
    WAITING_FOR_PLAYERS = "WAITING_FOR_PLAYERS"
    PLAYER_TURN = "PLAYER_TURN"
    DRAW = "DRAW"
    VICTORY = "VICTORY"
