from uuid import uuid4
from unittest.mock import Mock

from datasource.storage.storage import Storage
from datasource.model.game import Game as DatasourceGame
from datasource.model.board import Board as DatasourceBoard
from datasource.mapper.board_mapper import DatasourceBoardMapper
from datasource.mapper.game_mapper import DatasourceGameMapper
from domain.model.game import DomainGame as DomainGame
from domain.model.board import DomainBoard as DomainBoard
from datasource.repository.game_repository_implementation import GameRepositoryImpl
from domain.service.game_implementation_service import GameServiceImpl


def test_storage_save_and_get_game():
    game_uuid = uuid4()
    matrix = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]
    board = DatasourceBoard(matrix)
    game = DatasourceGame(game_uuid, board)
    storage = Storage()

    storage.save(game)
    result = storage.get(game_uuid)

    assert result is not None
    assert result.uuid == game_uuid
    assert result.board.matrix == matrix


def test_storage_get_unknown_uuid_returns_none():
    game_uuid = uuid4()
    storage = Storage()

    result = storage.get(game_uuid)
    assert result is None


def test_storage_save_same_uuid_updates_game():
    game_uuid = uuid4()
    matrix_1 = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]
    matrix_2 = [
        [0, 1, 2],
        [0, 2, 1],
        [1, 1, 2],
    ]

    game_1 = DatasourceGame(game_uuid, DatasourceBoard(matrix_1))
    game_2 = DatasourceGame(game_uuid, DatasourceBoard(matrix_2))

    storage = Storage()

    storage.save(game_1)
    storage.save(game_2)

    result = storage.get(game_uuid)

    assert result.board.matrix == matrix_2


def test_storage_save_creates_independent_copy():
    game_uuid = uuid4()
    matrix_1 = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]
    # matrix_2 = [
    #     [0, 1, 2],
    #     [0, 2, 1],
    #     [1, 1, 2],
    # ]

    game = DatasourceGame(game_uuid, DatasourceBoard(matrix_1))

    storage = Storage()
    storage.save(game)

    test_game = storage.get(game_uuid)

    test_game.board.matrix[2][0] = 1

    result = storage.get(game_uuid)

    assert test_game.board.matrix[2][0] == 1
    assert result.board.matrix == matrix_1


def test_storage_get_returns_independent_copy():
    game_uuid = uuid4()
    matrix_1 = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]
    # matrix_2 = [
    #     [0, 1, 2],
    #     [0, 2, 1],
    #     [1, 1, 2],
    # ]

    game = DatasourceGame(game_uuid, DatasourceBoard(matrix_1))

    storage = Storage()
    storage.save(game)
    test_game = storage.get(game_uuid)

    test_game.board.matrix[2][0] = 1
    result = storage.get(game_uuid)

    assert test_game.board.matrix[2][0] == 1
    assert result.board.matrix == matrix_1


def test_board_mapper_datasource_to_domain():
    matrix_1 = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]

    datasource_board = DatasourceBoard(matrix_1)
    board_mapper = DatasourceBoardMapper()
    domain_board = board_mapper.to_domain(datasource_board)

    assert isinstance(domain_board, DomainBoard)
    assert domain_board.matrix == matrix_1


def test_board_mapperdomain_to_datasource():
    matrix_1 = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]

    domain_board = DomainBoard(matrix_1)
    board_mapper = DatasourceBoardMapper()
    datasource_board = board_mapper.to_datasource(domain_board)

    assert isinstance(datasource_board, DatasourceBoard)
    assert datasource_board.matrix == matrix_1


def test_board_mapper_creates_independent_copy():
    matrix_1 = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]
    # matrix_2 = [
    #     [0, 1, 2],
    #     [0, 2, 1],
    #     [1, 1, 2],
    # ]

    domain_board = DomainBoard(matrix_1)
    board_mapper = DatasourceBoardMapper()
    datasource_board = board_mapper.to_datasource(domain_board)
    datasource_board.matrix[2][0] = 1

    assert datasource_board.matrix[2][0] == 1
    assert domain_board.matrix == matrix_1


def test_game_mapper_datasource_to_domain():
    uuid = uuid4()
    matrix_1 = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]

    datasource_board = DatasourceBoard(matrix_1)
    datasource_game = DatasourceGame(uuid, datasource_board)
    game_mapper = DatasourceGameMapper()

    domain_game = game_mapper.to_domain(datasource_game)

    assert isinstance(domain_game, DomainGame)
    assert domain_game.uuid == uuid
    assert domain_game.board.matrix == matrix_1
    assert isinstance(domain_game.board, DomainBoard)


def test_game_mapper_domain_to_datasource():
    uuid = uuid4()
    matrix_1 = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]

    domain_board = DomainBoard(matrix_1)
    domain_game = DomainGame(uuid, domain_board)
    game_mapper = DatasourceGameMapper()

    datasource_game = game_mapper.to_datasource(domain_game)

    assert isinstance(datasource_game, DatasourceGame)
    assert datasource_game.uuid == uuid
    assert datasource_game.board.matrix == matrix_1
    assert isinstance(datasource_game.board, DatasourceBoard)


def test_game_mapper_creates_independent_copy():
    uuid = uuid4()
    matrix_1 = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]
    # matrix_2 = [
    #     [0, 1, 2],
    #     [0, 2, 1],
    #     [1, 1, 2],
    # ]

    domain_board = DomainBoard(matrix_1)
    domain_game = DomainGame(uuid, domain_board)
    game_mapper = DatasourceGameMapper()

    datasource_game = game_mapper.to_datasource(domain_game)
    datasource_game.board.matrix[0][2] = 1

    assert domain_game.board.matrix == matrix_1


def test_game_repository_save_and_get_game():
    uuid = uuid4()
    matrix_1 = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]

    domain_board = DomainBoard(matrix_1)
    domain_game = DomainGame(uuid, domain_board)

    game_mapper = DatasourceGameMapper()
    storage = Storage()
    repository = GameRepositoryImpl(game_mapper, storage)

    repository.save(domain_game)
    load_game = repository.get(uuid)

    assert load_game is not None
    assert load_game.uuid == uuid
    assert load_game.board.matrix == matrix_1


def test_game_repository_get_unknown_uuid_returns_none():
    uuid = uuid4()
    game_mapper = DatasourceGameMapper()
    storage = Storage()
    repository = GameRepositoryImpl(game_mapper, storage)
    load_game = repository.get(uuid)

    assert load_game is None


def test_game_repository_get_returns_domain_game():
    uuid = uuid4()
    matrix_1 = [
        [0, 1, 2],
        [0, 2, 1],
        [0, 1, 2],
    ]

    domain_board = DomainBoard(matrix_1)
    domain_game = DomainGame(uuid, domain_board)

    game_mapper = DatasourceGameMapper()
    storage = Storage()
    repository = GameRepositoryImpl(game_mapper, storage)

    repository.save(domain_game)
    result = repository.get(uuid)

    assert isinstance(result, DomainGame)
    assert isinstance(result.board, DomainBoard)
    assert result.uuid == uuid
    assert result.board.matrix == matrix_1


def test_whose_move_returns_x_when_counts_are_equal():
    matrix = [
        [1, 2, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]

    repository = Mock(spec=GameRepositoryImpl)
    game_service = GameServiceImpl(repository)

    result = game_service.whose_move(matrix)

    assert result == 1


def test_whose_move_returns_o_when_x_has_one_extra_move():
    matrix = [
        [1, 2, 1],
        [0, 0, 0],
        [0, 0, 0],
    ]

    repository = Mock(spec=GameRepositoryImpl)
    game_service = GameServiceImpl(repository)

    result = game_service.whose_move(matrix)

    assert result == 2


def test_whose_move_returns_none_when_x_has_two_extra_moves():
    matrix = [
        [1, 1, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]

    repository = Mock(spec=GameRepositoryImpl)
    game_service = GameServiceImpl(repository)

    result = game_service.whose_move(matrix)

    assert result is None


def test_whose_move_returns_none_when_o_count_is_greater():
    matrix = [
        [2, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]

    repository = Mock(spec=GameRepositoryImpl)
    game_service = GameServiceImpl(repository)

    result = game_service.whose_move(matrix)

    assert result is None


def test_move_comp_returns_none_when_game_not_found():
    game_uuid = uuid4()

    repository = Mock(spec=GameRepositoryImpl)
    repository.get.return_value = None

    game_service = GameServiceImpl(repository)

    result = game_service._move_comp(game_uuid)

    assert result is None
    repository.get.assert_called_once_with(game_uuid)
    repository.save.assert_not_called()


def test_move_comp_returns_none_when_game_is_finish():
    game_uuid = uuid4()
    matrix = [
        [1, 1, 1],
        [2, 2, 0],
        [0, 0, 0],
    ]
    board = DomainBoard(matrix)
    game = DomainGame(game_uuid, board)
    repository = Mock(spec=GameRepositoryImpl)
    repository.get.return_value = game
    game_service = GameServiceImpl(repository)

    result = game_service._move_comp(game_uuid)

    assert result is None
    assert game.board.matrix == matrix
    repository.save.assert_not_called()


def test_move_comp_returns_none_when_it_is_user_turn():
    game_uuid = uuid4()
    matrix = [
        [1, 1, 0],
        [2, 2, 0],
        [0, 0, 0],
    ]
    old_matrix = [row[:] for row in matrix]
    board = DomainBoard(matrix)
    game = DomainGame(game_uuid, board)
    repository = Mock(spec=GameRepositoryImpl)
    repository.get.return_value = game
    game_service = GameServiceImpl(game_repository=repository)

    result = game_service._move_comp(game_uuid)

    assert result is None
    assert game.board.matrix == old_matrix
    repository.save.assert_not_called()


def test_move_comp_makes_computer_move():
    def check_matrices(matrix_old, matrix_new):
        cnt_x_old = 0
        cnt_x_new = 0
        cnt_o_old = 0
        cnt_o_new = 0

        if len(matrix_old) != len(matrix_new):
            return False
        for i in range(len(matrix_old)):
            if len(matrix_old[i]) != len(matrix_new[i]):
                return False
            for j in range(len(matrix_old[i])):
                if matrix_old[i][j] != 0 and matrix_old[i][j] != matrix_new[i][j]:
                    return False
                if matrix_old[i][j] == 1:
                    cnt_x_old += 1
                elif matrix_old[i][j] == 2:
                    cnt_o_old += 1
                if matrix_new[i][j] == 1:
                    cnt_x_new += 1
                elif matrix_new[i][j] == 2:
                    cnt_o_new += 1

        deff_x = cnt_x_new - cnt_x_old
        deff_o = cnt_o_new - cnt_o_old

        if deff_x == 0 and deff_o == 1:
            return True

        return False

    game_uuid = uuid4()
    matrix = [
        [1, 1, 0],
        [2, 2, 0],
        [1, 0, 0],
    ]
    board = DomainBoard(matrix)
    game = DomainGame(game_uuid, board)
    repository = Mock(spec=GameRepositoryImpl)
    repository.get.return_value = game
    game_service = GameServiceImpl(game_repository=repository)

    result = game_service._move_comp(game_uuid)

    assert result is not None
    assert result.board.matrix != matrix
    assert check_matrices(matrix, result.board.matrix)
    repository.save.assert_called_once()


def test_move_comp_saves_game_after_successful_move():
    game_uuid = uuid4()
    matrix = [
        [1, 1, 0],
        [2, 2, 0],
        [1, 0, 0],
    ]
    board = DomainBoard(matrix)
    game = DomainGame(game_uuid, board)

    repository = Mock(spec=GameRepositoryImpl)
    repository.get.return_value = game

    game_service = GameServiceImpl(
        game_repository=repository,
    )

    result = game_service._move_comp(game_uuid)

    repository.save.assert_called_once()
