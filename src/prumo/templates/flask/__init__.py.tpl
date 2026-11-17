"""Flask application factory."""

from flask import Flask

from app.routes import pages


def create_app() -> Flask:
    """Create the server-side web application."""
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.register_blueprint(pages)
    return app
