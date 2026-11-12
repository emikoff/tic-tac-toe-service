from uuid import uuid4

from datasource.mapper.board_mapper import DatasourceBoardMapper
from datasource.mapper.game_mapper import DatasourceGameMapper
from datasource.model.board import DatasourceBoard
from datasource.model.game import OrmGame
from domain.model.board import DomainBoard
from domain.model.game import DomainGame
from domain.model.game_mark import GameMark
from domain.model.game_state import GameState
from domain.model.opponent_type import OpponentType


def test_board_mapper_datasource_to_domain():
    matrix = [[0, 1, 2], [0, 2, 1], [0, 1, 2]]
    result = DatasourceBoardMapper().to_domain(DatasourceBoard(matrix))
    assert isinstance(result, DomainBoard)
    assert result.matrix == matrix


def test_board_mapper_domain_to_datasource():
    matrix = [[0, 1, 2], [0, 2, 1], [0, 1, 2]]
    result = DatasourceBoardMapper().to_datasource(DomainBoard(matrix))
    assert isinstance(result, DatasourceBoard)
    assert result.matrix == matrix


def test_board_mapper_creates_independent_copy():
    matrix = [[0, 1, 2], [0, 2, 1], [0, 1, 2]]
    domain_board = DomainBoard(matrix)
    datasource_board = DatasourceBoardMapper().to_datasource(domain_board)
    datasource_board.matrix[2][0] = 1
    assert domain_board.matrix == matrix


def test_game_mapper_orm_to_domain():
    game_uuid = uuid4()
    first_player_uuid = uuid4()
    second_player_uuid = uuid4()
    matrix = [[0, 1, 2], [0, 2, 1], [0, 1, 2]]
    orm_game = OrmGame(
        uuid=game_uuid,
        board=matrix,
        opponent_type=OpponentType.USER,
        state=GameState.PLAYER_TURN,
        first_player_uuid=first_player_uuid,
        second_player_uuid=second_player_uuid,
        current_player_uuid=first_player_uuid,
        winner_uuid=None,
        first_player_mark=GameMark.X,
        second_player_mark=GameMark.O,
    )
    result = DatasourceGameMapper.orm_to_domain(orm_game)
    assert isinstance(result, DomainGame)
    assert isinstance(result.board, DomainBoard)
    assert result.uuid == game_uuid
    assert result.board.matrix == matrix
    assert result.opponent_type == OpponentType.USER
    assert result.state == GameState.PLAYER_TURN
    assert result.first_player_uuid == first_player_uuid
    assert result.second_player_uuid == second_player_uuid
    assert result.current_player_uuid == first_player_uuid
    assert result.winner_uuid is None
    assert result.first_player_mark == GameMark.X
    assert result.second_player_mark == GameMark.O


def test_game_mapper_domain_to_orm():
    game_uuid = uuid4()
    first_player_uuid = uuid4()
    matrix = [[0, 1, 2], [0, 2, 1], [0, 1, 2]]
    domain_game = DomainGame(
        uuid=game_uuid,
        board=DomainBoard(matrix),
        opponent_type=OpponentType.USER,
        state=GameState.WAITING_FOR_PLAYERS,
        first_player_uuid=first_player_uuid,
    )
    result = DatasourceGameMapper.domain_to_orm(domain_game)
    assert isinstance(result, OrmGame)
    assert result.uuid == game_uuid
    assert result.board == matrix
    assert isinstance(result.board, list)
    assert result.opponent_type == OpponentType.USER
    assert result.state == GameState.WAITING_FOR_PLAYERS
    assert result.first_player_uuid == first_player_uuid
    assert result.second_player_uuid is None
    assert result.current_player_uuid is None
    assert result.winner_uuid is None
    assert result.first_player_mark == GameMark.X
    assert result.second_player_mark == GameMark.O


def test_game_mapper_creates_independent_copy():
    matrix = [[0, 1, 2], [0, 2, 1], [0, 1, 2]]
    domain_game = DomainGame(uuid4(), DomainBoard(matrix))
    orm_game = DatasourceGameMapper.domain_to_orm(domain_game)
    orm_game.board[0][2] = 1
    assert domain_game.board.matrix == matrix
