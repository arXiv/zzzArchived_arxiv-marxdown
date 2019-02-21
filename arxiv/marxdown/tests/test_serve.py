"""Test serving the built site."""

from unittest import TestCase, mock
import os
import shutil
import tempfile
from datetime import datetime
from pytz import UTC
import time
import git
import copy
from arxiv import status
from .. import factory

BUILD_DIR = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'data')
S3_BUCKET = 'test-bucket'
SITE_NAME = 'test'
VERSION = '0.4.2'
CDN = 'foo.static.com'

CONFIG = mock.MagicMock(**{
    'BUILD_PATH': BUILD_DIR,
    'SITE_NAME': SITE_NAME,
    'SITE_HUMAN_NAME': 'The test site of testiness',
    'SITE_HUMAN_SHORT_NAME': 'Test site',
    'SITE_SEARCH_ENABLED': 1,
    'FLASKS3_BUCKET_NAME': S3_BUCKET,
    'APP_VERSION': VERSION
})

CONFIG_WITH_CDN = copy.copy(CONFIG)
CONFIG_WITH_CDN.FLASKS3_CDN_DOMAIN = CDN


class TestServeSite(TestCase):
    """Serve the build site."""

    @mock.patch(f'{factory.__name__}.config', CONFIG)
    def test_serve(self):
        """Test the site."""
        app = factory.create_web_app()
        client = app.test_client()

        with app.app_context():
            response = client.get('/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn(b'<title>This is the index', response.data)
            self.assertIn(b'<h1 id="this-is-the-index">This is the index</h1>',
                          response.data)
            self.assertIn(b'<p>Here is <a href="foo">link</a>.</p>',
                          response.data)

            response = client.get('/foo')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn(b'<title>Another foo page', response.data)
            self.assertIn(b'<h1 id="another-foo-page">Another foo page</h1>',
                          response.data)
            self.assertIn(b'<p>See also <a href="baz">baz</a>.</p>',
                          response.data)

            response = client.get('/baz')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn(b'<title>Baz Page', response.data)
            self.assertIn(
                b'<h1 id="the-baz-index-page">The baz index page</h1>',
                response.data
            )

            response = client.get('/nope')
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @mock.patch(f'{factory.__name__}.config', CONFIG)
    def test_search(self):
        """Test the search page."""
        app = factory.create_web_app()
        client = app.test_client()

        with app.app_context():
            response = client.get('/search')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response = client.get('/search?q=foo')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn(b'<a href="/foo">Another foo page</a>',
                          response.data)

            response = client.get('/search?q=index')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn(b'<a href="/">This is the index</a>', response.data)

            response = client.get('/search?q=baz')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn(b'<a href="/baz">Baz Page</a>', response.data)

    @mock.patch(f'{factory.__name__}.config', CONFIG)
    def test_redirect(self):
        """Test redirection based on frontmatter."""
        app = factory.create_web_app()
        client = app.test_client()

        with app.app_context():
            response = client.get('/baz/redirectme', follow_redirects=False)
            self.assertEqual(response.status_code,
                             status.HTTP_301_MOVED_PERMANENTLY)
            self.assertEqual(response.headers['Location'],
                             'http://localhost/foo')

    @mock.patch(f'{factory.__name__}.config', CONFIG)
    def test_deleted(self):
        """Test redirection based on frontmatter."""
        app = factory.create_web_app()
        client = app.test_client()

        with app.app_context():
            response = client.get('/baz/deleted', follow_redirects=False)
            self.assertEqual(response.status_code,
                             status.HTTP_404_NOT_FOUND)
            self.assertIn(b'Not here', response.data)

    @mock.patch(f'{factory.__name__}.config', CONFIG)
    def test_serve_with_html(self):
        """Legacy URLs that end in .html should be handled gracefully."""
        app = factory.create_web_app()
        client = app.test_client()

        with app.app_context():
            response = client.get('/index.html', follow_redirects=True)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn(b'<title>This is the index', response.data)
            self.assertIn(b'<h1 id="this-is-the-index">This is the index</h1>',
                          response.data)
            self.assertIn(b'<p>Here is <a href="foo">link</a>.</p>',
                          response.data)

            response = client.get('/foo.html', follow_redirects=True)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn(b'<title>Another foo page', response.data)
            self.assertIn(b'<h1 id="another-foo-page">Another foo page</h1>',
                          response.data)
            self.assertIn(b'<p>See also <a href="baz">baz</a>.</p>',
                          response.data)

            response = client.get('/baz.html', follow_redirects=True)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn(b'<title>Baz Page', response.data)
            self.assertIn(
                b'<h1 id="the-baz-index-page">The baz index page</h1>',
                response.data
            )

            response = client.get('/nope.html', follow_redirects=True)
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

            response = client.get('/baz/deleted.html', follow_redirects=True)
            self.assertEqual(response.status_code,
                             status.HTTP_404_NOT_FOUND)
            self.assertIn(b'Not here', response.data)

            response = client.get('/baz/redirectme.html',
                                  follow_redirects=False)
            self.assertEqual(response.status_code,
                             status.HTTP_302_FOUND)
            self.assertEqual(response.headers['Location'],
                             'http://localhost/baz/redirectme')

    @mock.patch(f'{factory.__name__}.config', CONFIG)
    def test_serve_with_htm(self):
        """Legacy URLs that end in .htm should be handled gracefully."""
        app = factory.create_web_app()
        client = app.test_client()

        with app.app_context():
            response = client.get('/index.htm', follow_redirects=True)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn(b'<title>This is the index', response.data)
            self.assertIn(b'<h1 id="this-is-the-index">This is the index</h1>',
                          response.data)
            self.assertIn(b'<p>Here is <a href="foo">link</a>.</p>',
                          response.data)

            response = client.get('/foo.htm', follow_redirects=True)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn(b'<title>Another foo page', response.data)
            self.assertIn(b'<h1 id="another-foo-page">Another foo page</h1>',
                          response.data)
            self.assertIn(b'<p>See also <a href="baz">baz</a>.</p>',
                          response.data)

            response = client.get('/baz.htm', follow_redirects=True)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn(b'<title>Baz Page', response.data)
            self.assertIn(
                b'<h1 id="the-baz-index-page">The baz index page</h1>',
                response.data
            )

            response = client.get('/nope.htm', follow_redirects=True)
            self.assertEqual(response.status_code,
                             status.HTTP_404_NOT_FOUND)

            response = client.get('/baz/deleted.htm',
                                  follow_redirects=True)
            self.assertEqual(response.status_code,
                             status.HTTP_404_NOT_FOUND)
            self.assertIn(b'Not here', response.data)

            response = client.get('/baz/redirectme.htm',
                                  follow_redirects=False)
            self.assertEqual(response.status_code,
                             status.HTTP_302_FOUND)
            self.assertEqual(response.headers['Location'],
                             'http://localhost/baz/redirectme')

    @mock.patch(f'{factory.__name__}.config', CONFIG)
    def test_serve_static(self):
        """Requests for static URLs should be redirected."""
        app = factory.create_web_app()
        client = app.test_client()

        with app.app_context():
            response = client.get('/notapage.txt', follow_redirects=False)
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)
            self.assertEqual(
                response.headers['Location'],
                "https://%s.s3.amazonaws.com/static/arxiv.marxdown/%s/%s/%s"
                % (S3_BUCKET, VERSION, SITE_NAME, "notapage.txt")
            )

    @mock.patch(f'{factory.__name__}.config', CONFIG_WITH_CDN)
    def test_serve_cdn_static(self):
        """Requests for static URLs should be redirected."""
        app = factory.create_web_app()
        client = app.test_client()

        with app.app_context():
            response = client.get('/notapage.txt', follow_redirects=False)
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)
            self.assertEqual(
                response.headers['Location'],
                "https://%s/static/arxiv.marxdown/%s/%s/%s"
                % (CDN, VERSION, SITE_NAME, "notapage.txt")
            )
