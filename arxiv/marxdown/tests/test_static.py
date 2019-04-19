"""Test static file management."""

import os
from unittest import TestCase, mock
from moto import mock_s3
import boto3
from .. import upload_static_assets, factory

BUILD_DIR = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'data')
SITE_NAME = 'test'
APP_VERSION = '0.1'
APP_NAME = 'arxiv.marxdown'
BUCKET = 'test-bucket'
CONFIG = mock.MagicMock(**{
    'BUILD_PATH': BUILD_DIR,
    'SITE_NAME': SITE_NAME,
    'SITE_HUMAN_NAME': 'The test site of testiness',
    'SITE_HUMAN_SHORT_NAME': 'Test site',
    'SITE_SEARCH_ENABLED': 1,
    'FLASKS3_BUCKET_NAME': BUCKET,
    'FLASKS3_ACTIVE': 1,
    'APP_VERSION': APP_VERSION
})


class TestRelativeStaticPaths(TestCase):
    """Test relative static paths feature."""

    @mock.patch(f'{factory.__name__}.config',
                mock.MagicMock(**{
                    'BUILD_PATH': BUILD_DIR,
                    'SITE_NAME': SITE_NAME,
                    'SITE_HUMAN_NAME': 'The test site of testiness',
                    'SITE_HUMAN_SHORT_NAME': 'Test site',
                    'SITE_SEARCH_ENABLED': 1,
                    'FLASKS3_BUCKET_NAME': BUCKET,
                    'FLASKS3_ACTIVE': 1,
                    'APP_VERSION': APP_VERSION,
                    'RELATIVE_STATIC_PATHS': True,
                    'SITE_URL_PREFIX': '/test'
                }))
    def test_use_relative(self):
        """Relative static paths feature is enabled."""
        app = factory.create_web_app()
        self.assertTrue(app.blueprints['docs'].url_prefix.startswith('/test'),
                        'The blueprint is mounted below the site URL prefix.')

    @mock.patch(f'{factory.__name__}.config',
                mock.MagicMock(**{
                    'BUILD_PATH': BUILD_DIR,
                    'SITE_NAME': SITE_NAME,
                    'SITE_HUMAN_NAME': 'The test site of testiness',
                    'SITE_HUMAN_SHORT_NAME': 'Test site',
                    'SITE_SEARCH_ENABLED': 1,
                    'FLASKS3_BUCKET_NAME': BUCKET,
                    'FLASKS3_ACTIVE': 1,
                    'APP_VERSION': APP_VERSION,
                    'RELATIVE_STATIC_PATHS': False,
                    'SITE_URL_PREFIX': '/test'
                }))
    def test_dont_use_relative(self):
        """Relative static paths feature is enabled."""
        app = factory.create_web_app()
        self.assertTrue(
            app.blueprints['docs'].url_prefix.startswith('/_marxdown'),
            'The blueprint is mounted at the root path.'
        )


class TestUploadStaticFiles(TestCase):
    """Test uploading of static files to S3."""

    @mock_s3
    @mock.patch(f'{factory.__name__}.config', CONFIG)
    def test_upload(self):
        """Upload static files to S3."""
        upload_static_assets.upload_static_files()

        s3 = boto3.resource('s3', region_name='us-east-1')
        keys = [item.key for item in s3.Bucket(BUCKET).objects.all()]
        STATIC_PREFIX = f'static/{APP_NAME}/{APP_VERSION}/{SITE_NAME}'
        self.assertIn(f'{STATIC_PREFIX}/baz/foo.dat', keys)
        self.assertIn(f'{STATIC_PREFIX}/notapage.txt', keys)
