from flask import Flask
from web.route.game_routes import create_game_bp
from web.route.ui_routes import create_ui_bp
from di.container import Container
from web.module.game_module import GameModule


def create_app(game_module: GameModule):

    app = Flask(__name__, static_folder=None)

    app.register_blueprint(create_game_bp(game_module))
    app.register_blueprint(create_ui_bp())

    return app


container = Container()
game_module = GameModule(container.game_manager)

app = create_app(game_module)

if __name__ == "__main__":
    app.run(debug=True)
