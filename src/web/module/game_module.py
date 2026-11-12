from domain.service.game_implementation_service import GameServiceImpl


class GameModule:
    def __init__(self, game_manager: GameServiceImpl) -> None:
        self.game_manager = game_manager
