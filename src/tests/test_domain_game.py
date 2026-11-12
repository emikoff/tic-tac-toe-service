from uuid import uuid4

from domain.model.board import DomainBoard
from domain.model.game import DomainGame
from domain.model.game_mark import GameMark
from domain.model.game_state import GameState
from domain.model.opponent_type import OpponentType


def empty_board():
    return DomainBoard([[0, 0, 0], [0, 0, 0], [0, 0, 0]])


def test_legacy_game_defaults_to_game_with_computer():
    game_uuid = uuid4()

    game = DomainGame(game_uuid, empty_board())

    assert game.uuid == game_uuid
    assert game.opponent_type == OpponentType.COMPUTER
    assert game.state == GameState.PLAYER_TURN
    assert game.first_player_uuid is None
    assert game.second_player_uuid is None
    assert game.current_player_uuid is None
    assert game.winner_uuid is None
    assert game.first_player_mark == GameMark.X
    assert game.second_player_mark == GameMark.O


def test_game_can_wait_for_second_user():
    first_player_uuid = uuid4()

    game = DomainGame(
        uuid=uuid4(),
        board=empty_board(),
        opponent_type=OpponentType.USER,
        state=GameState.WAITING_FOR_PLAYERS,
        first_player_uuid=first_player_uuid,
        first_player_mark=GameMark.X,
        second_player_mark=GameMark.O,
    )

    assert game.first_player_uuid == first_player_uuid
    assert game.second_player_uuid is None
    assert game.current_player_uuid is None
    assert game.winner_uuid is None


def test_game_can_store_players_and_current_turn():
    first_player_uuid = uuid4()
    second_player_uuid = uuid4()

    game = DomainGame(
        uuid=uuid4(),
        board=empty_board(),
        opponent_type=OpponentType.USER,
        state=GameState.PLAYER_TURN,
        first_player_uuid=first_player_uuid,
        second_player_uuid=second_player_uuid,
        current_player_uuid=first_player_uuid,
        first_player_mark=GameMark.X,
        second_player_mark=GameMark.O,
    )

    assert game.first_player_uuid == first_player_uuid
    assert game.second_player_uuid == second_player_uuid
    assert game.current_player_uuid == first_player_uuid
    assert game.first_player_mark != game.second_player_mark


def test_game_can_store_winner_uuid():
    winner_uuid = uuid4()

    game = DomainGame(
        uuid=uuid4(),
        board=empty_board(),
        opponent_type=OpponentType.USER,
        state=GameState.VICTORY,
        first_player_uuid=winner_uuid,
        second_player_uuid=uuid4(),
        winner_uuid=winner_uuid,
    )

    assert game.state == GameState.VICTORY
    assert game.current_player_uuid is None
    assert game.winner_uuid == winner_uuid
