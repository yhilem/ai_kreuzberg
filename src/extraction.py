from mimetypes import guess_type
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import NamedTuple

from anyio import Path as AsyncPath

from src._extraction import (
    _extract_content_with_pandoc,
    _extract_file_with_pandoc,
    _extract_image_with_tesseract,
    _extract_pdf_file,
)
from src._string import safe_decode
from src.exceptions import ValidationError
from src.mime_types import (
    IMAGE_MIME_TYPE_EXT_MAP,
    IMAGE_MIME_TYPES,
    MARKDOWN_MIME_TYPE,
    PANDOC_SUPPORTED_MIME_TYPES,
    PDF_MIME_TYPE,
    PLAIN_TEXT_MIME_TYPE,
    SUPPORTED_MIME_TYPES,
)


class ExtractionResult(NamedTuple):
    """The result of a file extraction."""

    content: str
    """The extracted content."""
    mime_type: str
    """The mime type of the content."""


async def extract_file_content(*, content: bytes, mime_type: str) -> ExtractionResult:
    """Extract the textual content from a given byte string representing a file's contents.

    Args:
        content: The content to extract.
        mime_type: The mime type of the content.

    Raises:
        ValidationError: If the mime type is not supported.

    Returns:
        The extracted content and the mime type of the content.
    """
    if mime_type not in SUPPORTED_MIME_TYPES or not any(mime_type.startswith(value) for value in SUPPORTED_MIME_TYPES):
        raise ValidationError(
            f"Unsupported mime type: {mime_type}",
            context={"mime_type": mime_type, "supported_mimetypes": SUPPORTED_MIME_TYPES},
        )

    if mime_type == PDF_MIME_TYPE or any(mime_type.startswith(value) for value in PDF_MIME_TYPE):
        with NamedTemporaryFile(suffix=".pdf") as temp_file:
            temp_file.write(content)
            return ExtractionResult(
                content=await _extract_pdf_file(Path(temp_file.name)), mime_type=PLAIN_TEXT_MIME_TYPE
            )

    if mime_type in IMAGE_MIME_TYPES or any(mime_type.startswith(value) for value in IMAGE_MIME_TYPES):
        with NamedTemporaryFile(suffix=IMAGE_MIME_TYPE_EXT_MAP[mime_type]) as temp_file:
            temp_file.write(content)
            return ExtractionResult(
                content=await _extract_image_with_tesseract(temp_file.name), mime_type=PLAIN_TEXT_MIME_TYPE
            )

    if mime_type in PANDOC_SUPPORTED_MIME_TYPES or any(
        mime_type.startswith(value) for value in PANDOC_SUPPORTED_MIME_TYPES
    ):
        return ExtractionResult(
            content=await _extract_content_with_pandoc(content, mime_type), mime_type=MARKDOWN_MIME_TYPE
        )

    return ExtractionResult(
        content=safe_decode(content),
        mime_type=mime_type,
    )


async def extract_file(*, file_path: Path | str, mime_type: str | None = None) -> ExtractionResult:
    """Extract the textual content from a given file.

    Args:
        file_path: The path to the file.
        mime_type: The mime type of the file.

    Raises:
        ValidationError: If the mime type is not supported.

    Returns:
        The extracted content and the mime type of the content.
    """
    file_path = Path(file_path)
    mime_type = mime_type or guess_type(file_path.name)[0]
    if not mime_type:
        raise ValidationError("Could not determine the mime type of the file.", context={"file_path": str(file_path)})

    if mime_type not in SUPPORTED_MIME_TYPES or not any(mime_type.startswith(value) for value in SUPPORTED_MIME_TYPES):
        raise ValidationError(
            f"Unsupported mime type: {mime_type}",
            context={"mime_type": mime_type, "supported_mimetypes": SUPPORTED_MIME_TYPES},
        )

    if not await AsyncPath(file_path).exists():
        raise ValidationError("The file does not exist.", context={"file_path": str(file_path)})

    if mime_type == PDF_MIME_TYPE or any(mime_type.startswith(value) for value in PDF_MIME_TYPE):
        return ExtractionResult(content=await _extract_pdf_file(file_path), mime_type=PLAIN_TEXT_MIME_TYPE)

    if mime_type in IMAGE_MIME_TYPES or any(mime_type.startswith(value) for value in IMAGE_MIME_TYPES):
        return ExtractionResult(content=await _extract_image_with_tesseract(file_path), mime_type=PLAIN_TEXT_MIME_TYPE)

    if mime_type in PANDOC_SUPPORTED_MIME_TYPES or any(
        mime_type.startswith(value) for value in PANDOC_SUPPORTED_MIME_TYPES
    ):
        return ExtractionResult(
            content=await _extract_file_with_pandoc(file_path, mime_type), mime_type=MARKDOWN_MIME_TYPE
        )

    return ExtractionResult(content=await AsyncPath(file_path).read_text(), mime_type=PLAIN_TEXT_MIME_TYPE)
