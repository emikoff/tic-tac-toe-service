from flask import Blueprint, jsonify

from web.mapper.user_mapper import WebUserMapper
from web.module.user_module import UserModule


def create_user_bp(user_module: UserModule) -> Blueprint:
    user_bp = Blueprint("user", __name__, url_prefix="/user")
    user_service = user_module.user_service
    user_authenticator = user_module.user_authenticator
    web_user_mapper = WebUserMapper()

    @user_bp.get("/<uuid:user_uuid>")
    @user_authenticator.required
    def get_user(user_uuid):
        domain_user = user_service.get_by_uuid(user_uuid)
        if domain_user is None:
            return jsonify({"error": "User not found"}), 404

        web_user = web_user_mapper.domain_to_web(domain_user)
        return jsonify(
            {
                "uuid": str(web_user.uuid),
                "login": web_user.login,
            }
        ), 200

    return user_bp
