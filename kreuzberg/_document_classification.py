from __future__ import annotations

import re
from typing import TYPE_CHECKING

from kreuzberg._ocr import get_ocr_backend
from kreuzberg.exceptions import MissingDependencyError

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

if TYPE_CHECKING:
    from pathlib import Path

    from kreuzberg._types import ExtractionConfig, ExtractionResult


DOCUMENT_CLASSIFIERS = {
    "invoice": [
        r"invoice",
        r"bill to",
        r"invoice number",
        r"total amount",
        r"tax id",
    ],
    "receipt": [
        r"receipt",
        r"cash receipt",
        r"payment",
        r"subtotal",
        r"total due",
    ],
    "contract": [
        r"agreement",
        r"contract",
        r"party a",
        r"party b",
        r"terms and conditions",
        r"signature",
    ],
    "report": [r"report", r"summary", r"analysis", r"findings", r"conclusion"],
    "form": [r"form", r"fill out", r"signature", r"date", r"submit"],
}


def classify_document(result: ExtractionResult, config: ExtractionConfig) -> tuple[str | None, float | None]:
    """Classifies the document type based on keywords and patterns.

    Args:
        result: The extraction result containing the content.
        config: The extraction configuration.

    Returns:
        A tuple containing the detected document type and the confidence score,
        or (None, None) if no type is detected with sufficient confidence.
    """
    if not GoogleTranslator:
        raise MissingDependencyError(
            "The 'deep-translator' library is not installed. Please install it with: pip install 'kreuzberg[auto-classify-document-type]'"
        )

    translated_text = GoogleTranslator(source="auto", target="en").translate(result.content)
    content_lower = translated_text.lower()
    scores = dict.fromkeys(DOCUMENT_CLASSIFIERS, 0)

    for doc_type, patterns in DOCUMENT_CLASSIFIERS.items():
        for pattern in patterns:
            if re.search(pattern, content_lower):
                scores[doc_type] += 1

    total_score = sum(scores.values())
    if total_score == 0:
        return None, None

    confidences = {doc_type: score / total_score for doc_type, score in scores.items()}

    best_type, best_confidence = max(confidences.items(), key=lambda item: item[1])

    if best_confidence >= config.document_type_confidence_threshold:
        return best_type, best_confidence

    return None, None


def classify_document_from_layout(
    result: ExtractionResult, config: ExtractionConfig
) -> tuple[str | None, float | None]:
    """Classifies the document type based on layout information from OCR.

    Args:
        result: The extraction result containing the layout data.
        config: The extraction configuration.

    Returns:
        A tuple containing the detected document type and the confidence score,
        or (None, None) if no type is detected with sufficient confidence.
    """
    if not GoogleTranslator:
        raise MissingDependencyError(
            "The 'deep-translator' library is not installed. Please install it with: pip install 'kreuzberg[auto-classify-document-type]'"
        )

    if result.layout is None or result.layout.empty:
        return None, None

    layout_df = result.layout
    if not all(col in layout_df.columns for col in ["text", "top", "height"]):
        return None, None

    # Translate all text in the layout
    translated_text = GoogleTranslator(source="auto", target="en").translate_batch(layout_df["text"].tolist())
    layout_df["translated_text"] = translated_text

    page_height = layout_df["top"].max() + layout_df["height"].max()
    scores = dict.fromkeys(DOCUMENT_CLASSIFIERS, 0.0)

    for doc_type, patterns in DOCUMENT_CLASSIFIERS.items():
        for pattern in patterns:
            found_words = layout_df[layout_df["translated_text"].str.contains(pattern, case=False, na=False)]
            if not found_words.empty:
                scores[doc_type] += 1.0
                word_top = found_words.iloc[0]["top"]
                if word_top < page_height * 0.3:
                    scores[doc_type] += 0.5

    total_score = sum(scores.values())
    if total_score == 0:
        return None, None

    confidences = {doc_type: score / total_score for doc_type, score in scores.items()}

    best_type, best_confidence = max(confidences.items(), key=lambda item: item[1])

    if best_confidence >= config.document_type_confidence_threshold:
        return best_type, best_confidence

    return None, None


def auto_detect_document_type(
    result: ExtractionResult, config: ExtractionConfig, file_path: Path | None = None
) -> ExtractionResult:
    if config.document_classification_mode == "vision" and file_path:
        layout_result = get_ocr_backend("tesseract").process_file_sync(file_path, **config.get_config_dict())
        result.document_type, result.document_type_confidence = classify_document_from_layout(layout_result, config)
    else:
        result.document_type, result.document_type_confidence = classify_document(result, config)
    return result
