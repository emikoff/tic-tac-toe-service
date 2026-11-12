from web.model.game import WebGame
from domain.model.game import DomainGame

from web.mapper.board_mapper import WebBoardMapper


class WebGameMapper:
    def to_domain(self, web_game: WebGame) -> DomainGame:
        board_mapper = WebBoardMapper()
        domain_board = board_mapper.to_domain(web_game.board)
        domain_game = DomainGame(web_game.uuid, domain_board)

        return domain_game

    def to_web(self, domain_game: DomainGame) -> WebGame:
        board_mapper = WebBoardMapper()
        web_board = board_mapper.to_web(domain_game.board)
        web_game = WebGame(domain_game.uuid, web_board)

        return web_game
