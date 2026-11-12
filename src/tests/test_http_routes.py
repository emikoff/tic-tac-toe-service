import base64
from uuid import UUID, uuid4

import pytest

from app import create_app
from di.container import Container
from domain.model.board import DomainBoard
from domain.model.game_state import GameState
from web.module.game_module import GameModule


@pytest.fixture
def http_client(clean_database):
    container = Container()
    application = create_app(
        GameModule(container.game_manager, container.user_authenticator),
        container.authorization_module,
        user_module=container.user_module,
    )
    application.config.update(TESTING=True)

    with application.test_client() as client:
        yield client, container


def basic_header(login, password):
    credentials = base64.b64encode(
        f"{login}:{password}".encode()
    ).decode("ascii")
    return {"Authorization": f"Basic {credentials}"}


def register_user(client, login, password="secret-password"):
    response = client.post(
        "/auth/signup",
        json={"login": login, "password": password},
    )
    assert response.status_code == 201
    return basic_header(login, password)


@pytest.fixture
def authorized_http_client(http_client):
    client, container = http_client
    login = "alice"
    password = "secret-password"

    headers = register_user(client, login, password)

    yield client, container, headers


def create_game(client, headers, opponent_type="COMPUTER"):
    response = client.post(
        "/game",
        json={"opponent_type": opponent_type},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.is_json

    return response.get_json()


def test_game_page_is_public_and_contains_auth_form(http_client):
    client, _ = http_client

    response = client.get("/")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'id="auth-form"' in page
    assert 'data-auth-mode="login"' in page
    assert 'data-auth-mode="signup"' in page


def test_get_user_without_authorization_returns_401(authorized_http_client):
    client, _, headers = authorized_http_client
    user_uuid = client.post("/auth/login", headers=headers).get_json()["user_uuid"]

    response = client.get(f"/user/{user_uuid}")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_get_user_returns_uuid_and_login_without_password_hash(
    authorized_http_client,
):
    client, _, headers = authorized_http_client
    user_uuid = client.post("/auth/login", headers=headers).get_json()["user_uuid"]

    response = client.get(f"/user/{user_uuid}", headers=headers)

    assert response.status_code == 200
    assert response.get_json() == {
        "uuid": user_uuid,
        "login": "alice",
    }
    assert "password_hash" not in response.get_json()


def test_get_unknown_user_returns_404(authorized_http_client):
    client, _, headers = authorized_http_client

    response = client.get(f"/user/{uuid4()}", headers=headers)

    assert response.status_code == 404
    assert response.get_json() == {"error": "User not found"}


def test_game_page_contains_ui_and_static_assets(authorized_http_client):
    client, _, headers = authorized_http_client

    response = client.get("/", headers=headers)
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Крестики-нолики" in page
    assert "Вы —" in page
    assert "Компьютер —" in page
    assert 'id="board"' in page
    assert page.count('class="cell"') == 9
    assert 'id="new-game"' in page
    assert 'id="available-games"' in page
    assert 'value="COMPUTER"' in page
    assert 'value="USER"' in page
    assert "/static/style.css" in page
    assert "/static/game.js" in page

    css_response = client.get("/static/style.css")
    js_response = client.get("/static/game.js")

    assert css_response.status_code == 200
    assert css_response.mimetype == "text/css"
    assert js_response.status_code == 200
    assert js_response.mimetype == "text/javascript"


def test_create_game_without_authorization_returns_401(http_client):
    client, _ = http_client

    response = client.post("/game")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}
    assert response.headers["WWW-Authenticate"] == 'Basic realm="Tic-Tac-Toe"'


def test_create_game_with_wrong_password_returns_401(http_client):
    client, _ = http_client
    client.post(
        "/auth/signup",
        json={"login": "alice", "password": "secret-password"},
    )

    response = client.post(
        "/game",
        headers=basic_header("alice", "wrong-password"),
    )

    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_create_game_returns_and_saves_empty_game(authorized_http_client):
    client, container, headers = authorized_http_client

    response_data = create_game(client, headers)
    game_uuid = UUID(response_data["uuid"])
    first_player_uuid = UUID(response_data["first_player_uuid"])

    assert response_data == {
        "uuid": str(game_uuid),
        "board": {"matrix": [[0, 0, 0], [0, 0, 0], [0, 0, 0]]},
        "opponent_type": "COMPUTER",
        "state": "PLAYER_TURN",
        "first_player_uuid": str(first_player_uuid),
        "second_player_uuid": None,
        "current_player_uuid": str(first_player_uuid),
        "winner_uuid": None,
        "first_player_mark": "X",
        "second_player_mark": "O",
        "game_status": "CREATED_NEW_GAME",
    }
    stored_game = container.game_repository.get(game_uuid)
    assert stored_game is not None
    assert stored_game.first_player_uuid == first_player_uuid


def test_create_game_with_user_waits_for_second_player(authorized_http_client):
    client, container, headers = authorized_http_client

    response_data = create_game(client, headers, "USER")
    game_uuid = UUID(response_data["uuid"])
    first_player_uuid = UUID(response_data["first_player_uuid"])

    assert response_data["opponent_type"] == "USER"
    assert response_data["state"] == "WAITING_FOR_PLAYERS"
    assert response_data["current_player_uuid"] is None
    assert response_data["second_player_uuid"] is None
    stored_game = container.game_repository.get(game_uuid)
    assert stored_game.first_player_uuid == first_player_uuid
    assert stored_game.state.value == "WAITING_FOR_PLAYERS"


@pytest.mark.parametrize(
    ("request_kwargs", "expected_error"),
    [
        ({}, "Body must be a JSON object"),
        ({"json": []}, "Body must be a JSON object"),
        ({"json": {}}, "JSON object does not contain opponent_type"),
        ({"json": {"opponent_type": "ROBOT"}}, "Invalid opponent_type"),
        ({"json": {"opponent_type": None}}, "Invalid opponent_type"),
    ],
)
def test_create_game_validates_opponent_type(
    authorized_http_client,
    request_kwargs,
    expected_error,
):
    client, _, headers = authorized_http_client

    response = client.post("/game", headers=headers, **request_kwargs)

    assert response.status_code == 400
    assert response.get_json() == {"error": expected_error}


def test_get_available_games_without_authorization_returns_401(http_client):
    client, _ = http_client

    response = client.get("/game")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_get_available_games_returns_only_waiting_user_games(
    authorized_http_client,
):
    client, _, headers = authorized_http_client
    available_game = create_game(client, headers, "USER")
    create_game(client, headers, "COMPUTER")
    expected_game = {
        key: value
        for key, value in available_game.items()
        if key != "game_status"
    }

    response = client.get("/game", headers=headers)

    assert response.status_code == 200
    assert response.get_json() == {"games": [expected_game]}


def test_get_game_without_authorization_returns_401(authorized_http_client):
    client, _, headers = authorized_http_client
    game = create_game(client, headers)

    response = client.get(f"/game/{game['uuid']}")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_get_unknown_game_returns_404(authorized_http_client):
    client, _, headers = authorized_http_client

    response = client.get(f"/game/{uuid4()}", headers=headers)

    assert response.status_code == 404
    assert response.get_json() == {"error": "Game not found"}


def test_both_players_receive_same_current_game(authorized_http_client):
    client, _, first_player_headers = authorized_http_client
    second_player_headers = register_user(client, "bob")
    game = create_game(client, first_player_headers, "USER")
    join_response = client.post(
        f"/game/{game['uuid']}/join",
        headers=second_player_headers,
    )
    expected_game = join_response.get_json()

    first_player_response = client.get(
        f"/game/{game['uuid']}",
        headers=first_player_headers,
    )
    second_player_response = client.get(
        f"/game/{game['uuid']}",
        headers=second_player_headers,
    )

    assert first_player_response.status_code == 200
    assert second_player_response.status_code == 200
    assert first_player_response.get_json() == expected_game
    assert second_player_response.get_json() == expected_game


def test_join_game_without_authorization_returns_401(authorized_http_client):
    client, _, first_player_headers = authorized_http_client
    game = create_game(client, first_player_headers, "USER")

    response = client.post(f"/game/{game['uuid']}/join")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_second_user_can_join_waiting_game(authorized_http_client):
    client, container, first_player_headers = authorized_http_client
    second_player_headers = register_user(client, "bob")
    game = create_game(client, first_player_headers, "USER")

    response = client.post(
        f"/game/{game['uuid']}/join",
        headers=second_player_headers,
    )
    response_data = response.get_json()

    assert response.status_code == 200
    assert response_data["state"] == "PLAYER_TURN"
    assert response_data["second_player_uuid"] is not None
    assert response_data["current_player_uuid"] == game["first_player_uuid"]
    stored_game = container.game_repository.get(UUID(game["uuid"]))
    assert str(stored_game.second_player_uuid) == response_data["second_player_uuid"]


def test_first_user_cannot_join_own_game(authorized_http_client):
    client, _, first_player_headers = authorized_http_client
    game = create_game(client, first_player_headers, "USER")

    response = client.post(
        f"/game/{game['uuid']}/join",
        headers=first_player_headers,
    )

    assert response.status_code == 409
    assert response.get_json() == {"error": "Cannot join your own game"}


def test_join_unknown_game_returns_404(authorized_http_client):
    client, _, first_player_headers = authorized_http_client

    response = client.post(
        f"/game/{uuid4()}/join",
        headers=first_player_headers,
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Game not found"}


def test_third_user_cannot_join_started_game(authorized_http_client):
    client, _, first_player_headers = authorized_http_client
    second_player_headers = register_user(client, "bob")
    third_player_headers = register_user(client, "charlie")
    game = create_game(client, first_player_headers, "USER")
    client.post(
        f"/game/{game['uuid']}/join",
        headers=second_player_headers,
    )

    response = client.post(
        f"/game/{game['uuid']}/join",
        headers=third_player_headers,
    )

    assert response.status_code == 409
    assert response.get_json() == {"error": "Game is not available"}


def test_player_move_without_authorization_returns_401(authorized_http_client):
    client, _, headers = authorized_http_client
    game = create_game(client, headers)

    response = client.post(
        f"/game/{game['uuid']}",
        json={"matrix": [[1, 0, 0], [0, 0, 0], [0, 0, 0]]},
    )

    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_player_move_returns_computer_move(authorized_http_client):
    client, _, headers = authorized_http_client
    game = create_game(client, headers)
    player_board = [[1, 0, 0], [0, 0, 0], [0, 0, 0]]

    response = client.post(
        f"/game/{game['uuid']}",
        json={"matrix": player_board},
        headers=headers,
    )
    response_data = response.get_json()
    result_matrix = response_data["board"]["matrix"]

    assert response.status_code == 200
    assert response_data["uuid"] == game["uuid"]
    assert response_data["game_status"] == "GAME_CONTINUES"
    assert sum(row.count(1) for row in result_matrix) == 1
    assert sum(row.count(2) for row in result_matrix) == 1
    assert result_matrix[0][0] == 1


def test_games_have_independent_state(authorized_http_client):
    client, container, headers = authorized_http_client
    first_game = create_game(client, headers)
    second_game = create_game(client, headers)

    client.post(
        f"/game/{first_game['uuid']}",
        json={"matrix": [[1, 0, 0], [0, 0, 0], [0, 0, 0]]},
        headers=headers,
    )

    stored_second_game = container.game_repository.get(UUID(second_game["uuid"]))

    assert first_game["uuid"] != second_game["uuid"]
    assert stored_second_game.board.matrix == [[0, 0, 0], [0, 0, 0], [0, 0, 0]]


def test_unknown_game_returns_descriptive_error(authorized_http_client):
    client, _, headers = authorized_http_client

    response = client.post(
        f"/game/{uuid4()}",
        json={"matrix": [[1, 0, 0], [0, 0, 0], [0, 0, 0]]},
        headers=headers,
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Game not found"}


def test_invalid_move_returns_descriptive_error(authorized_http_client):
    client, _, headers = authorized_http_client
    game = create_game(client, headers)

    response = client.post(
        f"/game/{game['uuid']}",
        json={"matrix": [[0, 0, 0], [0, 0, 0], [0, 0, 0]]},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "game_status": "INVALID_MOVE",
        "error": "ERROR: INVALID MOVE",
    }


@pytest.mark.parametrize(
    ("request_kwargs", "expected_error"),
    [
        ({"data": "not json"}, "Body must be a JSON object"),
        ({"json": []}, "Body must be a JSON object"),
        ({"json": {}}, "JSON object does not contain matrix"),
        ({"json": {"matrix": "invalid"}}, "The matrix field must be a list"),
        ({"json": {"matrix": []}}, "Matrix has the wrong structure"),
        (
            {"json": {"matrix": [[0, 0, 0], [0, 0], [0, 0, 0]]}},
            "Matrix has the wrong structure",
        ),
        (
            {"json": {"matrix": [[0, 0, 0], [0, 3, 0], [0, 0, 0]]}},
            "Matrix has the wrong structure",
        ),
        (
            {"json": {"matrix": [[0, 0, 0], [0, True, 0], [0, 0, 0]]}},
            "Matrix has the wrong structure",
        ),
    ],
)
def test_invalid_request_body_returns_json_error(
    authorized_http_client,
    request_kwargs,
    expected_error,
):
    client, _, headers = authorized_http_client

    response = client.post(
        f"/game/{uuid4()}",
        headers=headers,
        **request_kwargs,
    )

    assert response.status_code == 400
    assert response.is_json
    assert response.get_json() == {"error": expected_error}


def test_invalid_uuid_in_url_returns_404(authorized_http_client):
    client, _, headers = authorized_http_client

    response = client.post(
        "/game/not-a-uuid",
        json={"matrix": [[1, 0, 0], [0, 0, 0], [0, 0, 0]]},
        headers=headers,
    )

    assert response.status_code == 404


def test_winning_player_move_returns_user_won(authorized_http_client):
    client, container, headers = authorized_http_client
    game = create_game(client, headers)
    game_uuid = UUID(game["uuid"])
    stored_game = container.game_repository.get(game_uuid)
    stored_game.board = DomainBoard([[1, 1, 0], [2, 2, 0], [0, 0, 0]])
    container.game_repository.save(stored_game)

    response = client.post(
        f"/game/{game_uuid}",
        json={"matrix": [[1, 1, 1], [2, 2, 0], [0, 0, 0]]},
        headers=headers,
    )

    assert response.status_code == 200
    response_data = response.get_json()
    assert response_data["game_status"] == "USER_WON"
    assert response_data["state"] == "VICTORY"
    assert response_data["winner_uuid"] == game["first_player_uuid"]
    assert response_data["current_player_uuid"] is None


def test_move_in_finished_game_returns_conflict(authorized_http_client):
    client, container, headers = authorized_http_client
    game = create_game(client, headers)
    game_uuid = UUID(game["uuid"])
    finished_matrix = [[1, 1, 1], [2, 2, 0], [0, 0, 0]]
    stored_game = container.game_repository.get(game_uuid)
    stored_game.board = DomainBoard(finished_matrix)
    stored_game.state = GameState.VICTORY
    stored_game.current_player_uuid = None
    stored_game.winner_uuid = stored_game.first_player_uuid
    container.game_repository.save(stored_game)

    same_board_response = client.post(
        f"/game/{game_uuid}",
        json={"matrix": finished_matrix},
        headers=headers,
    )
    changed_board_response = client.post(
        f"/game/{game_uuid}",
        json={"matrix": [[1, 1, 1], [2, 0, 0], [0, 0, 0]]},
        headers=headers,
    )

    assert same_board_response.status_code == 409
    assert same_board_response.get_json() == {"error": "Game is already finished"}
    assert changed_board_response.status_code == 409
    assert changed_board_response.get_json() == {
        "error": "Game is already finished"
    }


def test_user_game_switches_turn_between_players(authorized_http_client):
    client, _, first_player_headers = authorized_http_client
    second_player_headers = register_user(client, "bob")
    game = create_game(client, first_player_headers, "USER")
    joined_game = client.post(
        f"/game/{game['uuid']}/join",
        headers=second_player_headers,
    ).get_json()

    first_move_response = client.post(
        f"/game/{game['uuid']}",
        json={"matrix": [[1, 0, 0], [0, 0, 0], [0, 0, 0]]},
        headers=first_player_headers,
    )
    first_move = first_move_response.get_json()

    assert first_move_response.status_code == 200
    assert first_move["current_player_uuid"] == joined_game["second_player_uuid"]
    assert first_move["board"]["matrix"] == [
        [1, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]

    second_move_response = client.post(
        f"/game/{game['uuid']}",
        json={"matrix": [[1, 2, 0], [0, 0, 0], [0, 0, 0]]},
        headers=second_player_headers,
    )
    second_move = second_move_response.get_json()

    assert second_move_response.status_code == 200
    assert second_move["current_player_uuid"] == game["first_player_uuid"]
    assert second_move["board"]["matrix"] == [
        [1, 2, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]


def test_user_cannot_move_twice_in_a_row(authorized_http_client):
    client, _, first_player_headers = authorized_http_client
    second_player_headers = register_user(client, "bob")
    game = create_game(client, first_player_headers, "USER")
    client.post(
        f"/game/{game['uuid']}/join",
        headers=second_player_headers,
    )
    client.post(
        f"/game/{game['uuid']}",
        json={"matrix": [[1, 0, 0], [0, 0, 0], [0, 0, 0]]},
        headers=first_player_headers,
    )

    response = client.post(
        f"/game/{game['uuid']}",
        json={"matrix": [[1, 0, 0], [0, 1, 0], [0, 0, 0]]},
        headers=first_player_headers,
    )

    assert response.status_code == 409
    assert response.get_json() == {"error": "It is not your turn"}


def test_user_outside_game_cannot_move(authorized_http_client):
    client, _, first_player_headers = authorized_http_client
    outsider_headers = register_user(client, "bob")
    game = create_game(client, first_player_headers)

    response = client.post(
        f"/game/{game['uuid']}",
        json={"matrix": [[1, 0, 0], [0, 0, 0], [0, 0, 0]]},
        headers=outsider_headers,
    )

    assert response.status_code == 403
    assert response.get_json() == {"error": "User is not a game participant"}


def test_user_cannot_move_while_game_waits_for_opponent(
    authorized_http_client,
):
    client, _, first_player_headers = authorized_http_client
    game = create_game(client, first_player_headers, "USER")

    response = client.post(
        f"/game/{game['uuid']}",
        json={"matrix": [[1, 0, 0], [0, 0, 0], [0, 0, 0]]},
        headers=first_player_headers,
    )

    assert response.status_code == 409
    assert response.get_json() == {"error": "Game has not started"}
