from abc import ABC, abstractmethod
from uuid import UUID

from domain.model.board import DomainBoard
from domain.model.game import DomainGame
from domain.model.game_status import GameStatus
from domain.model.opponent_type import OpponentType


class GameService(ABC):
    @abstractmethod
    def whose_move(self, matrix: list[list[int]]) -> int | None:
        pass

    @abstractmethod
    def next_move(self, board: DomainBoard, player: int) -> DomainBoard:
        pass

    @abstractmethod
    def board_validate(self, old_board: DomainBoard, new_board: DomainBoard) -> bool:
        pass

    @abstractmethod
    def check_end_game_and_winner(self, matrix: list[list[int]]) -> tuple[bool, int]:
        pass

    @abstractmethod
    def new_game(
        self,
        first_player_uuid: UUID | None = None,
        opponent_type: OpponentType = OpponentType.COMPUTER,
    ) -> DomainGame:
        pass

    @abstractmethod
    def get_available_games(self) -> list[DomainGame]:
        pass

    @abstractmethod
    def get_game(self, game_uuid: UUID) -> DomainGame:
        pass

    @abstractmethod
    def join_game(self, game_uuid: UUID, user_uuid: UUID) -> DomainGame:
        pass

    @abstractmethod
    def move_player(
        self,
        game_uuid: UUID,
        user_uuid: UUID,
        new_board: DomainBoard,
    ) -> tuple[DomainGame, GameStatus]:
        pass
