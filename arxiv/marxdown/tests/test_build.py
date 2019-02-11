"""Tests for :mod:`.build`."""

from unittest import TestCase, mock
import os
import tempfile
from datetime import datetime
from pytz import UTC
import time
import git

from ..services import source
from .. import build


class TestBuild(TestCase):
    """Test building a site from source."""

    CONTENT = [
        ('index.md', '# This is the index\n\nHere is <a href="foo">link</a>.'),
        ('foo.md', '# Another foo page\n\nSee also <a href="baz">baz</a>.'),
        ('baz/index.md', '---\ntitle: Baz Page\n---\n# The baz index page'),
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
    def mock_configure(cls, mock_config):
        """Configure the source module."""
        mock_config.return_value = {'SOURCE_PATH': cls.source_path}
