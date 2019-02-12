"""Core data structs for the :mod:`sitemap` app."""

from typing import Dict
from datetime import datetime
from mypy_extensions import TypedDict


URL = TypedDict('URL', {
    'title': str,
    'path': str,
    'modified': datetime,
    'children': 'URLSet'
})
"""Represents a single URL in the sitemap, including its children."""

URLSet = Dict[str, URL]
"""
The sitemap as a whole.

This is a nested dict struct; see :const:`.URL`.
"""
