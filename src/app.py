import os
from flask import Flask
from dotenv import load_dotenv

from web.route.game_routes import create_game_bp
from web.route.authorization_routes import create_authorization_bp
from web.route.ui_routes import create_ui_bp
from web.route.user_routes import create_user_bp
from di.container import Container
from web.module.game_module import GameModule
from web.module.authorization_module import AuthorizationModule
from web.module.user_module import UserModule
from datasource.database import db


def create_app(
    game_module: GameModule,
    authorization_module: AuthorizationModule | None = None,
    test_config=None,
    user_module: UserModule | None = None,
):

    app = Flask(__name__, static_folder=None)

    if test_config is not None:
        app.config.update(test_config)
    else:
        database_url = os.getenv("DATABASE_URL")
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url

    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.register_blueprint(create_game_bp(game_module))
    if authorization_module is not None:
        app.register_blueprint(create_authorization_bp(authorization_module))
    if user_module is not None:
        app.register_blueprint(create_user_bp(user_module))
    app.register_blueprint(create_ui_bp())

    return app


load_dotenv()
container = Container()
game_module = GameModule(
    container.game_manager,
    container.user_authenticator,
)

app = create_app(
    game_module,
    container.authorization_module,
    user_module=container.user_module,
)


if __name__ == "__main__":
    app.run(debug=True)
