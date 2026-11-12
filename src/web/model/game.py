from dataclasses import dataclass
from uuid import UUID

from web.model.board import WebBoard
from domain.model.game_mark import GameMark
from domain.model.game_state import GameState
from domain.model.opponent_type import OpponentType


@dataclass
class WebGame:
    uuid: UUID
    board: WebBoard
    opponent_type: OpponentType = OpponentType.COMPUTER
    state: GameState = GameState.PLAYER_TURN
    first_player_uuid: UUID | None = None
    second_player_uuid: UUID | None = None
    current_player_uuid: UUID | None = None
    winner_uuid: UUID | None = None
    first_player_mark: GameMark = GameMark.X
    second_player_mark: GameMark = GameMark.O
