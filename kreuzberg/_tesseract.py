from __future__ import annotations

import re
import subprocess
import sys
from enum import Enum
from os import PathLike
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Any, Literal, TypeVar, Union, cast

from anyio import Path as AsyncPath
from anyio import Semaphore, create_task_group
from PIL.Image import Image

from kreuzberg import ExtractionResult, ParsingError
from kreuzberg._mime_types import PLAIN_TEXT_MIME_TYPE
from kreuzberg._ref import Ref
from kreuzberg._string import normalize_spaces
from kreuzberg._sync import run_sync
from kreuzberg.exceptions import MissingDependencyError, OCRError

if TYPE_CHECKING:
    from kreuzberg.config import Config


if sys.version_info < (3, 11):
    from exceptiongroup import ExceptionGroup

version_ref = {"checked": False}
semaphore_ref = Ref[Semaphore]()

T = TypeVar("T", bound=Union[Image, PathLike[str], str])

SupportedLanguages = Literal[
    "afr",
    "amh",
    "ara",
    "asm",
    "aze",
    "aze_cyrl",
    "bel",
    "ben",
    "bod",
    "bos",
    "bre",
    "bul",
    "cat",
    "ceb",
    "ces",
    "chi_sim",
    "chi_tra",
    "chr",
    "cos",
    "cym",
    "dan",
    "dan_frak",
    "deu",
    "deu_frak",
    "deu_latf",
    "dzo",
    "ell",
    "eng",
    "enm",
    "epo",
    "equ",
    "est",
    "eus",
    "fao",
    "fas",
    "fil",
    "fin",
    "fra",
    "frk",
    "frm",
    "fry",
    "gla",
    "gle",
    "glg",
    "grc",
    "guj",
    "hat",
    "heb",
    "hin",
    "hrv",
    "hun",
    "hye",
    "iku",
    "ind",
    "isl",
    "ita",
    "ita_old",
    "jav",
    "jpn",
    "kan",
    "kat",
    "kat_old",
    "kaz",
    "khm",
    "kir",
    "kmr",
    "kor",
    "kor_vert",
    "kur",
    "lao",
    "lat",
    "lav",
    "lit",
    "ltz",
    "mal",
    "mar",
    "mkd",
    "mlt",
    "mon",
    "mri",
    "msa",
    "mya",
    "nep",
    "nld",
    "nor",
    "oci",
    "ori",
    "osd",
    "pan",
    "pol",
    "por",
    "pus",
    "que",
    "ron",
    "rus",
    "san",
    "sin",
    "slk",
    "slk_frak",
    "slv",
    "snd",
    "spa",
    "spa_old",
    "sqi",
    "srp",
    "srp_latn",
    "sun",
    "swa",
    "swe",
    "syr",
    "tam",
    "tat",
    "tel",
    "tgk",
    "tgl",
    "tha",
    "tir",
    "ton",
    "tur",
    "uig",
    "ukr",
    "urd",
    "uzb",
    "uzb_cyrl",
    "vie",
    "yid",
    "yor",
]


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
        result = await run_sync(subprocess.run, command, capture_output=True)
        version_match = re.search(r"tesseract\s+(\d+)", result.stdout.decode())
        if not version_match or int(version_match.group(1)) < 5:
            raise MissingDependencyError("Tesseract version 5 or above is required.")

        version_ref["checked"] = True
    except FileNotFoundError as e:
        raise MissingDependencyError("Tesseract is not installed.") from e


async def process_file(
    input_file: str | PathLike[str], *, language: SupportedLanguages, psm: PSMMode, **kwargs: Any
) -> ExtractionResult:
    """Process a single image file using Tesseract OCR.

    Args:
        input_file: The path to the image file to process.
        language: The language code for OCR.
        psm: Page segmentation mode.
        **kwargs: Additional Tesseract configuration options as key-value pairs.

    Raises:
        OCRError: If OCR fails to extract text from the image.

    Returns:
        str: Extracted text from the image.
    """
    with NamedTemporaryFile(suffix=".txt") as output_file:
        # this is needed because tesseract adds .txt to the output file
        output_file_name = output_file.name.replace(".txt", "")
        try:
            command = [
                "tesseract",
                str(input_file),
                output_file_name,
                "-l",
                language,
                "--psm",
                str(psm.value),
            ]

            for key, value in kwargs.items():
                command.extend(["-c", f"{key}={value}"])

            result = await run_sync(
                subprocess.run,
                command,
                capture_output=True,
            )

            if not result.returncode == 0:
                raise OCRError("OCR failed with a non-0 return code.")

            output = await AsyncPath(output_file.name).read_text()
            return ExtractionResult(content=normalize_spaces(output), mime_type=PLAIN_TEXT_MIME_TYPE, metadata={})
        except (RuntimeError, OSError) as e:
            raise OCRError("Failed to OCR using tesseract") from e


async def process_image(image: Image, *, language: SupportedLanguages, psm: PSMMode, **kwargs: Any) -> ExtractionResult:
    """Process a single Pillow Image using Tesseract OCR.

    Args:
        image: The Pillow Image to process.
        language: The language code for OCR.
        psm: Page segmentation mode.
        **kwargs: Additional Tesseract configuration options as key-value pairs.

    Returns:
        str: Extracted text from the image.
    """
    with NamedTemporaryFile(suffix=".png") as image_file:
        await run_sync(image.save, image_file.name, format="PNG")
        return await process_file(image_file.name, language=language, psm=psm, **kwargs)


async def process_image_with_tesseract(
    image: Image | PathLike[str] | str,
    *,
    language: SupportedLanguages = "eng",
    psm: PSMMode = PSMMode.AUTO,
    **kwargs: Any,
) -> ExtractionResult:
    """Run Tesseract OCR asynchronously on a single Pillow Image or a list of Pillow Images.

    Args:
        image: A single Pillow Image, a pathlike or a string or a list of Pillow Images to process.
        language: The language code for OCR (default: "eng").
        psm: Page segmentation mode (default: PSMMode.AUTO).
        **kwargs: Additional Tesseract configuration options as key-value pairs.

    Raises:
        ValueError: If the input is not a Pillow Image or a list of Pillow Images.

    Returns:
        Extracted text as a string
    """
    await validate_tesseract_version()

    if isinstance(image, Image):
        return await process_image(image, language=language, psm=psm, **kwargs)

    if isinstance(image, (PathLike, str)):
        return await process_file(image, language=language, psm=psm, **kwargs)

    raise ValueError("Input must be one of: str, Pathlike or Pillow Image.")


async def batch_process_images(
    images: list[T],
    *,
    config: Config,
    language: SupportedLanguages = "eng",
    psm: PSMMode = PSMMode.AUTO,
    **kwargs: Any,
) -> list[ExtractionResult]:
    """Run Tesseract OCR asynchronously on multiple images with controlled concurrency.

    Args:
        images: A list of Pillow Images, paths or strings to process.
        config: The configuration object.
        language: The language code for OCR (default: "eng").
        psm: Page segmentation mode (default: PSMMode.AUTO).
        **kwargs: Additional Tesseract configuration options as key-value pairs.

    Raises:
        ParsingError: If OCR fails to extract text from any of the images.

    Returns:
        List of extracted text strings, one per input image.

    The function uses a semaphore to limit concurrent Tesseract processes,
    preventing resource exhaustion while still allowing parallel processing.
    The concurrency limit can be configured via the global config object.
    """
    await validate_tesseract_version()
    results = cast(list[ExtractionResult], list(range(len(images))))

    async def _process_image(index: int, image: T) -> None:
        if not semaphore_ref.value:
            semaphore_ref.value = Semaphore(config.concurrent_limit)

        async with semaphore_ref.value:
            results[index] = await process_image_with_tesseract(image, language=language, psm=psm, **kwargs)

    try:
        async with create_task_group() as tg:
            for i, image in enumerate(images):
                tg.start_soon(_process_image, i, image)
    except ExceptionGroup as eg:
        raise ParsingError("Failed to process images with Tesseract") from eg

    return results
