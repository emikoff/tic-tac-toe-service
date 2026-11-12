from domain.service.game_implementation_service import GameServiceImpl
from web.authenticator.user_authenticator import UserAuthenticator


class GameModule:
    def __init__(
        self,
        game_manager: GameServiceImpl,
        user_authenticator: UserAuthenticator,
    ) -> None:
        self.game_manager = game_manager
        self.user_authenticator = user_authenticator
