from pathlib import Path

import pytest

from kreuzberg._playa import extract_pdf_metadata


@pytest.mark.anyio
async def test_extract_pdf_metadata_test_article(test_article: Path) -> None:
    content = test_article.read_bytes()
    metadata = await extract_pdf_metadata(content)

    assert isinstance(metadata, dict)
    assert metadata.get("title") == "Inverted Honor"
    assert metadata.get("authors") == ["Na'aman Hirschfeld"]
    assert metadata.get("subject") == "The Treatment of Honor in The Life of Estevanillo Gonzales"
    assert "created_at" in metadata
    assert metadata.get("created_by") == "Writer (Producer: OpenOffice.org 3.1)"
    assert metadata.get("width") == 595
    assert metadata.get("height") == 842
    assert metadata.get("description") == "Table of Contents:\n- Bibliography"
    assert "summary" in metadata
    assert "PDF document with 28 pages" in metadata["summary"]


@pytest.mark.anyio
async def test_extract_pdf_metadata_searchable(searchable_pdf: Path) -> None:
    content = searchable_pdf.read_bytes()
    metadata = await extract_pdf_metadata(content)

    assert isinstance(metadata, dict)

    assert "width" in metadata
    assert "height" in metadata
    assert "summary" in metadata

    assert "PDF document with" in metadata["summary"]

    assert "printable" in metadata["summary"]
    assert "extractable" in metadata["summary"]


@pytest.mark.anyio
async def test_extract_pdf_metadata_non_searchable(non_searchable_pdf: Path) -> None:
    content = non_searchable_pdf.read_bytes()
    metadata = await extract_pdf_metadata(content)

    assert isinstance(metadata, dict)
    assert "width" in metadata
    assert "height" in metadata
    assert "summary" in metadata

    assert "PDF document with" in metadata["summary"]


@pytest.mark.anyio
async def test_extract_pdf_metadata_non_ascii(non_ascii_pdf: Path) -> None:
    content = non_ascii_pdf.read_bytes()
    metadata = await extract_pdf_metadata(content)

    assert isinstance(metadata, dict)
    assert "width" in metadata
    assert "height" in metadata
    assert "summary" in metadata

    assert "PDF version" in metadata["summary"]


@pytest.mark.anyio
async def test_extract_pdf_metadata_scanned(scanned_pdf: Path) -> None:
    content = scanned_pdf.read_bytes()
    metadata = await extract_pdf_metadata(content)

    assert isinstance(metadata, dict)
    assert "width" in metadata
    assert "height" in metadata
    assert "summary" in metadata

    assert "PDF document with" in metadata["summary"]

    assert "PDF version" in metadata["summary"]


@pytest.mark.anyio
async def test_extract_pdf_metadata_contract(test_contract: Path) -> None:
    content = test_contract.read_bytes()
    metadata = await extract_pdf_metadata(content)

    assert isinstance(metadata, dict)
    assert "width" in metadata
    assert "height" in metadata
    assert "summary" in metadata

    assert "PDF document with" in metadata["summary"]

    assert len(metadata["summary"]) > 20


@pytest.mark.anyio
async def test_extract_pdf_metadata_error_handling() -> None:
    from unittest.mock import patch

    from kreuzberg.exceptions import ParsingError

    with patch("kreuzberg._playa.parse", side_effect=ValueError("Test error")), pytest.raises(ParsingError):
        await extract_pdf_metadata(b"test content")

    result = await extract_pdf_metadata(b"not a valid PDF")
    assert isinstance(result, dict)

    assert "summary" in result
