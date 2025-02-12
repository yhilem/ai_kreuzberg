"""Tests for PDF extraction functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from kreuzberg import ExtractionResult
from kreuzberg._pdf import (
    _convert_pdf_to_images,
    _extract_pdf_searchable_text,
    _extract_pdf_text_with_ocr,
    extract_pdf_file,
)
from kreuzberg.exceptions import ParsingError


async def test_extract_pdf_searchable_text(searchable_pdf: Path) -> None:
    """Test extracting text from a searchable PDF."""
    result = await _extract_pdf_searchable_text(searchable_pdf)
    assert isinstance(result, str)
    assert result.strip()


async def test_extract_pdf_text_with_ocr(scanned_pdf: Path) -> None:
    """Test extracting text from a scanned PDF using OCR."""
    result = await _extract_pdf_text_with_ocr(scanned_pdf)
    assert isinstance(result, ExtractionResult)
    assert result.content.strip()


@pytest.mark.timeout(timeout=60)
async def test_extract_pdf_file(searchable_pdf: Path) -> None:
    """Test extracting text from a PDF file."""
    result = await extract_pdf_file(searchable_pdf)
    assert isinstance(result.content, str)
    assert result.content.strip()
    assert result.mime_type == "text/plain"


async def test_extract_pdf_file_non_searchable(non_searchable_pdf: Path) -> None:
    """Test extracting text from a non-searchable PDF file."""
    result = await extract_pdf_file(non_searchable_pdf)
    assert isinstance(result.content, str)
    assert result.content.strip()
    assert result.mime_type == "text/plain"


async def test_extract_pdf_file_invalid() -> None:
    """Test that attempting to extract from an invalid PDF raises an error."""
    with pytest.raises(FileNotFoundError):
        await extract_pdf_file(Path("/invalid/path.pdf"))


async def test_convert_pdf_to_images_raises_parsing_error(tmp_path: Path) -> None:
    """Test that attempting to convert an invalid PDF to images raises a ParsingError."""
    pdf_path = tmp_path / "invalid.pdf"
    pdf_path.write_text("invalid pdf content")

    with pytest.raises(ParsingError) as exc_info:
        await _convert_pdf_to_images(pdf_path)

    assert "Could not convert PDF to images" in str(exc_info.value)
    assert str(pdf_path) in str(exc_info.value.context["file_path"])


async def test_extract_pdf_searchable_text_raises_parsing_error(tmp_path: Path) -> None:
    """Test that attempting to extract text from an invalid PDF raises a ParsingError."""
    pdf_path = tmp_path / "invalid.pdf"
    pdf_path.write_text("invalid pdf content")

    with pytest.raises(ParsingError) as exc_info:
        await _extract_pdf_searchable_text(pdf_path)

    assert "Could not extract text from PDF file" in str(exc_info.value)
    assert str(pdf_path) in str(exc_info.value.context["file_path"])
