from domain.service.authorization_interface_service import AuthorizationService


class AuthorizationModule:
    def __init__(self, authorization_service: AuthorizationService):
        self.authorization_service = authorization_service
