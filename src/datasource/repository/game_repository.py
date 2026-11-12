from abc import ABC, abstractmethod
from uuid import UUID

from domain.model.game import DomainGame


class GameRepository(ABC):
    @abstractmethod
    def save(self, game: DomainGame) -> None:
        pass

    @abstractmethod
    def get(self, uuid: UUID) -> DomainGame | None:
        pass

    @abstractmethod
    def get_available(self) -> list[DomainGame]:
        pass
