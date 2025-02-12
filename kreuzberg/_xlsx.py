from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from xlsx2csv import Xlsx2csv

from kreuzberg import ExtractionResult, ParsingError
from kreuzberg._pandoc import process_file_with_pandoc
from kreuzberg._sync import run_sync


async def extract_xlsx_file(input_file: Path) -> ExtractionResult:
    """Extract text from an XLSX file by converting it to CSV and then to markdown.

    Args:
        input_file: The path to the XLSX file.

    Returns:
        The extracted text content.

    Raises:
        ParsingError: If the XLSX file could not be parsed.
    """
    try:
        await run_sync(Xlsx2csv(input_file).convert, input_file.name)
        return await process_file_with_pandoc(input_file.name, mime_type="text/csv")
    except Exception as e:
        raise ParsingError(
            "Could not extract text from XLSX",
            context={
                "error": str(e),
            },
        ) from e


async def extract_xlsx_content(content: bytes) -> ExtractionResult:
    """Extract text from an XLSX file content.

    Args:
        content: The XLSX file content.

    Returns:
        The extracted text content.
    """
    with NamedTemporaryFile(suffix=".xlsx") as xlsx_file:
        xlsx_file.write(content)
        return await extract_xlsx_file(Path(xlsx_file.name))
