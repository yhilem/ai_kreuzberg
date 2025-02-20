from __future__ import annotations

from json import dumps
from typing import Any


class KreuzbergError(Exception):
    """Base exception for all Kreuzberg errors."""

    context: Any
    """The context of the error."""

    def __init__(self, message: str, *, context: Any = None) -> None:
        self.context = context
        super().__init__(message)

    def _serialize_context(self, obj: Any) -> Any:
        """Recursively serialize context objects to ensure JSON compatibility."""
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        if isinstance(obj, dict):
            return {k: self._serialize_context(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._serialize_context(x) for x in obj]
        if isinstance(obj, Exception):
            return {
                "type": obj.__class__.__name__,
                "message": str(obj),
            }
        return obj

    def __str__(self) -> str:
        """Return a string representation of the exception."""
        if self.context:
            serialized_context = self._serialize_context(self.context)
            ctx = f"\n\nContext: {dumps(serialized_context)}"
        else:
            ctx = ""

        return f"{self.__class__.__name__}: {super().__str__()}{ctx}"


class ParsingError(KreuzbergError):
    """Raised when a parsing error occurs."""


class ValidationError(KreuzbergError):
    """Raised when a validation error occurs."""


class MissingDependencyError(KreuzbergError):
    """Raised when a dependency is missing."""


class OCRError(KreuzbergError):
    """Raised when an OCR error occurs."""
