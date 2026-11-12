from uuid import UUID
from threading import Lock
from copy import deepcopy

from datasource.model.game import Game


class Storage:
    def __init__(self) -> None:
        self.collection_games: dict[UUID, Game] = {}
        self.lock = Lock()

    def save(self, game: Game) -> None:
        with self.lock:
            self.collection_games[game.uuid] = deepcopy(game)

    def get(self, uuid: UUID) -> Game | None:
        with self.lock:
            return deepcopy(self.collection_games.get(uuid))
