from abc import ABC, abstractmethod
from uuid import UUID

from domain.model.user import DomainUser


class UserRepository(ABC):
    @abstractmethod
    def save(self, user: DomainUser) -> None:
        pass

    @abstractmethod
    def get_by_login(self, login: str) -> DomainUser | None:
        pass

    @abstractmethod
    def get_by_uuid(self, user_uuid: UUID) -> DomainUser | None:
        pass
