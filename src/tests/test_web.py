from uuid import uuid4

from web.model.game import WebGame
from web.model.board import WebBoard
from web.mapper.board_mapper import WebBoardMapper
from web.mapper.game_mapper import WebGameMapper
from domain.model.game import DomainGame
from domain.model.board import DomainBoard
from domain.model.game_mark import GameMark
from domain.model.game_state import GameState
from domain.model.opponent_type import OpponentType


def test_board_mapper_web_to_domain():
    matrix = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]

    web_board = WebBoard(matrix)
    board_mapper = WebBoardMapper()
    domain_board = board_mapper.to_domain(web_board)

    assert isinstance(domain_board, DomainBoard)
    assert domain_board.matrix == matrix


def test_board_mapper_domain_to_web():
    matrix = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]

    domain_board = DomainBoard(matrix)
    board_mapper = WebBoardMapper()
    web_board = board_mapper.to_web(domain_board)

    assert isinstance(web_board, WebBoard)
    assert web_board.matrix == matrix


def test_board_mapper_creates_independent_copy():
    matrix = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]

    domain_board = DomainBoard(matrix)
    board_mapper = WebBoardMapper()
    web_board = board_mapper.to_web(domain_board)
    web_board.matrix[2][0] = 1

    assert domain_board.matrix == matrix


def test_game_mapper_web_to_domain():
    game_uuid = uuid4()
    first_player_uuid = uuid4()
    matrix = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]

    web_board = WebBoard(matrix)
    web_game = WebGame(
        uuid=game_uuid,
        board=web_board,
        opponent_type=OpponentType.USER,
        state=GameState.WAITING_FOR_PLAYERS,
        first_player_uuid=first_player_uuid,
    )
    game_mapper = WebGameMapper()

    domain_game = game_mapper.web_to_domain(web_game)

    assert isinstance(domain_game, DomainGame)
    assert domain_game.uuid == game_uuid
    assert domain_game.board.matrix == matrix
    assert isinstance(domain_game.board, DomainBoard)
    assert domain_game.opponent_type == OpponentType.USER
    assert domain_game.state == GameState.WAITING_FOR_PLAYERS
    assert domain_game.first_player_uuid == first_player_uuid
    assert domain_game.first_player_mark == GameMark.X
    assert domain_game.second_player_mark == GameMark.O


def test_game_mapper_domain_to_web():
    game_uuid = uuid4()
    first_player_uuid = uuid4()
    matrix = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]

    domain_board = DomainBoard(matrix)
    domain_game = DomainGame(
        uuid=game_uuid,
        board=domain_board,
        opponent_type=OpponentType.COMPUTER,
        state=GameState.PLAYER_TURN,
        first_player_uuid=first_player_uuid,
        current_player_uuid=first_player_uuid,
    )
    game_mapper = WebGameMapper()

    web_game = game_mapper.domain_to_web(domain_game)

    assert isinstance(web_game, WebGame)
    assert web_game.uuid == game_uuid
    assert web_game.board.matrix == matrix
    assert isinstance(web_game.board, WebBoard)
    assert web_game.opponent_type == OpponentType.COMPUTER
    assert web_game.state == GameState.PLAYER_TURN
    assert web_game.first_player_uuid == first_player_uuid
    assert web_game.current_player_uuid == first_player_uuid
    assert web_game.first_player_mark == GameMark.X
    assert web_game.second_player_mark == GameMark.O


def test_game_mapper_creates_independent_copy():
    game_uuid = uuid4()
    matrix = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]

    domain_board = DomainBoard(matrix)
    domain_game = DomainGame(game_uuid, domain_board)
    game_mapper = WebGameMapper()

    web_game = game_mapper.domain_to_web(domain_game)
    web_game.board.matrix[2][0] = 1

    assert domain_game.board.matrix == matrix
