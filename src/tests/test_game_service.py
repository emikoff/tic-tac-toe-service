from uuid import uuid4
from unittest.mock import Mock

import pytest

from domain.model.board import DomainBoard
from domain.model.game import DomainGame
from domain.model.game_mark import GameMark
from domain.model.game_state import GameState
from domain.model.game_status import GameStatus
from domain.model.opponent_type import OpponentType
from domain.exception.game_exception import (
    CannotJoinOwnGameError,
    GameAlreadyFinishedError,
    GameNotAvailableError,
    GameNotFoundError,
    GameNotStartedError,
    InvalidGameMoveError,
    NotGameParticipantError,
    NotPlayerTurnError,
)
from domain.service.game_implementation_service import GameServiceImpl
from datasource.repository.game_repository_implementation import GameRepositoryImpl
from datasource.mapper.game_mapper import DatasourceGameMapper


@pytest.fixture
def service():
    return GameServiceImpl(Mock(spec=GameRepositoryImpl))


# =========================================================
# new_game
# =========================================================


def test_new_game_with_user_waits_for_second_player(service):
    first_player_uuid = uuid4()

    game = service.new_game(first_player_uuid, OpponentType.USER)

    assert game.opponent_type == OpponentType.USER
    assert game.state == GameState.WAITING_FOR_PLAYERS
    assert game.first_player_uuid == first_player_uuid
    assert game.second_player_uuid is None
    assert game.current_player_uuid is None
    assert game.winner_uuid is None
    assert game.first_player_mark == GameMark.X
    assert game.second_player_mark == GameMark.O
    assert game.board.matrix == [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    service.game_repository.save.assert_called_once_with(game)


def test_new_game_with_computer_starts_with_first_player_turn(service):
    first_player_uuid = uuid4()

    game = service.new_game(first_player_uuid, OpponentType.COMPUTER)

    assert game.opponent_type == OpponentType.COMPUTER
    assert game.state == GameState.PLAYER_TURN
    assert game.first_player_uuid == first_player_uuid
    assert game.second_player_uuid is None
    assert game.current_player_uuid == first_player_uuid
    assert game.winner_uuid is None
    assert game.first_player_mark == GameMark.X
    assert game.second_player_mark == GameMark.O
    assert game.board.matrix == [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    service.game_repository.save.assert_called_once_with(game)


def test_get_available_games_returns_repository_result(service):
    available_games = [Mock(), Mock()]
    service.game_repository.get_available.return_value = available_games

    result = service.get_available_games()

    assert result == available_games
    service.game_repository.get_available.assert_called_once_with()


def test_get_game_returns_repository_game(service):
    game = make_waiting_game(uuid4())
    service.game_repository.get.return_value = game

    result = service.get_game(game.uuid)

    assert result is game
    service.game_repository.get.assert_called_once_with(game.uuid)


def test_get_unknown_game_raises_error(service):
    game_uuid = uuid4()
    service.game_repository.get.return_value = None

    with pytest.raises(GameNotFoundError):
        service.get_game(game_uuid)

    service.game_repository.get.assert_called_once_with(game_uuid)


# =========================================================
# join_game
# =========================================================


def make_waiting_game(first_player_uuid):
    return DomainGame(
        uuid=uuid4(),
        board=DomainBoard([[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
        opponent_type=OpponentType.USER,
        state=GameState.WAITING_FOR_PLAYERS,
        first_player_uuid=first_player_uuid,
    )


def test_join_game_adds_second_player_and_starts_game(service):
    first_player_uuid = uuid4()
    second_player_uuid = uuid4()
    game = make_waiting_game(first_player_uuid)
    service.game_repository.get.return_value = game

    result = service.join_game(game.uuid, second_player_uuid)

    assert result is game
    assert game.second_player_uuid == second_player_uuid
    assert game.state == GameState.PLAYER_TURN
    assert game.current_player_uuid == first_player_uuid
    service.game_repository.save.assert_called_once_with(game)


def test_join_unknown_game_raises_error(service):
    service.game_repository.get.return_value = None

    with pytest.raises(GameNotFoundError):
        service.join_game(uuid4(), uuid4())

    service.game_repository.save.assert_not_called()


def test_first_player_cannot_join_own_game(service):
    first_player_uuid = uuid4()
    game = make_waiting_game(first_player_uuid)
    service.game_repository.get.return_value = game

    with pytest.raises(CannotJoinOwnGameError):
        service.join_game(game.uuid, first_player_uuid)

    service.game_repository.save.assert_not_called()


@pytest.mark.parametrize(
    ("opponent_type", "state", "second_player_uuid"),
    [
        (OpponentType.COMPUTER, GameState.PLAYER_TURN, None),
        (OpponentType.USER, GameState.PLAYER_TURN, uuid4()),
        (OpponentType.USER, GameState.VICTORY, uuid4()),
    ],
)
def test_user_cannot_join_unavailable_game(
    service,
    opponent_type,
    state,
    second_player_uuid,
):
    game = DomainGame(
        uuid=uuid4(),
        board=DomainBoard([[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
        opponent_type=opponent_type,
        state=state,
        first_player_uuid=uuid4(),
        second_player_uuid=second_player_uuid,
    )
    service.game_repository.get.return_value = game

    with pytest.raises(GameNotAvailableError):
        service.join_game(game.uuid, uuid4())

    service.game_repository.save.assert_not_called()


# =========================================================
# move_player
# =========================================================


def make_active_user_game(matrix=None):
    first_player_uuid = uuid4()
    second_player_uuid = uuid4()
    game = DomainGame(
        uuid=uuid4(),
        board=DomainBoard(
            matrix or [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        ),
        opponent_type=OpponentType.USER,
        state=GameState.PLAYER_TURN,
        first_player_uuid=first_player_uuid,
        second_player_uuid=second_player_uuid,
        current_player_uuid=first_player_uuid,
    )
    return game, first_player_uuid, second_player_uuid


def test_move_in_unknown_game_raises_error(service):
    service.game_repository.get.return_value = None

    with pytest.raises(GameNotFoundError):
        service.move_player(uuid4(), uuid4(), DomainBoard([]))


def test_user_outside_game_cannot_move(service):
    game, _, _ = make_active_user_game()
    service.game_repository.get.return_value = game

    with pytest.raises(NotGameParticipantError):
        service.move_player(game.uuid, uuid4(), DomainBoard([]))

    service.game_repository.save.assert_not_called()


def test_user_cannot_move_before_second_player_joins(service):
    first_player_uuid = uuid4()
    game = make_waiting_game(first_player_uuid)
    service.game_repository.get.return_value = game

    with pytest.raises(GameNotStartedError):
        service.move_player(game.uuid, first_player_uuid, DomainBoard([]))


def test_user_cannot_move_out_of_turn(service):
    game, _, second_player_uuid = make_active_user_game()
    service.game_repository.get.return_value = game

    with pytest.raises(NotPlayerTurnError):
        service.move_player(game.uuid, second_player_uuid, DomainBoard([]))


def test_invalid_board_change_is_rejected(service):
    game, first_player_uuid, _ = make_active_user_game()
    service.game_repository.get.return_value = game

    with pytest.raises(InvalidGameMoveError):
        service.move_player(
            game.uuid,
            first_player_uuid,
            DomainBoard([[1, 1, 0], [0, 0, 0], [0, 0, 0]]),
        )

    service.game_repository.save.assert_not_called()


def test_first_user_move_switches_turn_to_second_user(service):
    game, first_player_uuid, second_player_uuid = make_active_user_game()
    service.game_repository.get.return_value = game
    new_board = DomainBoard([[1, 0, 0], [0, 0, 0], [0, 0, 0]])

    result, status = service.move_player(
        game.uuid,
        first_player_uuid,
        new_board,
    )

    assert result.board == new_board
    assert result.current_player_uuid == second_player_uuid
    assert status == GameStatus.GAME_CONTINUES
    service.game_repository.save.assert_called_once_with(game)


def test_second_user_move_switches_turn_to_first_user(service):
    game, first_player_uuid, second_player_uuid = make_active_user_game(
        [[1, 0, 0], [0, 0, 0], [0, 0, 0]]
    )
    game.current_player_uuid = second_player_uuid
    service.game_repository.get.return_value = game

    result, status = service.move_player(
        game.uuid,
        second_player_uuid,
        DomainBoard([[1, 2, 0], [0, 0, 0], [0, 0, 0]]),
    )

    assert result.current_player_uuid == first_player_uuid
    assert status == GameStatus.GAME_CONTINUES


def test_winning_user_move_stores_state_and_winner(service):
    game, first_player_uuid, _ = make_active_user_game(
        [[1, 1, 0], [2, 2, 0], [0, 0, 0]]
    )
    service.game_repository.get.return_value = game

    result, status = service.move_player(
        game.uuid,
        first_player_uuid,
        DomainBoard([[1, 1, 1], [2, 2, 0], [0, 0, 0]]),
    )

    assert result.state == GameState.VICTORY
    assert result.winner_uuid == first_player_uuid
    assert result.current_player_uuid is None
    assert status == GameStatus.USER_WON


def test_second_player_victory_stores_second_player_uuid(service):
    game, _, second_player_uuid = make_active_user_game(
        [[2, 2, 0], [1, 1, 0], [1, 0, 0]]
    )
    game.current_player_uuid = second_player_uuid
    service.game_repository.get.return_value = game

    result, status = service.move_player(
        game.uuid,
        second_player_uuid,
        DomainBoard([[2, 2, 2], [1, 1, 0], [1, 0, 0]]),
    )

    assert result.state == GameState.VICTORY
    assert result.winner_uuid == second_player_uuid
    assert result.current_player_uuid is None
    assert status == GameStatus.USER_WON


def test_draw_move_stores_draw_state(service):
    game, first_player_uuid, _ = make_active_user_game(
        [[1, 2, 1], [1, 2, 2], [2, 1, 0]]
    )
    service.game_repository.get.return_value = game

    result, status = service.move_player(
        game.uuid,
        first_player_uuid,
        DomainBoard([[1, 2, 1], [1, 2, 2], [2, 1, 1]]),
    )

    assert result.state == GameState.DRAW
    assert result.winner_uuid is None
    assert result.current_player_uuid is None
    assert status == GameStatus.DRAW


def test_computer_moves_after_user_and_returns_turn(service):
    first_player_uuid = uuid4()
    game = DomainGame(
        uuid=uuid4(),
        board=DomainBoard([[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
        opponent_type=OpponentType.COMPUTER,
        state=GameState.PLAYER_TURN,
        first_player_uuid=first_player_uuid,
        current_player_uuid=first_player_uuid,
    )
    service.game_repository.get.return_value = game

    result, status = service.move_player(
        game.uuid,
        first_player_uuid,
        DomainBoard([[1, 0, 0], [0, 0, 0], [0, 0, 0]]),
    )

    assert sum(row.count(1) for row in result.board.matrix) == 1
    assert sum(row.count(2) for row in result.board.matrix) == 1
    assert result.current_player_uuid == first_player_uuid
    assert status == GameStatus.GAME_CONTINUES


def test_computer_victory_has_no_user_winner_uuid(service):
    first_player_uuid = uuid4()
    game = DomainGame(
        uuid=uuid4(),
        board=DomainBoard([[1, 1, 2], [0, 2, 0], [0, 0, 0]]),
        opponent_type=OpponentType.COMPUTER,
        state=GameState.PLAYER_TURN,
        first_player_uuid=first_player_uuid,
        current_player_uuid=first_player_uuid,
    )
    service.game_repository.get.return_value = game

    result, status = service.move_player(
        game.uuid,
        first_player_uuid,
        DomainBoard([[1, 1, 2], [1, 2, 0], [0, 0, 0]]),
    )

    assert result.state == GameState.VICTORY
    assert result.winner_uuid is None
    assert result.current_player_uuid is None
    assert status == GameStatus.COMPUTER_WON


@pytest.mark.parametrize("state", [GameState.DRAW, GameState.VICTORY])
def test_move_in_finished_game_is_rejected(service, state):
    game, first_player_uuid, _ = make_active_user_game()
    game.state = state
    game.current_player_uuid = None
    service.game_repository.get.return_value = game

    with pytest.raises(GameAlreadyFinishedError):
        service.move_player(game.uuid, first_player_uuid, DomainBoard([]))


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
