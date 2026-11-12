from unittest.mock import Mock

import pytest

from domain.model.board import DomainBoard
from domain.service.game_implementation_service import GameServiceImpl
from datasource.repository.game_repository_implementation import GameRepositoryImpl
from datasource.mapper.game_mapper import DatasourceGameMapper


@pytest.fixture
def service():
    return GameServiceImpl(Mock(spec=GameRepositoryImpl))


# =========================================================
# board_validate
# =========================================================


def test_board_validate_x_valid_move(service):
    old_board = DomainBoard(
        matrix=[
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    new_board = DomainBoard(
        matrix=[
            [1, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    assert service.board_validate(old_board, new_board) is True


def test_board_validate_o_valid_move(service):
    old_board = DomainBoard(
        matrix=[
            [1, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    new_board = DomainBoard(
        matrix=[
            [1, 2, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    assert service.board_validate(old_board, new_board) is True


def test_board_validate_no_move(service):
    old_board = DomainBoard(
        matrix=[
            [1, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    new_board = DomainBoard(
        matrix=[
            [1, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    assert service.board_validate(old_board, new_board) is False


def test_board_validate_two_moves_at_once(service):
    old_board = DomainBoard(
        matrix=[
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    new_board = DomainBoard(
        matrix=[
            [1, 1, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    assert service.board_validate(old_board, new_board) is False


def test_board_validate_change_existing_cell(service):
    old_board = DomainBoard(
        matrix=[
            [1, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    new_board = DomainBoard(
        matrix=[
            [2, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    assert service.board_validate(old_board, new_board) is False


def test_board_validate_remove_existing_cell(service):
    old_board = DomainBoard(
        matrix=[
            [1, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    new_board = DomainBoard(
        matrix=[
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    assert service.board_validate(old_board, new_board) is False


def test_board_validate_invalid_value(service):
    old_board = DomainBoard(
        matrix=[
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    new_board = DomainBoard(
        matrix=[
            [3, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    assert service.board_validate(old_board, new_board) is False


def test_board_validate_different_row_count(service):
    old_board = DomainBoard(
        matrix=[
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    new_board = DomainBoard(
        matrix=[
            [1, 0, 0],
            [0, 0, 0],
        ]
    )

    assert service.board_validate(old_board, new_board) is False


def test_board_validate_different_column_count(service):
    old_board = DomainBoard(
        matrix=[
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    new_board = DomainBoard(
        matrix=[
            [1, 0, 0],
            [0, 0],
            [0, 0, 0],
        ]
    )

    assert service.board_validate(old_board, new_board) is False


def test_board_validate_o_cannot_move_first(service):
    old_board = DomainBoard(
        matrix=[
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    new_board = DomainBoard(
        matrix=[
            [2, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    assert service.board_validate(old_board, new_board) is False


def test_board_validate_x_cannot_move_twice(service):
    old_board = DomainBoard(
        matrix=[
            [1, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    new_board = DomainBoard(
        matrix=[
            [1, 1, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    assert service.board_validate(old_board, new_board) is False


def test_board_validate_invalid_old_board_balance(service):
    old_board = DomainBoard(
        matrix=[
            [1, 1, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    new_board = DomainBoard(
        matrix=[
            [1, 1, 2],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    assert service.board_validate(old_board, new_board) is False


def test_board_validate_invalid_value_in_old_board(service):
    old_board = DomainBoard(
        matrix=[
            [3, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    new_board = DomainBoard(
        matrix=[
            [3, 1, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    assert service.board_validate(old_board, new_board) is False


# =========================================================
# check_end_game
# =========================================================


def test_check_end_game_x_wins_row(service):
    matrix = [
        [1, 1, 1],
        [2, 2, 0],
        [0, 0, 0],
    ]

    assert service.check_end_game_and_winner(matrix) == (True, 1)


def test_check_end_game_o_wins_row(service):
    matrix = [
        [1, 1, 0],
        [2, 2, 2],
        [1, 0, 0],
    ]

    assert service.check_end_game_and_winner(matrix) == (True, 2)


def test_check_end_game_x_wins_column(service):
    matrix = [
        [1, 2, 0],
        [1, 2, 0],
        [1, 0, 0],
    ]

    assert service.check_end_game_and_winner(matrix) == (True, 1)


def test_check_end_game_o_wins_column(service):
    matrix = [
        [1, 2, 1],
        [0, 2, 0],
        [1, 2, 0],
    ]

    assert service.check_end_game_and_winner(matrix) == (True, 2)


def test_check_end_game_x_wins_main_diagonal(service):
    matrix = [
        [1, 2, 0],
        [2, 1, 0],
        [0, 0, 1],
    ]

    assert service.check_end_game_and_winner(matrix) == (True, 1)


def test_check_end_game_o_wins_secondary_diagonal(service):
    matrix = [
        [1, 0, 2],
        [1, 2, 0],
        [2, 0, 1],
    ]

    assert service.check_end_game_and_winner(matrix) == (True, 2)


def test_check_end_game_draw(service):
    matrix = [
        [1, 2, 1],
        [1, 2, 2],
        [2, 1, 1],
    ]

    assert service.check_end_game_and_winner(matrix) == (True, 0)


def test_check_end_game_not_finished(service):
    matrix = [
        [1, 2, 0],
        [0, 1, 0],
        [2, 0, 0],
    ]

    assert service.check_end_game_and_winner(matrix) == (False, 0)


def test_check_end_game_empty_board(service):
    matrix = [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]

    assert service.check_end_game_and_winner(matrix) == (False, 0)


# =========================================================
# next_move
# =========================================================


def test_next_move_blocks_x_win(service):
    board = DomainBoard(
        matrix=[
            [1, 1, 0],
            [0, 2, 0],
            [0, 0, 0],
        ]
    )

    result = service.next_move(board)

    assert result.matrix[0][2] == 2


def test_next_move_takes_winning_move(service):
    board = DomainBoard(
        matrix=[
            [2, 2, 0],
            [1, 1, 0],
            [1, 0, 0],
        ]
    )

    result = service.next_move(board)

    # assert result.matrix[0][2] == 2
    assert result.matrix == [
        [2, 2, 2],
        [1, 1, 0],
        [1, 0, 0],
    ]

    end, winner = service.check_end_game_and_winner(result.matrix)

    assert end is True
    assert winner == 2


def test_next_move_adds_exactly_one_o(service):
    old_matrix = [
        [1, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]

    board = DomainBoard(matrix=[row[:] for row in old_matrix])

    result = service.next_move(board)

    old_o_count = sum(row.count(2) for row in old_matrix)
    new_o_count = sum(row.count(2) for row in result.matrix)

    assert new_o_count == old_o_count + 1


def test_next_move_does_not_change_existing_cells(service):
    old_matrix = [
        [1, 2, 1],
        [1, 2, 0],
        [0, 0, 0],
    ]

    board = DomainBoard(matrix=[row[:] for row in old_matrix])

    result = service.next_move(board)

    for i in range(3):
        for j in range(3):
            if old_matrix[i][j] != 0:
                assert result.matrix[i][j] == old_matrix[i][j]


def test_next_move_chooses_draw_instead_of_loss(service):
    board = DomainBoard(
        matrix=[
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 1],
        ]
    )

    result = service.next_move(board)

    assert result.matrix[1][1] == 2


# =========================================================
# minimax
# =========================================================


def test_minimax_o_has_winning_position(service):
    matrix = [
        [2, 2, 0],
        [1, 1, 0],
        [0, 0, 0],
    ]

    assert service._minimax(matrix, 2) == 1


def test_minimax_x_has_winning_position(service):
    matrix = [
        [1, 1, 0],
        [2, 0, 0],
        [0, 2, 0],
    ]

    assert service._minimax(matrix, 1) == -1


def test_minimax_draw_position(service):
    matrix = [
        [1, 2, 1],
        [1, 2, 2],
        [2, 1, 0],
    ]

    assert service._minimax(matrix, 2) == 0


def test_minimax_does_not_change_matrix(service):
    matrix = [
        [1, 2, 0],
        [0, 1, 0],
        [0, 0, 0],
    ]

    original_matrix = [row[:] for row in matrix]

    service._minimax(matrix, 2)

    assert matrix == original_matrix
