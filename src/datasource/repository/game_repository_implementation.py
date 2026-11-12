from uuid import UUID

from datasource.repository.game_repository import GameRepository
from datasource.storage.storage import Storage
from datasource.mapper.game_mapper import DatasourceGameMapper
from domain.model.game import DomainGame


class GameRepositoryImpl(GameRepository):
    def __init__(self, game_mapper: DatasourceGameMapper, storage: Storage):
        self.game_mapper = game_mapper
        self.storage = storage

    def save(self, domain_game: DomainGame) -> None:
        datasource_game = self.game_mapper.to_datasource(domain_game)
        self.storage.save(datasource_game)

    def get(self, uuid: UUID) -> DomainGame | None:
        datasource_game = self.storage.get(uuid)
        if datasource_game is not None:
            domain_game = self.game_mapper.to_domain(datasource_game)

            return domain_game

        return None
