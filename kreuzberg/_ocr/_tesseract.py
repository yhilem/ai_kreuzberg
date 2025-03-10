from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING, Any, ClassVar, Final, TypedDict

from anyio import Path as AsyncPath
from anyio import run_process

from kreuzberg._mime_types import PLAIN_TEXT_MIME_TYPE
from kreuzberg._ocr._base import OCRBackend
from kreuzberg._types import ExtractionResult, PSMMode
from kreuzberg._utils._string import normalize_spaces
from kreuzberg._utils._sync import run_sync
from kreuzberg._utils._tmp import create_temp_file
from kreuzberg.exceptions import MissingDependencyError, OCRError, ValidationError

if TYPE_CHECKING:
    from pathlib import Path

    from PIL.Image import Image

try:  # pragma: no cover
    from typing import NotRequired  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    from typing_extensions import NotRequired

try:  # pragma: no cover
    from typing import Unpack  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    from typing_extensions import Unpack

TESSERACT_SUPPORTED_LANGUAGE_CODES: Final[set[str]] = {
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
    "tha",  # codespell:ignore
    "tir",
    "ton",
    "tur",
    "uig",
    "ukr",
    "urd",
    "uzb",
    "uzb_cyrl",
    "vie",  # codespell:ignore
    "yid",
    "yor",
}

MINIMAL_SUPPORTED_TESSERACT_VERSION: Final[int] = 5


class TesseractConfig(TypedDict):
    """Configuration options for Tesseract OCR engine."""

    classify_use_pre_adapted_templates: NotRequired[bool]
    """Whether to use pre-adapted templates during classification to improve recognition accuracy."""
    language: NotRequired[str]
    """Language code to use for OCR (e.g., 'eng' for English, 'deu' for German)."""
    language_model_ngram_on: NotRequired[bool]
    """Enable or disable the use of n-gram-based language models for improved text recognition."""
    psm: NotRequired[PSMMode]
    """Page segmentation mode (PSM) to guide Tesseract on how to segment the image (e.g., single block, single line)."""
    tessedit_dont_blkrej_good_wds: NotRequired[bool]
    """If True, prevents block rejection of words identified as good, improving text output quality."""
    tessedit_dont_rowrej_good_wds: NotRequired[bool]
    """If True, prevents row rejection of words identified as good, avoiding unnecessary omissions."""
    tessedit_enable_dict_correction: NotRequired[bool]
    """Enable or disable dictionary-based correction for recognized text to improve word accuracy."""
    tessedit_use_primary_params_model: NotRequired[bool]
    """If True, forces the use of the primary parameters model for text recognition."""
    textord_space_size_is_variable: NotRequired[bool]
    """Allow variable spacing between words, useful for text with irregular spacing."""
    thresholding_method: NotRequired[bool]
    """Enable or disable specific thresholding methods during image preprocessing for better OCR accuracy."""


class TesseractBackend(OCRBackend[TesseractConfig]):
    _version_checked: ClassVar[bool] = False

    async def process_image(
        self,
        image: Image,
        **kwargs: Unpack[TesseractConfig],
    ) -> ExtractionResult:
        await self._validate_tesseract_version()
        image_path, unlink = await create_temp_file(".png")
        await run_sync(image.save, str(image_path), format="PNG")
        try:
            return await self.process_file(image_path, **kwargs)
        finally:
            await unlink()

    async def process_file(
        self,
        path: Path,
        **kwargs: Unpack[TesseractConfig],
    ) -> ExtractionResult:
        await self._validate_tesseract_version()
        output_path, unlink = await create_temp_file(".txt")
        language = self._validate_language_code(kwargs.pop("language", "eng"))
        psm = kwargs.pop("psm", PSMMode.AUTO)
        try:
            output_base = str(output_path).replace(".txt", "")
            command = [
                "tesseract",
                str(path),
                output_base,
                "-l",
                language,
                "--psm",
                str(psm.value),
                "--oem",
                "1",
                "--loglevel",
                "OFF",
            ]
            for kwarg, value in kwargs.items():
                command.extend(["-c", f"{kwarg}={1 if value else 0}"])

            env: dict[str, Any] | None = None
            if sys.platform.startswith("linux"):
                # we have to prevent multithreading this way otherwise we will get deadlocks ~keep
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

    @classmethod
    async def _validate_tesseract_version(cls) -> None:
        """Validate that Tesseract is installed and is version 5 or above.

        Raises:
            MissingDependencyError: If Tesseract is not installed or is below version 5.
        """
        try:
            if cls._version_checked:
                return

            command = ["tesseract", "--version"]
            result = await run_process(command)
            version_match = re.search(r"tesseract\s+v?(\d+)\.\d+\.\d+", result.stdout.decode())
            if not version_match or int(version_match.group(1)) < MINIMAL_SUPPORTED_TESSERACT_VERSION:
                raise MissingDependencyError("Tesseract version 5 or above is required.")

            cls._version_checked = True
        except FileNotFoundError as e:
            raise MissingDependencyError(
                "Tesseract is not installed or not in path. Please install tesseract 5 and above on your system."
            ) from e

    @staticmethod
    def _validate_language_code(lang_code: str) -> str:
        """Convert a language code to Tesseract format.

        Args:
            lang_code: ISO language code or language name

        Raises:
            ValidationError: If the language is not supported by Tesseract

        Returns:
            Language code compatible with Tesseract
        """
        normalized = lang_code.lower()
        if normalized in TESSERACT_SUPPORTED_LANGUAGE_CODES:
            return normalized

        raise ValidationError(
            "The provided language code is not supported by Tesseract",
            context={
                "language_code": lang_code,
                "supported_languages": ",".join(sorted(TESSERACT_SUPPORTED_LANGUAGE_CODES)),
            },
        )
