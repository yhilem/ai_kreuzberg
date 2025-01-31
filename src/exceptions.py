from json import dumps
from typing import Any


class KreuzbergError(Exception):
    """Base exception for all Kreuzberg errors."""

    context: Any
    """The context of the error."""

    def __init__(self, message: str, context: Any = None) -> None:
        self.context = context
        super().__init__(message)

    def __str__(self) -> str:
        """Return a string representation of the exception."""
        ctx = f"\n\nContext: {dumps(self.context)}" if self.context else ""

        return f"{self.__class__.__name__}: {super().__str__()}{ctx}"

    def __repr__(self) -> str:
        """Return a string representation of the exception."""
        return self.__str__()


class ParsingError(KreuzbergError):
    """Raised when a parsing error occurs."""


class ValidationError(KreuzbergError):
    """Raised when a validation error occurs."""
