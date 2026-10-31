"""Descriptor normalisation engine."""
import re
import unicodedata
from typing import Optional


class DescriptorNormalizer:
    """Standardises raw transaction descriptors into clean normalised tokens."""

    # Separators to replace with single spaces
    SEPARATOR_PATTERN = re.compile(r"[/\\_\-*|:#,;.]+")
    # Extra whitespace
    WHITESPACE_PATTERN = re.compile(r"\s+")

    @classmethod
    def normalize(cls, raw: Optional[str]) -> str:
        """Normalise a raw financial descriptor string safely.
        
        Examples:
        - " UPI/STREAMPULSE/BILLPAY/982138 " -> "upi streampulse billpay 982138"
        - "POS STRMPLSE INTL BLR" -> "pos strmplse intl blr"
        - "RAZORPAY*CLOUDDESK BLR" -> "razorpay clouddesk blr"
        """
        if raw is None:
            return ""

        text = str(raw).strip()
        if not text:
            return ""

        # Limit max input length for safety
        if len(text) > 500:
            text = text[:500].strip()

        # 1. Unicode decomposition (decompose accents/special characters)
        text = unicodedata.normalize("NFKD", text)

        # 2. Lowercase
        text = text.lower()

        # 3. Replace non-semantic delimiters with space
        text = cls.SEPARATOR_PATTERN.sub(" ", text)

        # 4. Collapse repeated whitespace
        text = cls.WHITESPACE_PATTERN.sub(" ", text).strip()

        return text

    @classmethod
    def extract_tokens(cls, normalized_text: str) -> list[str]:
        """Split normalised text into constituent tokens."""
        if not normalized_text:
            return []
        return normalized_text.split()
