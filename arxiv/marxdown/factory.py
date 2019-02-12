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


def create_web_app(build_path: Optional[str] = None,
                   with_search: Optional[bool] = None,
                   extra_config: Optional[dict] = None) -> Flask:
    """Initialize an instance of the static pages application."""
    app = Flask('arxiv.marxdown')
    app.config.from_object(config)
    if build_path is None:
        build_path = app.config.get('BUILD_PATH', "./")
    if with_search is None:
        with_search = app.config.get('SITE_SEARCH_ENABLED', True)

    if extra_config is not None:
        app.config.update(extra_config)

    Base(app)

    app.register_blueprint(routes.docs)     # Provides base templates.

    with app.app_context():     # Need the app context for the config to stick.
        # We build the blueprint on the fly, so that we get dynamic routing
        # to content pages.
        app.register_blueprint(
            routes.get_blueprint(
                build_path,
                with_search=with_search
            )
        )
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['simepledate'] = simepledate
    app.jinja_env.filters['pretty_path'] = pretty_path
    s3.init_app(app)
    return app
