from domain.model.game_mark import GameMark
from domain.model.game_state import GameState
from domain.model.opponent_type import OpponentType


def test_opponent_type_contains_user_and_computer():
    assert set(OpponentType) == {
        OpponentType.USER,
        OpponentType.COMPUTER,
    }


def test_game_state_contains_all_states_from_requirements():
    assert set(GameState) == {
        GameState.WAITING_FOR_PLAYERS,
        GameState.PLAYER_TURN,
        GameState.DRAW,
        GameState.VICTORY,
    }


def test_game_mark_contains_x_and_o():
    assert set(GameMark) == {GameMark.X, GameMark.O}


def test_game_types_have_stable_string_values():
    assert OpponentType.USER.value == "USER"
    assert OpponentType.COMPUTER.value == "COMPUTER"
    assert GameState.WAITING_FOR_PLAYERS.value == "WAITING_FOR_PLAYERS"
    assert GameState.PLAYER_TURN.value == "PLAYER_TURN"
    assert GameState.DRAW.value == "DRAW"
    assert GameState.VICTORY.value == "VICTORY"
    assert GameMark.X.value == "X"
    assert GameMark.O.value == "O"
