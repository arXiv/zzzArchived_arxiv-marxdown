"""Application factory for static site."""

import logging

from flask import Flask
from flask_s3 import FlaskS3
from arxiv.base import Base
from . import routes

s3 = FlaskS3()


def create_web_app() -> Flask:
    """Initialize an instance of the static pages application."""
    from . import config

    app = Flask(__name__)
    app.config.from_object(config)

    Base(app)

    app.register_blueprint(routes.docs)     # Provides base templates.
    app.register_blueprint(
        routes.get_blueprint(
            app.config.get('BUILD_PATH', "./"),
            with_search=app.config.get('SITE_SEARCH_ENABLED', True)
        )
    )
    s3.init_app(app)
    return app
