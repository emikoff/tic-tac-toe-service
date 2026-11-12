from uuid import uuid4
from unittest.mock import Mock
from flask import Flask

from web.model.game import WebGame
from web.model.board import WebBoard
from web.mapper.board_mapper import WebBoardMapper
from web.mapper.game_mapper import WebGameMapper
from domain.model.game import DomainGame
from domain.model.board import DomainBoard
from datasource.repository.game_repository_implementation import GameRepositoryImpl
from domain.service.game_implementation_service import GameServiceImpl
from domain.model.game_status import GameStatus
from app import app


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
    matrix = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]

    web_board = WebBoard(matrix)
    web_game = WebGame(game_uuid, web_board)
    game_mapper = WebGameMapper()

    domain_game = game_mapper.to_domain(web_game)

    assert isinstance(domain_game, DomainGame)
    assert domain_game.uuid == game_uuid
    assert domain_game.board.matrix == matrix
    assert isinstance(domain_game.board, DomainBoard)


def test_game_mapper_domain_to_web():
    game_uuid = uuid4()
    matrix = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]

    domain_board = DomainBoard(matrix)
    domain_game = DomainGame(game_uuid, domain_board)
    game_mapper = WebGameMapper()

    web_game = game_mapper.to_web(domain_game)

    assert isinstance(web_game, WebGame)
    assert web_game.uuid == game_uuid
    assert web_game.board.matrix == matrix
    assert isinstance(web_game.board, WebBoard)


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

    web_game = game_mapper.to_web(domain_game)
    web_game.board.matrix[2][0] = 1

    assert domain_game.board.matrix == matrix


def test_game_not_found():
    game_uuid = uuid4()
    new_board = Mock(spec=DomainBoard)
    repository = Mock(spec=GameRepositoryImpl)

    service = GameServiceImpl(repository)
    repository.get.return_value = None
    result_game, game_status = service.move_player(game_uuid, new_board)

    assert result_game is None
    assert game_status == GameStatus.GAME_NOT_FOUND


def test_invalid_move():
    game_uuid = uuid4()
    matrix1 = [
        [1, 0, 0],
        [2, 0, 0],
        [1, 0, 0],
    ]
    matrix2 = [[0, 1, 0], [2, 0, 2], [1, 0, 0]]
    old_board = DomainBoard(matrix1)
    new_board = DomainBoard(matrix2)
    game = DomainGame(game_uuid, old_board)

    repository = Mock(GameRepositoryImpl)
    repository.get.return_value = game
    service = GameServiceImpl(repository)
    result_game, game_status = service.move_player(game_uuid, new_board)

    assert result_game == None
    assert game_status == GameStatus.INVALID_MOVE


# Переименовать
def test_game_its_end():
    game_uuid = uuid4()
    matrix = [
        [1, 1, 1],
        [2, 2, 0],
        [0, 0, 0],
    ]

    old_board = DomainBoard(matrix)
    new_board = DomainBoard(matrix)
    game = DomainGame(game_uuid, old_board)

    repository = Mock(spec=GameRepositoryImpl)
    repository.get.return_value = game
    service = GameServiceImpl(repository)

    result_game, game_status = service.move_player(game_uuid, new_board)

    assert result_game == game
    assert game_status == GameStatus.USER_WON


# отсутствие компьютерного хода;
def test_user_won_comp_not_move():
    game_uuid = uuid4()
    matrix1 = [
        [1, 1, 0],
        [2, 2, 0],
        [0, 0, 0],
    ]
    matrix2 = [[1, 1, 1], [2, 2, 0], [0, 0, 0]]
    old_board = DomainBoard(matrix1)
    new_board = DomainBoard(matrix2)
    game = DomainGame(game_uuid, old_board)

    repository = Mock(spec=GameRepositoryImpl)
    repository.get.return_value = game
    service = GameServiceImpl(repository)
    result_game, game_status = service.move_player(game_uuid, new_board)

    assert result_game == game
    assert game_status == GameStatus.USER_WON
    repository.get.assert_called_once()
    repository.save.assert_called_once()


def test_user_move_and_end_game_draw():
    game_uuid = uuid4()
    matrix1 = [
        [1, 1, 2],
        [2, 2, 1],
        [1, 2, 0],
    ]
    matrix2 = [[1, 1, 2], [2, 2, 1], [1, 2, 1]]
    old_board = DomainBoard(matrix1)
    new_board = DomainBoard(matrix2)
    game = DomainGame(game_uuid, old_board)

    repository = Mock(spec=GameRepositoryImpl)
    repository.get.return_value = game
    service = GameServiceImpl(repository)
    result_game, game_status = service.move_player(game_uuid, new_board)

    assert result_game == game
    assert game_status == GameStatus.DRAW


def test_comp_move_and_comp_won():
    game_uuid = uuid4()
    matrix1 = [
        [1, 1, 2],
        [0, 2, 0],
        [0, 0, 0],
    ]
    matrix2 = [[1, 1, 2], [1, 2, 0], [0, 0, 0]]
    old_board = DomainBoard(matrix1)
    new_board = DomainBoard(matrix2)
    game = DomainGame(game_uuid, old_board)

    repository = Mock(spec=GameRepositoryImpl)
    repository.get.return_value = game
    service = GameServiceImpl(repository)
    result_game, game_status = service.move_player(game_uuid, new_board)

    assert result_game is not None
    assert game_status == GameStatus.COMPUTER_WON


def test_user_move_comp_move_game_continues():
    game_uuid = uuid4()
    matrix1 = [
        [1, 1, 2],
        [0, 2, 0],
        [0, 0, 0],
    ]
    matrix2 = [[1, 1, 2], [0, 2, 0], [1, 0, 0]]
    old_board = DomainBoard(matrix1)
    new_board = DomainBoard(matrix2)
    game = DomainGame(game_uuid, old_board)

    repository = Mock(spec=GameRepositoryImpl)
    repository.get.return_value = game
    service = GameServiceImpl(repository)
    result_game, game_status = service.move_player(game_uuid, new_board)

    assert result_game is not None
    assert game_status == GameStatus.GAME_CONTINUES
