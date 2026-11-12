import base64

import pytest

from app import create_app
from di.container import Container
from web.module.game_module import GameModule


@pytest.fixture
def auth_client(clean_database):
    container = Container()
    application = create_app(
        GameModule(container.game_manager, container.user_authenticator),
        container.authorization_module,
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": "postgresql+psycopg://games_user:postgres_password@127.0.0.1:25432/games_test"},
        container.user_module,
    )
    with application.test_client() as client:
        yield client


def basic_header(login, password):
    encoded = base64.b64encode(f"{login}:{password}".encode()).decode("ascii")
    return {"Authorization": f"Basic {encoded}"}


def test_signup_and_login(auth_client):
    signup = auth_client.post(
        "/auth/signup",
        json={"login": "alice", "password": "secret-password"},
    )
    login = auth_client.post(
        "/auth/login",
        headers=basic_header("alice", "secret-password"),
    )
    assert signup.status_code == 201
    assert signup.get_json() == {"success": True}
    assert login.status_code == 200
    assert "user_uuid" in login.get_json()


def test_signup_rejects_duplicate_login(auth_client):
    payload = {"login": "alice", "password": "secret-password"}
    assert auth_client.post("/auth/signup", json=payload).status_code == 201
    response = auth_client.post("/auth/signup", json=payload)
    assert response.status_code == 409
    assert response.get_json() == {"error": "Login already exists"}


@pytest.mark.parametrize(
    "payload, expected_error",
    [
        (None, "Invalid request body"),
        ({}, "Invalid request body"),
        ({"login": "alice"}, "Invalid request body"),
        ({"password": "secret-password"}, "Invalid request body"),
        ({"login": "ab", "password": "secret-password"}, "Invalid login"),
        ({"login": "alice", "password": "short"}, "Invalid password"),
    ],
)
def test_signup_validates_request(auth_client, payload, expected_error):
    response = auth_client.post("/auth/signup", json=payload)
    assert response.status_code == 400
    assert response.get_json() == {"error": expected_error}


@pytest.mark.parametrize(
    "headers",
    [{}, {"Authorization": "Bearer token"}, {"Authorization": "Basic !!!"}],
)
def test_login_rejects_invalid_header(auth_client, headers):
    response = auth_client.post("/auth/login", headers=headers)
    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}
    assert response.headers["WWW-Authenticate"] == 'Basic realm="Tic-Tac-Toe"'


def test_login_rejects_wrong_credentials(auth_client):
    auth_client.post(
        "/auth/signup",
        json={"login": "alice", "password": "secret-password"},
    )
    response = auth_client.post(
        "/auth/login", headers=basic_header("alice", "wrong-password")
    )
    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}
