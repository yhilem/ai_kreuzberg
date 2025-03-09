from __future__ import annotations

import platform
from importlib.util import find_spec
from typing import TYPE_CHECKING, Any, ClassVar, TypedDict

import numpy as np
from paddleocr import PaddleOCR
from PIL import Image

from kreuzberg._mime_types import PLAIN_TEXT_MIME_TYPE
from kreuzberg._ocr._base import OCRBackend
from kreuzberg._types import ExtractionResult, Metadata
from kreuzberg._utils._language import to_paddle
from kreuzberg._utils._string import normalize_spaces
from kreuzberg._utils._sync import run_sync
from kreuzberg.exceptions import OCRError

if TYPE_CHECKING:
    from pathlib import Path

try:  # pragma: no cover
    from typing import NotRequired  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    from typing_extensions import Literal, NotRequired

try:  # pragma: no cover
    from typing import Unpack  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    from typing_extensions import Unpack


class PaddleConfig(TypedDict):
    """Configuration options for PaddleOCR.

    This TypedDict provides type hints and documentation for all PaddleOCR parameters.
    """

    cls_image_shape: NotRequired[str]
    """Image shape for classification algorithm in format 'channels,height,width'. Default: '3,48,192'"""
    crop_res_save_dir: NotRequired[str]
    """Directory to save cropped text images. Default: './output'"""
    det_algorithm: NotRequired[Literal["DB", "EAST", "SAST", "PSE", "FCE", "PAN", "CT", "DB++", "Layout"]]
    """Detection algorithm. Default: 'DB'"""
    det_db_box_thresh: NotRequired[float]
    """Score threshold for detected boxes. Boxes below this value are discarded. Default: 0.5"""
    det_db_thresh: NotRequired[float]
    """Binarization threshold for DB output map. Default: 0.3"""
    det_db_unclip_ratio: NotRequired[float]
    """Expansion ratio for detected text boxes. Default: 2.0"""
    det_east_cover_thresh: NotRequired[float]
    """Score threshold for EAST output boxes. Default: 0.1"""
    det_east_nms_thresh: NotRequired[float]
    """NMS threshold for EAST model output boxes. Default: 0.2"""
    det_east_score_thresh: NotRequired[float]
    """Binarization threshold for EAST output map. Default: 0.8"""
    det_max_side_len: NotRequired[int]
    """Maximum size of image long side. Images exceeding this will be proportionally resized. Default: 960"""
    drop_score: NotRequired[float]
    """Filter recognition results by confidence score. Results below this are discarded. Default: 0.5"""
    enable_mkldnn: NotRequired[bool]
    """Whether to enable MKL-DNN acceleration (Intel CPU only). Default: False"""
    gpu_mem: NotRequired[int]
    """GPU memory size (in MB) to use for initialization. Default: 8000"""
    language: NotRequired[str]
    """Language to use for OCR."""
    max_text_length: NotRequired[int]
    """Maximum text length that the recognition algorithm can recognize. Default: 25"""
    rec: NotRequired[bool]
    """Enable text recognition when using the ocr() function. Default: True"""
    rec_algorithm: NotRequired[
        Literal[
            "CRNN",
            "SRN",
            "NRTR",
            "SAR",
            "SEED",
            "SVTR",
            "SVTR_LCNet",
            "ViTSTR",
            "ABINet",
            "VisionLAN",
            "SPIN",
            "RobustScanner",
            "RFL",
        ]
    ]
    """Recognition algorithm. Default: 'CRNN'"""
    rec_image_shape: NotRequired[str]
    """Image shape for recognition algorithm in format 'channels,height,width'. Default: '3,32,320'"""
    table: NotRequired[bool]
    """Whether to enable table recognition. Default: True"""
    use_angle_cls: NotRequired[bool]
    """Whether to use text orientation classification model. Default: True"""
    use_gpu: NotRequired[bool]
    """Whether to use GPU for inference. Requires installing the paddlepaddle-gpu package"""
    use_space_char: NotRequired[bool]
    """Whether to recognize spaces. Default: True"""
    use_zero_copy_run: NotRequired[bool]
    """Whether to enable zero_copy_run for inference optimization. Default: False"""


class PaddleBackend(OCRBackend[PaddleConfig]):
    _paddle_ocr: ClassVar[Any] = None

    async def process_image(self, image: Image.Image, **kwargs: Unpack[PaddleConfig]) -> ExtractionResult:
        """Asynchronously process an image and extract its text and metadata using PaddleOCR.

        Args:
            image: An instance of PIL.Image representing the input image.
            **kwargs: Configuration parameters for PaddleOCR including language, detection thresholds, etc.

        Returns:
            ExtractionResult: The extraction result containing text content, mime type, and metadata.

        Raises:
            OCRError: If OCR processing fails.
        """
        await self._init_paddle_ocr(**kwargs)
        image_np = np.array(image)
        try:
            result = await run_sync(self._paddle_ocr.ocr, image_np, cls=kwargs.get("use_angle_cls", True))
            return self._process_paddle_result(result, image)
        except Exception as e:
            raise OCRError(f"Failed to OCR using PaddleOCR: {e}") from e

    async def process_file(self, path: Path, **kwargs: Unpack[PaddleConfig]) -> ExtractionResult:
        """Asynchronously process a file and extract its text and metadata using PaddleOCR.

        Args:
            path: A Path object representing the file to be processed.
            **kwargs: Configuration parameters for PaddleOCR including language, detection thresholds, etc.

        Returns:
            ExtractionResult: The extraction result containing text content, mime type, and metadata.

        Raises:
            OCRError: If file loading or OCR processing fails.
        """
        await self._init_paddle_ocr(**kwargs)
        try:
            image = await run_sync(Image.open, path)
            return await self.process_image(image, **kwargs)
        except Exception as e:
            raise OCRError(f"Failed to load or process image using PaddleOCR: {e}") from e

    @staticmethod
    def _process_paddle_result(result: list[Any], image: Image.Image) -> ExtractionResult:
        """Process PaddleOCR result into an ExtractionResult with metadata.

        Args:
            result: The raw result from PaddleOCR.
            image: The original PIL image.

        Returns:
            ExtractionResult: The extraction result containing text content, mime type, and metadata.
        """
        text_content = ""
        confidence_sum = 0
        confidence_count = 0

        for page_result in result:
            if not page_result:
                continue

            sorted_boxes = sorted(page_result, key=lambda x: x[0][0][1])
            line_groups: list[list[Any]] = []
            current_line: list[Any] = []
            prev_y: float | None = None

            for box in sorted_boxes:
                box_points, (_, _) = box
                current_y = sum(point[1] for point in box_points) / 4
                min_box_distance = 20

                if prev_y is None or abs(current_y - prev_y) > min_box_distance:
                    if current_line:
                        line_groups.append(current_line)
                    current_line = [box]
                else:
                    current_line.append(box)

                prev_y = current_y

            if current_line:
                line_groups.append(current_line)

            for line in line_groups:
                line_sorted = sorted(line, key=lambda x: x[0][0][0])

                for box in line_sorted:
                    _, (text, confidence) = box
                    if text:
                        text_content += text + " "
                        confidence_sum += confidence
                        confidence_count += 1

                text_content += "\n"

        width, height = image.size
        metadata = Metadata(
            width=width,
            height=height,
        )

        return ExtractionResult(
            content=normalize_spaces(text_content),
            mime_type=PLAIN_TEXT_MIME_TYPE,
            metadata=metadata,
        )

    @classmethod
    def _is_mkldnn_supported(cls) -> bool:
        """Check if the current architecture supports MKL-DNN optimization.

        Returns:
            bool: True if MKL-DNN is supported on this architecture.
        """
        system = platform.system().lower()
        processor = platform.processor().lower()
        machine = platform.machine().lower()

        if system in ("linux", "windows"):
            return "intel" in processor or "x86" in machine or "amd64" in machine or "x86_64" in machine

        if system == "darwin":
            return machine == "x86_64"

        return False

    @classmethod
    async def _init_paddle_ocr(cls, **kwargs: Unpack[PaddleConfig]) -> None:
        """Initialize PaddleOCR with the provided configuration.

        Args:
            **kwargs: Configuration parameters for PaddleOCR including language, detection thresholds, etc.

        Raises:
            MissingDependencyError: If PaddleOCR is not installed.
            OCRError: If initialization fails.
        """
        if cls._paddle_ocr is not None:
            return

        try:
            language = to_paddle(kwargs.pop("language", "en"))
            has_gpu_package = bool(find_spec("paddlepaddle_gpu"))
            kwargs.setdefault("use_angle_cls", True)
            kwargs.setdefault("use_gpu", has_gpu_package)
            kwargs.setdefault("enable_mkldnn", cls._is_mkldnn_supported() and not has_gpu_package)
            kwargs.setdefault("det_db_thresh", 0.3)
            kwargs.setdefault("det_db_box_thresh", 0.5)
            kwargs.setdefault("det_db_unclip_ratio", 1.6)

            cls._paddle_ocr = await run_sync(
                PaddleOCR,
                lang=language,
                show_log=False,
            )
        except Exception as e:
            raise OCRError(f"Failed to initialize PaddleOCR: {e}") from e
