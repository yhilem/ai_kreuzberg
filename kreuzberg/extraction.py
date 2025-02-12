"""This module provides functions to extract textual content from files.

It includes vendored code:

- The extract PPTX logic is based on code vendored from `markitdown` to extract text from PPTX files.
    See: https://github.com/microsoft/markitdown/blob/main/src/markitdown/_markitdown.py
    Refer to the markitdown repository for it's license (MIT).
"""

from __future__ import annotations

from mimetypes import guess_type
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

import anyio
from anyio import Path as AsyncPath

from kreuzberg import ExtractionResult
from kreuzberg._html import extract_html_string
from kreuzberg._mime_types import (
    EXCEL_MIME_TYPE,
    HTML_MIME_TYPE,
    IMAGE_MIME_TYPE_EXT_MAP,
    IMAGE_MIME_TYPES,
    PANDOC_SUPPORTED_MIME_TYPES,
    PDF_MIME_TYPE,
    POWER_POINT_MIME_TYPE,
    SUPPORTED_MIME_TYPES,
)
from kreuzberg._pandoc import process_content_with_pandoc, process_file_with_pandoc
from kreuzberg._pdf import (
    extract_pdf_content,
    extract_pdf_file,
)
from kreuzberg._pptx import extract_pptx_file_content
from kreuzberg._string import safe_decode
from kreuzberg._tesseract import process_image_with_tesseract
from kreuzberg._xlsx import extract_xlsx_content, extract_xlsx_file
from kreuzberg.config import Config, default_config
from kreuzberg.exceptions import ValidationError

if TYPE_CHECKING:
    from os import PathLike


async def extract_bytes(
    content: bytes,
    mime_type: str,
    *,
    force_ocr: bool = False,
    config: Config | None = None,
) -> ExtractionResult:
    """Extract the textual content from a given byte string representing a file's contents.

    Args:
        content: The content to extract.
        mime_type: The mime type of the content.
        force_ocr: Whether to force OCR on PDF files that have a text layer.
        config: Configuration for text extraction.

    Raises:
        ValidationError: If the mime type is not supported.

    Returns:
        The extracted content and the mime type of the content.
    """
    if mime_type not in SUPPORTED_MIME_TYPES or not any(mime_type.startswith(value) for value in SUPPORTED_MIME_TYPES):
        raise ValidationError(
            f"Unsupported mime type: {mime_type}",
            context={"mime_type": mime_type, "supported_mimetypes": ",".join(sorted(SUPPORTED_MIME_TYPES))},
        )

    if mime_type == PDF_MIME_TYPE or mime_type.startswith(PDF_MIME_TYPE):
        return await extract_pdf_content(content, force_ocr=force_ocr, config=config)

    if mime_type == EXCEL_MIME_TYPE or mime_type.startswith(EXCEL_MIME_TYPE):
        return await extract_xlsx_content(content)

    if mime_type in IMAGE_MIME_TYPES or any(mime_type.startswith(value) for value in IMAGE_MIME_TYPES):
        with NamedTemporaryFile(suffix=IMAGE_MIME_TYPE_EXT_MAP[mime_type]) as temp_file:
            temp_file.write(content)
            return await process_image_with_tesseract(temp_file.name, config=config or default_config)

    if mime_type in PANDOC_SUPPORTED_MIME_TYPES or any(
        mime_type.startswith(value) for value in PANDOC_SUPPORTED_MIME_TYPES
    ):
        return await process_content_with_pandoc(content=content, mime_type=mime_type)

    if mime_type == POWER_POINT_MIME_TYPE or mime_type.startswith(POWER_POINT_MIME_TYPE):
        return await extract_pptx_file_content(content)

    if mime_type == HTML_MIME_TYPE or mime_type.startswith(HTML_MIME_TYPE):
        return await extract_html_string(content)

    return ExtractionResult(
        content=safe_decode(content),
        mime_type=mime_type,
        metadata={},
    )


def extract_bytes_sync(
    content: bytes,
    mime_type: str,
    *,
    config: Config | None = None,
    force_ocr: bool = False,
) -> ExtractionResult:
    """Synchronous version of extract_bytes.

    Args:
        content: The content to extract.
        mime_type: The mime type of the content.
        config: Optional configuration for text extraction.
        force_ocr: Whether or not to force OCR on PDF files that have a text layer.

    Returns:
        The extracted content and the mime type of the content.
    """
    return anyio.run(lambda: extract_bytes(content, mime_type, config=config, force_ocr=force_ocr))


def extract_file_sync(
    file_path: Path | str,
    mime_type: str | None = None,
    *,
    config: Config | None = None,
    force_ocr: bool = False,
) -> ExtractionResult:
    """Synchronous version of extract_file.

    Args:
        file_path: The path to the file.
        mime_type: The mime type of the file.
        config: Optional configuration for text extraction.
        force_ocr: Whether to force OCR on PDF files that have a text layer.

    Returns:
        The extracted content and the mime type of the content.
    """
    return anyio.run(lambda: extract_file(file_path, mime_type, config=config, force_ocr=force_ocr))


async def extract_file(
    file_path: PathLike[str] | str,
    mime_type: str | None = None,
    *,
    force_ocr: bool = False,
    config: Config | None = None,
) -> ExtractionResult:
    """Extract the textual content from a given file.

    Args:
        file_path: The path to the file.
        mime_type: The mime type of the file.
        force_ocr: Whether  to force OCR on PDF files that have a text layer.
        config: Configuration for text extraction.

    Raises:
        ValidationError: If the mime type is not supported.

    Returns:
        The extracted content and the mime type of the content.
    """
    input_file = await AsyncPath(file_path).resolve()

    mime_type = mime_type or guess_type(input_file.name)[0]
    if not mime_type:  # pragma: no cover
        raise ValidationError("Could not determine the mime type of the file.", context={"input_file": str(input_file)})

    if mime_type not in SUPPORTED_MIME_TYPES or not any(mime_type.startswith(value) for value in SUPPORTED_MIME_TYPES):
        raise ValidationError(
            f"Unsupported mime type: {mime_type}",
            context={"mime_type": mime_type, "supported_mimetypes": ",".join(sorted(SUPPORTED_MIME_TYPES))},
        )

    if not await input_file.exists():
        raise ValidationError("The file does not exist.", context={"input_file": str(input_file)})

    if mime_type == PDF_MIME_TYPE or mime_type.startswith(PDF_MIME_TYPE):
        return await extract_pdf_file(Path(input_file), force_ocr=force_ocr, config=config)

    if mime_type == EXCEL_MIME_TYPE or mime_type.startswith(EXCEL_MIME_TYPE):
        return await extract_xlsx_file(Path(input_file))

    if mime_type in IMAGE_MIME_TYPES or any(mime_type.startswith(value) for value in IMAGE_MIME_TYPES):
        return await process_image_with_tesseract(input_file, config=config or default_config)

    if mime_type in PANDOC_SUPPORTED_MIME_TYPES or any(
        mime_type.startswith(value) for value in PANDOC_SUPPORTED_MIME_TYPES
    ):
        return await process_file_with_pandoc(input_file=input_file, mime_type=mime_type)

    if mime_type == POWER_POINT_MIME_TYPE or mime_type.startswith(POWER_POINT_MIME_TYPE):
        return await extract_pptx_file_content(Path(input_file))

    if mime_type == HTML_MIME_TYPE or mime_type.startswith(HTML_MIME_TYPE):
        return await extract_html_string(Path(input_file))

    return ExtractionResult(content=safe_decode(await input_file.read_bytes()), mime_type=mime_type, metadata={})
