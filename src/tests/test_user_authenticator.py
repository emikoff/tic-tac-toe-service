from unittest.mock import Mock
from uuid import uuid4

import pytest
from flask import Flask, g

from domain.exception.authorization_exception import (
    InvalidAuthorizationHeaderError,
    InvalidCredentialsError,
)
from domain.service.authorization_interface_service import AuthorizationService
from web.authenticator.user_authenticator import UserAuthenticator


@pytest.fixture
def authorization_service():
    return Mock(spec=AuthorizationService)


@pytest.fixture
def endpoint_action():
    return Mock()


@pytest.fixture
def application(authorization_service, endpoint_action):
    app = Flask(__name__)
    app.config["TESTING"] = True

    authenticator = UserAuthenticator(authorization_service)

    @app.get("/protected")
    @authenticator.required
    def protected():
        endpoint_action(g.current_user_uuid)
        return {"success": True}, 200

    @app.get("/current-user")
    @authenticator.required
    def current_user():
        return {"user_uuid": str(g.current_user_uuid)}, 200

    @app.get("/resource/<resource_id>")
    @authenticator.required
    def resource(resource_id):
        return {"resource_id": resource_id}, 200

    return app


def test_missing_authorization_header_returns_401(
    authorization_service,
    application,
):
    authorization_service.authorize.side_effect = (
        InvalidAuthorizationHeaderError()
    )

    with application.test_client() as client:
        response = client.get("/protected")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}
    assert response.headers["WWW-Authenticate"] == 'Basic realm="Tic-Tac-Toe"'
    authorization_service.authorize.assert_called_once_with(None)


def test_invalid_credentials_return_401(
    authorization_service,
    application,
):
    authorization_service.authorize.side_effect = InvalidCredentialsError()

    with application.test_client() as client:
        response = client.get(
            "/protected",
            headers={"Authorization": "Basic invalid-data"},
        )

    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}
    assert response.headers["WWW-Authenticate"] == 'Basic realm="Tic-Tac-Toe"'
    authorization_service.authorize.assert_called_once_with("Basic invalid-data")


def test_endpoint_is_not_called_when_authentication_fails(
    authorization_service,
    application,
    endpoint_action,
):
    authorization_service.authorize.side_effect = InvalidCredentialsError()

    with application.test_client() as client:
        response = client.get(
            "/protected",
            headers={"Authorization": "Basic invalid-data"},
        )

    assert response.status_code == 401
    endpoint_action.assert_not_called()


def test_valid_credentials_execute_endpoint(
    authorization_service,
    application,
    endpoint_action,
):
    user_uuid = uuid4()
    authorization_service.authorize.return_value = user_uuid

    with application.test_client() as client:
        response = client.get(
            "/protected",
            headers={"Authorization": "Basic valid-data"},
        )

    assert response.status_code == 200
    assert response.get_json() == {"success": True}
    authorization_service.authorize.assert_called_once_with("Basic valid-data")
    endpoint_action.assert_called_once_with(user_uuid)


def test_authenticated_user_uuid_is_stored_in_g(
    authorization_service,
    application,
):
    user_uuid = uuid4()
    authorization_service.authorize.return_value = user_uuid

    with application.test_client() as client:
        response = client.get(
            "/current-user",
            headers={"Authorization": "Basic valid-data"},
        )

    assert response.status_code == 200
    assert response.get_json() == {"user_uuid": str(user_uuid)}


def test_decorator_passes_route_arguments(
    authorization_service,
    application,
):
    authorization_service.authorize.return_value = uuid4()

    with application.test_client() as client:
        response = client.get(
            "/resource/test-id",
            headers={"Authorization": "Basic valid-data"},
        )

    assert response.status_code == 200
    assert response.get_json() == {"resource_id": "test-id"}
