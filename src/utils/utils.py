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
