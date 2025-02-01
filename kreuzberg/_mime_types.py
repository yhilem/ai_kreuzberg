from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Mapping

MARKDOWN_MIME_TYPE: Final[str] = "text/markdown"
PLAIN_TEXT_MIME_TYPE: Final[str] = "text/plain"
PDF_MIME_TYPE: Final[str] = "application/pdf"

PLAIN_TEXT_MIME_TYPES: Final[set[str]] = {PLAIN_TEXT_MIME_TYPE, MARKDOWN_MIME_TYPE}

IMAGE_MIME_TYPES: Final[set[str]] = {
    "image/bmp",
    "image/gif",
    "image/jp2",
    "image/jpeg",
    "image/jpm",
    "image/jpx",
    "image/mj2",
    "image/pjpeg",
    "image/png",
    "image/tiff",
    "image/webp",
    "image/x-bmp",
    "image/x-ms-bmp",
    "image/x-portable-anymap",
    "image/x-portable-bitmap",
    "image/x-portable-graymap",
    "image/x-portable-pixmap",
    "image/x-tiff",
}
IMAGE_MIME_TYPE_EXT_MAP: Final[Mapping[str, str]] = {
    "image/bmp": "bmp",
    "image/x-bmp": "bmp",
    "image/x-ms-bmp": "bmp",
    "image/gif": "gif",
    "image/jpeg": "jpg",
    "image/pjpeg": "jpg",
    "image/png": "png",
    "image/tiff": "tiff",
    "image/x-tiff": "tiff",
    "image/jp2": "jp2",
    "image/jpx": "jpx",
    "image/jpm": "jpm",
    "image/mj2": "mj2",
    "image/webp": "webp",
    "image/x-portable-anymap": "pnm",
    "image/x-portable-bitmap": "pbm",
    "image/x-portable-graymap": "pgm",
    "image/x-portable-pixmap": "ppm",
}
PANDOC_SUPPORTED_MIME_TYPES: Final[set[str]] = {
    "application/csv",
    "application/latex",
    "application/rtf",
    "application/vnd.oasis.opendocument.text",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/x-csv",
    "application/x-latex",
    "application/x-rtf",
    "application/x-vnd.oasis.opendocument.text",
    "text/csv",
    "text/latex",
    "text/rst",
    "text/rtf",
    "text/tab-separated-values",
    "text/x-csv",
    "text/x-latex",
    "text/x-rst",
    "text/x-tsv",
}
PANDOC_MIME_TYPE_EXT_MAP: Final[Mapping[str, str]] = {
    "application/csv": "csv",
    "application/latex": "latex",
    "application/rtf": "rtf",
    "application/vnd.oasis.opendocument.text": "odt",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/x-csv": "csv",
    "application/x-latex": "latex",
    "application/x-rtf": "rtf",
    "application/x-vnd.oasis.opendocument.text": "odt",
    "text/csv": "csv",
    "text/latex": "latex",
    "text/rst": "rst",
    "text/rtf": "rtf",
    "text/tab-separated-values": "tsv",
    "text/x-csv": "csv",
    "text/x-latex": "latex",
    "text/x-rst": "rst",
    "text/x-tsv": "tsv",
}

SUPPORTED_MIME_TYPES: Final[set[str]] = (
    PLAIN_TEXT_MIME_TYPES | IMAGE_MIME_TYPES | PANDOC_SUPPORTED_MIME_TYPES | {PDF_MIME_TYPE}
)
