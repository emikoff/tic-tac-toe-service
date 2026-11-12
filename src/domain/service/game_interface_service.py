from abc import ABC, abstractmethod
from uuid import UUID

from domain.model.board import DomainBoard
from domain.model.game import DomainGame
from domain.model.game_status import GameStatus


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
    def new_game(self) -> DomainGame:
        pass

    @abstractmethod
    def move_player(
        self,
        game_uuid: UUID,
        new_board: DomainBoard,
    ) -> tuple[DomainGame | None, GameStatus]:
        pass
