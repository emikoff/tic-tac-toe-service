from uuid import UUID, uuid4

from domain.model.user import DomainUser
from domain.service.user_interface_service import UserService
from datasource.repository.user_repository import UserRepository
from domain.exception.user_exception import UserAlreadyExistsError


class UserServiceImpl(UserService):
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, login: str, password_hash: str) -> DomainUser:
        existing_user = self.user_repository.get_by_login(login)

        if existing_user is not None:
            raise UserAlreadyExistsError(login)

        domain_user = DomainUser(uuid=uuid4(), login=login, password_hash=password_hash)
        self.user_repository.save(domain_user)

        return domain_user

    def get_by_login(self, login: str) -> DomainUser | None:
        return self.user_repository.get_by_login(login=login)

    def get_by_uuid(self, user_uuid: UUID) -> DomainUser | None:
        return self.user_repository.get_by_uuid(user_uuid=user_uuid)
