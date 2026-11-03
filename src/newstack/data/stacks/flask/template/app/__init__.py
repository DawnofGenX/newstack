"""{{ title }} — {{ description }}"""

from __future__ import annotations

from flask import Flask


def create_app() -> Flask:
    """Build the application. A factory keeps tests isolated from each other."""
    app = Flask(__name__)
    from .routes import bp

    app.register_blueprint(bp)
    return app
