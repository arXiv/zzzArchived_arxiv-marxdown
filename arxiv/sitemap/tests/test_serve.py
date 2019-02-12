"""Tests for the sitemapp app as a whole."""

from unittest import TestCase, mock
import os
import shutil
import tempfile
from datetime import datetime
from pytz import UTC
import time
import git

from arxiv import status
from .. import factory

DATA_PATH = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'data')

CONFIG = mock.MagicMock(**{
    'URLSET_PATH': os.path.join(DATA_PATH, 'map.json'),
    'FLASKS3_BUCKET_NAME': 'test-bucket'
})


class TestServeSite(TestCase):
    """Serve the build site."""

    @mock.patch(f'{factory.__name__}.config', CONFIG)
    def test_serve(self):
        """Make requests to the sitemap routes."""
        app = factory.create_web_app()
        client = app.test_client()

        with app.app_context():
            response = client.get('/sitemap_index.xml')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.headers['Content-Type'],
                             'application/xml')

            response = client.get('/sitemap.html')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.headers['Content-Type'],
                             'text/html; charset=utf-8')
