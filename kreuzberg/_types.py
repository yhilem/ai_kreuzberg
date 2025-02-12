from __future__ import annotations

import sys
from typing import NamedTuple, TypedDict

if sys.version_info < (3, 10):
    from typing_extensions import NotRequired
else:
    from typing import NotRequired


class Metadata(TypedDict, total=False):
    """Document metadata.

    All fields are optional but will only be included if they contain non-empty values.
    Any field that would be empty or None is omitted from the dictionary.

    Different documents and extraction methods will yield different metadata.
    """

    title: NotRequired[str]
    """Document title."""
    subtitle: NotRequired[str]
    """Document subtitle."""
    abstract: NotRequired[str | list[str]]
    """Document abstract, summary or description."""
    authors: NotRequired[list[str]]
    """List of document authors."""
    date: NotRequired[str]
    """Document date as string to preserve original format."""
    subject: NotRequired[str]
    """Document subject or topic."""
    description: NotRequired[str]
    """Extended description."""
    keywords: NotRequired[list[str]]
    """Keywords or tags."""
    categories: NotRequired[list[str]]
    """Categories or classifications."""
    version: NotRequired[str]
    """Version identifier."""
    language: NotRequired[str]
    """Document language code."""
    references: NotRequired[list[str]]
    """Reference entries."""
    citations: NotRequired[list[str]]
    """Citation identifiers."""
    copyright: NotRequired[str]
    """Copyright information."""
    license: NotRequired[str]
    """License information."""
    identifier: NotRequired[str]
    """Document identifier."""
    publisher: NotRequired[str]
    """Publisher name."""
    contributors: NotRequired[list[str]]
    """Additional contributors."""
    creator: NotRequired[str]
    """Document creator."""
    institute: NotRequired[str | list[str]]
    """Institute or organization."""


class ExtractionResult(NamedTuple):
    """The result of a file extraction."""

    content: str
    """The extracted content."""
    mime_type: str
    """The mime type of the content."""
    metadata: Metadata
    """The metadata of the content."""
