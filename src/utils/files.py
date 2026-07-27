import base64


def danish_to_ascii(s: str) -> str:
    """Convert Danish characters to their ASCII equivalents."""
    return s.translate(str.maketrans({
        "æ": "ae",
        "ø": "oe",
        "å": "aa",
        "Æ": "Ae",
        "Ø": "Oe",
        "Å": "Aa",
    }))


# NOTE: Only supports PDF files (can easily be extended to support other file types if needed)
def decode_base64_file(base64_string: str) -> tuple[bytes, str]:
    """
    Decode raw base64 string into file bytes and MIME type (Note: only PDF is supported).

    Params:
        base64_string: Raw base64-encoded file content (no data URL prefix).

    Returns:
        A tuple containing:
            - file_bytes (bytes): The decoded file content.
            - mime_type (str): The detected MIME type.
    base64_string = "".join(base64_string.split())
    try:
        file_bytes = base64.b64decode(base64_string, validate=True)
    except Exception as e:
        raise ValueError("Invalid base64 content") from e

    if file_bytes.startswith(b"%PDF-"):
        return file_bytes, "application/pdf"
    raise ValueError("Unknown file type: only PDF is supported")
