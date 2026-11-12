import base64
from unittest.mock import Mock
from uuid import uuid4

import pytest
from werkzeug.security import check_password_hash, generate_password_hash

from domain.exception.authorization_exception import (
    InvalidAuthorizationHeaderError,
    InvalidCredentialsError,
    InvalidLoginError,
    InvalidPasswordError,
)
from domain.model.sign_up_request import SignUpRequest
from domain.model.user import DomainUser
from domain.service.authorization_implementation_service import (
    AuthorizationServiceImpl,
)
from domain.service.user_interface_service import UserService


@pytest.fixture
def user_service():
    return Mock(spec=UserService)


@pytest.fixture
def service(user_service):
    return AuthorizationServiceImpl(user_service)


def basic_header(login, password):
    encoded = base64.b64encode(f"{login}:{password}".encode()).decode("ascii")
    return f"Basic {encoded}"


def test_register_hashes_password(service, user_service):
    assert service.register(SignUpRequest("alice", "secret-password")) is True
    _, kwargs = user_service.create_user.call_args
    assert kwargs["login"] == "alice"
    assert kwargs["password_hash"] != "secret-password"
    assert check_password_hash(kwargs["password_hash"], "secret-password")


@pytest.mark.parametrize("login", [None, "", "ab", " alice", "alice ", "a b"])
def test_register_rejects_invalid_login(service, user_service, login):
    with pytest.raises(InvalidLoginError):
        service.register(SignUpRequest(login, "secret-password"))
    user_service.create_user.assert_not_called()


@pytest.mark.parametrize("password", [None, "", "short", "        "])
def test_register_rejects_invalid_password(service, user_service, password):
    with pytest.raises(InvalidPasswordError):
        service.register(SignUpRequest("alice", password))
    user_service.create_user.assert_not_called()


def test_authorize_returns_user_uuid(service, user_service):
    user = DomainUser(
        uuid4(), "alice", generate_password_hash("secret-password")
    )
    user_service.get_by_login.return_value = user
    assert service.authorize(basic_header("alice", "secret-password")) == user.uuid


def test_authorize_accepts_colon_in_password(service, user_service):
    password = "secret:password"
    user = DomainUser(uuid4(), "alice", generate_password_hash(password))
    user_service.get_by_login.return_value = user
    assert service.authorize(basic_header("alice", password)) == user.uuid


@pytest.mark.parametrize(
    "header",
    [None, "", "Bearer token", "Basic", "Basic !!!", "Basic YWxpY2U="],
)
def test_authorize_rejects_invalid_header(service, header):
    with pytest.raises(InvalidAuthorizationHeaderError):
        service.authorize(header)


def test_authorize_hides_unknown_login(service, user_service):
    user_service.get_by_login.return_value = None
    with pytest.raises(InvalidCredentialsError):
        service.authorize(basic_header("unknown", "secret-password"))


def test_authorize_hides_wrong_password(service, user_service):
    user_service.get_by_login.return_value = DomainUser(
        uuid4(), "alice", generate_password_hash("correct-password")
    )
    with pytest.raises(InvalidCredentialsError):
        service.authorize(basic_header("alice", "wrong-password"))
