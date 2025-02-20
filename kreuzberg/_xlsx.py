from __future__ import annotations

import csv
import sys
from functools import partial
from io import StringIO
from typing import TYPE_CHECKING

from anyio import Path as AsyncPath
from python_calamine import CalamineWorkbook

from kreuzberg import ExtractionResult, ParsingError
from kreuzberg._mime_types import MARKDOWN_MIME_TYPE
from kreuzberg._pandoc import process_file_with_pandoc
from kreuzberg._string import normalize_spaces
from kreuzberg._sync import run_sync, run_taskgroup
from kreuzberg._tmp import create_temp_file

if TYPE_CHECKING:  # pragma: no cover
    from pathlib import Path

if sys.version_info < (3, 11):  # pragma: no cover
    from exceptiongroup import ExceptionGroup  # type: ignore[import-not-found]


async def convert_sheet_to_text(workbook: CalamineWorkbook, sheet_name: str) -> str:
    values = workbook.get_sheet_by_name(sheet_name).to_python()

    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer)

    for row in values:
        writer.writerow(row)

    csv_data = csv_buffer.getvalue()
    csv_buffer.close()

    csv_path, unlink = await create_temp_file(".csv")
    await AsyncPath(csv_path).write_text(csv_data)

    result = await process_file_with_pandoc(csv_path, mime_type="text/csv")
    await unlink()
    return f"## {sheet_name}\n\n{normalize_spaces(result.content)}"


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
        workbook: CalamineWorkbook = await run_sync(CalamineWorkbook.from_path, str(input_file))
        results = await run_taskgroup(
            *[partial(convert_sheet_to_text, workbook, sheet_name) for sheet_name in workbook.sheet_names]
        )

        return ExtractionResult(
            content="\n\n".join(results),
            mime_type=MARKDOWN_MIME_TYPE,
            metadata={},
        )
    except ExceptionGroup as eg:
        raise ParsingError(
            "Failed to extract file data",
            context={"file": str(input_file), "errors": eg.exceptions},
        ) from eg


async def extract_xlsx_content(content: bytes) -> ExtractionResult:
    """Extract text from an XLSX file content.

    Args:
        content: The XLSX file content.

    Returns:
        The extracted text content.
    """
    xlsx_path, unlink = await create_temp_file(".xlsx")

    await AsyncPath(xlsx_path).write_bytes(content)
    result = await extract_xlsx_file(xlsx_path)
    await unlink()
    return result
