from __future__ import annotations

from contextlib import suppress

from charset_normalizer import detect

from kreuzberg.exceptions import ParsingError


def safe_decode(byte_data: bytes, encoding: str | None = None) -> str:
    """Decode a byte string safely, removing invalid sequences.

    Args:
        byte_data: The byte string to decode.
        encoding: The encoding to use when decoding the byte string.

    Raises:
        ParsingError: If the byte string could not be decoded.

    Returns:
        The decoded string.
    """
    if not byte_data:
        return ""

    encodings = [encoding, detect(byte_data).get("encoding", ""), "utf-8", "latin-1"]

    for enc in [e for e in encodings if e]:
        with suppress(UnicodeDecodeError):
            return byte_data.decode(enc)

    raise ParsingError("Could not decode byte string. Please provide an encoding.")


def normalize_spaces(text: str) -> str:
    """Normalize the spaces in a string.

    Args:
        text: The text to sanitize.

    Returns:
        The sanitized text.
    """
    return " ".join(text.strip().split())
