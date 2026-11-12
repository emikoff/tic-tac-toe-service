from uuid import UUID

from sqlalchemy import select

from datasource.database import db
from datasource.model.game import OrmGame
from datasource.mapper.game_mapper import DatasourceGameMapper
from domain.model.game import DomainGame
from domain.model.game_state import GameState
from domain.model.opponent_type import OpponentType
from datasource.repository.game_repository import GameRepository


class GameRepositoryImpl(GameRepository):
    def __init__(self, game_mapper: DatasourceGameMapper):
        self.game_mapper = game_mapper

    def save(self, domain_game: DomainGame) -> None:
        try:
            existing = db.session.get(OrmGame, domain_game.uuid)
            if existing is None:
                orm_game = self.game_mapper.domain_to_orm(domain_game)
                db.session.add(orm_game)
            else:
                # Целиком присваиваем новую структуру, чтобы сработал dirty check
                existing.board = [row[:] for row in domain_game.board.matrix]
                existing.opponent_type = domain_game.opponent_type
                existing.state = domain_game.state
                existing.first_player_uuid = domain_game.first_player_uuid
                existing.second_player_uuid = domain_game.second_player_uuid
                existing.current_player_uuid = domain_game.current_player_uuid
                existing.winner_uuid = domain_game.winner_uuid
                existing.first_player_mark = domain_game.first_player_mark
                existing.second_player_mark = domain_game.second_player_mark
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def get(self, game_uuid: UUID) -> DomainGame | None:
        orm_game = db.session.get(OrmGame, game_uuid)
        if orm_game is None:
            return None
        return self.game_mapper.orm_to_domain(orm_game)

    def get_available(self) -> list[DomainGame]:
        statement = (
            select(OrmGame)
            .where(
                OrmGame.opponent_type == OpponentType.USER,
                OrmGame.state == GameState.WAITING_FOR_PLAYERS,
            )
            .order_by(OrmGame.uuid)
        )
        orm_games = db.session.scalars(statement).all()
        return [self.game_mapper.orm_to_domain(game) for game in orm_games]
