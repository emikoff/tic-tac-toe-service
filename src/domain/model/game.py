from dataclasses import dataclass
from uuid import UUID

from domain.model.board import DomainBoard


@dataclass
class DomainGame:
    uuid: UUID
    board: DomainBoard
