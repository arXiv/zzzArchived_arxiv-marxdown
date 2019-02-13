"""Test static file management."""

import os
from unittest import TestCase, mock
from moto import mock_s3
import boto3
from .. import upload_static_assets, factory

DATA_PATH = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'data')
APP_VERSION = '0.1'
APP_NAME = 'arxiv.sitemap'
BUCKET = 'test-bucket'
CONFIG = mock.MagicMock(**{
    'URLSET_PATH': os.path.join(DATA_PATH, 'map.json'),
    'FLASKS3_BUCKET_NAME': BUCKET,
    'FLASKS3_ACTIVE': 1,
    'APP_VERSION': APP_VERSION
})


class TestUploadStaticFiles(TestCase):
    """Test uploading of static files to S3."""

    @mock_s3
    @mock.patch(f'{factory.__name__}.config', CONFIG)
    def test_upload(self):
        """Upload static files to S3."""
        upload_static_assets.upload_static_files()

        s3 = boto3.resource('s3', region_name='us-east-1')
        for item in s3.Bucket(BUCKET).objects.all():
            self.assertTrue(item.key.startswith('static/base'),
                            'The only static files involved are from base.')
