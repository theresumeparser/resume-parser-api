"""Algorithmic text extraction from PDF, DOCX, and image files.

Public API
----------
- :class:`ExtractionResult` — dataclass returned by all extractors
- :func:`extract_text` — content-type dispatcher (main entry point)
- :func:`score_quality` — compute text quality metrics
- :func:`is_text_sufficient` — convenience boolean check
"""

from src.extraction.base import ExtractionResult
from src.extraction.factory import extract_text
from src.extraction.quality import TextQuality, is_text_sufficient, score_quality

__all__ = [
    "ExtractionResult",
    "TextQuality",
    "extract_text",
    "is_text_sufficient",
    "score_quality",
]
