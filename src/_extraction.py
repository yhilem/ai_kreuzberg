from pathlib import Path
from typing import cast

from charset_normalizer import detect
from pypandoc import convert_file, convert_text
from pypdfium2 import PdfDocument, PdfiumError
from pytesseract import TesseractError, image_to_string

from src._sync import run_sync
from src.exceptions import ParsingError
from src.mime_types import PANDOC_MIME_TYPE_EXT_MAP


def _extract_pdf_with_tesseract(file_path: Path) -> str:
    """Extract text from a scanned PDF file using pytesseract.

    Args:
        file_path: The path to the PDF file.

    Raises:
        ParsingError: If the text could not be extracted from the PDF file.

    Returns:
        The extracted text.
    """
    try:
        # make it into an image here:
        pdf = PdfDocument(str(file_path))
        images = [page.render(scale=2.0).to_pil() for page in pdf]

        text = "\n".join(image_to_string(img) for img in images)
        return text.strip()
    except (PdfiumError, TesseractError) as e:
        raise ParsingError(
            "Could not extract text from PDF file", context={"file_path": str(file_path), "error": str(e)}
        ) from e


def _extract_pdf_with_pdfium2(file_path: Path) -> str:
    """Extract text from a searchable PDF file using pypdfium2.

    Args:
        file_path: The path to the PDF file.

    Raises:
        ParsingError: If the text could not be extracted from the PDF file.

    Returns:
        The extracted text.
    """
    try:
        document = PdfDocument(file_path)
        text = "\n".join(page.get_textpage().get_text_range() for page in document)
        return text.strip()
    except PdfiumError as e:
        raise ParsingError(
            "Could not extract text from PDF file", context={"file_path": str(file_path), "error": str(e)}
        ) from e


async def _extract_pdf_file(file_path: Path) -> str:
    """Extract text from a PDF file.

    Args:
        file_path: The path to the PDF file.

    Returns:
        The extracted text.
    """
    if content := await run_sync(_extract_pdf_with_pdfium2, file_path):
        return content

    return await run_sync(_extract_pdf_with_tesseract, file_path)


async def _extract_content_with_pandoc(file_data: bytes, mime_type: str, encoding: str | None = None) -> str:
    """Extract text using pandoc.

    Args:
        file_data: The content of the file.
        mime_type: The mime type of the file.
        encoding: An optional encoding to use when decoding the string.

    Raises:
        ParsingError: If the text could not be extracted from the file using pandoc.

    Returns:
        The extracted text.
    """
    ext = PANDOC_MIME_TYPE_EXT_MAP[mime_type]
    encoding = encoding or detect(file_data)["encoding"] or "utf-8"
    try:
        return cast(str, await run_sync(convert_text, file_data, to="md", format=ext, encoding=encoding))
    except RuntimeError as e:
        raise ParsingError(
            f"Could not extract text from {PANDOC_MIME_TYPE_EXT_MAP[mime_type]} file contents",
            context={"error": str(e)},
        ) from e


async def _extract_file_with_pandoc(file_path: Path | str, mime_type: str) -> str:
    """Extract text using pandoc.

    Args:
        file_path: The path to the file.
        mime_type: The mime type of the file.

    Raises:
        ParsingError: If the text could not be extracted from the file using pandoc.

    Returns:
        The extracted text.
    """
    ext = PANDOC_MIME_TYPE_EXT_MAP[mime_type]
    try:
        return cast(str, await run_sync(convert_file, file_path, to="md", format=ext))
    except RuntimeError as e:
        raise ParsingError(
            f"Could not extract text from {PANDOC_MIME_TYPE_EXT_MAP[mime_type]} file",
            context={"file_path": str(file_path), "error": str(e)},
        ) from e


async def _extract_image_with_tesseract(file_path: Path | str) -> str:
    """Extract text from an image file.

    Args:
        file_path: The path to the image file.

    Raises:
        ParsingError: If the text could not be extracted from the image file.

    Returns:
        The extracted content.
    """
    try:
        return cast(str, image_to_string(str(file_path)).strip())
    except TesseractError as e:
        raise ParsingError(
            "Could not extract text from image file", context={"file_path": str(file_path), "error": str(e)}
        ) from e
