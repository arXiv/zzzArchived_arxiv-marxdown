"""Application factory for static site."""

import logging
from typing import Optional
from datetime import datetime
import dateutil.parser
from pytz import timezone

from flask import Flask, Config
from flask_s3 import FlaskS3
from arxiv.base import Base
from . import routes, config

s3 = FlaskS3()


def format_datetime(datestring: str) -> str:
    """Render a date like ``Friday, January 01, 2019 at 22:05 US/Eastern``."""
    dt = dateutil.parser.parse(datestring)
    dt = dt.replace(tzinfo=timezone('US/Eastern'))
    return dt.strftime("%A, %B %m, %Y at %H:%M US/Eastern")


def simpledate(datestring: str) -> str:
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


def create_web_app(build_path: Optional[str] = None,
                   with_search: Optional[bool] = None,
                   extra_config: Optional[dict] = None,
                   instance_path: Optional[str] = None,
                   static_url_path: Optional[str] = None) -> Flask:
    """Initialize an instance of the static pages application."""
    app = Flask('arxiv.marxdown',
                static_url_path=static_url_path,
                instance_path=instance_path,
                instance_relative_config=True)

    app.config.from_object(config)  # Default configuration.

    # If available, use an instance config from the instance folder. See
    # https://flask.palletsprojects.com/en/1.1.x/config/#instance-folders.
    # Config params here will override defaults.
    app.config.from_pyfile('application.cfg', silent=True)

    build_path = build_path or app.config.get('BUILD_PATH', "./")
    with_search = with_search or app.config.get('SITE_SEARCH_ENABLED', True)

    if extra_config is not None:
        app.config.update(extra_config)

    Base(app)

    with app.app_context():     # Need the app context for the config to stick.
        # Provides base templates.
        app.register_blueprint(routes.get_docs_blueprint(app))

        # We build the blueprint on the fly, so that we get dynamic routing
        # to content pages.
        app.register_blueprint(
            routes.get_blueprint(build_path, with_search=with_search)
        )

    app.jinja_env.filters['format_datetime'] = format_datetime  # pylint: disable=no-member
    app.jinja_env.filters['simpledate'] = simpledate  # pylint: disable=no-member
    app.jinja_env.filters['pretty_path'] = pretty_path  # pylint: disable=no-member

    s3.init_app(app)
    return app
