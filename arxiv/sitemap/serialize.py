"""
Serialize :class:`URLSet` according to the Sitemaps Protocol.

Here's a simple example from the spec:

.. code-block:: xml

   <?xml version="1.0" encoding="UTF-8"?>
   <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
     <url>
       <loc>http://www.example.com/</loc>
       <lastmod>2005-01-01</lastmod>
       <changefreq>monthly</changefreq>
       <priority>0.8</priority>
     </url>
   </urlset>


See `https://www.sitemaps.org/protocol.html`_. For details.
"""

from typing import Iterable
# from lxml import etree    # Issues with lxml version in mod_wsgi. :-(
import io
from xml.etree import ElementTree as etree

from .domain import URLSet, URL

SITEMAPS_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"


def sitemap_xml(urlset: URLSet) -> str:
    """Generate a sitemap XML document."""
    root = etree.Element("urlset", xmlns=SITEMAPS_NAMESPACE)
    for url in iter_urls(urlset):
        root.append(url_xml(url))
    buffer = io.BytesIO()
    tree = etree.ElementTree(root)
    tree.write(buffer, encoding="UTF-8", xml_declaration=True)
    buffer.seek(0)
    return buffer.read()
    # return root.read()
    # If we ever get to use lxml....
    # xml_declaration=True
    # pretty_print=True


def iter_urls(urlset: URLSet) -> Iterable[URL]:
    """Pull all of the :class:`.URL`s from an :class:`.URLSet`."""
    for _, url in urlset.items():
        yield url
        for child_url in iter_urls(url["children"]):
            yield child_url


def lastmod(url: URL) -> etree.Element:
    """
    Date of last modification of the file.

    This date should be in W3C Datetime format. This format allows you to omit
    the time portion, if desired, and use YYYY-MM-DD.

    Note that this tag is separate from the If-Modified-Since (304) header the
    server can return, and search engines may use the information from both
    sources differently.
    """
    element = etree.Element("lastmod")
    element.text = url["modified"].isoformat()
    return element


def loc(url: URL) -> etree.Element:
    """
    URL of the page.

    This URL must begin with the protocol (such as http) and end with a
    trailing slash, if your web server requires it. This value must be less
    than 2,048 characters.
    """
    element = etree.Element("loc")
    element.text = url["path"]
    return element


def changefreq(url: URL) -> etree.Element:
    """
    How frequently the page is likely to change.

    This value provides general information to search engines and may not
    correlate exactly to how often they crawl the page. Valid values are:

    - always
    - hourly
    - daily
    - weekly
    - monthly
    - yearly
    - never

    The value "always" should be used to describe documents that change each
    time they are accessed. The value "never" should be used to describe
    archived URLs.

    Please note that the value of this tag is considered a hint and not a
    command. Even though search engine crawlers may consider this information
    when making decisions, they may crawl pages marked "hourly" less frequently
    than that, and they may crawl pages marked "yearly" more frequently than
    that. Crawlers may periodically crawl pages marked "never" so that they can
    handle unexpected changes to those pages.
    """
    element = etree.Element("changefreq")
    element.text = url.get("changefreq", "monthly")
    return element


def url_xml(url: URL) -> etree.Element:
    """Generate an :class:`etree.Element` for a single URL."""
    url_element = etree.Element("url")
    url_element.append(loc(url))
    try:
        url_element.append(lastmod(url))
    except KeyError:    # No modified date.
        pass
    url_element.append(changefreq(url))
    return url_element
