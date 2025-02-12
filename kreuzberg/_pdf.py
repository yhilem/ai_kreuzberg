from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

import pypdfium2

from kreuzberg import ExtractionResult
from kreuzberg._mime_types import PLAIN_TEXT_MIME_TYPE
from kreuzberg._string import normalize_spaces
from kreuzberg._sync import run_sync
from kreuzberg._tesseract import batch_process_images
from kreuzberg.config import Config, default_config
from kreuzberg.exceptions import ParsingError

if TYPE_CHECKING:  # pragma: no cover
    from PIL.Image import Image


async def _convert_pdf_to_images(input_file: Path) -> list[Image]:
    """Convert a PDF file to images.

    Args:
        input_file: The path to the PDF file.

    Raises:
        ParsingError: If the PDF file could not be converted to images.

    Returns:
        A list of Pillow Images.
    """
    try:
        pdf = await run_sync(pypdfium2.PdfDocument, str(input_file))
        return [page.render(scale=2.0).to_pil() for page in pdf]
    except pypdfium2.PdfiumError as e:
        raise ParsingError(
            "Could not convert PDF to images", context={"file_path": str(input_file), "error": str(e)}
        ) from e


async def _extract_pdf_text_with_ocr(input_file: Path, *, config: Config | None = None) -> ExtractionResult:
    """Extract text from a scanned PDF file using pytesseract.

    Args:
        input_file: The path to the PDF file.
        config: Optional configuration for text extraction.

    Returns:
        The extracted text.
    """
    images = await _convert_pdf_to_images(input_file)
    ocr_results = await batch_process_images(images, config=config or default_config)
    return ExtractionResult(
        content="\n".join([v.content for v in ocr_results]), mime_type=PLAIN_TEXT_MIME_TYPE, metadata={}
    )


async def _extract_pdf_searchable_text(input_file: Path) -> str:
    """Extract text from a searchable PDF file using pypdfium2.

    Args:
        input_file: The path to the PDF file.

    Raises:
        ParsingError: If the text could not be extracted from the PDF file.

    Returns:
        The extracted text.
    """
    try:
        document = await run_sync(pypdfium2.PdfDocument, str(input_file))
        text = "\n".join(page.get_textpage().get_text_bounded() for page in document)
        return normalize_spaces(text)
    except pypdfium2.PdfiumError as e:
        raise ParsingError(
            "Could not extract text from PDF file", context={"file_path": str(input_file), "error": str(e)}
        ) from e


async def extract_pdf_file(
    input_file: Path, force_ocr: bool = False, *, config: Config | None = None
) -> ExtractionResult:
    """Extract text from a PDF file.

    Args:
        input_file: The path to the PDF file.
        force_ocr: Whether to force OCR on the PDF file
        config: Optional configuration for text extraction.

    Returns:
        The extracted text.
    """
    if not force_ocr and (content := await _extract_pdf_searchable_text(input_file)):
        return ExtractionResult(content=content, mime_type=PLAIN_TEXT_MIME_TYPE, metadata={})

    return await _extract_pdf_text_with_ocr(input_file, config=config)


async def extract_pdf_content(
    content: bytes, *, config: Config | None = None, force_ocr: bool = False
) -> ExtractionResult:
    with NamedTemporaryFile(suffix=".pdf") as pdf_file:
        pdf_file.write(content)
        file_path = Path(pdf_file.name)

        return await extract_pdf_file(file_path, force_ocr=force_ocr, config=config)
