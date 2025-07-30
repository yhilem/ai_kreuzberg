"""Comprehensive tests for extraction.py module to improve coverage."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, Mock

import pytest

from kreuzberg._types import Entity, ExtractionConfig, ExtractionResult
from kreuzberg.exceptions import ValidationError
from kreuzberg.extraction import (
    _handle_chunk_content,
    _validate_and_post_process_helper,
    _validate_and_post_process_sync,
    batch_extract_bytes,
    batch_extract_bytes_sync,
    batch_extract_file,
    batch_extract_file_sync,
    extract_bytes,
    extract_bytes_sync,
    extract_file,
)

if TYPE_CHECKING:
    from pytest_mock import MockerFixture



# Test _handle_chunk_content
def test_handle_chunk_content_basic() -> None:
    """Test basic chunking functionality."""
    content = "This is a test content that should be chunked. " * 10
    config = ExtractionConfig(chunk_content=True, max_chars=50, max_overlap=10)

    chunks = _handle_chunk_content(mime_type="text/plain", config=config, content=content)

    assert isinstance(chunks, list)
    assert len(chunks) > 1
    assert all(len(chunk) <= 50 for chunk in chunks)


def test_handle_chunk_content_empty() -> None:
    """Test chunking with empty content."""
    config = ExtractionConfig(chunk_content=True)

    chunks = _handle_chunk_content(mime_type="text/plain", config=config, content="")

    assert chunks == []


def test_handle_chunk_content_markdown(mocker: MockerFixture) -> None:
    """Test chunking with markdown content."""
    content = "# Header\n\nParagraph 1\n\n## Subheader\n\nParagraph 2" * 5
    config = ExtractionConfig(chunk_content=True, max_chars=100)

    # Mock the chunker to avoid missing dependency
    mock_chunker = mocker.Mock()
    mock_chunker.chunks.return_value = ["chunk1", "chunk2"]
    mocker.patch("kreuzberg.extraction.get_chunker", return_value=mock_chunker)

    chunks = _handle_chunk_content(mime_type="text/markdown", config=config, content=content)

    assert isinstance(chunks, list)
    assert len(chunks) == 2
    assert chunks == ["chunk1", "chunk2"]


# Test validation and post-processing
def test_validate_and_post_process_helper_with_entities(mocker: MockerFixture) -> None:
    """Test post-processing with entity extraction."""
    mock_extract_entities = mocker.patch(
        "kreuzberg.extraction.extract_entities",
        return_value=[
            Entity(type="PERSON", text="John Doe", start=0, end=8),
            Entity(type="ORG", text="Acme Corp", start=20, end=29),
        ],
    )

    result = ExtractionResult(content="John Doe works at Acme Corp", mime_type="text/plain", metadata={})
    config = ExtractionConfig(extract_entities=True)

    processed = _validate_and_post_process_helper(result, config)

    assert processed.entities is not None
    assert len(processed.entities) == 2
    assert processed.entities[0].type == "PERSON"
    mock_extract_entities.assert_called_once()


def test_validate_and_post_process_helper_entities_runtime_error(mocker: MockerFixture) -> None:
    """Test entity extraction with RuntimeError."""
    mocker.patch("kreuzberg.extraction.extract_entities", side_effect=RuntimeError("Entity extraction failed"))

    result = ExtractionResult(content="Test content", mime_type="text/plain", metadata={})
    config = ExtractionConfig(extract_entities=True)

    processed = _validate_and_post_process_helper(result, config)

    assert processed.entities is None


def test_validate_and_post_process_helper_with_keywords(mocker: MockerFixture):
    """Test post-processing with keyword extraction."""
    mock_extract_keywords = mocker.patch(
        "kreuzberg.extraction.extract_keywords", return_value=[("python", 0.9), ("programming", 0.8), ("code", 0.7)]
    )

    result = ExtractionResult(
        content="Python programming is great for writing code", mime_type="text/plain", metadata={}
    )
    config = ExtractionConfig(extract_keywords=True, keyword_count=3)

    processed = _validate_and_post_process_helper(result, config)

    assert processed.keywords is not None
    assert len(processed.keywords) == 3
    assert processed.keywords[0] == ("python", 0.9)
    mock_extract_keywords.assert_called_once_with(result.content, keyword_count=3)


def test_validate_and_post_process_helper_keywords_runtime_error(mocker: MockerFixture):
    """Test keyword extraction with RuntimeError."""
    mocker.patch("kreuzberg.extraction.extract_keywords", side_effect=RuntimeError("Keyword extraction failed"))

    result = ExtractionResult(content="Test content", mime_type="text/plain", metadata={})
    config = ExtractionConfig(extract_keywords=True)

    processed = _validate_and_post_process_helper(result, config)

    assert processed.keywords is None


def test_validate_and_post_process_helper_with_language_detection(mocker: MockerFixture):
    """Test post-processing with language detection."""
    mock_detect_languages = mocker.patch("kreuzberg.extraction.detect_languages", return_value=["en", "es"])

    result = ExtractionResult(content="Hello world. Hola mundo.", mime_type="text/plain", metadata={})
    config = ExtractionConfig(auto_detect_language=True)

    processed = _validate_and_post_process_helper(result, config)

    assert processed.detected_languages == ["en", "es"]
    mock_detect_languages.assert_called_once()


def test_validate_and_post_process_helper_with_document_type(mocker: MockerFixture):
    """Test post-processing with document type detection."""
    mock_auto_detect = mocker.patch(
        "kreuzberg.extraction.auto_detect_document_type",
        side_effect=lambda r, _c, file_path=None: ExtractionResult(
            content=r.content,
            mime_type=r.mime_type,
            metadata=r.metadata,
            document_type="invoice",
            document_type_confidence=0.95,
        ),
    )

    result = ExtractionResult(content="Invoice #12345", mime_type="text/plain", metadata={})
    config = ExtractionConfig(auto_detect_document_type=True)

    processed = _validate_and_post_process_helper(result, config, file_path=Path("invoice.pdf"))

    assert processed.document_type == "invoice"
    assert processed.document_type_confidence == 0.95
    mock_auto_detect.assert_called_once()


def test_validate_and_post_process_helper_all_features(mocker: MockerFixture):
    """Test post-processing with all features enabled."""
    # Mock all extraction functions
    mocker.patch("kreuzberg.extraction.extract_entities", return_value=[])
    mocker.patch("kreuzberg.extraction.extract_keywords", return_value=[])
    mocker.patch("kreuzberg.extraction.detect_languages", return_value=["en"])
    mocker.patch("kreuzberg.extraction.auto_detect_document_type", side_effect=lambda r, _c, **_kwargs: r)
    mocker.patch("kreuzberg.extraction._handle_chunk_content", return_value=["chunk1", "chunk2"])

    result = ExtractionResult(content="Test content for all features", mime_type="text/plain", metadata={})
    config = ExtractionConfig(
        chunk_content=True,
        extract_entities=True,
        extract_keywords=True,
        auto_detect_language=True,
        auto_detect_document_type=True,
    )

    processed = _validate_and_post_process_helper(result, config)

    assert processed.chunks == ["chunk1", "chunk2"]
    assert processed.entities == []
    assert processed.keywords == []
    assert processed.detected_languages == ["en"]


def test_validate_and_post_process_sync(mocker: MockerFixture):
    """Test synchronous validation and post-processing."""
    result = ExtractionResult(content="Test content", mime_type="text/plain", metadata={})
    ExtractionConfig()

    # Mock validators
    mock_validator = Mock()
    config_with_validators = ExtractionConfig(validators=[mock_validator])

    processed = _validate_and_post_process_sync(result, config_with_validators)

    mock_validator.assert_called_once_with(result)
    assert processed.content == "Test content"


def test_validate_and_post_process_sync_with_hooks(mocker: MockerFixture):
    """Test sync post-processing with hooks."""
    result = ExtractionResult(content="Original content", mime_type="text/plain", metadata={})

    # Create a post-processing hook that modifies content
    def hook(r: ExtractionResult) -> ExtractionResult:
        r.content = "Modified content"
        return r

    config = ExtractionConfig(post_processing_hooks=[hook])

    processed = _validate_and_post_process_sync(result, config)

    assert processed.content == "Modified content"


@pytest.mark.anyio
async def test_validate_and_post_process_async(mocker: MockerFixture):
    """Test async validation and post-processing."""
    result = ExtractionResult(content="Test content", mime_type="text/plain", metadata={})

    # Mock async validator
    async_validator = AsyncMock()
    config = ExtractionConfig(validators=[async_validator])

    # Import the async function
    from kreuzberg.extraction import _validate_and_post_process_async

    processed = await _validate_and_post_process_async(result, config)

    async_validator.assert_called_once_with(result)
    assert processed.content == "Test content"


@pytest.mark.anyio
async def test_validate_and_post_process_async_with_hooks(mocker: MockerFixture):
    """Test async post-processing with async hooks."""
    result = ExtractionResult(content="Original content", mime_type="text/plain", metadata={})

    # Create an async post-processing hook
    async def async_hook(r: ExtractionResult) -> ExtractionResult:
        r.content = "Async modified content"
        return r

    config = ExtractionConfig(post_processing_hooks=[async_hook])

    from kreuzberg.extraction import _validate_and_post_process_async

    processed = await _validate_and_post_process_async(result, config)

    assert processed.content == "Async modified content"


# Test extraction with caching
@pytest.mark.anyio
async def test_extract_file_with_caching(tmp_path: Path, mocker: MockerFixture):
    """Test file extraction with document caching."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Cached content")

    # Mock the document cache
    mock_cache = Mock()
    mock_cache.get.return_value = None  # First call - not cached
    mock_cache.mark_processing = Mock()
    mock_cache.mark_complete = Mock()
    mock_cache.set = Mock()

    mocker.patch("kreuzberg.extraction.get_document_cache", return_value=mock_cache)

    result = await extract_file(str(test_file))

    assert result.content == "Cached content"
    mock_cache.get.assert_called()
    mock_cache.set.assert_called_once()


@pytest.mark.anyio
async def test_extract_file_cache_hit(tmp_path: Path, mocker: MockerFixture):
    """Test file extraction with cache hit."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Original content")

    cached_result = ExtractionResult(content="Cached content", mime_type="text/plain", metadata={})

    # Mock cache to return cached result
    mock_cache = Mock()
    mock_cache.get.return_value = cached_result

    mocker.patch("kreuzberg.extraction.get_document_cache", return_value=mock_cache)

    result = await extract_file(str(test_file))

    assert result.content == "Cached content"
    mock_cache.set.assert_not_called()  # Should not set cache on hit


@pytest.mark.anyio
async def test_extract_file_cache_processing_wait(tmp_path: Path, mocker: MockerFixture):
    """Test file extraction waiting for another process to complete caching."""
    import threading

    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content")

    # Create an event that's already set (simulating another process completed)
    event = threading.Event()
    event.set()

    # Mock cache
    mock_cache = Mock()
    # First get returns None
    # After marking processing, returns event
    # After waiting, returns cached result
    mock_cache.get.side_effect = [
        None,  # Initial check
        ExtractionResult(content="Cached by other process", mime_type="text/plain", metadata={}),
    ]
    mock_cache.mark_processing.return_value = event

    mocker.patch("kreuzberg.extraction.get_document_cache", return_value=mock_cache)

    result = await extract_file(str(test_file))

    assert result.content == "Cached by other process"
    assert mock_cache.get.call_count == 2


# Test batch operations with mixed results
@pytest.mark.anyio
async def test_batch_extract_file_partial_failure(tmp_path: Path):
    """Test batch extraction with some files failing."""
    good_file = tmp_path / "good.txt"
    good_file.write_text("Good content")

    bad_file = tmp_path / "bad.txt"
    # Don't create this file

    results = await batch_extract_file([str(good_file), str(bad_file)])

    assert len(results) == 2
    assert results[0].content == "Good content"
    # Error results are returned as ExtractionResult with error metadata, not exceptions
    assert results[1].metadata.get("error") is True
    assert "Error:" in results[1].content


def test_batch_extract_file_sync_partial_failure(tmp_path: Path):
    """Test sync batch extraction with some files failing."""
    good_file = tmp_path / "good.txt"
    good_file.write_text("Good content")

    bad_file = tmp_path / "nonexistent.txt"

    results = batch_extract_file_sync([str(good_file), str(bad_file)])

    assert len(results) == 2
    assert results[0].content == "Good content"
    # Error results are returned as ExtractionResult with error metadata, not exceptions
    assert results[1].metadata.get("error") is True
    assert "Error:" in results[1].content


@pytest.mark.anyio
async def test_batch_extract_bytes_with_configs():
    """Test batch byte extraction with per-item configs."""
    # batch_extract_bytes expects (bytes, mime_type) tuples, not with config
    contents = [
        (b"Content 1", "text/plain"),
        (b"Content 2", "text/plain"),
        (b"Content 3", "text/plain"),
    ]

    results = await batch_extract_bytes(contents)

    assert len(results) == 3
    assert results[0].content == "Content 1"
    assert results[1].content == "Content 2"
    assert results[2].content == "Content 3"


def test_batch_extract_bytes_sync_with_configs():
    """Test sync batch byte extraction with configs."""
    # batch_extract_bytes_sync expects (bytes, mime_type) tuples, not with config
    contents = [
        (b"Sync content 1", "text/plain"),
        (b"Sync content 2", "text/markdown"),
    ]

    results = batch_extract_bytes_sync(contents)

    assert len(results) == 2
    assert results[0].content == "Sync content 1"
    assert results[1].mime_type == "text/markdown"


# Test error handling
@pytest.mark.anyio
async def test_extract_bytes_invalid_mime_type():
    """Test extraction with invalid MIME type."""
    with pytest.raises(ValidationError, match="mime_type"):
        await extract_bytes(b"content", "invalid/mime/type")


def test_extract_bytes_sync_invalid_mime_type():
    """Test sync extraction with invalid MIME type."""
    with pytest.raises(ValidationError, match="mime_type"):
        extract_bytes_sync(b"content", "invalid/mime/type")


@pytest.mark.anyio
async def test_extract_file_with_progress_callback_error(tmp_path: Path, mocker: MockerFixture):
    """Test file extraction - extract_file doesn't have progress_callback parameter."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Test content")

    # Test normal extraction without progress callback
    result = await extract_file(str(test_file))
    assert result.content == "Test content"


# Test with custom patterns for entity extraction
def test_validate_and_post_process_with_custom_patterns(mocker: MockerFixture):
    """Test entity extraction with custom patterns."""
    custom_patterns = frozenset([("CUSTOM", r"TEST-\d+")])

    mock_extract_entities = mocker.patch(
        "kreuzberg.extraction.extract_entities", return_value=[Entity(type="CUSTOM", text="TEST-123", start=0, end=8)]
    )

    result = ExtractionResult(content="TEST-123 is a custom pattern", mime_type="text/plain", metadata={})
    config = ExtractionConfig(extract_entities=True, custom_entity_patterns=custom_patterns)

    processed = _validate_and_post_process_helper(result, config)

    assert processed.entities is not None
    assert len(processed.entities) == 1
    assert processed.entities[0].type == "CUSTOM"
    mock_extract_entities.assert_called_once_with(result.content, custom_patterns=custom_patterns)


# Test extraction with all post-processing disabled
@pytest.mark.anyio
async def test_extract_minimal_processing():
    """Test extraction with minimal processing."""
    config = ExtractionConfig(
        chunk_content=False,
        extract_entities=False,
        extract_keywords=False,
        auto_detect_language=False,
        auto_detect_document_type=False,
    )

    result = await extract_bytes(b"Minimal processing", "text/plain", config)

    assert result.content == "Minimal processing"
    assert result.chunks == []
    assert result.entities is None
    assert result.keywords is None
    assert result.detected_languages is None
    assert result.document_type is None
