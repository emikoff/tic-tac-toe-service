import base64
import binascii
import re
from uuid import UUID

from werkzeug.security import check_password_hash, generate_password_hash

from domain.exception.authorization_exception import (
    InvalidAuthorizationHeaderError,
    InvalidCredentialsError,
    InvalidLoginError,
    InvalidPasswordError,
)
from domain.model.sign_up_request import SignUpRequest
from domain.service.authorization_interface_service import AuthorizationService
from domain.service.user_interface_service import UserService


class AuthorizationServiceImpl(AuthorizationService):
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def register(self, request: SignUpRequest) -> bool:
        self._validate_login(request.login)
        self._validate_password(request.password)

        password_hash = generate_password_hash(request.password)
        self.user_service.create_user(
            login=request.login,
            password_hash=password_hash,
        )
        return True

    def authorize(self, authorization_header: str) -> UUID:
        login, password = self._decode_basic_auth(authorization_header)
        user = self.user_service.get_by_login(login)

        if user is None:
            raise InvalidCredentialsError()

        if not check_password_hash(user.password_hash, password):
            raise InvalidCredentialsError()

        return user.uuid

    def _validate_login(self, login: str) -> None:
        if not isinstance(login, str):
            raise InvalidLoginError()
        if len(login) < 3 or len(login) > 50:
            raise InvalidLoginError()
        if login != login.strip():
            raise InvalidLoginError()
        if re.fullmatch(r"[A-Za-z0-9_]+", login) is None:
            raise InvalidLoginError()

    def _validate_password(self, password: str) -> None:
        if not isinstance(password, str):
            raise InvalidPasswordError()
        if len(password) < 8 or len(password) > 128:
            raise InvalidPasswordError()
        if not password.strip():
            raise InvalidPasswordError()

    def _decode_basic_auth(self, authorization_header: str) -> tuple[str, str]:
        if not isinstance(authorization_header, str):
            raise InvalidAuthorizationHeaderError()

        parts = authorization_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "basic" or not parts[1]:
            raise InvalidAuthorizationHeaderError()

        try:
            decoded_bytes = base64.b64decode(parts[1], validate=True)
            decoded = decoded_bytes.decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            raise InvalidAuthorizationHeaderError()

        if ":" not in decoded:
            raise InvalidAuthorizationHeaderError()

        login, password = decoded.split(":", 1)
        if not login:
            raise InvalidAuthorizationHeaderError()

        return login, password
