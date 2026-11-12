from abc import ABC, abstractmethod
from uuid import UUID

from domain.model.user import DomainUser


class UserService(ABC):
    @abstractmethod
    def create_user(self, login: str, password_hash: str) -> DomainUser:
        pass

    @abstractmethod
    def get_by_login(self, login: str) -> DomainUser | None:
        pass

    @abstractmethod
    def get_by_uuid(self, user_uuid: UUID) -> DomainUser | None:
        pass
