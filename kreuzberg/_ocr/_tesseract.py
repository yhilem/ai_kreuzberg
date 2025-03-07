from __future__ import annotations

import re
import sys
from enum import Enum
from os import PathLike
from typing import Any, TypeVar, Union

from anyio import Path as AsyncPath
from anyio import run_process
from PIL.Image import Image

from kreuzberg._constants import DEFAULT_MAX_PROCESSES, MINIMAL_SUPPORTED_TESSERACT_VERSION
from kreuzberg._mime_types import PLAIN_TEXT_MIME_TYPE
from kreuzberg._types import ExtractionResult
from kreuzberg._utils._string import normalize_spaces
from kreuzberg._utils._sync import run_sync, run_taskgroup_batched
from kreuzberg._utils._tmp import create_temp_file
from kreuzberg.exceptions import MissingDependencyError, OCRError, ParsingError

if sys.version_info < (3, 11):  # pragma: no cover
    from exceptiongroup import ExceptionGroup  # type: ignore[import-not-found]

version_ref = {"checked": False}

T = TypeVar("T", bound=Union[Image, PathLike[str], str])


class PSMMode(Enum):
    """Enum for Tesseract Page Segmentation Modes (PSM) with human-readable values."""

    OSD_ONLY = 0
    """Orientation and script detection only."""
    AUTO_OSD = 1
    """Automatic page segmentation with orientation and script detection."""
    AUTO_ONLY = 2
    """Automatic page segmentation without OSD."""
    AUTO = 3
    """Fully automatic page segmentation (default)."""
    SINGLE_COLUMN = 4
    """Assume a single column of text."""
    SINGLE_BLOCK_VERTICAL = 5
    """Assume a single uniform block of vertically aligned text."""
    SINGLE_BLOCK = 6
    """Assume a single uniform block of text."""
    SINGLE_LINE = 7
    """Treat the image as a single text line."""
    SINGLE_WORD = 8
    """Treat the image as a single word."""
    CIRCLE_WORD = 9
    """Treat the image as a single word in a circle."""
    SINGLE_CHAR = 10
    """Treat the image as a single character."""


async def validate_tesseract_version() -> None:
    """Validate that Tesseract is installed and is version 5 or above.

    Raises:
        MissingDependencyError: If Tesseract is not installed or is below version 5.
    """
    try:
        if version_ref["checked"]:
            return

        command = ["tesseract", "--version"]
        result = await run_process(command)
        version_match = re.search(r"tesseract\s+v?(\d+)\.\d+\.\d+", result.stdout.decode())
        if not version_match or int(version_match.group(1)) < MINIMAL_SUPPORTED_TESSERACT_VERSION:
            raise MissingDependencyError("Tesseract version 5 or above is required.")

        version_ref["checked"] = True
    except FileNotFoundError as e:
        raise MissingDependencyError(
            "Tesseract is not installed or not in path. Please install tesseract 5 and above on your system."
        ) from e


async def process_file(
    input_file: str | PathLike[str],
    *,
    language: str,
    psm: PSMMode,
) -> ExtractionResult:
    """Process a single image file using Tesseract OCR.

    Args:
        input_file: The path to the image file to process.
        language: The language code for OCR.
        psm: Page segmentation mode.

    Raises:
        OCRError: If OCR fails to extract text from the image.

    Returns:
        ExtractionResult: The extracted text from the image.
    """
    output_path, unlink = await create_temp_file(".txt")
    try:
        output_base = str(output_path).replace(".txt", "")

        command = [
            "tesseract",
            str(input_file),
            output_base,
            "-l",
            language,
            "--psm",
            str(psm.value),
            "--oem",
            "1",
            "--loglevel",
            "OFF",
            "-c",
            "thresholding_method=1",
            "-c",
            "tessedit_enable_dict_correction=1",
            "-c",
            "language_model_ngram_on=1",
            "-c",
            "textord_space_size_is_variable=1",
            "-c",
            "classify_use_pre_adapted_templates=1",
            "-c",
            "tessedit_dont_blkrej_good_wds=1",
            "-c",
            "tessedit_dont_rowrej_good_wds=1",
            "-c",
            "tessedit_use_primary_params_model=1",
        ]

        env: dict[str, Any] | None = None
        if sys.platform.startswith("linux"):
            env = {"OMP_THREAD_LIMIT": "1"}

        result = await run_process(command, env=env)

        if not result.returncode == 0:
            raise OCRError(
                "OCR failed with a non-0 return code.",
                context={"error": result.stderr.decode() if isinstance(result.stderr, bytes) else result.stderr},
            )

        output = await AsyncPath(output_path).read_text("utf-8")
        return ExtractionResult(content=normalize_spaces(output), mime_type=PLAIN_TEXT_MIME_TYPE, metadata={})
    except (RuntimeError, OSError) as e:
        raise OCRError(f"Failed to OCR using tesseract: {e}") from e
    finally:
        await unlink()


async def process_image(
    image: Image,
    *,
    language: str,
    psm: PSMMode,
) -> ExtractionResult:
    """Process a single Pillow Image using Tesseract OCR.

    Args:
        image: The Pillow Image to process.
        language: The language code for OCR.
        psm: Page segmentation mode.

    Returns:
        ExtractionResult: The extracted text from the image.
    """
    image_path, unlink = await create_temp_file(".png")
    await run_sync(image.save, str(image_path), format="PNG")
    try:
        return await process_file(image_path, language=language, psm=psm)
    finally:
        await unlink()


async def process_image_with_tesseract(
    image: Image | PathLike[str] | str,
    *,
    language: str = "eng",
    psm: PSMMode = PSMMode.AUTO,
) -> ExtractionResult:
    """Run Tesseract OCR asynchronously on a single Pillow Image or a list of Pillow Images.

    Args:
        image: A single Pillow Image, a pathlike or a string or a list of Pillow Images to process.
        language: The language code for OCR (default: "eng").
        psm: Page segmentation mode (default: PSMMode.AUTO).

    Raises:
        ValueError: If the input is not a Pillow Image or a list of Pillow Images.

    Returns:
        Extracted text as a string
    """
    await validate_tesseract_version()

    if isinstance(image, Image):
        return await process_image(image, language=language, psm=psm)

    if isinstance(image, (PathLike, str)):
        return await process_file(image, language=language, psm=psm)

    raise ValueError("Input must be one of: str, Pathlike or Pillow Image.")


async def batch_process_images(
    images: list[T],
    *,
    language: str = "eng",
    psm: PSMMode = PSMMode.AUTO,
    max_processes: int = DEFAULT_MAX_PROCESSES,
) -> list[ExtractionResult]:
    """Run Tesseract OCR asynchronously on multiple images with controlled concurrency.

    Args:
        images: A list of Pillow Images, paths or strings to process.
        language: The language code for OCR (default: "eng").
        psm: Page segmentation mode (default: PSMMode.AUTO).
        max_processes: Maximum number of concurrent processes (default: CPU count / 2).

    Raises:
        ParsingError: If OCR fails to extract text from any of the images.

    Returns:
        List of ExtractionResult objects, one per input image.
    """
    await validate_tesseract_version()
    try:
        tasks = [process_image_with_tesseract(image, language=language, psm=psm) for image in images]
        return await run_taskgroup_batched(*tasks, batch_size=max_processes)
    except ExceptionGroup as eg:
        raise ParsingError("Failed to process images with Tesseract", context={"errors": eg.exceptions}) from eg
