from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from kreuzberg._ocr._easyocr import (
    EasyOCRBackend,
)
from kreuzberg._types import ExtractionResult
from kreuzberg.exceptions import MissingDependencyError, OCRError, ValidationError

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture


def raise_import_error(name: str, *args: Any, **kwargs: Any) -> Any:
    """Helper function to raise ImportError for specific modules."""
    if name == "easyocr":
        raise ImportError("No module named 'easyocr'")
    if name == "torch":
        raise ImportError("No module named 'torch'")
    return __import__(name, *args, **kwargs)


@pytest.fixture
def backend() -> EasyOCRBackend:
    EasyOCRBackend._reader = None
    return EasyOCRBackend()


@pytest.fixture
def mock_easyocr_reader() -> Mock:
    """Mock the EasyOCR Reader object."""
    mock_reader = Mock()
    mock_reader.readtext.return_value = [
        (
            [[0, 0], [100, 0], [100, 20], [0, 20]],
            "Sample OCR text",
            0.95,
        )
    ]
    return mock_reader


@pytest.fixture(autouse=True)
def reset_reader(mocker: MockerFixture) -> None:
    """Reset EasyOCR reader between tests."""
    EasyOCRBackend._reader = None


@pytest.mark.parametrize(
    "language_code,expected_result",
    [
        ("en", ["en"]),
        ("EN", ["en"]),
        ("fr", ["fr"]),
        ("de", ["de"]),
        ("ja", ["ja"]),
        ("ch_sim", ["ch_sim"]),
        ("ch_tra", ["ch_tra"]),
        ("ko", ["ko"]),
    ],
)
def test_validate_language_code_valid(language_code: str, expected_result: list[str]) -> None:
    """Test that valid language codes are correctly validated and normalized."""
    result = EasyOCRBackend._validate_language_code(language_code)
    assert result == expected_result


@pytest.mark.parametrize(
    "invalid_language_code",
    [
        "invalid",
        "english",
        "español",
        "русский",
        "eng",
        "deu",
        "fra",
        "jpn",
        "",
        "123",
    ],
)
def test_validate_language_code_invalid(invalid_language_code: str) -> None:
    """Test that invalid language codes raise ValidationError with appropriate context."""
    with pytest.raises(ValidationError) as excinfo:
        EasyOCRBackend._validate_language_code(invalid_language_code)

    assert "language_code" in excinfo.value.context
    assert excinfo.value.context["language_code"] == invalid_language_code
    assert "supported_languages" in excinfo.value.context
    assert "not supported by EasyOCR" in str(excinfo.value)


@pytest.mark.anyio
async def test_init_easyocr_with_invalid_language(backend: EasyOCRBackend) -> None:
    """Test initializing EasyOCR with an invalid language raises ValidationError."""
    with pytest.raises(ValidationError, match="not supported by EasyOCR"):
        await backend._init_easyocr(language="invalid")


def test_is_gpu_available() -> None:
    """Test GPU availability check."""

    mock_torch = Mock()
    mock_torch.cuda.is_available.return_value = True

    with patch.object(EasyOCRBackend, "_is_gpu_available", return_value=True):
        assert EasyOCRBackend._is_gpu_available() is True

    with patch.object(EasyOCRBackend, "_is_gpu_available", return_value=False):
        assert EasyOCRBackend._is_gpu_available() is False


@pytest.mark.anyio
async def test_init_easyocr_missing_dependency() -> None:
    """Test that MissingDependencyError is raised when easyocr is not installed."""

    with patch(
        "builtins.__import__", side_effect=lambda name, *args, **kwargs: raise_import_error(name, *args, **kwargs)
    ):
        backend = EasyOCRBackend()
        with pytest.raises(MissingDependencyError, match="easyocr.*not installed"):
            await backend._init_easyocr(language="en")


@pytest.mark.anyio
async def test_init_easyocr(mock_easyocr_reader: Mock) -> None:
    """Test successful initialization of EasyOCR."""

    mock_easyocr = Mock()
    mock_reader_class = Mock(return_value=mock_easyocr_reader)
    mock_easyocr.Reader = mock_reader_class

    with (
        patch.dict("sys.modules", {"easyocr": mock_easyocr}),
        patch("kreuzberg._ocr._easyocr.run_sync", return_value=mock_easyocr_reader) as run_sync_mock,
    ):
        backend = EasyOCRBackend()
        await backend._init_easyocr(language="en")

        run_sync_mock.assert_called_once()
        assert run_sync_mock.call_args[0][0] == mock_easyocr.Reader
        assert run_sync_mock.call_args[0][1] == ["en"]
        assert "verbose" in run_sync_mock.call_args[1]
        assert run_sync_mock.call_args[1]["verbose"] is False


@pytest.mark.anyio
async def test_init_easyocr_error(mocker: MockerFixture) -> None:
    """Test error handling during EasyOCR initialization."""
    error_message = "Failed to initialize"
    mocker.patch("kreuzberg._ocr._easyocr.run_sync", side_effect=Exception(error_message))

    backend = EasyOCRBackend()
    with pytest.raises(OCRError, match=f"Failed to initialize EasyOCR: {error_message}"):
        await backend._init_easyocr()


@pytest.mark.anyio
async def test_process_image(backend: EasyOCRBackend, mock_easyocr_reader: Mock) -> None:
    """Test processing an image with EasyOCR."""

    image = Image.new("RGB", (100, 100))

    with patch.object(backend, "_init_easyocr", return_value=None):
        backend._reader = mock_easyocr_reader  # type: ignore[misc]

        with patch("kreuzberg._ocr._easyocr.run_sync", return_value=mock_easyocr_reader.readtext.return_value):
            result = await backend.process_image(image, language="en")

            assert isinstance(result, ExtractionResult)
            assert "Sample OCR text" in result.content
            assert result.mime_type == "text/plain"
            assert isinstance(result.metadata, dict)
            assert result.metadata["width"] == 100
            assert result.metadata["height"] == 100


@pytest.mark.anyio
async def test_process_image_error(backend: EasyOCRBackend) -> None:
    """Test error handling when processing an image."""

    image = Image.new("RGB", (100, 100))

    with patch.object(backend, "_init_easyocr", return_value=None):
        backend._reader = Mock()  # type: ignore[misc]

        error_message = "OCR processing failed"
        with patch("kreuzberg._ocr._easyocr.run_sync", side_effect=Exception(error_message)):
            with pytest.raises(OCRError) as excinfo:
                await backend.process_image(image, language="en")

            assert "Failed to OCR using EasyOCR" in str(excinfo.value)


@pytest.mark.anyio
async def test_process_file(backend: EasyOCRBackend, tmp_path: Path) -> None:
    """Test processing a file with EasyOCR."""

    test_image = Image.new("RGB", (100, 100))
    image_path = tmp_path / "test_image.png"
    test_image.save(image_path)

    expected_result = ExtractionResult(
        content="Sample OCR text", mime_type="text/plain", metadata={"width": 100, "height": 100}
    )

    with (
        patch.object(backend, "process_image", return_value=expected_result),
        patch.object(backend, "_init_easyocr", return_value=None),
    ):
        result = await backend.process_file(image_path, language="en")

        assert result == expected_result
        backend.process_image.assert_called_once()  # type: ignore[attr-defined]


@pytest.mark.anyio
async def test_process_file_error(backend: EasyOCRBackend, tmp_path: Path) -> None:
    """Test error handling when processing a file."""

    test_image = Image.new("RGB", (100, 100))
    image_path = tmp_path / "test_image.png"
    test_image.save(image_path)

    with patch.object(backend, "_init_easyocr", return_value=None):
        error_message = "Failed to load image"
        with patch.object(backend, "process_image", side_effect=Exception(error_message)):
            with pytest.raises(OCRError) as excinfo:
                await backend.process_file(image_path, language="en")

            assert "Failed to load or process image using EasyOCR" in str(excinfo.value)


@pytest.mark.anyio
async def test_process_easyocr_result_empty(backend: EasyOCRBackend) -> None:
    """Test processing empty EasyOCR results."""
    image = Image.new("RGB", (100, 100))
    result = backend._process_easyocr_result([], image)

    assert result.content == ""
    assert result.mime_type == "text/plain"
    assert result.metadata["width"] == 100
    assert result.metadata["height"] == 100


@pytest.mark.anyio
async def test_process_easyocr_result_simple_format(backend: EasyOCRBackend) -> None:
    """Test processing EasyOCR results in simple format (text, confidence)."""
    image = Image.new("RGB", (100, 100))
    easyocr_result = [
        ("Line 1", 0.95),
        ("Line 2", 0.90),
    ]

    result = backend._process_easyocr_result(easyocr_result, image)

    assert "Line 1" in result.content
    assert "Line 2" in result.content
    assert result.mime_type == "text/plain"
    assert result.metadata["width"] == 100
    assert result.metadata["height"] == 100


@pytest.mark.anyio
async def test_process_easyocr_result_full_format(backend: EasyOCRBackend) -> None:
    """Test processing EasyOCR results in full format (box, text, confidence)."""
    image = Image.new("RGB", (100, 100))
    easyocr_result = [
        (
            [[0, 0], [100, 0], [100, 20], [0, 20]],
            "Line 1",
            0.95,
        ),
        (
            [[0, 30], [100, 30], [100, 50], [0, 50]],
            "Line 2",
            0.90,
        ),
    ]

    result = backend._process_easyocr_result(easyocr_result, image)

    assert "Line 1" in result.content
    assert "Line 2" in result.content
    assert result.mime_type == "text/plain"
    assert result.metadata["width"] == 100
    assert result.metadata["height"] == 100
