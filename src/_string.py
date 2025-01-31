from charset_normalizer import detect


def safe_decode(byte_data: bytes, encoding: str | None = None) -> str:
    """Decode a byte string to a string, more safely.

    Args:
        byte_data: The byte string to decode.
        encoding: An optional encoding to use when decoding the string.

    Returns:
        The decoded string.
    """
    if not byte_data:
        return ""

    if encoding:
        try:
            return byte_data.decode(encoding)
        except UnicodeDecodeError:
            pass

    encodings = ["utf-8", "latin-1"]
    if encoding := detect(byte_data).get("encoding"):
        encodings.append(encoding)

    for encoding in encodings:
        try:
            return byte_data.decode(encoding)
        except UnicodeDecodeError:
            pass

    return byte_data.decode(errors="ignore")
