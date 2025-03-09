from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypedDict

import numpy as np
from easyocr import easyocr
from PIL import Image

from kreuzberg._mime_types import PLAIN_TEXT_MIME_TYPE
from kreuzberg._ocr._base import OCRBackend
from kreuzberg._types import ExtractionResult, Metadata
from kreuzberg._utils._language import to_easyocr
from kreuzberg._utils._string import normalize_spaces
from kreuzberg._utils._sync import run_sync
from kreuzberg.exceptions import OCRError

if TYPE_CHECKING:
    from pathlib import Path

try:  # pragma: no cover
    from typing import NotRequired  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    from typing_extensions import NotRequired

try:  # pragma: no cover
    from typing import Unpack  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    from typing_extensions import Unpack


class EasyOCRConfig(TypedDict):
    """Configuration options for EasyOCR."""

    add_margin: NotRequired[float]
    """Extend bounding boxes in all directions. Default: 0.1"""
    adjust_contrast: NotRequired[float]
    """Target contrast level for low contrast text. Default: 0.5"""
    beamWidth: NotRequired[int]
    """Beam width for beam search in recognition. Default: 5"""
    canvas_size: NotRequired[int]
    """Maximum image dimension for detection. Default: 2560"""
    contrast_ths: NotRequired[float]
    """Contrast threshold for preprocessing. Default: 0.1"""
    decoder: NotRequired[Literal["greedy", "beamsearch", "wordbeamsearch"]]
    """Decoder method. Options: 'greedy', 'beamsearch', 'wordbeamsearch'. Default: 'greedy'"""
    height_ths: NotRequired[float]
    """Maximum difference in box height for merging. Default: 0.5"""
    language: NotRequired[str]
    """Language to use for OCR."""
    link_threshold: NotRequired[float]
    """Link confidence threshold. Default: 0.4"""
    low_text: NotRequired[float]
    """Text low-bound score. Default: 0.4"""
    mag_ratio: NotRequired[float]
    """Image magnification ratio. Default: 1.0"""
    min_size: NotRequired[int]
    """Minimum text box size in pixels. Default: 10"""
    rotation_info: NotRequired[list[int]]
    """List of angles to try for detection. Default: None (no rotation)"""
    slope_ths: NotRequired[float]
    """Maximum slope for merging text boxes. Default: 0.1"""
    text_threshold: NotRequired[float]
    """Text confidence threshold. Default: 0.7"""
    use_gpu: NotRequired[bool]
    """Whether to use GPU for inference. Default: False"""
    width_ths: NotRequired[float]
    """Maximum horizontal distance for merging boxes. Default: 0.5"""
    x_ths: NotRequired[float]
    """Maximum horizontal distance for paragraph merging. Default: 1.0"""
    y_ths: NotRequired[float]
    """Maximum vertical distance for paragraph merging. Default: 0.5"""
    ycenter_ths: NotRequired[float]
    """Maximum shift in y direction for merging. Default: 0.5"""


class EasyOCRBackend(OCRBackend[EasyOCRConfig]):
    _reader: ClassVar[Any] = None

    async def process_image(self, image: Image.Image, **kwargs: Unpack[EasyOCRConfig]) -> ExtractionResult:
        """Asynchronously process an image and extract its text and metadata using EasyOCR.

        Args:
            image: An instance of PIL.Image representing the input image.
            **kwargs: Configuration parameters for EasyOCR including language, detection thresholds, etc.

        Returns:
            ExtractionResult: The extraction result containing text content, mime type, and metadata.

        Raises:
            OCRError: If OCR processing fails.
        """
        await self._init_easyocr(**kwargs)
        image_np = np.array(image)
        try:
            result = await run_sync(
                self._reader.readtext,
                image_np,
                decoder=kwargs.get("decoder", "greedy"),
                beamWidth=kwargs.get("beamWidth", 5),
                min_size=kwargs.get("min_size", 10),
                rotation_info=kwargs.get("rotation_info"),
                contrast_ths=kwargs.get("contrast_ths", 0.1),
                adjust_contrast=kwargs.get("adjust_contrast", 0.5),
                text_threshold=kwargs.get("text_threshold", 0.7),
                low_text=kwargs.get("low_text", 0.4),
                link_threshold=kwargs.get("link_threshold", 0.4),
                canvas_size=kwargs.get("canvas_size", 2560),
                mag_ratio=kwargs.get("mag_ratio", 1.0),
                slope_ths=kwargs.get("slope_ths", 0.1),
                ycenter_ths=kwargs.get("ycenter_ths", 0.5),
                height_ths=kwargs.get("height_ths", 0.5),
                width_ths=kwargs.get("width_ths", 0.5),
                add_margin=kwargs.get("add_margin", 0.1),
            )

            return self._process_easyocr_result(result, image)
        except Exception as e:
            raise OCRError(f"Failed to OCR using EasyOCR: {e}") from e

    async def process_file(self, path: Path, **kwargs: Unpack[EasyOCRConfig]) -> ExtractionResult:
        """Asynchronously process a file and extract its text and metadata using EasyOCR.

        Args:
            path: A Path object representing the file to be processed.
            **kwargs: Configuration parameters for EasyOCR including language, detection thresholds, etc.

        Returns:
            ExtractionResult: The extraction result containing text content, mime type, and metadata.

        Raises:
            OCRError: If file loading or OCR processing fails.
        """
        await self._init_easyocr(**kwargs)
        try:
            image = await run_sync(Image.open, path)
            return await self.process_image(image, **kwargs)
        except Exception as e:
            raise OCRError(f"Failed to load or process image using EasyOCR: {e}") from e

    @staticmethod
    def _process_easyocr_result(result: list[Any], image: Image.Image) -> ExtractionResult:
        """Process EasyOCR result into an ExtractionResult with metadata.

        Args:
            result: The raw result from EasyOCR.
            image: The original PIL image.

        Returns:
            ExtractionResult: The extraction result containing text content, mime type, and metadata.
        """
        if not result:
            return ExtractionResult(
                content="",
                mime_type=PLAIN_TEXT_MIME_TYPE,
                metadata=Metadata(width=image.width, height=image.height),
            )

        if all(len(item) == 2 for item in result):
            text_content = ""
            confidence_sum = 0
            confidence_count = 0

            for text, confidence in result:
                if text:
                    text_content += text + "\n"
                    confidence_sum += confidence
                    confidence_count += 1

            metadata = Metadata(
                width=image.width,
                height=image.height,
            )

            return ExtractionResult(
                content=normalize_spaces(text_content),
                mime_type=PLAIN_TEXT_MIME_TYPE,
                metadata=metadata,
            )

        sorted_results = sorted(result, key=lambda x: x[0][0][1] + x[0][2][1])
        line_groups: list[list[Any]] = []
        current_line: list[Any] = []
        prev_y_center: float | None = None
        line_height_threshold = 20

        for item in sorted_results:
            box, text, confidence = item
            y_center = sum(point[1] for point in box) / 4

            if prev_y_center is None or abs(y_center - prev_y_center) > line_height_threshold:
                if current_line:
                    line_groups.append(current_line)
                current_line = [item]
            else:
                current_line.append(item)

            prev_y_center = y_center

        if current_line:
            line_groups.append(current_line)

        text_content = ""
        confidence_sum = 0
        confidence_count = 0

        for line in line_groups:
            line_sorted = sorted(line, key=lambda x: x[0][0][0])

            for item in line_sorted:
                _, text, confidence = item
                if text:
                    text_content += text + " "
                    confidence_sum += confidence
                    confidence_count += 1

            text_content += "\n"

        metadata = Metadata(
            width=image.width,
            height=image.height,
        )

        return ExtractionResult(
            content=normalize_spaces(text_content),
            mime_type=PLAIN_TEXT_MIME_TYPE,
            metadata=metadata,
        )

    @classmethod
    def _is_gpu_available(cls) -> bool:
        """Check if GPU is available for EasyOCR.

        Returns:
            bool: True if GPU support is available.
        """
        try:
            import torch

            return torch.cuda.is_available()
        except ImportError:
            return False

    @classmethod
    async def _init_easyocr(cls, **kwargs: Unpack[EasyOCRConfig]) -> None:
        """Initialize EasyOCR with the provided configuration.

        Args:
            **kwargs: Configuration parameters for EasyOCR including language, etc.

        Raises:
            MissingDependencyError: If EasyOCR is not installed.
            OCRError: If initialization fails.
        """
        if cls._reader is not None:
            return

        try:
            languages = to_easyocr(kwargs.pop("language", "en"))
            has_gpu = cls._is_gpu_available()

            kwargs.setdefault("gpu", has_gpu)
            kwargs.setdefault("detector", True)
            kwargs.setdefault("recognizer", True)
            kwargs.setdefault("download_enabled", True)
            kwargs.setdefault("recog_network", "standard")

            cls._reader = await run_sync(
                easyocr.Reader,
                languages,
                gpu=kwargs.get("use_gpu"),
                verbose=False,
            )
        except Exception as e:
            raise OCRError(f"Failed to initialize EasyOCR: {e}") from e
