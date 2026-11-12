from flask import Blueprint, g, jsonify, request

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
from domain.model.opponent_type import OpponentType
from web.mapper.board_mapper import WebBoardMapper
from web.model.board import WebBoard
from web.mapper.game_mapper import WebGameMapper
from web.module.game_module import GameModule

HTTP_STATUS_400 = {
    "INVALID_MOVE": "ERROR: INVALID MOVE",
}


def web_game_to_dict(web_game):
    def uuid_or_none(value):
        return str(value) if value is not None else None

    return {
        "uuid": str(web_game.uuid),
        "board": {"matrix": web_game.board.matrix},
        "opponent_type": web_game.opponent_type.value,
        "state": web_game.state.value,
        "first_player_uuid": uuid_or_none(web_game.first_player_uuid),
        "second_player_uuid": uuid_or_none(web_game.second_player_uuid),
        "current_player_uuid": uuid_or_none(web_game.current_player_uuid),
        "winner_uuid": uuid_or_none(web_game.winner_uuid),
        "first_player_mark": web_game.first_player_mark.value,
        "second_player_mark": web_game.second_player_mark.value,
    }


def create_game_bp(game_module: GameModule) -> Blueprint:
    game_bp = Blueprint("game", __name__, url_prefix="/game")

    game_manager = game_module.game_manager
    user_authenticator = game_module.user_authenticator
    web_game_mapper = WebGameMapper()
    web_board_mapper = WebBoardMapper()

    @game_bp.route("", methods=["POST"])
    @user_authenticator.required
    def create_game():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "Body must be a JSON object"}), 400
        if "opponent_type" not in data:
            return jsonify(
                {"error": "JSON object does not contain opponent_type"}
            ), 400

        try:
            opponent_type = OpponentType(data["opponent_type"])
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid opponent_type"}), 400

        domain_game = game_manager.new_game(
            g.current_user_uuid,
            opponent_type,
        )
        get_web_game = web_game_mapper.domain_to_web(domain_game)

        result = web_game_to_dict(get_web_game)
        result["game_status"] = "CREATED_NEW_GAME"

        return jsonify(result), 200

    @game_bp.get("")
    @user_authenticator.required
    def get_available_games():
        games = game_manager.get_available_games()
        result = [
            web_game_to_dict(web_game_mapper.domain_to_web(game))
            for game in games
        ]
        return jsonify({"games": result}), 200

    @game_bp.get("/<uuid:game_uuid>")
    @user_authenticator.required
    def get_game(game_uuid):
        try:
            game = game_manager.get_game(game_uuid)
        except GameNotFoundError:
            return jsonify({"error": "Game not found"}), 404

        web_game = web_game_mapper.domain_to_web(game)
        return jsonify(web_game_to_dict(web_game)), 200

    @game_bp.post("/<uuid:game_uuid>/join")
    @user_authenticator.required
    def join_game(game_uuid):
        try:
            game = game_manager.join_game(game_uuid, g.current_user_uuid)
        except GameNotFoundError:
            return jsonify({"error": "Game not found"}), 404
        except CannotJoinOwnGameError:
            return jsonify({"error": "Cannot join your own game"}), 409
        except GameNotAvailableError:
            return jsonify({"error": "Game is not available"}), 409

        web_game = web_game_mapper.domain_to_web(game)
        return jsonify(web_game_to_dict(web_game)), 200

    @game_bp.route("/<uuid:game_uuid>", methods=["POST"])
    @user_authenticator.required
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

        try:
            domain_game, game_status = game_manager.move_player(
                game_uuid,
                g.current_user_uuid,
                new_board,
            )
        except GameNotFoundError:
            return jsonify({"error": "Game not found"}), 404
        except NotGameParticipantError:
            return jsonify({"error": "User is not a game participant"}), 403
        except GameNotStartedError:
            return jsonify({"error": "Game has not started"}), 409
        except GameAlreadyFinishedError:
            return jsonify({"error": "Game is already finished"}), 409
        except NotPlayerTurnError:
            return jsonify({"error": "It is not your turn"}), 409
        except InvalidGameMoveError:
            return jsonify(
                {
                    "game_status": "INVALID_MOVE",
                    "error": HTTP_STATUS_400["INVALID_MOVE"],
                }
            ), 400

        web_game = web_game_mapper.domain_to_web(domain_game)
        result = web_game_to_dict(web_game)
        result["game_status"] = game_status.name
        return jsonify(result), 200

    return game_bp
