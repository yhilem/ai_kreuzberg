"""Comprehensive tests for _document_classification.py module to improve coverage."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from kreuzberg._document_classification import (
    DOCUMENT_CLASSIFIERS,
    auto_detect_document_type,
    classify_document,
    classify_document_from_layout,
)
from kreuzberg._types import ExtractionConfig, ExtractionResult

if TYPE_CHECKING:
    from pytest_mock import MockerFixture



# Test DOCUMENT_CLASSIFIERS constant
def test_document_classifiers_constant() -> None:
    """Test that DOCUMENT_CLASSIFIERS contains expected document types."""
    expected_types = {"invoice", "receipt", "contract", "report", "form"}
    assert set(DOCUMENT_CLASSIFIERS.keys()) == expected_types

    # Check that each type has patterns
    for patterns in DOCUMENT_CLASSIFIERS.values():
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        assert all(isinstance(pattern, str) for pattern in patterns)


# Test classify_document function
def test_classify_document_disabled() -> None:
    """Test document classification when auto_detect_document_type is False."""
    result = ExtractionResult(content="This is an invoice with total amount $100", mime_type="text/plain", metadata={})
    config = ExtractionConfig(auto_detect_document_type=False)

    doc_type, confidence = classify_document(result, config)

    assert doc_type is None
    assert confidence is None


def test_classify_document_invoice(mocker: MockerFixture) -> None:
    """Test document classification for invoice type."""
    # Mock the translation function to avoid dependency
    mock_translate = mocker.patch(
        "kreuzberg._document_classification._get_translated_text",
        return_value="this is an invoice with invoice number 12345 and total amount $100",
    )

    result = ExtractionResult(
        content="This is an invoice with invoice number 12345 and total amount $100",
        mime_type="text/plain",
        metadata={},
    )
    config = ExtractionConfig(auto_detect_document_type=True, document_type_confidence_threshold=0.3)

    doc_type, confidence = classify_document(result, config)

    assert doc_type == "invoice"
    assert confidence is not None
    assert confidence > 0.3
    mock_translate.assert_called_once_with(result)


def test_classify_document_receipt(mocker: MockerFixture) -> None:
    """Test document classification for receipt type."""
    mocker.patch(
        "kreuzberg._document_classification._get_translated_text",
        return_value="cash receipt subtotal $50 total due $55",
    )

    result = ExtractionResult(content="Cash receipt subtotal $50 total due $55", mime_type="text/plain", metadata={})
    config = ExtractionConfig(auto_detect_document_type=True, document_type_confidence_threshold=0.3)

    doc_type, confidence = classify_document(result, config)

    assert doc_type == "receipt"
    assert confidence is not None
    assert confidence > 0.3


def test_classify_document_contract(mocker: MockerFixture) -> None:
    """Test document classification for contract type."""
    mocker.patch(
        "kreuzberg._document_classification._get_translated_text",
        return_value="this agreement between party a and party b includes terms and conditions",
    )

    result = ExtractionResult(
        content="This agreement between party A and party B includes terms and conditions",
        mime_type="text/plain",
        metadata={},
    )
    config = ExtractionConfig(auto_detect_document_type=True, document_type_confidence_threshold=0.3)

    doc_type, confidence = classify_document(result, config)

    assert doc_type == "contract"
    assert confidence is not None
    assert confidence > 0.3


def test_classify_document_no_match(mocker: MockerFixture) -> None:
    """Test document classification with no matching patterns."""
    mocker.patch(
        "kreuzberg._document_classification._get_translated_text",
        return_value="this is just some random text with no specific document indicators",
    )

    result = ExtractionResult(
        content="This is just some random text with no specific document indicators",
        mime_type="text/plain",
        metadata={},
    )
    config = ExtractionConfig(auto_detect_document_type=True)

    doc_type, confidence = classify_document(result, config)

    assert doc_type is None
    assert confidence is None


def test_classify_document_low_confidence(mocker: MockerFixture) -> None:
    """Test document classification with confidence below threshold."""
    mocker.patch(
        "kreuzberg._document_classification._get_translated_text",
        return_value="random text without clear patterns",  # No strong matches
    )

    result = ExtractionResult(content="random text", mime_type="text/plain", metadata={})
    config = ExtractionConfig(auto_detect_document_type=True, document_type_confidence_threshold=0.8)

    doc_type, confidence = classify_document(result, config)

    # With no matches, should not classify
    assert doc_type is None
    assert confidence is None


def test_classify_document_with_metadata(mocker: MockerFixture) -> None:
    """Test document classification including metadata."""
    # The _get_translated_text function should be called with result that includes metadata
    mock_translate = mocker.patch(
        "kreuzberg._document_classification._get_translated_text",
        return_value="invoice document title invoice number 12345",
    )

    result = ExtractionResult(content="Document content", mime_type="text/plain", metadata={"title": "Invoice"})
    config = ExtractionConfig(auto_detect_document_type=True, document_type_confidence_threshold=0.3)

    doc_type, confidence = classify_document(result, config)

    assert doc_type == "invoice"
    mock_translate.assert_called_once_with(result)


# Test classify_document_from_layout function
def test_classify_document_from_layout_disabled() -> None:
    """Test layout-based classification when auto_detect_document_type is False."""
    result = ExtractionResult(content="Test content", mime_type="text/plain", metadata={})
    config = ExtractionConfig(auto_detect_document_type=False)

    doc_type, confidence = classify_document_from_layout(result, config)

    assert doc_type is None
    assert confidence is None


def test_classify_document_from_layout_no_layout() -> None:
    """Test layout-based classification with no layout data."""
    result = ExtractionResult(content="Test content", mime_type="text/plain", metadata={}, layout=None)
    config = ExtractionConfig(auto_detect_document_type=True)

    doc_type, confidence = classify_document_from_layout(result, config)

    assert doc_type is None
    assert confidence is None


def test_classify_document_from_layout_empty_layout() -> None:
    """Test layout-based classification with empty layout data."""
    empty_df = pd.DataFrame()
    result = ExtractionResult(content="Test content", mime_type="text/plain", metadata={}, layout=empty_df)
    config = ExtractionConfig(auto_detect_document_type=True)

    doc_type, confidence = classify_document_from_layout(result, config)

    assert doc_type is None
    assert confidence is None


def test_classify_document_from_layout_missing_columns():
    """Test layout-based classification with missing required columns."""
    layout_df = pd.DataFrame({"text": ["some text"], "left": [10]})  # Missing "top" and "height"
    result = ExtractionResult(content="Test content", mime_type="text/plain", metadata={}, layout=layout_df)
    config = ExtractionConfig(auto_detect_document_type=True)

    doc_type, confidence = classify_document_from_layout(result, config)

    assert doc_type is None
    assert confidence is None


def test_classify_document_from_layout_invoice(mocker: MockerFixture):
    """Test layout-based classification for invoice."""
    layout_df = pd.DataFrame(
        {
            "text": ["INVOICE", "Invoice Number: 12345", "Total Amount: $500"],
            "top": [10, 50, 100],
            "height": [20, 15, 15],
        }
    )

    result = ExtractionResult(content="Test content", mime_type="text/plain", metadata={}, layout=layout_df)
    config = ExtractionConfig(auto_detect_document_type=True, document_type_confidence_threshold=0.3)

    # Mock the GoogleTranslator
    mock_translator = mocker.Mock()
    mock_translator.translate.return_value = "invoice invoice number 12345 total amount $500"
    mocker.patch("deep_translator.GoogleTranslator", return_value=mock_translator)

    doc_type, confidence = classify_document_from_layout(result, config)

    assert doc_type == "invoice"
    assert confidence is not None
    assert confidence > 0.3


def test_classify_document_from_layout_translation_error(mocker: MockerFixture):
    """Test layout-based classification when translation fails."""
    layout_df = pd.DataFrame({"text": ["INVOICE", "Total Amount: $500"], "top": [10, 50], "height": [20, 15]})

    result = ExtractionResult(content="Test content", mime_type="text/plain", metadata={}, layout=layout_df)
    config = ExtractionConfig(auto_detect_document_type=True, document_type_confidence_threshold=0.3)

    # Mock the GoogleTranslator to raise an exception
    mocker.patch("deep_translator.GoogleTranslator", side_effect=Exception("Translation failed"))

    doc_type, confidence = classify_document_from_layout(result, config)

    assert doc_type == "invoice"  # Should still work with fallback text
    assert confidence is not None
    assert confidence > 0.3


def test_classify_document_from_layout_header_bonus():
    """Test layout-based classification with header position bonus."""
    layout_df = pd.DataFrame(
        {
            "text": ["INVOICE"],  # This appears at the top, should get bonus
            "top": [5],  # Very close to top (< 30% of page height)
            "height": [20],
        }
    )

    result = ExtractionResult(content="Test content", mime_type="text/plain", metadata={}, layout=layout_df)
    config = ExtractionConfig(auto_detect_document_type=True, document_type_confidence_threshold=0.3)

    # Don't mock translation - should work with lowercase fallback
    doc_type, confidence = classify_document_from_layout(result, config)

    assert doc_type == "invoice"
    assert confidence is not None


# Test _get_translated_text function
def test_get_translated_text_basic(mocker: MockerFixture):
    """Test basic text translation functionality."""
    from kreuzberg._document_classification import _get_translated_text

    mock_translator = mocker.Mock()
    mock_translator.translate.return_value = "This is translated text"
    mocker.patch("deep_translator.GoogleTranslator", return_value=mock_translator)

    result = ExtractionResult(content="Original text", mime_type="text/plain", metadata={})

    translated = _get_translated_text(result)

    assert translated == "this is translated text"
    mock_translator.translate.assert_called_once_with("Original text")


def test_get_translated_text_with_metadata(mocker: MockerFixture):
    """Test text translation with metadata included."""
    from kreuzberg._document_classification import _get_translated_text

    mock_translator = mocker.Mock()
    mock_translator.translate.return_value = "Translated content with metadata"
    mocker.patch("deep_translator.GoogleTranslator", return_value=mock_translator)

    result = ExtractionResult(content="Original content", mime_type="text/plain", metadata={"title": "Document Title"})

    translated = _get_translated_text(result)

    assert translated == "translated content with metadata"
    # Should include metadata values in the text to translate
    expected_call = "Original content Document Title"
    mock_translator.translate.assert_called_once_with(expected_call)


def test_get_translated_text_translation_error(mocker: MockerFixture):
    """Test text translation fallback when translation fails."""
    from kreuzberg._document_classification import _get_translated_text

    # Mock GoogleTranslator to raise an exception
    mocker.patch("deep_translator.GoogleTranslator", side_effect=Exception("Translation API error"))

    result = ExtractionResult(content="Original Text", mime_type="text/plain", metadata={})

    translated = _get_translated_text(result)

    # Should fallback to lowercase original text
    assert translated == "original text"


# Note: Test for missing dependency is covered by pragma: no cover in the source code


# Test auto_detect_document_type function
def test_auto_detect_document_type_text_mode(mocker: MockerFixture):
    """Test auto_detect_document_type in text mode."""
    mock_classify = mocker.patch("kreuzberg._document_classification.classify_document", return_value=("invoice", 0.8))

    result = ExtractionResult(content="Invoice content", mime_type="text/plain", metadata={})
    config = ExtractionConfig(auto_detect_document_type=True, document_classification_mode="text")

    updated_result = auto_detect_document_type(result, config)

    assert updated_result.document_type == "invoice"
    assert updated_result.document_type_confidence == 0.8
    mock_classify.assert_called_once_with(result, config)


def test_auto_detect_document_type_vision_mode_with_file(mocker: MockerFixture):
    """Test auto_detect_document_type in vision mode with file path."""
    # Mock OCR backend
    mock_ocr_result = ExtractionResult(
        content="OCR extracted text",
        mime_type="text/plain",
        metadata={},
        layout=pd.DataFrame({"text": ["INVOICE", "Total: $100"], "top": [10, 50], "height": [20, 15]}),
    )

    mock_ocr_backend = mocker.Mock()
    mock_ocr_backend.process_file_sync.return_value = mock_ocr_result
    mocker.patch("kreuzberg._document_classification.get_ocr_backend", return_value=mock_ocr_backend)

    mock_classify_layout = mocker.patch(
        "kreuzberg._document_classification.classify_document_from_layout", return_value=("invoice", 0.9)
    )

    result = ExtractionResult(content="Original content", mime_type="text/plain", metadata={})
    config = ExtractionConfig(auto_detect_document_type=True, document_classification_mode="vision")
    file_path = Path("/path/to/test.pdf")

    updated_result = auto_detect_document_type(result, config, file_path)

    assert updated_result.document_type == "invoice"
    assert updated_result.document_type_confidence == 0.9
    mock_classify_layout.assert_called_once_with(mock_ocr_result, config)


def test_auto_detect_document_type_vision_mode_no_file(mocker: MockerFixture):
    """Test auto_detect_document_type in vision mode without file path."""
    mock_classify = mocker.patch("kreuzberg._document_classification.classify_document", return_value=("report", 0.7))

    result = ExtractionResult(content="Report content", mime_type="text/plain", metadata={})
    config = ExtractionConfig(auto_detect_document_type=True, document_classification_mode="vision")

    updated_result = auto_detect_document_type(result, config, file_path=None)

    assert updated_result.document_type == "report"
    assert updated_result.document_type_confidence == 0.7
    mock_classify.assert_called_once_with(result, config)


def test_auto_detect_document_type_with_existing_layout(mocker: MockerFixture):
    """Test auto_detect_document_type with existing layout data."""
    layout_df = pd.DataFrame({"text": ["CONTRACT", "Agreement between parties"], "top": [10, 50], "height": [20, 15]})

    result = ExtractionResult(content="Contract content", mime_type="text/plain", metadata={}, layout=layout_df)

    mock_classify_layout = mocker.patch(
        "kreuzberg._document_classification.classify_document_from_layout", return_value=("contract", 0.85)
    )

    config = ExtractionConfig(auto_detect_document_type=True)

    updated_result = auto_detect_document_type(result, config)

    assert updated_result.document_type == "contract"
    assert updated_result.document_type_confidence == 0.85
    mock_classify_layout.assert_called_once_with(result, config)


def test_auto_detect_document_type_mixed_patterns(mocker: MockerFixture):
    """Test document classification with mixed patterns from different types."""
    mocker.patch(
        "kreuzberg._document_classification._get_translated_text",
        return_value="invoice receipt contract report form",  # Contains patterns from all types
    )

    result = ExtractionResult(content="Mixed document with various keywords", mime_type="text/plain", metadata={})
    config = ExtractionConfig(auto_detect_document_type=True, document_type_confidence_threshold=0.15)

    doc_type, confidence = classify_document(result, config)

    # Should pick the type with the most matches or highest confidence
    assert doc_type is not None
    assert confidence is not None
    assert confidence >= 0.15


def test_classify_document_confidence_calculation(mocker: MockerFixture):
    """Test confidence calculation in document classification."""
    # Create a scenario where we can predict the confidence
    mocker.patch(
        "kreuzberg._document_classification._get_translated_text",
        return_value="invoice invoice number total amount",  # 3 invoice matches
    )

    result = ExtractionResult(content="Test content", mime_type="text/plain", metadata={})
    config = ExtractionConfig(auto_detect_document_type=True, document_type_confidence_threshold=0.5)

    doc_type, confidence = classify_document(result, config)

    assert doc_type == "invoice"
    assert confidence == 1.0  # All 3 matches are for invoice, so 3/3 = 1.0
