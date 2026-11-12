from uuid import uuid4

from datasource.mapper.game_mapper import DatasourceGameMapper
from datasource.repository.game_repository_implementation import GameRepositoryImpl
from datasource.mapper.user_mapper import DatasourceUserMapper
from datasource.repository.user_repository_implementation import UserRepositoryImpl
from domain.model.board import DomainBoard
from domain.model.game import DomainGame
from domain.model.game_mark import GameMark
from domain.model.game_state import GameState
from domain.model.opponent_type import OpponentType
from domain.model.user import DomainUser


def make_game(matrix=None):
    return DomainGame(
        uuid=uuid4(),
        board=DomainBoard(matrix or [[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
    )


def save_user(user_uuid):
    repository = UserRepositoryImpl(DatasourceUserMapper())
    repository.save(DomainUser(user_uuid, str(user_uuid), "password-hash"))


def test_save_and_get_game(clean_database):
    repository = GameRepositoryImpl(DatasourceGameMapper())
    game = make_game([[0, 1, 2], [0, 2, 1], [0, 1, 2]])
    repository.save(game)
    result = repository.get(game.uuid)
    assert result is not None
    assert isinstance(result, DomainGame)
    assert isinstance(result.board, DomainBoard)
    assert result.uuid == game.uuid
    assert result.board.matrix == game.board.matrix


def test_get_unknown_uuid_returns_none(clean_database):
    repository = GameRepositoryImpl(DatasourceGameMapper())
    assert repository.get(uuid4()) is None


def test_save_same_uuid_updates_board(clean_database):
    repository = GameRepositoryImpl(DatasourceGameMapper())
    game = make_game()
    repository.save(game)
    updated_matrix = [[1, 0, 0], [0, 2, 0], [0, 0, 0]]
    repository.save(DomainGame(game.uuid, DomainBoard(updated_matrix)))
    assert repository.get(game.uuid).board.matrix == updated_matrix


def test_loaded_game_has_independent_board(clean_database):
    repository = GameRepositoryImpl(DatasourceGameMapper())
    original_matrix = [[0, 1, 2], [0, 2, 1], [0, 1, 2]]
    game = make_game(original_matrix)
    repository.save(game)
    loaded = repository.get(game.uuid)
    loaded.board.matrix[0][0] = 2
    assert repository.get(game.uuid).board.matrix == original_matrix


def test_save_and_get_game_preserves_multiplayer_fields(clean_database):
    repository = GameRepositoryImpl(DatasourceGameMapper())
    first_player_uuid = uuid4()
    second_player_uuid = uuid4()
    save_user(first_player_uuid)
    save_user(second_player_uuid)
    game = DomainGame(
        uuid=uuid4(),
        board=DomainBoard([[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
        opponent_type=OpponentType.USER,
        state=GameState.PLAYER_TURN,
        first_player_uuid=first_player_uuid,
        second_player_uuid=second_player_uuid,
        current_player_uuid=first_player_uuid,
        first_player_mark=GameMark.X,
        second_player_mark=GameMark.O,
    )

    repository.save(game)
    result = repository.get(game.uuid)

    assert result == game


def test_save_existing_game_updates_state_and_winner(clean_database):
    repository = GameRepositoryImpl(DatasourceGameMapper())
    first_player_uuid = uuid4()
    second_player_uuid = uuid4()
    save_user(first_player_uuid)
    save_user(second_player_uuid)
    game = DomainGame(
        uuid=uuid4(),
        board=DomainBoard([[1, 1, 0], [2, 2, 0], [0, 0, 0]]),
        opponent_type=OpponentType.USER,
        state=GameState.PLAYER_TURN,
        first_player_uuid=first_player_uuid,
        second_player_uuid=second_player_uuid,
        current_player_uuid=first_player_uuid,
    )
    repository.save(game)

    game.board = DomainBoard([[1, 1, 1], [2, 2, 0], [0, 0, 0]])
    game.state = GameState.VICTORY
    game.current_player_uuid = None
    game.winner_uuid = first_player_uuid
    repository.save(game)

    result = repository.get(game.uuid)
    assert result == game


def test_get_available_returns_only_waiting_user_games(clean_database):
    repository = GameRepositoryImpl(DatasourceGameMapper())
    first_player_uuid = uuid4()
    save_user(first_player_uuid)
    available_game = DomainGame(
        uuid=uuid4(),
        board=DomainBoard([[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
        opponent_type=OpponentType.USER,
        state=GameState.WAITING_FOR_PLAYERS,
        first_player_uuid=first_player_uuid,
    )
    started_user_game = DomainGame(
        uuid=uuid4(),
        board=DomainBoard([[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
        opponent_type=OpponentType.USER,
        state=GameState.PLAYER_TURN,
        first_player_uuid=first_player_uuid,
        current_player_uuid=first_player_uuid,
    )
    computer_game = DomainGame(
        uuid=uuid4(),
        board=DomainBoard([[0, 0, 0], [0, 0, 0], [0, 0, 0]]),
        opponent_type=OpponentType.COMPUTER,
        state=GameState.PLAYER_TURN,
        first_player_uuid=first_player_uuid,
        current_player_uuid=first_player_uuid,
    )
    repository.save(available_game)
    repository.save(started_user_game)
    repository.save(computer_game)

    result = repository.get_available()

    assert result == [available_game]
