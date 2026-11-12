from dataclasses import dataclass
from uuid import UUID

from datasource.model.board import Board


@dataclass
class Game:
    uuid: UUID
    board: Board
