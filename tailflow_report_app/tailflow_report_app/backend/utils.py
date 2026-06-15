"""Shared backend helpers — pure Python, no Streamlit imports."""
import io
import re
from datetime import datetime

import pandas as pd

# Emoji / pictographic ranges to strip from product names. Keeps ™ (U+2122),
# ® and ordinary punctuation — removes 🎁 and friends plus variation selectors.
_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000026FF\U00002700-\U000027BF"
    "\U0001F1E6-\U0001F1FF\U00002B00-\U00002BFF\uFE0F\u200D]"
)


def clean_name(value):
    """Remove emoji/pictographs and collapse whitespace in a product name."""
    s = _EMOJI.sub("", str(value))
    return re.sub(r"\s{2,}", " ", s).strip()


def safe_csv(uploaded, **kwargs):
    """Read a CSV from a Streamlit UploadedFile (or a path) without exhausting
    the file cursor. Streamlit UploadedFile objects can only be streamed once;
    reading them a second time silently returns an empty frame. Wrapping the
    raw bytes in a fresh BytesIO on every call avoids that.
    """
    if hasattr(uploaded, "getvalue"):
        return pd.read_csv(io.BytesIO(uploaded.getvalue()), **kwargs)
    return pd.read_csv(uploaded, **kwargs)


def detect_year(name, default="unknown"):
    """Pull a 4-digit year (20xx) out of a filename, e.g. TailflowProduct_2025.csv."""
    m = re.search(r"(20\d{2})", str(name))
    return m.group(1) if m else default


def month_label(value):
    """'2024-01-01T00:00:00' -> 'Jan-2024'."""
    d = datetime.fromisoformat(str(value)[:19])
    return d.strftime("%b-%Y")


def to_int(value, default=0):
    try:
        if pd.isna(value):
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default


def to_float(value, default=0.0):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (ValueError, TypeError):
        return default
