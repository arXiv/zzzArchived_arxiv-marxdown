"""Tests for :mod:`.source`."""

from unittest import TestCase, mock
import os
import shutil
import tempfile
from datetime import datetime
from pytz import UTC
import time
import git

from .. import source


class TestLoadSource(TestCase):
    """Test loading a site source."""

    CONTENT = [
        ('index.md', '# This is the index\n\nHere is <a href="foo">link</a>.'),
        ('foo.md', '# Another foo page\n\nSee also <a href="baz">baz</a>.'),
        ('baz/index.md', '---\ntitle: Baz Page\n---\n# The baz index page'),
        ('baz/redirectme.md', '---\nresponse:\n  status: 301\n  location: ../foo\n---'),
        ('baz/deleted.md', '---\nresponse:\n  deleted: true\n---\nNot here'),
        ('notapage.txt', 'some non-markdown content here'),
        ('baz/foo.dat', 'some more non-markdown content here'),
        ('_hidden/baz.dat', 'this is not here'),
        ('_templates/sometemplate.html', '<html><body>what</body></html>'),
        ('_templates/notatemplate.txt', 'nope'),
    ]

    @classmethod
    def setUpClass(cls):
        """Create a minimal site source in a Git repository."""
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
        shutil.rmtree(cls.repo_path)

    @classmethod
    def mock_configure(cls, mock_config):
        """Configure the source module."""
        mock_config.return_value = {'SOURCE_PATH': cls.source_path}

    @mock.patch(f'{source.__name__}.config')
    def test_get_repo_path(self, mock_config):
        """Test :func:`source.get_repo_path`."""
        self.mock_configure(mock_config)
        self.assertEqual(source.get_repo_path(self.source_path),
                         self.repo_path)

    @mock.patch(f'{source.__name__}.config')
    def test_get_source_path(self, mock_config):
        """Test :func:`source.get_source_path`."""
        self.mock_configure(mock_config)
        self.assertEqual(source.get_source_path(), self.source_path)

    @mock.patch(f'{source.__name__}.config')
    def test_get_path_for_page(self, mock_config):
        """Test :func:`source.get_path_for_page`."""
        self.mock_configure(mock_config)
        self.assertEqual(source.get_path_for_page('foo'),
                         os.path.join(self.source_path, 'foo.md'))

    @mock.patch(f'{source.__name__}.config')
    def test_page_exists(self, mock_config):
        """Test :func:`source.page_exists`."""
        self.mock_configure(mock_config)
        self.assertTrue(source.page_exists(self.source_path, 'index'))
        self.assertTrue(source.page_exists(self.source_path, 'foo'))
        self.assertTrue(source.page_exists(self.source_path, 'baz/index'))
        self.assertFalse(source.page_exists(self.source_path, 'baz/bar'))

    @mock.patch(f'{source.__name__}.config')
    def test_load_page(self, mock_config):
        """Load pages from the source."""
        self.mock_configure(mock_config)
        page = source.load_page(self.source_path, 'index')
        self.assertEqual(page.page_path, 'index')
        self.assertEqual(page.title, 'This is the index')
        self.assertEqual(len(page.parents), 0)
        self.assertEqual(
            page.content,
            '# This is the index\n\nHere is <a href="foo">link</a>.'
        )
        self.assertEqual(len(page.metadata['parents']), 0)
        self.assertEqual(page.metadata['modified'], self.created['index.md'])
        self.assertEqual(page.metadata['version'], self.version)
        url, datestamp, message = page.metadata['history'][0]
        self.assertTrue(
            url.startswith(f'https://github.com/{self.repo_name}/tree/')
        )
        self.assertTrue(url.endswith(f'/{self.site_dir}/index.md'))
        self.assertEqual(datestamp, self.created['index.md'])
        self.assertEqual(message, 'added index.md')

        page = source.load_page(self.source_path, 'foo')
        self.assertEqual(page.page_path, 'foo')
        self.assertEqual(page.title, 'Another foo page')
        self.assertEqual(len(page.parents), 0)
        self.assertEqual(
            page.content,
            '# Another foo page\n\nSee also <a href="baz">baz</a>.'
        )
        self.assertEqual(len(page.metadata['parents']), 0)
        self.assertEqual(page.metadata['modified'], self.created['foo.md'])
        self.assertEqual(page.metadata['version'], self.version)
        self.assertEqual(len(page.metadata['history']), 1)
        url, datestamp, message = page.metadata['history'][0]
        self.assertTrue(
            url.startswith(f'https://github.com/{self.repo_name}/tree/')
        )
        self.assertTrue(url.endswith(f'/{self.site_dir}/foo.md'))
        self.assertEqual(datestamp, self.created['foo.md'])
        self.assertEqual(message, 'added foo.md')

        page = source.load_page(self.source_path, 'baz/index')
        self.assertEqual(page.page_path, 'baz/index')
        self.assertEqual(page.title, 'Baz Page')
        self.assertEqual(len(page.parents), 1)
        self.assertEqual(page.content, '# The baz index page')
        self.assertEqual(len(page.metadata['parents']), 1)
        self.assertEqual(page.metadata['modified'],
                         self.created['baz/index.md'])
        self.assertEqual(page.metadata['version'], self.version)
        self.assertEqual(len(page.metadata['history']), 1)
        url, datestamp, message = page.metadata['history'][0]
        self.assertTrue(
            url.startswith(f'https://github.com/{self.repo_name}/tree/')
        )
        self.assertTrue(url.endswith(f'/{self.site_dir}/baz/index.md'))
        self.assertEqual(datestamp, self.created['baz/index.md'])
        self.assertEqual(message, 'added baz/index.md')

    @mock.patch(f'{source.__name__}.config')
    def test_load_pages(self, mock_config):
        """Load all the pages."""
        self.mock_configure(mock_config)
        pages = [page for page in source.load_pages()]
        self.assertEqual(len(pages), 5)
        for page in pages:
            self.assertIsInstance(page, source.SourcePage)

    @mock.patch(f'{source.__name__}.config')
    def test_load_static_paths(self, mock_config):
        """Load paths for all the static files."""
        self.mock_configure(mock_config)
        paths = source.load_static_paths()
        self.assertEqual(len(paths), 2)
        self.assertEqual(paths[0][0], 'notapage.txt')
        self.assertTrue(paths[0][1].endswith(f'{self.site_dir}/notapage.txt'))

        self.assertEqual(paths[1][0], 'baz/foo.dat')
        self.assertTrue(paths[1][1].endswith(f'{self.site_dir}/baz/foo.dat'))

    @mock.patch(f'{source.__name__}.config')
    def test_load_template_paths(self, mock_config):
        """Load paths for all the templates."""
        self.mock_configure(mock_config)
        paths = source.load_template_paths()
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0][0], 'sometemplate.html')
        self.assertTrue(
            paths[0][1].endswith(
                f'{self.site_dir}/_templates/sometemplate.html'
            )
        )
