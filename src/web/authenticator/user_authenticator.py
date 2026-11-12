from functools import wraps

from flask import g, jsonify, request

from domain.exception.authorization_exception import (
    InvalidAuthorizationHeaderError,
    InvalidCredentialsError,
)
from domain.service.authorization_interface_service import AuthorizationService


class UserAuthenticator:
    def __init__(self, authorization_service: AuthorizationService):
        self.authorization_service = authorization_service

    def required(self, endpoint):
        @wraps(endpoint)
        def wrapper(*args, **kwargs):
            authorization_header = request.headers.get("Authorization")

            try:
                user_uuid = self.authorization_service.authorize(
                    authorization_header
                )
            except (
                InvalidAuthorizationHeaderError,
                InvalidCredentialsError,
            ):
                response = jsonify({"error": "Unauthorized"})
                response.status_code = 401
                response.headers["WWW-Authenticate"] = (
                    'Basic realm="Tic-Tac-Toe"'
                )
                return response

            g.current_user_uuid = user_uuid
            return endpoint(*args, **kwargs)

        return wrapper
