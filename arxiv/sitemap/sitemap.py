"""
Loads a sitemap.

This module relies on a sitemap JSON document, that looks like this:

.. code-block:: json

   {
     "/help": {
       "children": {
         "/help/00README": {
           "title": "The 00README.XXX file",
           "path": "/help/00README",
           "modified": "2019-01-04T22:05:42",
           "children": {...}
         },
         ...


"""


from typing import Any
import json

from arxiv.util.serialize import ISO8601JSONDecoder
from arxiv.base.globals import get_application_config
from .domain import URLSet


class URLDecoder(ISO8601JSONDecoder):
    """JSON Decoder that rewrites paths as full URLs."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Pass :func:`object_hook` to the base constructor."""
        self._url_root = kwargs.pop('url_root', '').rstrip('/')
        kwargs['object_hook'] = kwargs.get('object_hook', self.object_hook)
        super(URLDecoder, self).__init__(*args, **kwargs)

    def object_hook(self, data: dict, **extra: Any) -> Any:
        """Intercept and update paths to full URLs."""
        for key, value in data.items():
            if key == "path" and "://" not in value:
                data[key] = f"{self._url_root}{value}"
        return super(URLDecoder, self).object_hook(data, **extra)


def load_urlset(url_root: str, urlset_path: str) -> URLSet:
    """Load a :const:`URLSet` from a JSON document."""
    with open(urlset_path) as f:
        data: URLSet = json.load(f, cls=URLDecoder, url_root=url_root)
    return data
