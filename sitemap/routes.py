"""Provides the main routes for the application."""

from typing import Dict, Callable
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from werkzeug.urls import Href, url_encode, url_parse, url_unparse, url_encode

from flask import Blueprint, render_template_string, request, \
    render_template, Response, current_app, url_for
import jinja2
from werkzeug.exceptions import NotFound

from arxiv import status

from . import serialize
from . import sitemap


blueprint = Blueprint('sitemap', __name__, url_prefix='')


@blueprint.route('/sitemap_index.xml', methods=['GET'])
def get_xml_sitemap() -> Response:
    return Response(
        serialize.sitemap_xml(sitemap.load_urlset(request.url_root)),
        content_type="application/xml"
    )


@blueprint.route('/sitemap.html', methods=['GET'])
def get_html_sitemap() -> Response:
    return render_template(
        "sitemap/sitemap.html",
        urlset=sitemap.load_urlset(request.url_root)
    )
