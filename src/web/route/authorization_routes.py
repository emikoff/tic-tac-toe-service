from flask import Blueprint, jsonify, request

from domain.exception.authorization_exception import (
    InvalidAuthorizationHeaderError,
    InvalidCredentialsError,
    InvalidLoginError,
    InvalidPasswordError,
)
from domain.exception.user_exception import UserAlreadyExistsError
from domain.model.sign_up_request import SignUpRequest
from web.module.authorization_module import AuthorizationModule


def create_authorization_bp(authorization_module: AuthorizationModule) -> Blueprint:
    authorization_bp = Blueprint("authorization", __name__, url_prefix="/auth")
    authorization_service = authorization_module.authorization_service

    @authorization_bp.post("/signup")
    def signup_user():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "Invalid request body"}), 400
        if "login" not in data or "password" not in data:
            return jsonify({"error": "Invalid request body"}), 400

        sign_up_request = SignUpRequest(
            login=data["login"],
            password=data["password"],
        )

        try:
            authorization_service.register(sign_up_request)
        except InvalidLoginError:
            return jsonify({"error": "Invalid login"}), 400
        except InvalidPasswordError:
            return jsonify({"error": "Invalid password"}), 400
        except UserAlreadyExistsError:
            return jsonify({"error": "Login already exists"}), 409

        return jsonify({"success": True}), 201

    @authorization_bp.post("/login")
    def login_user():
        authorization_header = request.headers.get("Authorization")

        try:
            user_uuid = authorization_service.authorize(authorization_header)
        except (InvalidAuthorizationHeaderError, InvalidCredentialsError):
            response = jsonify({"error": "Unauthorized"})
            response.status_code = 401
            response.headers["WWW-Authenticate"] = 'Basic realm="Tic-Tac-Toe"'
            return response

        return jsonify({"user_uuid": str(user_uuid)}), 200

    return authorization_bp
