from unittest import TestCase
import re
from .. import render


class TestEscapeBrackets(TestCase):
    """Braces are common in TeX; we should not confuse them with Jinja."""

    def test_escape_bibtex(self):
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
        self.assertEqual(re.sub("\s+", "", render.render(raw)),
                         re.sub("\s+", "", expected))
