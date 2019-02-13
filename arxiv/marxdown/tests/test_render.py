from unittest import TestCase, mock
import re
from .. import render


class TestMailToLinks(TestCase):
    """Link processing should not break ``mailto:`` links."""

    def test_mailto_is_untouched(self):
        """If a link starts with ``mailto:``, it shouldn't be fiddled with."""
        raw = """click [here](mailto:help@arxiv.org)."""
        expected = """<p>click <a href="mailto:help@arxiv.org">here</a>.</p>"""
        self.assertEqual(render.render(raw), expected)


class TestEscapeBrackets(TestCase):
    """Braces are common in TeX; we should not confuse them with Jinja."""

    def test_escape_bibtex(self):
        """Indeed, BibTeX has lots of braces; we should escape those."""
        raw = """
            like this,
            ```
             @Article{Beneke:1997hv,
                  author    = "M. Beneke and G. Buchalla and I. Dunietz",
                  title     = "{Mixing induced CP asymmetries in inclusive B decays}",
                  journal   = "Phys. Lett.",
                  volume    = "B393",
                  year      = "1997",
                  pages     = "132-142",
                  **eprint        = "hep-ph/9609357"**
             }
            ```"""
        expected = """
            <div class="codehilite"><pre><span></span>        like this,
            ```
             @Article{{ '{' }}Beneke:1997hv,
                  author    = &quot;M. Beneke and G. Buchalla and I. Dunietz&quot;,
                  title     = &quot;{{ '{' }}Mixing induced CP asymmetries in inclusive B decays{{ '}' }}&quot;,
                  journal   = &quot;Phys. Lett.&quot;,
                  volume    = &quot;B393&quot;,
                  year      = &quot;1997&quot;,
                  pages     = &quot;132-142&quot;,
                  **eprint        = &quot;hep-ph/9609357&quot;**
             {{ '}' }}
            ```
            </pre></div>"""
        self.assertEqual(re.sub(r"\s+", "", render.render(raw)),
                         re.sub(r"\s+", "", expected),
                         "Braces in the BibTeX are replaced")

    def test_dont_escape_jinja(self):
        """But we still need Jinja support; so look out for that."""
        raw = """here is some $jinja {{ real_jinja() }} jinja$"""
        expected = """<p>here is some {{ real_jinja() }}</p>"""
        self.assertEqual(render.render(raw), expected,
                         "Jinja marked as such is not replaced.")

    def test_dont_escape_links(self):
        """Jinja for URL generation should not be escaped."""
        raw = """here [is a link](to/somewhere.md)."""
        expected = """<p>here <a href="{{ url_for('name.from_sitemap', page_path='to/somewhere') }}">is a link</a>.</p>"""
        dereferencer = render.get_deferencer(mock.MagicMock(), "name")
        self.assertEqual(render.render(raw, dereferencer), expected,
                         "Injected url_for tags are not escaped")
