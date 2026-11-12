from flask import Blueprint, render_template


def create_ui_bp() -> Blueprint:
    ui_bp = Blueprint(
        "ui",
        __name__,
        template_folder="../templates",
        static_folder="../static",
        static_url_path="/static",
    )

    @ui_bp.get("/")
    def game_page():
        return render_template("game.html")

    return ui_bp
