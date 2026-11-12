from datasource.model.game import OrmGame
from domain.model.game import DomainGame
from domain.model.board import DomainBoard


class DatasourceGameMapper:
    @staticmethod
    def orm_to_domain(orm_game: OrmGame) -> DomainGame:
        # Воссоздаём независимую матрицу для доменного слоя
        board_copy = [row[:] for row in orm_game.board]
        return DomainGame(
            uuid=orm_game.uuid,
            board=DomainBoard(matrix=board_copy),
            opponent_type=orm_game.opponent_type,
            state=orm_game.state,
            first_player_uuid=orm_game.first_player_uuid,
            second_player_uuid=orm_game.second_player_uuid,
            current_player_uuid=orm_game.current_player_uuid,
            winner_uuid=orm_game.winner_uuid,
            first_player_mark=orm_game.first_player_mark,
            second_player_mark=orm_game.second_player_mark,
        )

    @staticmethod
    def domain_to_orm(domain_game: DomainGame) -> OrmGame:
        # Отдаём в ORM свежую копию
        board_copy = [row[:] for row in domain_game.board.matrix]
        return OrmGame(
            uuid=domain_game.uuid,
            board=board_copy,
            opponent_type=domain_game.opponent_type,
            state=domain_game.state,
            first_player_uuid=domain_game.first_player_uuid,
            second_player_uuid=domain_game.second_player_uuid,
            current_player_uuid=domain_game.current_player_uuid,
            winner_uuid=domain_game.winner_uuid,
            first_player_mark=domain_game.first_player_mark,
            second_player_mark=domain_game.second_player_mark,
        )
