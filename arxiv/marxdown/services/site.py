"""Provides an interface to the built site at runtime."""

from typing import Iterable, Tuple, Dict

import os
import json

from arxiv.base.globals import get_application_config as config
from arxiv.util.serialize import ISO8601JSONEncoder
from arxiv.base import logging
from ..domain import Page, SiteTree

logger = logging.getLogger(__name__)


class PageNotFound(Exception):
    """A non-existant page was requested."""


def create_all(site_path: str) -> None:
    """Create all build paths required for the site."""
    for path in [get_static_path(), get_data_path(), get_pages_path(),
                 get_templates_path()]:
        if not os.path.exists(path):
            os.makedirs(path)


def walk() -> Iterable[Tuple[str, str, dict]]:
    """
    Walk the site tree.

    Returns
    -------
    generator
        Yields the parent, path, and metadata of each page.

    """
    prefix = get_url_prefix()
    for parent, dirs, files in os.walk(get_pages_path()):
        for fname in files:
            child = fname.rsplit('.j2', 1)[0]
            rel_parent = parent.split(get_pages_path().rstrip("/"), 1)[1]
            this_parent = str(rel_parent)
            if not this_parent.startswith("/"):
                this_parent = "/" + this_parent

            # /foo/bar, index -> /foo, bar
            if child == "index":
                this_parent, child = this_parent.rsplit('/', 1)
            if not this_parent.startswith("/"):
                this_parent = "/" + this_parent

            if this_parent == "/":  # Avoid a double slash.
                pattern = prefix.rstrip("/") + "/" + child
            else:
                pattern = prefix.rstrip("/") + this_parent + "/" + child

            # load_metadata needs actual file name (e.g. 'index')
            path = (rel_parent + "/" + fname.rsplit('.j2', 1)[0]).lstrip("/")
            this_parent = prefix + this_parent
            yield this_parent, pattern.rstrip("/"), load_metadata(path)


def get_tree() -> SiteTree:
    """
    Get the site tree.

    Returns
    -------
    dict

    """
    prefix = get_url_prefix()
    if not prefix.startswith("/"):
        prefix = "/" + prefix
    tree = {
        prefix: {
            "children": {},
            "title": get_site_human_name(),
            "path": prefix
        }
    }

    def _get_subpaths(parent: str) -> Iterable[str]:
        parent_parts = [prefix] \
            + parent.split(prefix, 1)[1].strip("/").split("/")
        subpaths = set()
        subpath = ""
        for part in parent_parts:
            subpath = subpath.rstrip("/") + "/" + part.strip("/")
            if len(subpath) > 1 and subpath.endswith("/"):
                subpath = subpath[:-1]
            subpaths.add(subpath)
        return sorted(subpaths, key=len)

    for parent, pattern, metadata in walk():
        if 'response' in metadata:
            if metadata['response'].get('deleted'):
                continue
            elif int(metadata['response'].get('status', 200)) > 299:
                continue
        subtree = tree[prefix]
        for subpath in _get_subpaths(parent):
            if subpath != subtree['path']:
                if subpath not in subtree['children']:
                    subtree['children'][subpath] = {
                        'children': {},
                        'path': subpath
                    }
                subtree = subtree['children'][subpath]
        if pattern == subtree['path']:
            subtree.update({
                'title': metadata['title'],
                'modified': metadata['modified']
            })
        elif pattern in subtree['children']:
            subtree['children'][pattern].update({
                'title': metadata['title'],
                'modified': metadata['modified'],
                'path': pattern
            })
        else:
            subtree['children'][pattern] = {
                'title': metadata['title'],
                'path': pattern,
                'modified': metadata['modified'],
                'children': {}
            }
    return tree


def get_static_path() -> str:
    """Get the absolute path for the site static directory."""
    build_path = config().get('BUILD_PATH', './')
    logger.debug('get static path with build path %s, site name %s',
                 build_path, get_site_name())
    return os.path.abspath(os.path.join(build_path, 'static', get_site_name()))


def get_site_name() -> str:
    """Get the name of this site."""
    return config().get('SITE_NAME', 'arxiv')


def get_url_prefix() -> str:
    """Get the URL prefix for this site."""
    return config().get('SITE_URL_PREFIX', '/')


def get_site_human_name() -> str:
    """Get the human name for this site."""
    return config().get('SITE_HUMAN_NAME', 'arXiv static pages')


def get_site_human_short_name() -> str:
    """Get the human short name for this site."""
    return config().get('SITE_HUMAN_SHORT_NAME', 'Static')


def get_data_path() -> str:
    """Get the absolute path for the site data directory."""
    return os.path.abspath(
        os.path.join(config().get('BUILD_PATH', './'), 'data'))


def get_templates_path() -> str:
    """Get the absolute path for the site templates directory."""
    return os.path.abspath(
        os.path.join(config().get('BUILD_PATH', './'), 'templates'))


def get_pages_path() -> str:
    """Get the absolute path for the site pages directory."""
    return os.path.abspath(
        os.path.join(config().get('BUILD_PATH', './'), 'pages'))


def get_page_filename(page_path: str) -> str:
    """Generate a filename for a rendered page."""
    return f'{page_path}.j2'


def get_path_for_page(page_path: str) -> str:
    """Generate an absolute path for a rendered page."""
    return os.path.join(get_pages_path(), get_page_filename(page_path))


def get_path_for_static(static_path: str) -> str:
    return os.path.join(get_static_path(), static_path)


def get_path_for_template(template_path: str) -> str:
    return os.path.join(get_templates_path(), template_path)


def get_path_for_data(page_path: str) -> str:
    return os.path.join(get_data_path(), f'{page_path}.json')


def store_metadata(page_path: str, data: dict) -> None:
    parent_dir, _ = os.path.split(get_path_for_data(page_path))
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
    with open(get_path_for_data(page_path), 'w') as f:
        json.dump(data, f, cls=ISO8601JSONEncoder)


def store_page_content(page_path: str, content: str) -> None:
    parent_dir, _ = os.path.split(get_path_for_page(page_path))
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
    with open(get_path_for_page(page_path), 'w') as f:
        f.write(content)


def load_page_content(page_path: str) -> str:
    if get_pages_path() not in os.path.normpath(get_path_for_page(page_path)):
        raise PageNotFound(f'Page {page_path} not found')

    with open(get_path_for_page(page_path), 'rb') as f:
        return f.read().decode('utf-8')


def load_metadata(page_path: str) -> dict:
    if not os.path.exists(get_path_for_data(page_path)):
        return {}
    with open(get_path_for_data(page_path), 'r') as f:
        return json.load(f)


def load_page(page_path: str) -> Page:
    if not os.path.exists(get_path_for_page(page_path)):
        index_path = os.path.join(page_path, 'index')
        if os.path.exists(get_path_for_page(index_path)):
            page_path = index_path
        else:
            raise PageNotFound(f'Page {page_path} not found')
    return Page(
        page_path=page_path,
        content=load_page_content(page_path),
        metadata=load_metadata(page_path)
    )
