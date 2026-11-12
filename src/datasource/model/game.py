from uuid import UUID as PythonUUID

from sqlalchemy import Enum as SqlEnum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from datasource.database import db
from domain.model.game_mark import GameMark
from domain.model.game_state import GameState
from domain.model.opponent_type import OpponentType


opponent_type_enum = SqlEnum(OpponentType, name="opponent_type")
game_state_enum = SqlEnum(GameState, name="game_state")
game_mark_enum = SqlEnum(GameMark, name="game_mark")


class OrmGame(db.Model):
    __tablename__ = "games"

    uuid: Mapped[PythonUUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    board: Mapped[list[list[int]]] = mapped_column(JSONB, nullable=False)
    opponent_type: Mapped[OpponentType] = mapped_column(
        opponent_type_enum,
        nullable=False,
        default=OpponentType.COMPUTER,
    )
    state: Mapped[GameState] = mapped_column(
        game_state_enum,
        nullable=False,
        default=GameState.PLAYER_TURN,
    )
    first_player_uuid: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.uuid"),
        nullable=True,
    )
    second_player_uuid: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.uuid"),
        nullable=True,
    )
    current_player_uuid: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.uuid"),
        nullable=True,
    )
    winner_uuid: Mapped[PythonUUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.uuid"),
        nullable=True,
    )
    first_player_mark: Mapped[GameMark] = mapped_column(
        game_mark_enum,
        nullable=False,
        default=GameMark.X,
    )
    second_player_mark: Mapped[GameMark] = mapped_column(
        game_mark_enum,
        nullable=False,
        default=GameMark.O,
    )
