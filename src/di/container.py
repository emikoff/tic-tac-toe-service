from datasource.repository.game_repository_implementation import GameRepositoryImpl
from datasource.mapper.game_mapper import DatasourceGameMapper
from domain.service.game_implementation_service import GameServiceImpl

from datasource.repository.user_repository_implementation import UserRepositoryImpl
from datasource.mapper.user_mapper import DatasourceUserMapper
from domain.service.user_implementation_service import UserServiceImpl
from domain.service.authorization_implementation_service import (
    AuthorizationServiceImpl,
)

from web.module.authorization_module import AuthorizationModule
from web.module.user_module import UserModule
from web.authenticator.user_authenticator import UserAuthenticator


class Container:
    def __init__(self) -> None:
        self.game_mapper = DatasourceGameMapper()
        self.game_repository = GameRepositoryImpl(self.game_mapper)
        self.game_manager = GameServiceImpl(self.game_repository)

        self.user_mapper = DatasourceUserMapper()
        self.user_repository = UserRepositoryImpl(self.user_mapper)
        self.user_service = UserServiceImpl(self.user_repository)

        self.authorization_service = AuthorizationServiceImpl(self.user_service)
        self.authorization_module = AuthorizationModule(self.authorization_service)
        self.user_authenticator = UserAuthenticator(self.authorization_service)
        self.user_module = UserModule(
            self.user_service,
            self.user_authenticator,
        )
