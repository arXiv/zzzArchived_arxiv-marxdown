"""Application factory for static site."""

import logging

from datetime import datetime
import dateutil.parser
from pytz import timezone

from flask import Flask
from flask_s3 import FlaskS3
from arxiv.base import Base
from . import routes

s3 = FlaskS3()


def format_datetime(datestring: str) -> str:
    """Render a date like ``Friday, January 01, 2019 at 22:05 US/Eastern``."""
    dt = dateutil.parser.parse(datestring)
    dt = dt.replace(tzinfo=timezone('US/Eastern'))
    return dt.strftime("%A, %B %m, %Y at %H:%M US/Eastern")


def simepledate(datestring: str) -> str:
    """Render a date like ``1992-05-02``."""
    dt = dateutil.parser.parse(datestring)
    return dt.strftime("%Y-%m-%d")


def create_web_app() -> Flask:
    """Initialize an instance of the static pages application."""
    from . import config

    app = Flask(config.SITE_NAME)
    app.config.from_object(config)

    Base(app)

    app.register_blueprint(routes.docs)     # Provides base templates.
    app.register_blueprint(
        routes.get_blueprint(
            app.config.get('BUILD_PATH', "./"),
            with_search=app.config.get('SITE_SEARCH_ENABLED', True)
        )
    )
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['simepledate'] = simepledate
    s3.init_app(app)
    return app
