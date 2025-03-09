from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING, Any, ClassVar, Final, TypedDict

from anyio import Path as AsyncPath
from anyio import run_process

from kreuzberg._mime_types import PLAIN_TEXT_MIME_TYPE
from kreuzberg._ocr._base import OCRBackend
from kreuzberg._types import ExtractionResult, PSMMode
from kreuzberg._utils._language import to_tesseract
from kreuzberg._utils._string import normalize_spaces
from kreuzberg._utils._sync import run_sync
from kreuzberg._utils._tmp import create_temp_file
from kreuzberg.exceptions import MissingDependencyError, OCRError

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

MINIMAL_SUPPORTED_TESSERACT_VERSION: Final[int] = 5


class TesseractConfig(TypedDict):
    language: NotRequired[str]
    psm: NotRequired[PSMMode]


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
        language = to_tesseract(kwargs.get("language", "eng"))
        psm = kwargs.get("psm", PSMMode.AUTO)
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
