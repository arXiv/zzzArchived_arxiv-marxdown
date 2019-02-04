from unittest import TestCase

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
