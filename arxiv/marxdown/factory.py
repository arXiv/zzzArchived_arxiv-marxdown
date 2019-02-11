"""Application factory for static site."""

import logging

from datetime import datetime
import dateutil.parser
from pytz import timezone

from flask import Flask
from flask_s3 import FlaskS3
from arxiv.base import Base
from . import routes, config

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


def pretty_path(path: str) -> str:
    """Make a relative path fit for consumption."""
    if path.endswith('/index'):
        return path.rsplit('/index', 1)[0]
    elif path == 'index':
        return '/'
    return path


def create_web_app() -> Flask:
    """Initialize an instance of the static pages application."""
    app = Flask(config.SITE_NAME)
    app.config.from_object(config)

    Base(app)

    app.register_blueprint(routes.docs)     # Provides base templates.

    with app.app_context():     # Need the app context for the config to stick.
        # We build the blueprint on the fly, so that we get dynamic routing
        # to content pages.
        app.register_blueprint(
            routes.get_blueprint(
                app.config.get('BUILD_PATH', "./"),
                with_search=app.config.get('SITE_SEARCH_ENABLED', True)
            )
        )
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['simepledate'] = simepledate
    app.jinja_env.filters['pretty_path'] = pretty_path
    s3.init_app(app)
    return app
