"""
Build a sitemap.

This script builds a conglomerate site-map from a set of marXdown sites. It
is assumed that these sites are under Git version control, and that the
person/process running this script has authorization to read from them.

This script reads from a config file that contains a set of site
specifications. Here is an example:

.. code-block:: json

   {
     "sites": [
       {
         "name": "help",
         "repo": "git@github.com:arXiv/arxiv-docs.git",
         "source_dir": "help",
         "source_ref": "develop",
         "human_name": "arXiv Help",
         "url_prefix": "/help"
       },
       {
         "name": "labs",
         "repo": "git@github.com:arXiv/arxiv-docs.git",
         "source_dir": "labs",
         "source_ref": "develop",
         "human_name": "arXiv Labs",
         "url_prefix": "",
         "server": "https://labs.arxiv.org"
       }
     ]
   }


Most of these keys correspond to variables used in the marXdown application:

``name``
    Sets the ``SITE_NAME`` used when building the marXdown site.
``repo``
    Full path to the Git repository containing the marXdown site.
``source_dir``
    Relative path within the Git repository, used to build the full
    ``SOURCE_PATH`` once the repo is cloned locally.
``human_name``
    Sets the ``SITE_HUMAN_NAME`` used when building the marXdown site, and
    is used as the title of the root of the site's tree if there is no
    root index page.
``url_prefix``
    Sets the ``SITE_URL_PREFIX`` used when building the marXdown site.
``server``
    Optional. The base URL (not including the ``url_prefix``) where the site
    is deployed in production. If provided, paths in the site's tree will be
    prefixed with this server address.


To build the sitemap:

.. code-block:: bash

   pipenv run python map.py -s /path/to/sites.json -o /path/to/map.json


``-s`` specifies the site spec file (above), and ``-o`` specifies the sitemap
output file that is used by the :mod:`sitemap` application to serve the
sitemap.

"""

import json
import re
import tempfile
import sys
import subprocess
import os

from mypy_extensions import TypedDict
from flask import Flask

from arxiv.base.globals import get_application_config
from arxiv.base import logging
from arxiv.util.serialize import ISO8601JSONEncoder

from arxiv.marxdown.factory import create_web_app
from arxiv.marxdown.services import site
from arxiv.marxdown import build
from arxiv.marxdown.domain import SiteTree, SiteTreePart

import click

logger = logging.getLogger(__name__)


@click.command()
@click.option('--spec-file', '-s', help="Path to the site spec file (json).")
@click.option('--out-file', '-o', help="Path to the write the sitemap (json)")
def create_site_map(spec_file: str, out_file: str) -> None:
    """Create a site map from a site spec (JSON)."""
    do_create_site_map(spec_file, out_file)


def do_create_site_map(spec_file: str, out_file: str) -> None:
    """Create a site map from a site spec (JSON)."""
    with open(spec_file) as f:
        specs = json.load(f)

    tree = {}
    working_path = tempfile.mkdtemp()   # Create a temporary working directory.

    # Validate ahead of time so we don't do costly things.
    for spec in specs['sites']:
        _validate_spec(spec)

    for spec in specs['sites']:
        # Retrieve source for site.
        repo_path = _retrieve_repository(working_path, spec)

        # Build the site.
        app = create_web_app(extra_config=_get_site_config(repo_path, spec))
        with app.app_context():
            build._build_site(False)
            subtree = site.get_tree()
            if "server" in spec:
                subtree = {
                    f"{spec['server']}{key}":
                        _paths_to_urls(spec["server"], part)
                    for key, part in subtree.items()
                }
            tree.update(subtree)

    # Write the tree to a JSON document. This is used to serve the sitemap.
    with open(out_file, 'w') as f:
        json.dump(tree, f, indent=2, cls=ISO8601JSONEncoder)


SiteSpec = TypedDict(
    'SiteSpec',
    {
        'name': str,
        'repo': str,
        'source_dir': str,
        'source_ref': str,
        'human_name': str,
        'url_prefix': str,
        'server': str
    }
)


def _validate_spec(spec: SiteSpec) -> None:
    """Check a :class:`.SiteSpec` for common problems."""
    if 'name' not in spec:
        raise ValueError('missing name')
    if re.search(r'[^a-zA-Z_]+', spec['name']):
        raise ValueError(f'{spec["name"]}: name must contain only [a-ZA-Z_]')
    if 'repo' not in spec:
        raise ValueError(f'{spec["name"]}: missing repo')
    if ':' not in spec['repo'] \
            or '.git' not in spec['repo'] \
            or 'git@' not in spec['repo']:
        raise ValueError(f'{spec["name"]}: that does not look like a git repo')
    if 'source_dir' not in spec:
        raise ValueError(f'{spec["name"]}: missing source_dir')
    if 'source_ref' not in spec:
        raise ValueError(f'{spec["name"]}: source_ref must be a tag or branch')
    if 'human_name' not in spec:
        raise ValueError(f'{spec["name"]}: missing human_name')
    if 'url_prefix' not in spec:
        raise ValueError(f'{spec["name"]}: missing url_prefix')
    if 'server' in spec and '://' not in spec['server']:
        raise ValueError(f'{spec["name"]}: server should have protocol')


def _retrieve_repository(working_path: str, spec: SiteSpec):
    """Clone a git repo if it doesn't already exist under ``working_path``."""
    repo_path = os.path.join(working_path, spec['name'])
    if not os.path.exists(repo_path):
        r = subprocess.run(
            f"git clone --branch {spec['source_ref']}"
            f" {spec['repo']} {repo_path}",
            cwd=working_path,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if r.returncode != 0:
            raise RuntimeError(
                f"Failed to clone {spec['repo']}: {r.stdout} // {r.stderr}"
            )
    return repo_path


def _get_site_config(repo_path: str, spec: SiteSpec) -> dict:
    """Configure marXdown from the site spec."""
    source_path = os.path.join(repo_path, spec['source_dir'])
    # if not os.path.exists(source_path):
    #     raise RuntimeError(f'{spec["name"]}: {spec["source_dir"]} does not'
    #                        f' exist in {spec["repo"]}')
    build_path = tempfile.mkdtemp()
    logger.debug('configure site with build path %s', build_path)
    config = {}
    config['SITE_NAME'] = spec['name']
    config['SITE_URL_PREFIX'] = spec['url_prefix']
    config['SOURCE_PATH'] = source_path
    config['SITE_HUMAN_NAME'] = spec['human_name']
    config['BUILD_PATH'] = build_path
    return config


def _paths_to_urls(server: str, tree_part: SiteTreePart) -> SiteTreePart:
    """Reformat paths in a :const:`SiteTreePart` using a ``server`` URL."""
    tree_part["path"] = f"{server}{tree_part['path']}"
    if "children" in tree_part:
        tree_part["children"] = {
            f"{server}{key}": _paths_to_urls(server, child)
            for key, child in tree_part["children"].items()
        }
    return tree_part


if __name__ == '__main__':
    create_site_map()
