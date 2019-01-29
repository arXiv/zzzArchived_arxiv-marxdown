"""Provides the main routes for the application."""

from typing import Dict, Callable
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from werkzeug.urls import Href, url_encode, url_parse, url_unparse, url_encode

from flask import Blueprint, request, render_template, Response, current_app
import jinja2
from werkzeug.exceptions import NotFound

from arxiv import status

from . import serialize
from . import sitemap


blueprint = Blueprint('sitemap', __name__, url_prefix='')


@blueprint.route('/sitemap_index.xml', methods=['GET'])
def get_xml_sitemap() -> Response:
    urlset_path = current_app.config['URLSET_PATH']
    urlset = sitemap.load_urlset(request.url_root, urlset_path)
    return Response(
        serialize.sitemap_xml(urlset),
        content_type="application/xml"
    )


@blueprint.route('/sitemap.html', methods=['GET'])
def get_html_sitemap() -> Response:
    return render_template(
        "sitemap/sitemap.html",
        urlset=sitemap.load_urlset(request.url_root)
    )
