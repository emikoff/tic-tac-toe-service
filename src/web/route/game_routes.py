from flask import Blueprint, jsonify, request

from web.mapper.board_mapper import WebBoardMapper
from web.model.board import WebBoard
from web.mapper.game_mapper import WebGameMapper
from web.module.game_module import GameModule

HTTP_STATUS_200 = {
    "DRAW": "Игра закончилась: Нечья",
    "USER_WON": "Игра закончилась: Победил игрок",
    "COMPUTER_WON": "Игра закончилась: Победил компьютер",
    "GAME_CONTINUES": "Игра продолжается",
}
HTTP_STATUS_400 = {
    "GAME_NOT_FOUND": "ERROR: GAME NOT FOUND",
    "INVALID_MOVE": "ERROR: INVALID MOVE",
}
HTTP_STATUS_500 = {
    "INTERNAL_ERROR": "INTERNAL ERROR",
    "INVALID_WINNER": "INVALID WINNER",
}


def create_game_bp(game_module: GameModule) -> Blueprint:
    game_bp = Blueprint("game", __name__, url_prefix="/game")

    game_manager = game_module.game_manager
    web_game_mapper = WebGameMapper()
    web_board_mapper = WebBoardMapper()

    @game_bp.route("", methods=["POST"])
    def create_game():
        get_web_game = web_game_mapper.to_web(game_manager.new_game())

        result = {
            "uuid": str(get_web_game.uuid),
            "board": {"matrix": get_web_game.board.matrix},
            "game_status": "CREATED_NEW_GAME",
        }

        return jsonify(result), 200

    @game_bp.route("/<uuid:game_uuid>", methods=["POST"])
    def move_user(game_uuid):
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({"error": "Body must be a JSON object"}), 400

        if "matrix" not in data:
            return jsonify({"error": "JSON object does not contain matrix"}), 400

        if not isinstance(data["matrix"], list):
            return jsonify({"error": "The matrix field must be a list"}), 400

        if len(data["matrix"]) != 3:
            return jsonify({"error": "Matrix has the wrong structure"}), 400

        for row in data["matrix"]:
            if (
                not isinstance(row, list)
                or len(row) != 3
                or not all(type(el) == int and 0 <= el <= 2 for el in row)
            ):
                return jsonify({"error": "Matrix has the wrong structure"}), 400

        new_board = web_board_mapper.to_domain(WebBoard(data["matrix"]))

        domain_game, game_status = game_manager.move_player(game_uuid, new_board)

        if domain_game is not None and game_status.name in HTTP_STATUS_200:
            http_status = 200
            web_game = web_game_mapper.to_web(domain_game)
            result = {
                "uuid": str(web_game.uuid),
                "board": {"matrix": web_game.board.matrix},
                "game_status": str(game_status.name),
            }
        elif game_status.name in HTTP_STATUS_400:
            http_status = 400
            result = {
                "game_status": str(game_status.name),
                "error": HTTP_STATUS_400[game_status.name],
            }
        elif game_status.name in HTTP_STATUS_500:
            http_status = 500
            result = {
                "game_status": str(game_status.name),
                "error": HTTP_STATUS_500[game_status.name],
            }
        else:
            http_status = 500
            result = {
                "game_status": "Unknown game status",
                "error": "Unknown ERROR",
            }

        return jsonify(result), http_status

    return game_bp
