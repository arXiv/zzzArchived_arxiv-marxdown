# arXiv marXdown

This project implements a markdown-driven static site for arXiv static pages.

## Overview

The arXiv-marXdown application builds and serves static pages from markdown
sources. In order to provide portability, and to integrate with Flask's URL
building and other goodies, this occurs in two steps:

1. Build: convert markdown source into Jinja2 template fragments ahead of time.
   Optionally, build a file-based index of the site for searching.
2. Serve: serve the site from the Jinja2 template fragments, rendering HTML on
   the fly.

## Site structure

Each site should be contained in a single directory. For example:

```
mysite/
├── index.md
├── specifics/
|   ├── impressive.png
|   └── coolstory.md
└── _templates
    └── mysite
        └── custom.html
```

Custom templates go in ``_templates/<SITE NAME>``.

### Pages

The directory structure in the site directory determines the site map. A
file at ``foo/baz/bat.md`` will be served at
``https://some.site/foo/baz/bat``. But note that the file
``foo/baz/index.md`` will be served at ``https://some.site/foo/baz``.

Everything is relative. You can add a link in ``foo/baz/index.md``
like ``[click here for cool](bat)``, and the link will be rendered as
``https://some.site/foo/baz/bat``.

You can put static files in the same directory structure. If the page
``specifics/coolstory.md`` has an image tag like
``![my alt text](impressive.png)``, this will get rendered as
``https://some.site/specifics/impressive.png``. In other words, it will just
work.

Only ``.md`` (markdown) files will be treated like pages. Everything else is
general static content and won't get rendered like a page (fancy headers,
etc).

Inside of your ``.md`` files, you can add some front-matter. For example,
if you want the title in the browser tab and breadcrumbs to be different from
whatever is in the content of the page, you could do:

```markdown
---
title: This is the title that I like in the browser tab
---
# This is the title that gets displayed as an H1 on the page.

Bacon ipsum dolor sit amet...
```

### Templates

You can add custom templates (otherwise a generic arXiv template gets used,
with nice breadcrumbs). For example, in one of your pages you could choose to
use the template at ``_templates/mysite/custom.html`` by setting the
frontmatter:

```markdown
---
template: mysite/custom.html
---
```

## Installation

You can install the latest release of ``arxiv.marxdown`` from PyPI:

```bash
pipenv install arxiv-marxdown
```

or from the source in this repository:

```bash
pipenv install ./
```

## Building a site

### Building a local site with Flask

To build a site from markdown sources, you will need to specify the
``SITE_NAME``, ``SOURCE_PATH``, and ``BUILD_PATH`` (see
[configuration](#configuration), below).

```bash
SITE_NAME=mysite SOURCE_PATH=/path/to/mysite BUILD_PATH=/tmp/mysite pipenv run python -m arxiv.marxdown.build
```

You can serve the site with Flask, using:

```bash
SITE_NAME=mysite SOURCE_PATH=/path/to/mysite BUILD_PATH=/tmp/mysite FLASK_APP=arxiv.marxdown.app pipenv run flask run
```

### Building a local site with Docker

You can use the ``Makefile`` in the root of this repo to build a site.

You'll need [Docker](https://www.docker.com/products/docker-desktop) to do
this.

To build a site from a local directory, you can do something like:

```bash
make local SOURCE_REF=0.1 SOURCE_DIR=/path/to/my/site SITE_NAME=mysite IMAGE_NAME=arxiv/mysite
```

Note that as each folder in the root directory is served separately SOURCE_DIR
needs to include the specific folder (ex 'help', 'about').

You should see lots of things happening, and maybe this will take a few minutes
if you have a big site. At the end, you should see something like:

```bash
Successfully built 297b169df71f
Successfully tagged arxiv/mysite:0.1
```

Note that the tag is `${IMAGE_NAME}:${SOURCE_REF}``.

You can then run the site by doing:

```bash
docker run -it -p 8000:8000 arxiv/mysite:0.1
```

In your browser, go to http://localhost:8000/mysite (or whatever
page you want). Note http://localhost:8000 is what works in Ubuntu.

### Building a remote site

You can also build a site that is on GitHub, using a specific [tag](https://help.github.com/articles/working-with-tags/).

You will need to pick a place on your computer to do the building. Preferably
something in ``/tmp``.

```bash
make remote SOURCE_REF=0.1 IMAGE_NAME=arxiv/mysite REPO_ORG=arxiv REPO_NAME=arxiv-docs SOURCE_DIR=help
```

- ``SOURCE_REF=0.1`` This is the tag that you're building.
- ``IMAGE_NAME=arxiv/mysite`` The name of the image that you're building.
- ``REPO_ORG=arxiv`` The organization that owns the repo.
- ``REPO_NAME=arxiv-docs`` The name of the repo.
- ``SOURCE_DIR=help`` The directory in the repo that contains the site.

This should work just like the local build, except that it might take a bit
longer because it has to download things.

### Configuration

| Parameter | Used in Build | Used at Runtime | Description |
| --- | :---: | :---: | --- |
| SITE_NAME | Yes | Yes | Name of the site, used for building links. Must be lowercase alphanumeric. |
| SOURCE_PATH | Yes | No | Path to the markdown source directory for the site. |
| BUILD_PATH | Yes | Yes | Path where the built site is/should be stored. |
| SITE_HUMAN_NAME | No | Yes | Human-readable name of the site. |
| SITE_HUMAN_SHORT_NAME | No | Yes | Human-readable short name; e.g. for breadcrumbs. |
| SITE_URL_PREFIX | No | Yes | Path where the site should be served. Must start with ``/`` (default: ``/``). |
| SITE_SEARCH_ENABLED | Yes | Yes | If set to 0, the search feature is excluded (default: 1). |


## Search

You can access the search page at ``<SITE_URL_PREFIX>/search``.

## Controlling the HTTP response (deletion, redirects)

You can control the HTTP response to the user's agent using the ``response``
key in the frontmatter. The following parameters are supported:

| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| ``response.status`` | int | ``200`` | The HTTP status code for the response. |
| ``response.location`` | str | None | Sets the ``Location`` header; this can be used to redirect the user. |
| ``response.deleted`` | bool | ``false`` | If ``true``, a status code of ``404`` will be returned, and a special "deleted" template will be rendered. |

### Example of a deleted page

```
---
response:
  deleted: true
---
This page was deleted because it was not that great.
```


### Example of a redirect

```
---
response:
  status: 301
  location: the/new/location
---
```

## Revision history

You can insert the revision history for a page using the ``render_history()``
macro. This is the commit history, with links to the corresponding source
on GitHub.

```
### Revision history

- 2018-02-26 - Current version 1 created.
$jinja {{ render_history(history) }} jinja$
```

## Sitemap application

### Build

The script ``map.py`` builds a conglomerate site-map from a set of marXdown
sites. It is assumed that these sites are under Git version control, and that
the person/process running this script has authorization to read from them.

This script reads from a config file that contains a set of site
specifications. Here is an example:

```json
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
```


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

```bash
pipenv run python map.py -s /path/to/sites.json -o /path/to/map.json
```

``-s`` specifies the site spec file (above), and ``-o`` specifies the sitemap
output file that is used by the ``sitemap`` application to serve the
sitemap (below).

There is a sample spec file at [``sample/sites.json``](sample/sites.json) in
this repo.

### Serve

The ``sitemap`` app (``sitemapp``?) serves a sitemap from the output file
generated by ``map.py``. To serve the sitemap for dev/test purposes, do:

```bash
URLSET_PATH=/path/to/map.json FLASK_DEBUG=1 FLASK_APP=sitemapp.py pipenv run flask run
```

There is a sample map file at [``sample/map.json``](sample/map.json) in
this repo.

You should be able to access the XML sitemap (per
https://www.sitemaps.org/protocol.html) at
http://localhost:5000/sitemap_index.xml, and the human-readable sitemap (using
a quick and dirty template) at http://localhost:5000/sitemap.html

### Deployment

1. Clone your site source wherever you're deploying it.

```bash
git clone git@github.com:arxiv/arxiv-docs ./docs-site
```

2. Install arXiv-marXdown.

```bash
cd ./docs-site
pipenv install arxiv-marxdown
```

Note that you will need to know the location of your virtual environment if you
are deploying with ``mod_wsgi``. To get it, run:

```bash
pipenv --venv
```

3. Build the site. ``BUILD_PATH`` must be accessible by your web server.

```bash
SITE_NAME=mysite SOURCE_PATH=/path/to/docs-site BUILD_PATH=/opt/mysite pipenv run python -m arxiv.marxdown.build
```

4. Deploy static files to S3. You need keys with write privileges to the S3
   bucket.

```bash
AWS_ACCESS_KEY_ID=[your access key] \
    AWS_SECRET_ACESS_KEY=[your secret key] \
    AWS_REGION=[some region] \
    FLASKS3_ACTIVE=1 \
    FLASKS3_BUCKET_NAME=some-bucket \
    SITE_NAME=mysite \
    BUILD_PATH=/opt/mysite \
    pipenv run python -m arxiv.marxdown.upload_static_assets

```

5. Configure the web server to run the marXdown app with your built site.

If you are using ``mod_wsgi``, you will need to create a script called
``wsgi.py`` that can be accessed by the server. This should load the marxdown
app. For example:

```python
"""Web Server Gateway Interface entry-point."""

import os
from arxiv.marxdown.factory import create_web_app


def application(environ, start_response):
    """WSGI application factory."""
    for key, value in environ.items():
        os.environ[key] = str(value)
    app = create_web_app()
    return app(environ, start_response)

```

An Apache config might look like:

```
SetEnvIf Request_URI "^/mysite" BASE_SERVER=[ wherever.site.org ]
SetEnvIf Request_URI "^/mysite" AWS_ACCESS_KEY_ID=[ your access key ]
SetEnvIf Request_URI "^/mysite" AWS_SECRET_ACCESS_KEY=[ your secret key ]
SetEnvIf Request_URI "^/mysite" AWS_REGION=[ your region ]
SetEnvIf Request_URI "^/mysite" FLASKS3_ACTIVE=1
SetEnvIf Request_URI "^/mysite" FLASKS3_BUCKET_NAME=[ your S3 bucket ]
SetEnvIf Request_URI "^/mysite" SITE_NAME=mysite
SetEnvIf Request_URI "^/mysite" SITE_HUMAN_NAME="My awesome site"
SetEnvIf Request_URI "^/mysite" SITE_HUMAN_SHORT_NAME=Mine!
SetEnvIf Request_URI "^/mysite" SOURCE_PATH=/path/to/docs-site
SetEnvIf Request_URI "^/mysite" BUILD_PATH=/opt/mysite

WSGIDaemonProcess mysite user=someuser group=somegroup threads=16 python-home=[ path to your venv ]  header-buffer-size=65536
WSGIScriptAlias /mysite /opt/docs-site/wsgi.py/ process-group=mysite

<Directory /opt/mysite>
  WSGIProcessGroup mysite
  WSGIApplicationGroup %{GLOBAL}
  WSGIScriptReloading On

  Order allow,deny
  Allow from all
</Directory>
```
