from datasource.model.board import Board as DatasourceBoard
from domain.model.board import DomainBoard as DomainBoard


class DatasourceBoardMapper:
    def to_domain(self, ds_board: DatasourceBoard) -> DomainBoard:
        matrix = [[el for el in row] for row in ds_board.matrix]
        domain_board = DomainBoard(matrix)

        return domain_board

    def to_datasource(self, domain_board: DomainBoard) -> DatasourceBoard:
        matrix = [[el for el in row] for row in domain_board.matrix]
        ds_board = DatasourceBoard(matrix)

        return ds_board
