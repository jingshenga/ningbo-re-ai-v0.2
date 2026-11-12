"""Text normalization shared by parser evaluation and sample validation."""
import re
import unicodedata


def normalize_text_for_comparison(value: str) -> str:
    """Collapse whitespace and canonical Unicode forms for text comparisons."""
    return unicodedata.normalize('NFC', re.sub(r'\s+', ' ', value).strip())
