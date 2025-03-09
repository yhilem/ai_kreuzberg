from __future__ import annotations

import pytest

from kreuzberg._utils import _language


"""Tests for the language normalization functions."""

@pytest.mark.parametrize(
        ("lang_code", "expected"),
        [
            # Test standard ISO codes
            ("en", ["en"]),
            ("eng", ["en"]),
            ("fr", ["fr"]),
            ("fra", ["fr"]),
            ("de", ["de"]),
            ("deu", ["de"]),
            # Test Chinese variants
            ("zh", ["ch_sim"]),
            ("zh_hans", ["ch_sim"]),
            ("zh_hant", ["ch_tra"]),
            ("zho", ["ch_sim"]),
            # Test case insensitivity
            ("EN", ["en"]),
            ("En", ["en"]),
            ("FR", ["fr"]),
            # Test unsupported language (should default to "en")
            ("xyz", ["en"]),
            # Test languages with special mappings
            ("sr_cyrl", ["rs_cyrillic"]),
            ("sr_latn", ["rs_latin"]),
            ("srp_cyrl", ["rs_cyrillic"]),
            ("srp_latn", ["rs_latin"]),
        ],
    )
def test_to_easyocr(lang_code: str, expected: list[str]) -> None:
    """Test conversion of language codes to EasyOCR format."""
    assert _language.to_easyocr(lang_code) == expected

@pytest.mark.parametrize(
        ("lang_code", "expected"),
        [
            # Test standard ISO codes
            ("en", "en"),
            ("eng", "en"),
            ("fr", "french"),
            ("fra", "french"),
            ("de", "german"),
            ("deu", "german"),
            # Test Japanese and Korean
            ("ja", "japan"),
            ("jpn", "japan"),
            ("ko", "korean"),
            ("kor", "korean"),
            # Test Chinese variants
            ("zh", "ch"),
            ("zh_hans", "ch"),
            ("zh_hant", "ch"),
            ("zho", "ch"),
            # Test case insensitivity
            ("EN", "en"),
            ("En", "en"),
            ("FR", "french"),
            # Test unsupported language (should default to "en")
            ("es", "en"),
            ("spa", "en"),
            ("xyz", "en"),
        ],
    )
def test_to_paddle(lang_code: str, expected: str) -> None:
    """Test conversion of language codes to PaddleOCR format."""
    assert _language.to_paddle(lang_code) == expected

@pytest.mark.parametrize(
        ("lang_code", "expected"),
        [
            # Test standard ISO codes
            ("en", "eng"),
            ("eng", "eng"),
            ("fr", "fra"),
            ("fra", "fra"),
            ("de", "deu"),
            ("deu", "deu"),
            # Test languages with specific Tesseract codes
            ("cs", "ces"),
            ("el", "ell"),
            ("fa", "fas"),
            ("he", "heb"),
            ("hr", "hrv"),
            ("is", "isl"),
            # Test Chinese variants
            ("zh", "chi_sim"),
            ("zh_hans", "chi_sim"),
            ("zh_hant", "chi_tra"),
            ("zho", "chi_sim"),
            # Test Norwegian variants
            ("nb", "nor"),
            ("nn", "nor"),
            # Test case insensitivity
            ("EN", "eng"),
            ("En", "eng"),
            ("FR", "fra"),
            # Test unsupported language (should default to "eng")
            ("xyz", "eng"),
        ],
    )
def test_to_tesseract(lang_code: str, expected: str) -> None:
    """Test conversion of language codes to Tesseract format."""
    assert _language.to_tesseract(lang_code) == expected

@pytest.mark.parametrize(
        ("lang_code", "expected"),
        [
            # Test supported languages
            ("en", True),
            ("eng", True),
            ("fr", True),
            ("de", True),
            ("zh", True),  # Mapped to ch_sim
            ("zh_hans", True),  # Mapped to ch_sim
            ("zh_hant", True),  # Mapped to ch_tra
            # Test case insensitivity
            ("EN", True),
            ("Fr", True),
            # Test languages directly in EasyOCR format
            ("ch_sim", True),
            ("ch_tra", True),
            # Test unsupported languages
            ("xyz", False),
            ("invalid", False),
        ],
    )
def test_is_supported_by_easyocr(lang_code: str, expected: bool) -> None:
    """Test checking if a language is supported by EasyOCR."""
    assert _language.is_supported_by_easyocr(lang_code) == expected

@pytest.mark.parametrize(
        ("lang_code", "expected"),
        [
            # Test supported languages
            ("en", True),
            ("eng", True),
            ("fr", True),
            ("fra", True),
            ("de", True),
            ("deu", True),
            ("ja", True),
            ("jpn", True),
            ("ko", True),
            ("kor", True),
            ("zh", True),
            ("zh_hans", True),
            ("zh_hant", True),
            # Test case insensitivity
            ("EN", True),
            ("Fr", True),
            ("GERMAN", True),
            # Test languages directly in PaddleOCR format
            ("french", True),
            ("german", True),
            ("japan", True),
            ("korean", True),
            ("ch", True),
            # Test unsupported languages
            ("es", False),
            ("spa", False),
            ("it", False),
            ("ita", False),
            ("xyz", False),
        ],
    )
def test_is_supported_by_paddle(lang_code: str, expected: bool) -> None:
    """Test checking if a language is supported by PaddleOCR."""
    assert _language.is_supported_by_paddle(lang_code) == expected

@pytest.mark.parametrize(
        ("lang_code", "expected"),
        [
            # Test supported languages
            ("eng", True),
            ("fra", True),
            ("deu", True),
            ("chi_sim", True),
            ("chi_tra", True),
            # Test languages with specific Tesseract codes
            ("ces", True),
            ("ell", True),
            ("fas", True),
            ("heb", True),
            ("hrv", True),
            ("isl", True),
            # Test languages directly in Tesseract format
            ("jpn", True),
            ("kor", True),
            # Test unsupported languages
            ("xyz", False),
            ("invalid", False),
        ],
    )
def test_is_supported_by_tesseract(lang_code: str, expected: bool) -> None:
    """Test checking if a language is supported by Tesseract."""
    assert _language.is_supported_by_tesseract(lang_code) == expected

def test_default_behavior_for_unsupported_languages() -> None:
    """Test default behavior when unsupported languages are provided."""
    unsupported_lang = "xyz"

    # EasyOCR should default to "en"
    assert _language.to_easyocr(unsupported_lang) == ["en"]

    # PaddleOCR should default to "en"
    assert _language.to_paddle(unsupported_lang) == "en"

    # Tesseract should default to "eng"
    assert _language.to_tesseract(unsupported_lang) == "eng"

    # Support check should return False
    assert not _language.is_supported_by_easyocr(unsupported_lang)
    assert not _language.is_supported_by_paddle(unsupported_lang)
    assert not _language.is_supported_by_tesseract(unsupported_lang)
