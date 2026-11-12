from uuid import UUID, uuid4

import pytest

from app import create_app
from di.container import Container
from domain.model.board import DomainBoard
from domain.model.game import DomainGame
from web.module.game_module import GameModule


@pytest.fixture
def http_client():
    container = Container()
    application = create_app(GameModule(container.game_manager))
    application.config.update(TESTING=True)

    with application.test_client() as client:
        yield client, container


def create_game(client):
    response = client.post("/game")

    assert response.status_code == 200
    assert response.is_json

    return response.get_json()


def test_game_page_contains_ui_and_static_assets(http_client):
    client, _ = http_client

    response = client.get("/")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Крестики-нолики" in page
    assert "Вы —" in page
    assert "Компьютер —" in page
    assert 'id="board"' in page
    assert page.count('class="cell"') == 9
    assert 'id="new-game"' in page
    assert "/static/style.css" in page
    assert "/static/game.js" in page

    css_response = client.get("/static/style.css")
    js_response = client.get("/static/game.js")

    assert css_response.status_code == 200
    assert css_response.mimetype == "text/css"
    assert js_response.status_code == 200
    assert js_response.mimetype == "text/javascript"


def test_create_game_returns_and_saves_empty_game(http_client):
    client, container = http_client

    response_data = create_game(client)
    game_uuid = UUID(response_data["uuid"])

    assert response_data == {
        "uuid": str(game_uuid),
        "board": {"matrix": [[0, 0, 0], [0, 0, 0], [0, 0, 0]]},
        "game_status": "CREATED_NEW_GAME",
    }
    assert container.game_repository.get(game_uuid) is not None


def test_player_move_returns_computer_move(http_client):
    client, _ = http_client
    game = create_game(client)
    player_board = [[1, 0, 0], [0, 0, 0], [0, 0, 0]]

    response = client.post(
        f"/game/{game['uuid']}",
        json={"matrix": player_board},
    )
    response_data = response.get_json()
    result_matrix = response_data["board"]["matrix"]

    assert response.status_code == 200
    assert response_data["uuid"] == game["uuid"]
    assert response_data["game_status"] == "GAME_CONTINUES"
    assert sum(row.count(1) for row in result_matrix) == 1
    assert sum(row.count(2) for row in result_matrix) == 1
    assert result_matrix[0][0] == 1


def test_games_have_independent_state(http_client):
    client, container = http_client
    first_game = create_game(client)
    second_game = create_game(client)

    client.post(
        f"/game/{first_game['uuid']}",
        json={"matrix": [[1, 0, 0], [0, 0, 0], [0, 0, 0]]},
    )

    stored_second_game = container.game_repository.get(UUID(second_game["uuid"]))

    assert first_game["uuid"] != second_game["uuid"]
    assert stored_second_game.board.matrix == [[0, 0, 0], [0, 0, 0], [0, 0, 0]]


def test_unknown_game_returns_descriptive_error(http_client):
    client, _ = http_client

    response = client.post(
        f"/game/{uuid4()}",
        json={"matrix": [[1, 0, 0], [0, 0, 0], [0, 0, 0]]},
    )

    assert response.status_code == 400
    assert response.get_json() == {
        "game_status": "GAME_NOT_FOUND",
        "error": "ERROR: GAME NOT FOUND",
    }


def test_invalid_move_returns_descriptive_error(http_client):
    client, _ = http_client
    game = create_game(client)

    response = client.post(
        f"/game/{game['uuid']}",
        json={"matrix": [[0, 0, 0], [0, 0, 0], [0, 0, 0]]},
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
    http_client,
    request_kwargs,
    expected_error,
):
    client, _ = http_client

    response = client.post(f"/game/{uuid4()}", **request_kwargs)

    assert response.status_code == 400
    assert response.is_json
    assert response.get_json() == {"error": expected_error}


def test_invalid_uuid_in_url_returns_404(http_client):
    client, _ = http_client

    response = client.post(
        "/game/not-a-uuid",
        json={"matrix": [[1, 0, 0], [0, 0, 0], [0, 0, 0]]},
    )

    assert response.status_code == 404


def test_winning_player_move_returns_user_won(http_client):
    client, container = http_client
    game_uuid = uuid4()
    container.game_repository.save(
        DomainGame(
            game_uuid,
            DomainBoard([[1, 1, 0], [2, 2, 0], [0, 0, 0]]),
        )
    )

    response = client.post(
        f"/game/{game_uuid}",
        json={"matrix": [[1, 1, 1], [2, 2, 0], [0, 0, 0]]},
    )

    assert response.status_code == 200
    assert response.get_json()["game_status"] == "USER_WON"


def test_move_in_finished_game_must_match_saved_board(http_client):
    client, container = http_client
    game_uuid = uuid4()
    finished_matrix = [[1, 1, 1], [2, 2, 0], [0, 0, 0]]
    container.game_repository.save(
        DomainGame(game_uuid, DomainBoard(finished_matrix))
    )

    same_board_response = client.post(
        f"/game/{game_uuid}",
        json={"matrix": finished_matrix},
    )
    changed_board_response = client.post(
        f"/game/{game_uuid}",
        json={"matrix": [[1, 1, 1], [2, 0, 0], [0, 0, 0]]},
    )

    assert same_board_response.status_code == 200
    assert same_board_response.get_json()["game_status"] == "USER_WON"
    assert changed_board_response.status_code == 400
    assert changed_board_response.get_json()["game_status"] == "INVALID_MOVE"
