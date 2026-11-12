from datasource.storage.storage import Storage
from datasource.repository.game_repository_implementation import GameRepositoryImpl
from datasource.mapper.game_mapper import DatasourceGameMapper

from domain.service.game_implementation_service import GameServiceImpl


class Container:
    def __init__(self) -> None:
        self.storage = Storage()

        self.game_mapper = DatasourceGameMapper()

        self.game_repository = GameRepositoryImpl(
            self.game_mapper,
            self.storage,
        )

        self.game_manager = GameServiceImpl(
            self.game_repository,
        )
