"""Tests for Excel extraction functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from kreuzberg._xlsx import extract_xlsx_file
from kreuzberg.exceptions import ParsingError


async def test_extract_xlsx_file(excel_document: Path) -> None:
    """Test extracting text from an Excel file."""
    result = await extract_xlsx_file(excel_document)
    assert isinstance(result.content, str)
    assert result.content.strip()
    assert result.mime_type == "text/markdown"


async def test_extract_xlsx_file_invalid() -> None:
    """Test that attempting to extract from an invalid Excel file raises an error."""
    with pytest.raises(ParsingError) as exc_info:
        await extract_xlsx_file(Path("/invalid/path.xlsx"))

    assert "Could not extract text from XLSX" in str(exc_info.value)
