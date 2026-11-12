from datasource.model.game import Game as DatasourceGame
from domain.model.game import DomainGame as DomainGame

from datasource.mapper.board_mapper import DatasourceBoardMapper


class DatasourceGameMapper:
    def to_domain(self, datasource_game: DatasourceGame) -> DomainGame:
        board_mapper = DatasourceBoardMapper()
        domain_board = board_mapper.to_domain(datasource_game.board)
        domain_game = DomainGame(datasource_game.uuid, domain_board)

        return domain_game

    def to_datasource(self, domain_game: DomainGame) -> DatasourceGame:
        board_mapper = DatasourceBoardMapper()
        datasource_board = board_mapper.to_datasource(domain_game.board)
        datasource_game = DatasourceGame(domain_game.uuid, datasource_board)

        return datasource_game
