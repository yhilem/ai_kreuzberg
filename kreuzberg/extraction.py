from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Final, cast

import anyio

from kreuzberg import ExtractionResult
from kreuzberg._extractors._base import ExtractionConfig, Extractor
from kreuzberg._extractors._html import HTMLExtractor
from kreuzberg._extractors._image import ImageExtractor
from kreuzberg._extractors._pandoc import (
    BibliographyExtractor,
    EbookExtractor,
    LaTeXExtractor,
    MarkdownExtractor,
    MiscFormatExtractor,
    OfficeDocumentExtractor,
    StructuredTextExtractor,
    TabularDataExtractor,
    XMLBasedExtractor,
)
from kreuzberg._extractors._pdf import PDFExtractor
from kreuzberg._extractors._presentation import PresentationExtractor
from kreuzberg._extractors._spread_sheet import SpreadSheetExtractor
from kreuzberg._mime_types import (
    validate_mime_type,
)
from kreuzberg._utils._string import safe_decode

if TYPE_CHECKING:
    from collections.abc import Sequence
    from os import PathLike

DEFAULT_CONFIG: Final[ExtractionConfig] = ExtractionConfig()


@lru_cache
def get_extractor(mime_type: str | None, config: ExtractionConfig) -> Extractor | None:
    """Gets the extractor for the mimetype.

    Args:
        mime_type: The mime type of the content.
        config: Extraction options object, defaults to the default object.

    Returns:
        The extractor
    """
    if mime_type:
        for extractor in [
            # order by how likely the mimetype is to match first.
            PDFExtractor,
            OfficeDocumentExtractor,
            PresentationExtractor,
            SpreadSheetExtractor,
            HTMLExtractor,
            MarkdownExtractor,
            ImageExtractor,
            BibliographyExtractor,
            EbookExtractor,
            LaTeXExtractor,
            MiscFormatExtractor,
            StructuredTextExtractor,
            TabularDataExtractor,
            XMLBasedExtractor,
        ]:
            if extractor.supports_mimetype(mime_type):
                return extractor(mime_type=mime_type, config=config)  # type: ignore[abstract]

    return None


async def extract_bytes(content: bytes, mime_type: str, config: ExtractionConfig = DEFAULT_CONFIG) -> ExtractionResult:
    """Extract the textual content from a given byte string representing a file's contents.

    Args:
        content: The content to extract.
        mime_type: The mime type of the content.
        config: Extraction options object, defaults to the default object.


    Returns:
        The extracted content and the mime type of the content.
    """
    mime_type = validate_mime_type(mime_type=mime_type)
    if extractor := get_extractor(mime_type=mime_type, config=config):
        return await extractor.extract_bytes_async(content)

    return ExtractionResult(
        content=safe_decode(content),
        mime_type=mime_type,
        metadata={},
    )


async def extract_file(
    file_path: PathLike[str] | str, mime_type: str | None = None, config: ExtractionConfig = DEFAULT_CONFIG
) -> ExtractionResult:
    """Extract the textual content from a given file.

    Args:
        file_path: The path to the file.
        mime_type: The mime type of the content.
        config: Extraction options object, defaults to the default object.

    Returns:
        The extracted content and the mime type of the content.
    """
    mime_type = validate_mime_type(file_path=file_path, mime_type=mime_type)
    if extractor := get_extractor(mime_type=mime_type, config=config):
        return await extractor.extract_path_async(Path(file_path))

    return ExtractionResult(
        content=safe_decode(await anyio.Path(file_path).read_bytes()), mime_type=mime_type, metadata={}
    )


async def batch_extract_file(
    file_paths: Sequence[PathLike[str] | str], config: ExtractionConfig = DEFAULT_CONFIG
) -> list[ExtractionResult]:
    """Extract text from multiple files concurrently.

    Args:
        file_paths: A sequence of paths to files to extract text from.
        config: Extraction options object, defaults to the default object.

    Returns:
        A list of extraction results in the same order as the input paths.
    """
    results = cast(list[ExtractionResult], ([None] * len(file_paths)))

    async def _extract_file(path: PathLike[str] | str, index: int) -> None:
        result = await extract_file(
            path,
            None,
            config,
        )
        results[index] = result

    async with anyio.create_task_group() as tg:
        for i, path in enumerate(file_paths):
            tg.start_soon(_extract_file, path, i)

    return results


async def batch_extract_bytes(
    contents: Sequence[tuple[bytes, str]], config: ExtractionConfig = DEFAULT_CONFIG
) -> list[ExtractionResult]:
    """Extract text from multiple byte contents concurrently.

    Args:
        contents: A sequence of tuples containing (content, mime_type) pairs.
        config: Extraction options object, defaults to the default object.

    Returns:
        A list of extraction results in the same order as the input contents.
    """
    results = cast(list[ExtractionResult], [None] * len(contents))

    async def _extract_bytes(content: bytes, mime_type: str, index: int) -> None:
        result = await extract_bytes(content, mime_type, config)
        results[index] = result

    async with anyio.create_task_group() as tg:
        for i, (content, mime_type) in enumerate(contents):
            tg.start_soon(_extract_bytes, content, mime_type, i)

    return results


### Sync proxies


def extract_bytes_sync(content: bytes, mime_type: str, config: ExtractionConfig = DEFAULT_CONFIG) -> ExtractionResult:
    """Synchronous version of extract_bytes.

    Args:
        content: The content to extract.
        mime_type: The mime type of the content.
        config: Extraction options object, defaults to the default object.

    Returns:
        The extracted content and the mime type of the content.
    """
    mime_type = validate_mime_type(mime_type=mime_type)
    if extractor := get_extractor(mime_type=mime_type, config=config):
        return extractor.extract_bytes_sync(content)

    return ExtractionResult(
        content=safe_decode(content),
        mime_type=mime_type,
        metadata={},
    )


def extract_file_sync(
    file_path: Path | str, mime_type: str | None = None, config: ExtractionConfig = DEFAULT_CONFIG
) -> ExtractionResult:
    """Synchronous version of extract_file.

    Args:
        file_path: The path to the file.
        mime_type: The mime type of the content.
        config: Extraction options object, defaults to the default object.

    Returns:
        The extracted content and the mime type of the content.
    """
    mime_type = validate_mime_type(file_path=file_path, mime_type=mime_type)
    if extractor := get_extractor(mime_type=mime_type, config=config):
        return extractor.extract_path_sync(Path(file_path))

    return ExtractionResult(
        content=Path(file_path).read_text(),
        mime_type=mime_type,
        metadata={},
    )


def batch_extract_file_sync(
    file_paths: Sequence[PathLike[str] | str], config: ExtractionConfig = DEFAULT_CONFIG
) -> list[ExtractionResult]:
    """Synchronous version of batch_extract_file.

    Args:
        file_paths: A sequence of paths to files to extract text from.
        config: Extraction options object, defaults to the default object.

    Returns:
        A list of extraction results in the same order as the input paths.
    """
    return [extract_file_sync(file_path=Path(file_path), mime_type=None, config=config) for file_path in file_paths]


def batch_extract_bytes_sync(
    contents: Sequence[tuple[bytes, str]], config: ExtractionConfig = DEFAULT_CONFIG
) -> list[ExtractionResult]:
    """Synchronous version of batch_extract_bytes.

    Args:
        contents: A sequence of tuples containing (content, mime_type) pairs.
        config: Extraction options object, defaults to the default object.

    Returns:
        A list of extraction results in the same order as the input contents.
    """
    return [extract_bytes_sync(content=content, mime_type=mime_type, config=config) for content, mime_type in contents]
