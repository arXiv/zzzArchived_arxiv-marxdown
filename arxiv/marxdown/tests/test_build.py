"""Tests for :mod:`.build`."""

from unittest import TestCase, mock
import os
import shutil
import tempfile
from datetime import datetime
from pytz import UTC
import time
import git

from ..services import source, index, site
from .. import build


class TestBuild(TestCase):
    """Test building a site from source."""

    CONTENT = [
        ('index.md', '# This is the index\n\nHere is <a href="foo">link</a>.'),
        ('foo.md', '# Another foo page\n\nSee also <a href="baz">baz</a>.'),
        ('baz/index.md', '---\ntitle: Baz Page\n---\n# The baz index page'),
        ('notapage.txt', 'some non-markdown content here'),
        ('baz/foo.dat', 'some more non-markdown content here'),
        ('baz/redirectme.md',
         '---\nresponse:\n  status: 301\n  location: ../foo\n---'),
        ('baz/deleted.md', '---\nresponse:\n  deleted: true\n---\nNot here'),
        ('_hidden/baz.dat', 'this is not here'),
        ('_templates/sometemplate.html', '<html><body>what</body></html>'),
        ('_templates/notatemplate.txt', 'nope'),
    ]

    @classmethod
    def setUpClass(cls):
        """Create a minimal site source in a Git repository."""
        cls.build_dir = tempfile.mkdtemp()
        cls.site_dir = "test"
        cls.repo_path = tempfile.mkdtemp()
        cls.source_path = os.path.join(cls.repo_path, cls.site_dir)
        cls.repo = git.Repo.init(cls.repo_path)
        cls.repo_name = 'arxiv/foo'
        cls.repo.create_remote('origin', f'git@github.com:{cls.repo_name}.git')
        cls.created = {}

        # Add and commit files to the repo.
        for path, content in cls.CONTENT:
            fpath = os.path.join(cls.source_path, path)
            parent, _ = os.path.split(fpath)
            if not os.path.exists(parent):
                os.makedirs(parent)
            with open(fpath, 'w') as f:
                f.write(content)
            cls.repo.index.add([fpath])
            commit = cls.repo.index.commit("added %s" % path)
            created = datetime.utcfromtimestamp(commit.committed_date)
            cls.created[path] = created.replace(tzinfo=UTC)
            time.sleep(0.25)   # So that the creation times might vary.
        cls.branch = cls.repo.create_head('new')
        cls.repo.head.reference = cls.branch
        cls.version = '0.4.5'
        cls.latest_tag = cls.repo.create_tag(cls.version, message='message!')

    @classmethod
    def tearDownClass(cls):
        """Clean up."""
        shutil.rmtree(cls.build_dir)
        shutil.rmtree(cls.repo_path)

    @classmethod
    def mock_configure(cls, mock_config):
        """Configure the source module."""
        mock_config.return_value = {
            'SOURCE_PATH': cls.source_path,
            'BUILD_PATH': cls.build_dir,
            'SITE_NAME': 'test',
            'SITE_HUMAN_NAME': 'The test site of testiness',
            'SITE_HUMAN_SHORT_NAME': 'Test site',
            'SITE_SEARCH_ENABLED': 1,
        }

    @mock.patch(f'{site.__name__}.config')
    @mock.patch(f'{index.__name__}.config')
    @mock.patch(f'{source.__name__}.config')
    def test_build_site(self, *configs):
        """Build the site, yo."""
        for config in configs:
            self.mock_configure(config)
        build._build_site()

        index_path = os.path.join(self.build_dir, 'idx')

        # Data object is created for each page.
        data_path = os.path.join(self.build_dir, 'data')
        self.assertTrue(os.path.exists(data_path))
        self.assertTrue(os.path.exists(os.path.join(data_path, 'index.json')))
        self.assertTrue(os.path.exists(os.path.join(data_path, 'foo.json')))
        self.assertTrue(
            os.path.exists(os.path.join(data_path, 'baz/index.json')))
        self.assertTrue(
            os.path.exists(os.path.join(data_path, 'baz/redirectme.json')))
        self.assertTrue(
            os.path.exists(os.path.join(data_path, 'baz/deleted.json')))

        # Template fragment is created for each page.
        pages_path = os.path.join(self.build_dir, 'pages')
        self.assertTrue(os.path.exists(pages_path))
        self.assertTrue(os.path.exists(os.path.join(pages_path, 'index.j2')))
        self.assertTrue(os.path.exists(os.path.join(pages_path, 'foo.j2')))
        self.assertTrue(
            os.path.exists(os.path.join(pages_path, 'baz/index.j2')))
        self.assertTrue(
            os.path.exists(os.path.join(pages_path, 'baz/redirectme.j2')))
        self.assertTrue(
            os.path.exists(os.path.join(pages_path, 'baz/deleted.j2')))

        # Templates are copied in.
        templates_path = os.path.join(self.build_dir, 'templates')
        self.assertTrue(os.path.exists(templates_path))
        self.assertTrue(
            os.path.exists(os.path.join(templates_path, 'sometemplate.html')))

        # Static files are copied in.
        static_path = os.path.join(self.build_dir, 'static', self.site_dir)
        self.assertTrue(os.path.exists(static_path))
        self.assertTrue(
            os.path.exists(os.path.join(static_path, 'notapage.txt')))
        self.assertTrue(
            os.path.exists(os.path.join(static_path, 'baz/foo.dat')))

        self.assertTrue(os.path.exists(index_path))
