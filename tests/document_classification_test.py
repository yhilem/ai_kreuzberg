"""Tests for document classification functionality."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from kreuzberg._document_classification import (
    DOCUMENT_CLASSIFIERS,
    _get_translated_text,
    auto_detect_document_type,
    classify_document,
    classify_document_from_layout,
)
from kreuzberg._types import ExtractionConfig, ExtractionResult, Metadata, TableData
from kreuzberg.exceptions import MissingDependencyError

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("doc_type", "file_name"),
    [
        ("invoice", "invoice_test.txt"),
        ("receipt", "receipt_test.txt"),
        ("contract", "contract_test.txt"),
        ("report", "report_test.txt"),
        ("form", "form_test.txt"),
    ],
)
async def test_extract_file_with_all_document_types(doc_type: str, file_name: str, test_files_path: Path) -> None:
    """Test that document classification works for all document types."""
    from kreuzberg import extract_file

    test_file = test_files_path / file_name
    config = ExtractionConfig(auto_detect_document_type=True)
    result = await extract_file(test_file, config=config)
    assert result.document_type == doc_type
    assert result.document_type_confidence is not None
    assert result.document_type_confidence > 0.5


def test_classify_document_low_confidence() -> None:
    """Test that no document type is returned for low confidence."""
    content = "This is a generic document with no clear keywords."
    result = ExtractionResult(content=content, mime_type="text/plain", metadata={})
    config = ExtractionConfig(document_type_confidence_threshold=0.9)
    doc_type, confidence = classify_document(result, config)
    assert doc_type is None
    assert confidence is None


def test_vision_based_classification() -> None:
    """Test that vision-based document classification works."""
    import pandas as pd

    from kreuzberg._document_classification import classify_document_from_layout

    # Create a mock layout DataFrame
    layout_data = {
        "text": ["AGREEMENT", "Party A", "Signature", "Party B"],
        "top": [10, 200, 800, 810],
        "height": [10, 10, 10, 10],
    }
    layout_df = pd.DataFrame(layout_data)

    # Create a mock ExtractionResult
    result = ExtractionResult(
        content="AGREEMENT Party A Signature Party B Signature",
        mime_type="text/plain",
        metadata={},
        layout=layout_df,
    )
    config = ExtractionConfig()

    doc_type, confidence = classify_document_from_layout(result, config)
    assert doc_type == "contract"
    assert confidence is not None
    assert confidence >= 0.8


@pytest.mark.anyio
async def test_extract_file_without_document_classification(tmp_path: Path) -> None:
    """Test that document classification is not performed when disabled."""
    from kreuzberg import extract_file

    test_file = tmp_path / "test.txt"
    test_file.write_text("This is a test document.")
    config = ExtractionConfig(auto_detect_document_type=False)
    result = await extract_file(test_file, config=config)
    assert result.document_type is None
    assert result.document_type_confidence is None


class TestDocumentClassifiers:
    """Test document classifier constants."""

    def test_document_classifiers_structure(self) -> None:
        """Test that document classifiers are properly structured."""
        assert isinstance(DOCUMENT_CLASSIFIERS, dict)
        assert len(DOCUMENT_CLASSIFIERS) > 0

        # Check specific document types exist
        expected_types = {"invoice", "receipt", "contract", "report", "form"}
        assert expected_types.issubset(set(DOCUMENT_CLASSIFIERS.keys()))

        # Check all patterns are strings
        for patterns in DOCUMENT_CLASSIFIERS.values():
            assert isinstance(patterns, list)
            assert len(patterns) > 0
            for pattern in patterns:
                assert isinstance(pattern, str)
                assert len(pattern) > 0

    def test_invoice_patterns(self) -> None:
        """Test invoice document patterns."""
        invoice_patterns = DOCUMENT_CLASSIFIERS["invoice"]
        expected_patterns = {"invoice", "bill to", "invoice number", "total amount", "tax id"}
        assert set(invoice_patterns) == expected_patterns

    def test_receipt_patterns(self) -> None:
        """Test receipt document patterns."""
        receipt_patterns = DOCUMENT_CLASSIFIERS["receipt"]
        expected_patterns = {"receipt", "cash receipt", "payment", "subtotal", "total due"}
        assert set(receipt_patterns) == expected_patterns


class TestGetTranslatedText:
    """Test _get_translated_text function."""

    def test_get_translated_text_success(self) -> None:
        """Test successful text translation."""
        result = ExtractionResult(content="This is a test invoice", mime_type="text/plain", metadata={})

        # Mock the GoogleTranslator class
        mock_translator_class = Mock()
        mock_instance = Mock()
        mock_instance.translate.return_value = "This is a test invoice"
        mock_translator_class.return_value = mock_instance

        with patch.dict("sys.modules", {"deep_translator": Mock(GoogleTranslator=mock_translator_class)}):
            translated = _get_translated_text(result)

            assert translated == "this is a test invoice"
            mock_translator_class.assert_called_once_with(source="auto", target="en")
            mock_instance.translate.assert_called_once_with("This is a test invoice")

    def test_get_translated_text_with_non_english(self) -> None:
        """Test translation of non-English text."""
        result = ExtractionResult(content="Factura número 12345", mime_type="text/plain", metadata={})

        # Mock the GoogleTranslator class
        mock_translator_class = Mock()
        mock_instance = Mock()
        mock_instance.translate.return_value = "Invoice number 12345"
        mock_translator_class.return_value = mock_instance

        with patch.dict("sys.modules", {"deep_translator": Mock(GoogleTranslator=mock_translator_class)}):
            translated = _get_translated_text(result)

            assert translated == "invoice number 12345"

    def test_get_translated_text_missing_dependency(self) -> None:
        """Test handling of missing deep-translator dependency."""
        result = ExtractionResult(content="Test content", mime_type="text/plain", metadata={})

        # Mock the import to fail
        import builtins

        original_import = builtins.__import__

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "deep_translator":
                raise ImportError("No module named 'deep_translator'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(MissingDependencyError, match="deep-translator' library is not installed"):
                _get_translated_text(result)

    def test_get_translated_text_translation_error(self) -> None:
        """Test handling of translation errors."""
        result = ExtractionResult(content="Test content", mime_type="text/plain", metadata={})

        # Mock the GoogleTranslator class
        mock_translator_class = Mock()
        mock_instance = Mock()
        mock_instance.translate.side_effect = Exception("Translation failed")
        mock_translator_class.return_value = mock_instance

        with patch.dict("sys.modules", {"deep_translator": Mock(GoogleTranslator=mock_translator_class)}):
            # Should return original lowercase text on error
            translated = _get_translated_text(result)
            assert translated == "test content"

    def test_get_translated_text_empty_content(self) -> None:
        """Test translation with empty content."""
        result = ExtractionResult(content="", mime_type="text/plain", metadata={})

        # Mock the GoogleTranslator class
        mock_translator_class = Mock()
        mock_instance = Mock()
        mock_instance.translate.return_value = ""
        mock_translator_class.return_value = mock_instance

        with patch.dict("sys.modules", {"deep_translator": Mock(GoogleTranslator=mock_translator_class)}):
            translated = _get_translated_text(result)
            assert translated == ""


class TestClassifyDocument:
    """Test classify_document function."""

    def test_classify_document_text_mode_invoice(self) -> None:
        """Test text-based classification for invoice."""
        content = "INVOICE #12345\nBill To: John Doe\nTotal Amount: $100.00\nTax ID: 123456789"
        result = ExtractionResult(content=content, mime_type="text/plain", metadata={})
        config = ExtractionConfig()

        doc_type, confidence = classify_document(result, config)

        assert doc_type == "invoice"
        assert confidence is not None
        assert confidence > 0.8

    def test_classify_document_text_mode_receipt(self) -> None:
        """Test text-based classification for receipt."""
        content = "RECEIPT\nCash Receipt\nPayment received\nSubtotal: $50.00\nTotal Due: $0.00"
        result = ExtractionResult(content=content, mime_type="text/plain", metadata={})
        config = ExtractionConfig()

        doc_type, confidence = classify_document(result, config)

        assert doc_type == "receipt"
        assert confidence is not None
        assert confidence > 0.8

    def test_classify_document_text_mode_contract(self) -> None:
        """Test text-based classification for contract."""
        content = """AGREEMENT
        This agreement is entered into between Party A and Party B.
        Terms and conditions apply.
        Signature: ________________
        Date: ________________"""
        result = ExtractionResult(content=content, mime_type="text/plain", metadata={})
        config = ExtractionConfig()

        doc_type, confidence = classify_document(result, config)

        assert doc_type == "contract"
        assert confidence is not None
        assert confidence > 0.5

    def test_classify_document_high_confidence_threshold(self) -> None:
        """Test classification with high confidence threshold."""
        content = "This document contains the word invoice."
        result = ExtractionResult(content=content, mime_type="text/plain", metadata={})
        config = ExtractionConfig(document_type_confidence_threshold=0.9)

        doc_type, confidence = classify_document(result, config)

        assert doc_type is None
        assert confidence is None

    def test_classify_document_low_confidence_threshold(self) -> None:
        """Test classification with low confidence threshold."""
        content = "This document contains the word invoice."
        result = ExtractionResult(content=content, mime_type="text/plain", metadata={})
        config = ExtractionConfig(document_type_confidence_threshold=0.1)

        doc_type, confidence = classify_document(result, config)

        assert doc_type == "invoice"
        assert confidence is not None

    def test_classify_document_vision_mode_with_layout(self) -> None:
        """Test vision-based classification with layout data."""
        layout_data = {
            "text": ["INVOICE", "#12345", "Bill To:", "Total:"],
            "top": [10, 20, 100, 500],
            "height": [20, 10, 10, 10],
        }
        layout_df = pd.DataFrame(layout_data)

        result = ExtractionResult(
            content="INVOICE #12345 Bill To: Total:",
            mime_type="text/plain",
            metadata={},
            layout=layout_df,
        )
        config = ExtractionConfig()

        doc_type, confidence = classify_document(result, config)

        assert doc_type == "invoice"
        assert confidence is not None

    def test_classify_document_vision_mode_without_layout(self) -> None:
        """Test vision-based classification without layout data."""
        result = ExtractionResult(
            content="INVOICE #12345",
            mime_type="text/plain",
            metadata={},
            layout=None,
        )
        config = ExtractionConfig()

        doc_type, confidence = classify_document(result, config)

        # Should fall back to text mode
        assert doc_type == "invoice"
        assert confidence is not None

    def test_classify_document_auto_mode_with_layout(self) -> None:
        """Test auto mode classification with layout data."""
        layout_data = {
            "text": ["INVOICE", "#12345"],
            "top": [10, 20],
            "height": [20, 10],
        }
        layout_df = pd.DataFrame(layout_data)

        result = ExtractionResult(
            content="INVOICE #12345",
            mime_type="text/plain",
            metadata={},
            layout=layout_df,
        )
        config = ExtractionConfig()

        doc_type, confidence = classify_document(result, config)

        assert doc_type == "invoice"
        assert confidence is not None

    def test_classify_document_auto_mode_without_layout(self) -> None:
        """Test auto mode classification without layout data."""
        result = ExtractionResult(
            content="INVOICE #12345",
            mime_type="text/plain",
            metadata={},
            layout=None,
        )
        config = ExtractionConfig()

        doc_type, confidence = classify_document(result, config)

        assert doc_type == "invoice"
        assert confidence is not None

    def test_classify_document_no_matches(self) -> None:
        """Test classification with no pattern matches."""
        content = "This is a generic document with no specific patterns."
        result = ExtractionResult(content=content, mime_type="text/plain", metadata={})
        config = ExtractionConfig()

        doc_type, confidence = classify_document(result, config)

        assert doc_type is None
        assert confidence is None

    def test_classify_document_multiple_matches(self) -> None:
        """Test classification with multiple document type matches."""
        content = """INVOICE and RECEIPT
        This document contains patterns from multiple types.
        Invoice Number: 123
        Receipt Number: 456
        Payment received"""
        result = ExtractionResult(content=content, mime_type="text/plain", metadata={})
        config = ExtractionConfig()

        doc_type, confidence = classify_document(result, config)

        # Should return the type with highest confidence
        assert doc_type in ["invoice", "receipt"]
        assert confidence is not None


class TestClassifyDocumentFromLayout:
    """Test classify_document_from_layout function."""

    def test_classify_document_from_layout_invoice(self) -> None:
        """Test layout-based classification for invoice."""
        layout_data = {
            "text": ["INVOICE", "Invoice #", "12345", "Bill To:", "John Doe", "Total:", "$100.00"],
            "top": [10, 50, 50, 100, 120, 500, 500],
            "height": [30, 10, 10, 10, 10, 10, 10],
        }
        layout_df = pd.DataFrame(layout_data)

        result = ExtractionResult(
            content="INVOICE Invoice # 12345 Bill To: John Doe Total: $100.00",
            mime_type="text/plain",
            metadata={},
            layout=layout_df,
        )
        config = ExtractionConfig()

        doc_type, confidence = classify_document_from_layout(result, config)

        assert doc_type == "invoice"
        assert confidence is not None
        assert confidence > 0.7

    def test_classify_document_from_layout_contract(self) -> None:
        """Test layout-based classification for contract."""
        layout_data = {
            "text": ["AGREEMENT", "Between", "Party A", "and", "Party B", "Signature:", "_____", "Date:", "_____"],
            "top": [10, 100, 120, 140, 160, 800, 800, 850, 850],
            "height": [30, 10, 10, 10, 10, 10, 10, 10, 10],
        }
        layout_df = pd.DataFrame(layout_data)

        result = ExtractionResult(
            content="AGREEMENT Between Party A and Party B Signature: _____ Date: _____",
            mime_type="text/plain",
            metadata={},
            layout=layout_df,
        )
        config = ExtractionConfig()

        doc_type, confidence = classify_document_from_layout(result, config)

        assert doc_type == "contract"
        assert confidence is not None
        assert confidence > 0.7

    def test_classify_document_from_layout_missing_pandas(self) -> None:
        """Test layout classification with missing pandas dependency."""
        result = ExtractionResult(
            content="Test content",
            mime_type="text/plain",
            metadata={},
            layout=pd.DataFrame({"text": ["Test"], "top": [10], "height": [10]}),
        )
        config = ExtractionConfig()

        # Mock pandas import to fail
        import builtins

        original_import = builtins.__import__

        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name == "pandas":
                raise ImportError("No module named 'pandas'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(MissingDependencyError, match="pandas is required"):
                classify_document_from_layout(result, config)

    def test_classify_document_from_layout_no_layout(self) -> None:
        """Test layout classification with no layout data."""
        result = ExtractionResult(
            content="Test content",
            mime_type="text/plain",
            metadata={},
            layout=None,
        )
        config = ExtractionConfig()

        doc_type, confidence = classify_document_from_layout(result, config)

        assert doc_type is None
        assert confidence is None

    def test_classify_document_from_layout_empty_layout(self) -> None:
        """Test layout classification with empty layout DataFrame."""
        layout_df = pd.DataFrame({"text": [], "top": [], "height": []})

        result = ExtractionResult(
            content="",
            mime_type="text/plain",
            metadata={},
            layout=layout_df,
        )
        config = ExtractionConfig()

        doc_type, confidence = classify_document_from_layout(result, config)

        assert doc_type is None
        assert confidence is None

    def test_classify_document_from_layout_header_patterns(self) -> None:
        """Test layout classification focusing on header patterns."""
        # Large header text should boost confidence
        layout_data = {
            "text": ["INVOICE", "Some", "other", "text"],
            "top": [10, 100, 200, 300],
            "height": [50, 10, 10, 10],  # First item has large height
        }
        layout_df = pd.DataFrame(layout_data)

        result = ExtractionResult(
            content="INVOICE Some other text",
            mime_type="text/plain",
            metadata={},
            layout=layout_df,
        )
        config = ExtractionConfig()

        doc_type, confidence = classify_document_from_layout(result, config)

        assert doc_type == "invoice"
        assert confidence is not None
        assert confidence > 0.8  # Should have high confidence due to header

    def test_classify_document_from_layout_signature_area(self) -> None:
        """Test layout classification with signature area detection."""
        layout_data = {
            "text": ["Some", "text", "Signature:", "_____", "Date:", "_____"],
            "top": [10, 100, 700, 700, 750, 750],  # Signature area at bottom
            "height": [10, 10, 10, 10, 10, 10],
        }
        layout_df = pd.DataFrame(layout_data)

        result = ExtractionResult(
            content="Some text Signature: _____ Date: _____",
            mime_type="text/plain",
            metadata={},
            layout=layout_df,
        )
        config = ExtractionConfig()

        doc_type, confidence = classify_document_from_layout(result, config)

        # Signature area suggests contract or form
        assert doc_type in ["contract", "form"]
        assert confidence is not None


class TestAutoDetectDocumentType:
    """Test auto_detect_document_type function."""

    def test_auto_detect_document_type_enabled(self) -> None:
        """Test auto document type detection when enabled."""
        content = "INVOICE #12345\nBill To: John Doe\nTotal Amount: $100.00"
        result = ExtractionResult(content=content, mime_type="text/plain", metadata={})
        config = ExtractionConfig(auto_detect_document_type=True)

        updated_result = auto_detect_document_type(result, config)

        assert updated_result.document_type == "invoice"
        assert updated_result.document_type_confidence is not None
        assert updated_result.document_type_confidence > 0.5

    def test_auto_detect_document_type_disabled(self) -> None:
        """Test auto document type detection when disabled."""
        content = "INVOICE #12345\nBill To: John Doe\nTotal Amount: $100.00"
        result = ExtractionResult(content=content, mime_type="text/plain", metadata={})
        config = ExtractionConfig(auto_detect_document_type=False)

        updated_result = auto_detect_document_type(result, config)

        assert updated_result.document_type is None
        assert updated_result.document_type_confidence is None
        assert updated_result == result  # Should return unchanged

    def test_auto_detect_document_type_preserves_other_fields(self) -> None:
        """Test that auto detection preserves other result fields."""
        metadata: Metadata = {"title": "Test Document"}
        import pandas as pd

        table_df = pd.DataFrame({"Col1": ["Data"]})
        tables: list[TableData] = [
            {
                "headers": ["Col1"],
                "rows": [["Data"]],
                "text": "| Col1 |\n|------|\n| Data |",
                "df": table_df,
                "page_number": 1,
                "cropped_image": None,  # type: ignore[typeddict-item]
            }
        ]

        result = ExtractionResult(
            content="INVOICE #12345",
            mime_type="text/plain",
            metadata=metadata,
            tables=tables,
            layout=None,
        )
        config = ExtractionConfig(auto_detect_document_type=True)

        updated_result = auto_detect_document_type(result, config)

        assert updated_result.document_type == "invoice"
        assert updated_result.metadata == metadata
        assert updated_result.tables == tables

    def test_auto_detect_document_type_no_match(self) -> None:
        """Test auto detection with no document type match."""
        content = "This is a generic document with no specific patterns."
        result = ExtractionResult(content=content, mime_type="text/plain", metadata={})
        config = ExtractionConfig(auto_detect_document_type=True)

        updated_result = auto_detect_document_type(result, config)

        assert updated_result.document_type is None
        assert updated_result.document_type_confidence is None


class TestDocumentClassificationIntegration:
    """Integration tests for document classification."""

    def test_classification_with_translation(self) -> None:
        """Test classification with translation enabled."""
        content = "Factura número 12345"  # Spanish for "Invoice number 12345"
        result = ExtractionResult(content=content, mime_type="text/plain", metadata={})
        config = ExtractionConfig()

        # Mock the GoogleTranslator
        mock_translator_class = Mock()
        mock_instance = Mock()
        mock_instance.translate.return_value = "Invoice number 12345"
        mock_translator_class.return_value = mock_instance

        with patch.dict("sys.modules", {"deep_translator": Mock(GoogleTranslator=mock_translator_class)}):
            doc_type, confidence = classify_document(result, config)

            assert doc_type == "invoice"
            assert confidence is not None

    def test_classification_confidence_calculation(self) -> None:
        """Test confidence score calculation."""
        # Document with many invoice patterns should have high confidence
        content = """INVOICE
        Invoice Number: 12345
        Bill To: Customer Name
        Tax ID: 123-45-6789
        Total Amount Due: $1,000.00
        """
        result = ExtractionResult(content=content, mime_type="text/plain", metadata={})
        config = ExtractionConfig()

        doc_type, confidence = classify_document(result, config)

        assert doc_type == "invoice"
        assert confidence is not None
        assert confidence > 0.9  # Should have very high confidence

    def test_classification_edge_cases(self) -> None:
        """Test classification edge cases."""
        # Test with very short content
        result = ExtractionResult(content="Invoice", mime_type="text/plain", metadata={})
        config = ExtractionConfig()

        doc_type, confidence = classify_document(result, config)
        assert doc_type == "invoice"
        assert confidence is not None

        # Test with empty content
        result = ExtractionResult(content="", mime_type="text/plain", metadata={})
        doc_type, confidence = classify_document(result, config)
        assert doc_type is None
        assert confidence is None

        # Test with only whitespace
        result = ExtractionResult(content="   \n\t  ", mime_type="text/plain", metadata={})
        doc_type, confidence = classify_document(result, config)
        assert doc_type is None
        assert confidence is None
