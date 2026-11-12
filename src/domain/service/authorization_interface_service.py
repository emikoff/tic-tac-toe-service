from abc import ABC, abstractmethod
from uuid import UUID

from domain.model.sign_up_request import SignUpRequest


class AuthorizationService(ABC):
    @abstractmethod
    def register(self, request: SignUpRequest) -> bool:
        pass

    @abstractmethod
    def authorize(self, authorization_header: str) -> UUID:
        pass
