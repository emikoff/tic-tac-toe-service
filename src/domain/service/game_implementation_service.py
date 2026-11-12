from copy import deepcopy
from uuid import UUID, uuid4

from domain.service.game_interface_service import GameService
from domain.exception.game_exception import (
    CannotJoinOwnGameError,
    GameAlreadyFinishedError,
    GameNotAvailableError,
    GameNotFoundError,
    GameNotStartedError,
    InvalidGameMoveError,
    NotGameParticipantError,
    NotPlayerTurnError,
)
from domain.model.board import DomainBoard
from domain.model.game import DomainGame
from domain.model.game_mark import GameMark
from domain.model.game_state import GameState
from domain.model.opponent_type import OpponentType
from datasource.repository.game_repository import GameRepository
from domain.model.game_status import GameStatus


class GameServiceImpl(GameService):
    def __init__(self, game_repository: GameRepository) -> None:
        self.game_repository = game_repository
        self.x = 1
        self.o = 2
        self.user_mark = self.x
        self.comp_mark = self.o

    def whose_move(self, matrix: list[list[int]]) -> int | None:
        cnt_x = 0
        cnt_o = 0

        for i in range(len(matrix)):
            for j in range(len(matrix[i])):
                if matrix[i][j] == self.x:
                    cnt_x += 1
                elif matrix[i][j] == self.o:
                    cnt_o += 1

        diff = cnt_x - cnt_o
        if diff == 0:
            return self.x
        elif diff == 1:
            return self.o
        return None

    def board_validate(self, old_board: DomainBoard, new_board: DomainBoard) -> bool:
        len_new_board = len(new_board.matrix)
        len_old_board = len(old_board.matrix)
        target_cnt = 1
        cnt = 0
        cnt_x = 0
        cnt_o = 0
        new_val = 0

        if len_old_board != len_new_board:
            return False

        for i in range(len_old_board):
            if len(new_board.matrix[i]) != len(old_board.matrix[i]):
                return False

            for j in range(len(old_board.matrix[i])):
                if new_board.matrix[i][j] not in (0, 1, 2):
                    return False

                if old_board.matrix[i][j] == self.x:
                    cnt_x += 1
                elif old_board.matrix[i][j] == self.o:
                    cnt_o += 1

                if old_board.matrix[i][j] == 0 and new_board.matrix[i][j] != 0:
                    cnt += 1
                    new_val = new_board.matrix[i][j]
                    if cnt > target_cnt:
                        return False

                if (
                    old_board.matrix[i][j] != 0
                    and old_board.matrix[i][j] != new_board.matrix[i][j]
                ):
                    return False

        if cnt != target_cnt:
            return False

        diff = cnt_x - cnt_o
        if diff not in (0, 1):
            return False
        if diff == 0 and new_val != self.x:
            return False
        elif diff == 1 and new_val != self.o:
            return False

        return True

    def check_end_game_and_winner(self, matrix: list[list[int]]) -> tuple[bool, int]:

        def check_win(matrix: list[list[int]]) -> tuple[bool, int]:
            for row in matrix:
                if (row[0] != 0) and all(el == row[0] for el in row):
                    return True, row[0]
            return False, 0

        def check_end(matrix: list[list[int]]) -> tuple[bool, int]:
            cnt_0 = 0
            for row in matrix:
                if 0 in row:
                    cnt_0 += 1
            if cnt_0 == 0:
                return True, 0

            return False, 0

        end, winner = check_win(matrix)
        if end:
            return True, winner

        rotate_matrix = [[] for _ in range(len(matrix))]
        diagonals = [[], []]

        len_matrix = len(matrix)

        for i in range(len_matrix):
            len_row_matrix = len(matrix[i])

            for j in range(len_row_matrix):
                rotate_matrix[j].append(matrix[i][j])

            r = len_row_matrix - i - 1
            diagonals[0].append(matrix[i][i])
            diagonals[1].append(matrix[i][r])

        end, winner = check_win(rotate_matrix)
        if end:
            return True, winner

        end, winner = check_win(diagonals)
        if end:
            return True, winner

        end, winner = check_end(matrix)
        if end:
            return True, winner

        return False, winner

    def next_move(self, board: DomainBoard, player: int = 2) -> DomainBoard:
        old_matrix = board.matrix
        best_move_index = []
        best_move_price = -2

        new_matrix = [
            [old_matrix[i][j] for j in range(len(old_matrix[i]))]
            for i in range(len(old_matrix))
        ]

        for i in range(len(old_matrix)):
            for j in range(len(old_matrix[i])):
                if new_matrix[i][j] == 0:
                    new_matrix[i][j] = player
                    if player == self.comp_mark:
                        next_player = self.user_mark
                    else:
                        next_player = self.comp_mark
                    move_price = self._minimax(new_matrix, next_player)
                    new_matrix[i][j] = 0

                    if move_price > best_move_price:
                        best_move_index = [i, j]
                        best_move_price = move_price

        i, j = best_move_index
        new_matrix[i][j] = player
        board.matrix = new_matrix

        return board

    def _minimax(self, matrix: list[list[int]], player: int = 1) -> int:
        def end_move(winner: int) -> int:
            if winner == self.comp_mark:
                return 1
            elif winner == self.user_mark:
                return -1
            return 0

        its_end, winner = self.check_end_game_and_winner(matrix)
        if its_end:
            return end_move(winner)

        var_move = []

        for i in range(len(matrix)):
            for j in range(len(matrix[i])):
                if matrix[i][j] == 0:
                    matrix[i][j] = player
                    its_end, winner = self.check_end_game_and_winner(matrix)

                    if its_end:
                        var_move.append(end_move(winner))
                    else:
                        if player == self.comp_mark:
                            next_player = self.user_mark
                        else:
                            next_player = self.comp_mark
                        var_move.append(self._minimax(matrix, next_player))

                    matrix[i][j] = 0

        if player == self.comp_mark:
            return max(var_move)
        return min(var_move)

    def _update_finished_state(self, game: DomainGame) -> GameStatus | None:
        is_finished, winner = self.check_end_game_and_winner(game.board.matrix)
        if not is_finished:
            return None

        game.current_player_uuid = None
        if winner == 0:
            game.state = GameState.DRAW
            game.winner_uuid = None
            return GameStatus.DRAW

        game.state = GameState.VICTORY
        if winner == self.x:
            game.winner_uuid = game.first_player_uuid
            return GameStatus.USER_WON

        game.winner_uuid = game.second_player_uuid
        if game.opponent_type == OpponentType.COMPUTER:
            return GameStatus.COMPUTER_WON
        return GameStatus.USER_WON

    def move_player(
        self,
        game_uuid: UUID,
        user_uuid: UUID,
        new_board: DomainBoard,
    ) -> tuple[DomainGame, GameStatus]:
        game = self.game_repository.get(game_uuid)
        if game is None:
            raise GameNotFoundError

        participants = {game.first_player_uuid, game.second_player_uuid}
        if user_uuid not in participants:
            raise NotGameParticipantError
        if game.state == GameState.WAITING_FOR_PLAYERS:
            raise GameNotStartedError
        if game.state in (GameState.DRAW, GameState.VICTORY):
            raise GameAlreadyFinishedError
        if game.current_player_uuid != user_uuid:
            raise NotPlayerTurnError
        if not self.board_validate(game.board, new_board):
            raise InvalidGameMoveError

        game.board = new_board
        game_status = self._update_finished_state(game)
        if game_status is not None:
            self.game_repository.save(game)
            return game, game_status

        if game.opponent_type == OpponentType.USER:
            if user_uuid == game.first_player_uuid:
                game.current_player_uuid = game.second_player_uuid
            else:
                game.current_player_uuid = game.first_player_uuid
        else:
            game.board = self.next_move(deepcopy(game.board), self.comp_mark)
            game_status = self._update_finished_state(game)
            if game_status is not None:
                self.game_repository.save(game)
                return game, game_status
            game.current_player_uuid = game.first_player_uuid

        self.game_repository.save(game)
        return game, GameStatus.GAME_CONTINUES

    def new_game(
        self,
        first_player_uuid: UUID | None = None,
        opponent_type: OpponentType = OpponentType.COMPUTER,
    ) -> DomainGame:
        game_uuid = uuid4()

        matrix = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]

        if opponent_type == OpponentType.USER:
            state = GameState.WAITING_FOR_PLAYERS
            current_player_uuid = None
        else:
            state = GameState.PLAYER_TURN
            current_player_uuid = first_player_uuid

        domain_board = DomainBoard(matrix)
        domain_game = DomainGame(
            uuid=game_uuid,
            board=domain_board,
            opponent_type=opponent_type,
            state=state,
            first_player_uuid=first_player_uuid,
            second_player_uuid=None,
            current_player_uuid=current_player_uuid,
            winner_uuid=None,
            first_player_mark=GameMark.X,
            second_player_mark=GameMark.O,
        )

        self.game_repository.save(domain_game)

        return domain_game

    def get_available_games(self) -> list[DomainGame]:
        return self.game_repository.get_available()

    def get_game(self, game_uuid: UUID) -> DomainGame:
        game = self.game_repository.get(game_uuid)
        if game is None:
            raise GameNotFoundError
        return game

    def join_game(self, game_uuid: UUID, user_uuid: UUID) -> DomainGame:
        game = self.game_repository.get(game_uuid)
        if game is None:
            raise GameNotFoundError
        if game.first_player_uuid == user_uuid:
            raise CannotJoinOwnGameError
        if (
            game.opponent_type != OpponentType.USER
            or game.state != GameState.WAITING_FOR_PLAYERS
            or game.second_player_uuid is not None
        ):
            raise GameNotAvailableError

        game.second_player_uuid = user_uuid
        game.state = GameState.PLAYER_TURN
        game.current_player_uuid = game.first_player_uuid
        self.game_repository.save(game)
        return game
