"""Tests for :mod:`.build`."""

from unittest import TestCase, mock
import os
import shutil
import tempfile
import json
from .. import build


class TestBuildMap(TestCase):
    """Test map-building."""

    # This is the site spec; it describes the separate sites that will be
    # included in the sitemap.
    SPEC = {
      "sites": [
        {
          "name": "help",
          "repo": "git@github.com:arXiv/arxiv-docs.git",
          "source_dir": "help",
          "source_ref": "develop",
          "human_name": "arXiv Help",
          "url_prefix": "/ng/help",
          "server": "https://beta.arxiv.org"
        },
        {
          "name": "corr",
          "repo": "git@github.com:arXiv/arxiv-docs.git",
          "source_dir": "corr",
          "source_ref": "develop",
          "human_name": "Computing Research Repository (CoRR)",
          "url_prefix": "/ng/corr",
          "server": "https://beta.arxiv.org"
        },
        {
          "name": "new",
          "repo": "git@github.com:arXiv/arxiv-docs.git",
          "source_dir": "new",
          "source_ref": "develop",
          "human_name": "What's been New on the arXiv.org e-print archives",
          "url_prefix": "/ng/new",
          "server": "https://beta.arxiv.org"
        }
      ]
    }

    # These are the site trees returned for each of the sites; used to mock
    # ``site.get_tree()``, below.
    TREES = [
      {
        "/help/foo": {
          "children": {
            "/help/foo/baz": {
              "title": "Another foo page",
              "path": "/help/foo/baz",
              "modified": "2019-02-11T18:41:35+00:00",
              "children": {}
            }
          },
          "title": "The foo page",
          "modified": "2019-02-11T18:41:35+00:00",
          "path": "/help/foo"
        }
      },
      {
        "/corr/foo": {
          "children": {
            "/corr/foo/baz": {
              "title": "Another foo page",
              "path": "/corr/foo/baz",
              "modified": "2019-02-11T18:41:35+00:00",
              "children": {}
            }
          },
          "title": "The foo page",
          "modified": "2019-02-11T18:41:35+00:00",
          "path": "/corr/foo"
        }
      },
      {
        "/new/foo": {
          "children": {
            "/new/foo/baz": {
              "title": "Another foo page",
              "path": "/new/foo/baz",
              "modified": "2019-02-11T18:41:35+00:00",
              "children": {}
            }
          },
          "title": "The foo page",
          "modified": "2019-02-11T18:41:35+00:00",
          "path": "/new/foo"
        }
      }
    ]

    # This is the expected sitemap.
    EXPECTED = {
      "https://beta.arxiv.org/help/foo": {
        "children": {
          "https://beta.arxiv.org/help/foo/baz": {
            "title": "Another foo page",
            "path": "https://beta.arxiv.org/help/foo/baz",
            "modified": "2019-02-11T18:41:35+00:00",
            "children": {}
          }
        },
        "title": "The foo page",
        "modified": "2019-02-11T18:41:35+00:00",
        "path": "https://beta.arxiv.org/help/foo"
      },
      "https://beta.arxiv.org/corr/foo": {
        "children": {
          "https://beta.arxiv.org/corr/foo/baz": {
            "title": "Another foo page",
            "path": "https://beta.arxiv.org/corr/foo/baz",
            "modified": "2019-02-11T18:41:35+00:00",
            "children": {}
          }
        },
        "title": "The foo page",
        "modified": "2019-02-11T18:41:35+00:00",
        "path": "https://beta.arxiv.org/corr/foo"
      },
      "https://beta.arxiv.org/new/foo": {
        "children": {
          "https://beta.arxiv.org/new/foo/baz": {
            "title": "Another foo page",
            "path": "https://beta.arxiv.org/new/foo/baz",
            "modified": "2019-02-11T18:41:35+00:00",
            "children": {}
          }
        },
        "title": "The foo page",
        "modified": "2019-02-11T18:41:35+00:00",
        "path": "https://beta.arxiv.org/new/foo"
      }
    }

    def setUp(self):
        """Write a spec file and create an output directory."""
        _, self.spec_file = tempfile.mkstemp()
        self.out_dir = tempfile.mkdtemp()
        self.out_file = os.path.join(self.out_dir, 'map.json')
        with open(self.spec_file, 'w') as f:
            json.dump(self.SPEC, f)

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.out_dir)
        os.unlink(self.spec_file)

    @mock.patch(f'{build.__name__}.site')
    @mock.patch(f'{build.__name__}.build')
    @mock.patch(f'{build.__name__}.subprocess')
    def test_build(self, mock_subprocess, mock_build, mock_site):
        """Build the sitemap."""
        mock_subprocess.run.return_value = mock.MagicMock(
            returncode=0,
            stdout=b'',
            stderr=b'',
        )
        mock_site.get_tree.side_effect = self.TREES

        build.do_create_site_map(self.spec_file, self.out_file)
        with open(self.out_file) as f:
            self.assertDictEqual(json.load(f), self.EXPECTED)
