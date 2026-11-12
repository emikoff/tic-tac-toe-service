from web.model.board import WebBoard
from domain.model.board import DomainBoard


class WebBoardMapper:
    def to_domain(self, web_board: WebBoard) -> DomainBoard:
        matrix = [[el for el in row] for row in web_board.matrix]
        domain_board = DomainBoard(matrix)

        return domain_board

    def to_web(self, domain_board: DomainBoard) -> WebBoard:
        matrix = [[el for el in row] for row in domain_board.matrix]
        web_board = WebBoard(matrix)

        return web_board
