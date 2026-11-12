from domain.service.user_interface_service import UserService
from web.authenticator.user_authenticator import UserAuthenticator


class UserModule:
    def __init__(
        self,
        user_service: UserService,
        user_authenticator: UserAuthenticator,
    ) -> None:
        self.user_service = user_service
        self.user_authenticator = user_authenticator
