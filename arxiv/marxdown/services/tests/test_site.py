"""Tests for :mod:`.site`."""

from unittest import TestCase, mock
import os
import shutil
import tempfile
from datetime import datetime
from pytz import UTC
import time
import git

from .. import site

BUILD_DIR = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'data')
CONFIG = mock.MagicMock(return_value={
    'BUILD_PATH': BUILD_DIR,
    'SITE_NAME': 'test',
    'SITE_HUMAN_NAME': 'The test site of testiness',
    'SITE_HUMAN_SHORT_NAME': 'Test site',
})


class TestSiteTree(TestCase):
    """Tests building the site tree."""

    @mock.patch(f'{site.__name__}.config', CONFIG)
    def test_get_tree(self):
        """Test :func:`site.get_tree`."""
        tree = site.get_tree()
        self.assertDictEqual(
            tree,
            {
                '/': {
                    'children': {
                        '/foo': {
                            'title': 'Another foo page',
                            'path': '/foo',
                            'modified': '2019-02-11T18:41:35+00:00',
                            'children': {}
                        },
                        '': {
                            'title': 'This is the index',
                            'path': '',
                            'modified': '2019-02-11T18:41:34+00:00',
                            'children': {}
                        },
                        '/baz': {
                            'title': 'Baz Page',
                            'path': '/baz',
                            'modified': '2019-02-11T18:41:35+00:00',
                            'children': {}
                        }
                    },
                    'title': 'The test site of testiness',
                    'path': '/'
                }
            }
        )
