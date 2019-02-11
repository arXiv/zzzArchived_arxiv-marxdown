"""API for loading content from a markdown site source."""

import os
import re
from datetime import datetime
from pytz import UTC
import frontmatter
import subprocess
from functools import lru_cache as memoize
from typing import NamedTuple
from typing import Optional, List, Tuple, Iterable, Dict
import git
from arxiv.base.globals import get_application_config as config
from arxiv.base import logging

from ..domain import SourcePage

logger = logging.getLogger(__name__)

GIT_REF = re.compile(r"git@github\.com:([^\.]+)\.git")
GITHUB_COM = "https://github.com"


@memoize()
def get_repo_path(source_path: str) -> str:
    logger.debug('Get repository path for %s', source_path)
    r = subprocess.run("git rev-parse --show-toplevel", cwd=source_path,
                       shell=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    path = r.stdout.decode('utf-8').strip()
    if path.startswith("/private"):
        return path.split("/private", 1)[1]
    return path


@memoize()
def _get_repo(source_path: str) -> git.Repo:
    logger.debug('Get repository for source path %s', source_path)
    return git.Repo(get_repo_path(source_path))


@memoize()
def _get_repo_name(source_path: str) -> Optional[str]:
    logger.debug('Get repository name for source path %s', source_path)
    repo = _get_repo(source_path)
    remotes = list(repo.remotes[0].urls)
    if not remotes:
        return None
    match = GIT_REF.match(remotes[0])
    if not match:
        return None
    return match.groups()[0]


@memoize()
def _get_path_in_repo(source_path: str, page_path: str) -> str:
    logger.debug('Get page %s for source path %s', page_path, source_path)
    repo_path = get_repo_path(source_path)
    return get_path_for_page(page_path).split(repo_path, 1)[1].lstrip("/")


@memoize()
def _get_last_commit(source_path: str, page_path: str) -> Optional[git.Commit]:
    logger.debug('Get last commit for %s in source %s', page_path, source_path)
    fpath = _get_path_in_repo(source_path, page_path)
    repo = _get_repo(source_path)
    commits = list(repo.iter_commits(paths=fpath, max_count=1))
    if not commits:
        return None
    commit: git.Commit = commits[0]
    return commit


def _get_revision_history(source_path: str, page_path: str) \
        -> List[Tuple[Optional[str], datetime, str]]:
    logger.debug('Get rev history for %s in source %s', page_path, source_path)
    fpath = _get_path_in_repo(source_path, page_path)
    repo = _get_repo(source_path)
    return [
        (
            _github_url(source_path, c.name_rev.split()[0], page_path),
            datetime.utcfromtimestamp(c.committed_date).replace(tzinfo=UTC),
            c.message.strip()
        )
        for c in repo.iter_commits(paths=fpath)
    ]


def _get_mtime(source_path: str, page_path: str) -> datetime:
    logger.debug('Get rev history for %s in source %s', page_path, source_path)
    commit = _get_last_commit(source_path, page_path)
    if commit is not None:  # Use the time of the last commit, if possible.
        mt = datetime.utcfromtimestamp(commit.committed_date)
    else:   # Just use the filesystem modified time.
        path = get_path_for_page(page_path)
        mt = datetime.utcfromtimestamp(os.path.getmtime(path))
    mt = mt.replace(tzinfo=UTC)     # Localize.
    return mt


@memoize()
def _get_last_version(source_path: str) -> str:
    logger.debug('Get last version for source %s', source_path)
    repo = _get_repo(source_path)
    return repo.tags[-1].name


def _github_url(source_path, rev, page_path) -> Optional[str]:
    logger.debug('Generate GitHub URL for %s rev %s in source %s',
                 page_path, rev, source_path)
    fpath = _get_path_in_repo(source_path, page_path)
    repo_name = _get_repo_name(source_path)
    if repo_name:
        return f"{GITHUB_COM}/{repo_name}/tree/{rev}/{fpath}"
    return None


@memoize()
def _get_last_modified_url(source_path: str, page_path: str) -> Optional[str]:
    logger.debug('Generate last modified GitHub URL for %s in source %s',
                 page_path, source_path)
    commit = _get_last_commit(source_path, page_path)
    if commit is not None:
        rev = commit.name_rev[:8]
        return _github_url(source_path, rev, page_path)
    return None


@memoize()
def _get_last_version_url(source_path: str) -> Optional[str]:
    logger.debug('Generate last version GitHub URL for source %s', source_path)
    version = _get_last_version(source_path)
    repo_name = _get_repo_name(source_path)
    if repo_name:
        return f"{GITHUB_COM}/{repo_name}/releases/tag/{version}"
    return None


def get_source_path() -> str:
    """Get the absolute path to the site source."""
    return os.path.abspath(config().get('SOURCE_PATH', './'))


def get_templates_path() -> str:
    """Get the absolute path to the templates in the site source."""
    return os.path.join(get_source_path(), '_templates')


def get_path_for_page(page_path: str) -> str:
    """Get the absolute path for a source page based on its relative path."""
    return os.path.join(get_source_path(), f'{page_path}.md')


@memoize(maxsize=1024)
def page_exists(source_path: str, page_path: str) -> bool:
    """Check whether a source page exists."""
    return os.path.exists(get_path_for_page(page_path))


def get_parents(source_path: str, page_path: str) -> List[Dict[str, str]]:
    """Get the paths for a source page's parent pages."""
    path_parts = page_path.split('/')
    parents = []
    for i in range(1, len(path_parts)):
        path = '/'.join(path_parts[:i])
        if page_exists(source_path, path):
            parent_page = load_page(source_path, path, False)
            parents.append({'page_path': path,
                            'title': parent_page.title})
        elif page_exists(source_path, f'{path}/index'):
            parent_page = load_page(source_path, f'{path}/index', False)
            parents.append({'page_path': f'{path}/index',
                            'title': parent_page.title,
                            'path_for_reference': path})
    return parents


@memoize(maxsize=1024)
def load_page(source_path: str, page_path: str, parents: bool = True) \
        -> SourcePage:
    """Load content and data for a source page."""
    page_data = frontmatter.load(get_path_for_page(page_path))
    if parents:
        parents = get_parents(source_path, page_path)
    else:
        parents = []
    metadata = {k: v for k, v in page_data.metadata.items()}
    metadata['parents'] = parents
    metadata['title'] = _get_title(page_data, page_path)
    metadata['modified'] = _get_mtime(source_path, page_path)
    metadata['version'] = _get_last_version(source_path)
    metadata['source_url'] = _get_last_modified_url(source_path, page_path)
    metadata['version_url'] = _get_last_version_url(source_path)
    metadata['history'] = _get_revision_history(source_path, page_path)

    return SourcePage(
        page_path=page_path,
        title=_get_title(page_data, page_path),
        content=page_data.content,
        metadata=metadata,
        template=page_data.get('template'),
        parents=parents
    )


def load_pages() -> Iterable[SourcePage]:
    """(Lazily) load all pages in the site source."""
    source_path = get_source_path()
    for dirpath, dirnames, filenames in os.walk(source_path):
        for filename in filenames:
            if filename.endswith('.md'):
                full_path = os.path.join(dirpath, filename)
                page_path = full_path.split(source_path, 1)[1][1:-3]
                yield load_page(source_path, page_path)


def load_static_paths() -> List[Tuple[str, str]]:
    """
    Get all of the paths to static files in the site source.

    Returns
    -------
    list
        Items are Tuple[str, str], where the first element is the relative
        path (key) for the static file, and the second element is the absolute
        path to the static file in the site source.

    """
    source_path = get_source_path()
    files = []
    for dirpath, dirnames, filenames in os.walk(source_path):
        rdir = os.path.abspath(dirpath).split(source_path, 1)[1].lstrip('/')
        if rdir.startswith('_'):
            continue

        for filename in filenames:
            if filename.endswith('.md') or filename.startswith('.'):
                continue
            content_path = os.path.join(dirpath, filename)
            page_path = content_path[len(source_path):].strip('/')
            files.append((page_path, content_path))
    return files


def load_template_paths() -> List[Tuple[str, str]]:
    """
    Get all of the paths to templates in the site source.

    Returns
    -------
    list
        Items are Tuple[str, str], where the first element is the relative
        path (key) for the template, and the second element is the absolute
        path to the template file in the site source.

    """
    templates_path = get_templates_path()
    if not os.path.exists(templates_path):
        return []
    files = []
    for dirpath, dirnames, filenames in os.walk(templates_path):
        for filename in filenames:
            if not filename.endswith('.html') or filename.startswith('.'):
                continue
            content_path = os.path.join(dirpath, filename)
            template_path = content_path[len(templates_path):].strip('/')
            files.append((template_path, content_path))
    return files


def _get_title(page_data: dict, page_path: str) -> str:
    """Get the title of a source page."""
    title = page_data.get('title')
    if title is None:
        for line in page_data.content.split('\n'):
            cleaned = line.replace('#', '').strip()
            if cleaned:
                title = cleaned
                break
    if title is None:
        title = os.path.split(page_path)[1]
    return title
