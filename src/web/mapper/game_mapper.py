from web.model.game import WebGame
from domain.model.game import DomainGame

from web.mapper.board_mapper import WebBoardMapper


class WebGameMapper:
    def web_to_domain(self, web_game: WebGame) -> DomainGame:
        board_mapper = WebBoardMapper()
        domain_board = board_mapper.to_domain(web_game.board)

        domain_game = DomainGame(
            uuid=web_game.uuid,
            board=domain_board,
            opponent_type=web_game.opponent_type,
            state=web_game.state,
            first_player_uuid=web_game.first_player_uuid,
            second_player_uuid=web_game.second_player_uuid,
            current_player_uuid=web_game.current_player_uuid,
            winner_uuid=web_game.winner_uuid,
            first_player_mark=web_game.first_player_mark,
            second_player_mark=web_game.second_player_mark,
        )

        return domain_game

    def domain_to_web(self, domain_game: DomainGame) -> WebGame:
        board_mapper = WebBoardMapper()
        web_board = board_mapper.to_web(domain_game.board)

        web_game = WebGame(
            uuid=domain_game.uuid,
            board=web_board,
            opponent_type=domain_game.opponent_type,
            state=domain_game.state,
            first_player_uuid=domain_game.first_player_uuid,
            second_player_uuid=domain_game.second_player_uuid,
            current_player_uuid=domain_game.current_player_uuid,
            winner_uuid=domain_game.winner_uuid,
            first_player_mark=domain_game.first_player_mark,
            second_player_mark=domain_game.second_player_mark,
        )

        return web_game
