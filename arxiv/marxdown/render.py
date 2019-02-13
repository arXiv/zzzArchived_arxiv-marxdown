"""Responsible for rendering markdown content to HTML."""

from typing import Callable, Optional, Mapping, Union, Tuple, List
import re
import warnings
from functools import wraps
import xml.etree.ElementTree as ET
from markdown import markdown, Markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from mdx_partial_gfm import PartialGithubFlavoredMarkdownExtension

from arxiv.base import logging

from .domain import SourcePage

logger = logging.getLogger(__name__)

ALLOWED_JINJA = r"\$jinja\s*{{ '([{}%]+)' }}([^{]+){{ '([{}%]+)' }}\s*jinja\$"


def render(content: str, dereferencer: Optional[Callable] = None) -> str:
    """
    Render markdown content to HTML.

    Parameters
    ----------
    content : str
        Markdown content.
    dereferencer : function
        Used for generating URLs from internal paths and slugs. Should accept
        a HREF value (str), and return a URL (str). Optional.
    static_dereferencer : function
        Used for generating URLs for static files. Should accept
        a src value (str), and return a URL (str). Optional.

    Returns
    -------
    str
        Rendered HTML.

    """
    extensions = ['markdown.extensions.tables',
                  'markdown.extensions.fenced_code',
                  'markdown.extensions.codehilite',
                  'markdown.extensions.toc',
                  'markdown.extensions.attr_list',
                  PartialGithubFlavoredMarkdownExtension(),
                  StyleClassExtension(tag="table",
                                      classes=["table", "is-striped"])]
    if dereferencer is not None:
        extensions.append(ReferenceExtension(tag='a', attr='href',
                                             dereferencer=dereferencer))
        extensions.append(ReferenceExtension(tag='img', attr='src',
                                             dereferencer=dereferencer))

    # The GFM extension doesn't implement the changes related to positional
    # arguments described in the Markdown v2.6 release notes.
    # https://python-markdown.github.io/change_log/release-2.6/#positional-arguments-deprecated
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return escape_braces(markdown(content, extensions=extensions))


def escape_braces(content: str) -> str:
    """
    Curly braces in content must be escaped.

    Otherwise, they are treated as Jinja2 syntax.
    """
    def repl(match):
        print(match.groups())
        return "foo"
    return re.sub(ALLOWED_JINJA, r"\1\2\3",
                  re.sub(r"([{}%]+)", r"{{ '\g<1>' }}", content))


class StyleClassProcessor(Treeprocessor):
    """Adds CSS classes to elements."""

    def __init__(self, tag: str = "html", classes: List[str] = []) -> None:
        """Set the target tag and classes to add."""
        self.tag = tag
        self.classes = classes

    def run(self, root: ET.ElementTree) -> None:
        """Add some CSS classes to a table when we find one."""
        for child in root:
            if child.tag == self.tag:
                existing = child.attrib.get("class", "").split()
                child.attrib["class"] = " ".join(existing + self.classes)


class ReferenceProcessor(Treeprocessor):
    """Convert internal links to full paths."""

    def __init__(self, tag: str = "a", attr: str = "href",
                 dereferencer: Optional[Callable] = None) -> None:
        """Set the link dereferencer for use during processing."""
        self.dereferencer = dereferencer
        self.tag = tag
        self.attr = attr

    def run(self, root: ET.ElementTree) -> None:
        """Perform link conversion on ``root``."""
        if self.dereferencer is not None:
            self.translate_anchors(root)

    def translate_anchors(self, element: ET.Element) -> None:
        """Traverse ``element`` looking for and updating anchor elements."""
        for child in element:
            if child.tag == self.tag:
                value = child.attrib.get(self.attr)
                try:
                    child.attrib[self.attr] = self.dereferencer(value)
                except KeyError:
                    continue
            self.translate_anchors(child)


class ReferenceExtension(Extension):
    """Adds :class:`.ReferenceProcessor` to the markdown processor."""

    def __init__(self, tag: str = "a", attr: str = "href",
                 dereferencer: Optional[Callable] = None) -> None:
        """Set the link dereferencer for use during processing."""
        self.tag = tag
        self.attr = attr
        self.dereferencer = dereferencer

    def extendMarkdown(self, md: Markdown, md_globals: Mapping) -> None:
        """Add :class:`.ReferenceProcessor` to the markdown processor."""
        inst = ReferenceProcessor(tag=self.tag, attr=self.attr,
                                  dereferencer=self.dereferencer)
        md.treeprocessors[f'{self.tag}_{self.attr}_reference_processor'] = inst


class StyleClassExtension(Extension):
    """Adds :class:`.ReferenceProcessor` to the markdown processor."""

    def __init__(self, tag: str = "a", classes: List[str] = []) -> None:
        """Set the link dereferencer for use during processing."""
        self.tag = tag
        self.classes = classes

    def extendMarkdown(self, md: Markdown, md_globals: Mapping) -> None:
        """Add :class:`.ReferenceProcessor` to the markdown processor."""
        inst = StyleClassProcessor(tag=self.tag, classes=self.classes)
        md.treeprocessors[f'{self.tag}_style_class_processor'] = inst


def get_linker(page: SourcePage, site_name: str) -> Callable:
    def linker(href: str) -> Tuple[str, str, str, Optional[str]]:
        # We don't want to mess with things that are clearly not ours to
        # fiddle with.
        if not href \
                or '://' in href \
                or href.startswith('/') \
                or href.startswith('#') \
                or href.startswith('mailto:'):
            return href, None, None, None
        anchor = None
        if '#' in href:
            href, anchor = href.split('#', 1)
        if href.endswith('.md'):
            path = href[:-3]
            route = f'{site_name}.from_sitemap'
            kwarg = 'page_path'
        elif '.' not in href.split('/')[-1]:
            path = href
            route = f'{site_name}.from_sitemap'
            kwarg = 'page_path'
        else:
            path = href
            route = f'{site_name}.static'
            kwarg = 'filename'
        base_path = '/'.join(page.page_path.split('/')[:-1])
        target_path = '/'.join([base_path, path.rstrip('/')]).lstrip('/')
        return route, kwarg, target_path, anchor
    return linker


def get_deferencer(page: SourcePage, site_name: str) -> Callable:
    def link_dereferencer(href: str) -> str:
        route, kwarg, target_path, anchor = get_linker(page, site_name)(href)
        if kwarg is None:
            return route
        if anchor is not None:
            return "$jinja {{ url_for('%s', %s='%s', _anchor='%s') }} jinja$" \
                % (route, kwarg, target_path, anchor)
        return "$jinja {{ url_for('%s', %s='%s') }} jinja$" \
            % (route, kwarg, target_path)
    return link_dereferencer
