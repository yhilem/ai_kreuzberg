from __future__ import annotations

from typing import TYPE_CHECKING

import html_to_markdown
from anyio import Path as AsyncPath

from kreuzberg import ExtractionResult
from kreuzberg._mime_types import MARKDOWN_MIME_TYPE
from kreuzberg._string import normalize_spaces, safe_decode

if TYPE_CHECKING:
    from pathlib import Path


async def extract_html_string(file_path_or_contents: Path | bytes) -> ExtractionResult:
    """Extract text from an HTML string.

    Args:
        file_path_or_contents: The HTML content.

    Returns:
        The extracted text content.
    """
    content = (
        safe_decode(file_path_or_contents)
        if isinstance(file_path_or_contents, bytes)
        else await AsyncPath(file_path_or_contents).read_text()
    )
    result = html_to_markdown.convert_to_markdown(content)
    return ExtractionResult(content=normalize_spaces(result), mime_type=MARKDOWN_MIME_TYPE, metadata={})
