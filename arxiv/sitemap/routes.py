"""Provides the main routes for the application."""

from typing import Dict, Callable

from flask import Blueprint, request, render_template, Response, current_app
import jinja2
from werkzeug.exceptions import NotFound

from arxiv import status

from . import serialize
from . import load


blueprint = Blueprint('sitemap', __name__, url_prefix='',
                      template_folder='templates')


@blueprint.route('/sitemap_index.xml', methods=['GET'])
def get_xml_sitemap() -> Response:
    """Get a machine-readable XML sitemap."""
    urlset_path = current_app.config['URLSET_PATH']
    urlset = load.load_urlset(request.url_root, urlset_path)
    return Response(serialize.sitemap_xml(urlset),
                    content_type="application/xml")


@blueprint.route('/sitemap.html', methods=['GET'])
def get_html_sitemap() -> Response:
    """Get a human-readable HTML sitemap."""
    urlset_path = current_app.config['URLSET_PATH']
    return render_template(
        "sitemap/sitemap.html",
        urlset=load.load_urlset(request.url_root, urlset_path)
    )
