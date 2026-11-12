class AuthorizationError(Exception):
    pass


class InvalidLoginError(AuthorizationError):
    pass


class InvalidPasswordError(AuthorizationError):
    pass


class InvalidAuthorizationHeaderError(AuthorizationError):
    pass


class InvalidCredentialsError(AuthorizationError):
    pass
