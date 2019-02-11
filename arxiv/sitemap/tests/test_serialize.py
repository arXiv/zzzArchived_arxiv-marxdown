"""Tests for :mod:`sitemap.serialize`."""

from unittest import TestCase, mock
import os
from lxml import etree

from .. import serialize, sitemap

DATA_PATH = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'data')


class TestSitemapXML(TestCase):
    """Tests for XML serialization of a sitemap (JSON) document."""

    def test_regression(self):
        """Regression test with sample data."""
        urlset_path = os.path.join(DATA_PATH, 'sitemap.json')
        xml_path = os.path.join(DATA_PATH, 'sitemap_index.xml')
        urlset = sitemap.load_urlset('http://foosite.com', urlset_path)

        with open(xml_path, 'rb') as f:
            expected_xml = etree.parse(f).getroot()

        generated_xml = etree.fromstring(serialize.sitemap_xml(urlset))

        def elements_equal(element_a, element_b):
            """Recursively compare two :class:`etree.Element` instances."""
            self.assertEqual(element_a.text, element_b.text)
            self.assertEqual(element_a.tag, element_b.tag)
            self.assertEqual(element_a.tail, element_b.tail)
            self.assertEqual(element_a.attrib, element_b.attrib)
            self.assertEqual(len(element_a), len(element_b))
            for child_a, child_b in zip(element_a, element_b):
                self.assertTrue(elements_equal(child_a, child_b))
            return True     # If we make it this far...

        self.assertTrue(elements_equal(generated_xml, expected_xml))
