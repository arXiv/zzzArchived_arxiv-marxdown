"""Tests for :mod:`sitemap.serialize`."""

from unittest import TestCase, mock
import os
from xml.etree import ElementTree as etree
import io

from .. import serialize, load

DATA_PATH = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'data')


class TestSitemapXML(TestCase):
    """Tests for XML serialization of a sitemap (JSON) document."""

    def test_regression(self):
        """Regression test with sample data, to make sure we don't break it."""
        urlset_path = os.path.join(DATA_PATH, 'sitemap.json')
        xml_path = os.path.join(DATA_PATH, 'sitemap_index.xml')
        urlset = load.load_urlset('http://foosite.com', urlset_path)

        with open(xml_path, 'rb') as f:
            expected_urlset = etree.parse(f).getroot()

        generated_xml = serialize.sitemap_xml(urlset)
        generated_urlset = etree.parse(io.BytesIO(generated_xml)).getroot()

        def elements_equal(element_a, element_b):
            """Recursively compare two :class:`etree.Element` instances."""
            if element_a.text or element_b.text:
                self.assertEqual(element_a.text, element_b.text)
            self.assertEqual(element_a.tag, element_b.tag)
            self.assertEqual(element_a.tail, element_b.tail)
            self.assertEqual(element_a.attrib, element_b.attrib)
            self.assertEqual(len(element_a), len(element_b))
            for child_a, child_b in zip(element_a, element_b):
                self.assertTrue(elements_equal(child_a, child_b))
            return True     # If we make it this far...

        self.assertTrue(elements_equal(generated_urlset, expected_urlset))
