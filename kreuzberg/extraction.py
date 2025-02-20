"""This module provides functions to extract textual content from files.

It includes vendored code:

- The extract PPTX logic is based on code vendored from `markitdown` to extract text from PPTX files.
    See: https://github.com/microsoft/markitdown/blob/main/src/markitdown/_markitdown.py
    Refer to the markitdown repository for it's license (MIT).
"""

from __future__ import annotations

from functools import partial
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, cast

import anyio
from anyio import Path as AsyncPath
from PIL.Image import open as open_image

from kreuzberg import ExtractionResult
from kreuzberg._constants import DEFAULT_MAX_PROCESSES
from kreuzberg._html import extract_html_string
from kreuzberg._mime_types import (
    EXCEL_MIME_TYPE,
    HTML_MIME_TYPE,
    IMAGE_MIME_TYPES,
    PANDOC_SUPPORTED_MIME_TYPES,
    PDF_MIME_TYPE,
    POWER_POINT_MIME_TYPE,
    SUPPORTED_MIME_TYPES,
    validate_mime_type,
)
from kreuzberg._pandoc import process_content_with_pandoc, process_file_with_pandoc
from kreuzberg._pdf import (
    extract_pdf_content,
    extract_pdf_file,
)
from kreuzberg._pptx import extract_pptx_file_content
from kreuzberg._string import safe_decode
from kreuzberg._tesseract import PSMMode, process_image_with_tesseract
from kreuzberg._xlsx import extract_xlsx_content, extract_xlsx_file
from kreuzberg.exceptions import ValidationError

if TYPE_CHECKING:
    from collections.abc import Sequence
    from os import PathLike


async def extract_bytes(
    content: bytes,
    mime_type: str,
    *,
    force_ocr: bool = False,
    language: str = "eng",
    max_processes: int = DEFAULT_MAX_PROCESSES,
    psm: PSMMode = PSMMode.AUTO,
) -> ExtractionResult:
    """Extract the textual content from a given byte string representing a file's contents.

    Args:
        content: The content to extract.
        mime_type: The mime type of the content.
        force_ocr: Whether to force OCR on PDF files that have a text layer.
        language: The language code for OCR. Defaults to "eng".
        max_processes: Maximum number of concurrent processes. Defaults to CPU count / 2 (minimum 1).
        psm: Page segmentation mode for Tesseract OCR. Defaults to PSMMode.AUTO.

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
        return await extract_pdf_content(
            content, force_ocr=force_ocr, max_processes=max_processes, psm=psm, language=language
        )

    if mime_type == EXCEL_MIME_TYPE or mime_type.startswith(EXCEL_MIME_TYPE):
        return await extract_xlsx_content(content)

    if mime_type in IMAGE_MIME_TYPES or any(mime_type.startswith(value) for value in IMAGE_MIME_TYPES):
        return await process_image_with_tesseract(open_image(BytesIO(content)), psm=psm, language=language)

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


async def extract_file(
    file_path: PathLike[str] | str,
    mime_type: str | None = None,
    *,
    force_ocr: bool = False,
    language: str = "eng",
    max_processes: int = DEFAULT_MAX_PROCESSES,
    psm: PSMMode = PSMMode.AUTO,
) -> ExtractionResult:
    """Extract the textual content from a given file.

    Args:
        file_path: The path to the file.
        mime_type: The mime type of the content.
        force_ocr: Whether to force OCR on PDF files that have a text layer.
        language: The language code for OCR. Defaults to "eng".
        max_processes: Maximum number of concurrent processes. Defaults to CPU count / 2 (minimum 1).
        psm: Page segmentation mode for Tesseract OCR. Defaults to PSMMode.AUTO.

    Raises:
        ValidationError: If the mime type is not supported.

    Returns:
        The extracted content and the mime type of the content.
    """
    input_file = await AsyncPath(file_path).resolve()

    mime_type = validate_mime_type(input_file, mime_type)

    if not await input_file.exists():
        raise ValidationError("The file does not exist.", context={"input_file": str(input_file)})

    if mime_type == PDF_MIME_TYPE or mime_type.startswith(PDF_MIME_TYPE):
        return await extract_pdf_file(
            Path(input_file), force_ocr=force_ocr, max_processes=max_processes, psm=psm, language=language
        )

    if mime_type == EXCEL_MIME_TYPE or mime_type.startswith(EXCEL_MIME_TYPE):
        return await extract_xlsx_file(Path(input_file))

    if mime_type in IMAGE_MIME_TYPES or any(mime_type.startswith(value) for value in IMAGE_MIME_TYPES):
        return await process_image_with_tesseract(input_file, psm=psm, language=language)

    if mime_type in PANDOC_SUPPORTED_MIME_TYPES or any(
        mime_type.startswith(value) for value in PANDOC_SUPPORTED_MIME_TYPES
    ):
        return await process_file_with_pandoc(input_file=input_file, mime_type=mime_type)

    if mime_type == POWER_POINT_MIME_TYPE or mime_type.startswith(POWER_POINT_MIME_TYPE):
        return await extract_pptx_file_content(Path(input_file))

    if mime_type == HTML_MIME_TYPE or mime_type.startswith(HTML_MIME_TYPE):
        return await extract_html_string(Path(input_file))

    return ExtractionResult(content=safe_decode(await input_file.read_bytes()), mime_type=mime_type, metadata={})


async def batch_extract_file(
    file_paths: Sequence[PathLike[str] | str],
    *,
    force_ocr: bool = False,
    language: str = "eng",
    max_processes: int = DEFAULT_MAX_PROCESSES,
    psm: PSMMode = PSMMode.AUTO,
) -> list[ExtractionResult]:
    """Extract text from multiple files concurrently.

    Args:
        file_paths: A sequence of paths to files to extract text from.
        force_ocr: Whether to force OCR on PDF files that have a text layer.
        language: The language code for OCR. Defaults to "eng".
        max_processes: Maximum number of concurrent processes. Defaults to CPU count / 2 (minimum 1).
        psm: Page segmentation mode for Tesseract OCR. Defaults to PSMMode.AUTO.

    Returns:
        A list of extraction results in the same order as the input paths.
    """
    results = cast(list[ExtractionResult], ([None] * len(file_paths)))

    async def _extract_file(path: PathLike[str] | str, index: int) -> None:
        result = await extract_file(
            path,
            force_ocr=force_ocr,
            max_processes=max_processes,
            psm=psm,
            language=language,
        )
        results[index] = result

    async with anyio.create_task_group() as tg:
        for i, path in enumerate(file_paths):
            tg.start_soon(_extract_file, path, i)

    return results


async def batch_extract_bytes(
    contents: Sequence[tuple[bytes, str]],
    *,
    force_ocr: bool = False,
    language: str = "eng",
    max_processes: int = DEFAULT_MAX_PROCESSES,
    psm: PSMMode = PSMMode.AUTO,
) -> list[ExtractionResult]:
    """Extract text from multiple byte contents concurrently.

    Args:
        contents: A sequence of tuples containing (content, mime_type) pairs.
        force_ocr: Whether to force OCR on PDF files that have a text layer.
        language: The language code for OCR. Defaults to "eng".
        max_processes: Maximum number of concurrent processes. Defaults to CPU count / 2 (minimum 1).
        psm: Page segmentation mode for Tesseract OCR. Defaults to PSMMode.AUTO.

    Returns:
        A list of extraction results in the same order as the input contents.
    """
    results = cast(list[ExtractionResult], [None] * len(contents))

    async def _extract_bytes(content: bytes, mime_type: str, index: int) -> None:
        result = await extract_bytes(
            content,
            mime_type,
            force_ocr=force_ocr,
            max_processes=max_processes,
            psm=psm,
            language=language,
        )
        results[index] = result

    async with anyio.create_task_group() as tg:
        for i, (content, mime_type) in enumerate(contents):
            tg.start_soon(_extract_bytes, content, mime_type, i)

    return results


### Sync proxies


def extract_bytes_sync(
    content: bytes,
    mime_type: str,
    *,
    force_ocr: bool = False,
    language: str = "eng",
    max_processes: int = DEFAULT_MAX_PROCESSES,
    psm: PSMMode = PSMMode.AUTO,
) -> ExtractionResult:
    """Synchronous version of extract_bytes.

    Args:
        content: The content to extract.
        mime_type: The mime type of the content.
        force_ocr: Whether to force OCR on PDF files that have a text layer.
        language: The language code for OCR. Defaults to "eng".
        max_processes: Maximum number of concurrent processes. Defaults to CPU count / 2 (minimum 1).
        psm: Page segmentation mode for Tesseract OCR. Defaults to PSMMode.AUTO.

    Returns:
        The extracted content and the mime type of the content.
    """
    handler = partial(
        extract_bytes, content, mime_type, max_processes=max_processes, force_ocr=force_ocr, language=language, psm=psm
    )
    return anyio.run(handler)


def extract_file_sync(
    file_path: Path | str,
    mime_type: str | None = None,
    *,
    force_ocr: bool = False,
    language: str = "eng",
    max_processes: int = DEFAULT_MAX_PROCESSES,
    psm: PSMMode = PSMMode.AUTO,
) -> ExtractionResult:
    """Synchronous version of extract_file.

    Args:
        file_path: The path to the file.
        mime_type: The mime type of the content.
        force_ocr: Whether to force OCR on PDF files that have a text layer.
        language: The language code for OCR. Defaults to "eng".
        max_processes: Maximum number of concurrent processes. Defaults to CPU count / 2 (minimum 1).
        psm: Page segmentation mode for Tesseract OCR. Defaults to PSMMode.AUTO.

    Returns:
        The extracted content and the mime type of the content.
    """
    handler = partial(
        extract_file, file_path, mime_type, max_processes=max_processes, force_ocr=force_ocr, language=language, psm=psm
    )
    return anyio.run(handler)


def batch_extract_file_sync(
    file_paths: Sequence[PathLike[str] | str],
    *,
    force_ocr: bool = False,
    language: str = "eng",
    max_processes: int = DEFAULT_MAX_PROCESSES,
    psm: PSMMode = PSMMode.AUTO,
) -> list[ExtractionResult]:
    """Synchronous version of batch_extract_file.

    Args:
        file_paths: A sequence of paths to files to extract text from.
        force_ocr: Whether to force OCR on PDF files that have a text layer.
        language: The language code for OCR. Defaults to "eng".
        max_processes: Maximum number of concurrent processes. Defaults to CPU count / 2 (minimum 1).
        psm: Page segmentation mode for Tesseract OCR. Defaults to PSMMode.AUTO.

    Returns:
        A list of extraction results in the same order as the input paths.
    """
    handler = partial(
        batch_extract_file,
        file_paths,
        force_ocr=force_ocr,
        max_processes=max_processes,
        language=language,
        psm=psm,
    )
    return anyio.run(handler)


def batch_extract_bytes_sync(
    contents: Sequence[tuple[bytes, str]],
    *,
    force_ocr: bool = False,
    language: str = "eng",
    max_processes: int = DEFAULT_MAX_PROCESSES,
    psm: PSMMode = PSMMode.AUTO,
) -> list[ExtractionResult]:
    """Synchronous version of batch_extract_bytes.

    Args:
        contents: A sequence of tuples containing (content, mime_type) pairs.
        force_ocr: Whether to force OCR on PDF files that have a text layer.
        language: The language code for OCR. Defaults to "eng".
        max_processes: Maximum number of concurrent processes. Defaults to CPU count / 2 (minimum 1).
        psm: Page segmentation mode for Tesseract OCR. Defaults to PSMMode.AUTO.

    Returns:
        A list of extraction results in the same order as the input contents.
    """
    handler = partial(
        batch_extract_bytes,
        contents,
        force_ocr=force_ocr,
        max_processes=max_processes,
        language=language,
        psm=psm,
    )
    return anyio.run(handler)
