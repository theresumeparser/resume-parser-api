"""Text quality scoring heuristic.

The pipeline uses this module to decide whether algorithmically-extracted
text is good enough to send to the LLM, or whether OCR is needed first.

Scoring criteria
----------------
Three independent checks are combined into a final ``score`` (0.0-1.0):

1. **Character count** — fewer than ``MIN_CHARS`` characters almost
   certainly means the page has no selectable text.
2. **Word count** — fewer than ``MIN_WORDS`` words suggests the text is
   too fragmented to represent a real document.
3. **Alpha ratio** — the fraction of non-whitespace characters that are
   alphabetic.  A low ratio indicates the "text" is mostly symbols,
   numbers, or encoding artifacts (common in scanned PDFs whose text
   layer is garbled).

Each criterion contributes equally to the score (1/3 per criterion met).
``is_text_sufficient`` returns ``True`` only when *all three* criteria
pass — a single failing criterion is enough to route to OCR.
"""

from dataclasses import dataclass

# Minimum character count for text to be considered non-trivial.
MIN_CHARS: int = 100

# Minimum word count (whitespace-separated tokens).
MIN_WORDS: int = 20

# Minimum fraction of non-whitespace characters that must be alphabetic.
MIN_ALPHA_RATIO: float = 0.5


@dataclass(frozen=True)
class TextQuality:
    """Quality metrics for a piece of extracted text.

    Attributes
    ----------
    score:
        A float in [0.0, 1.0].  Each of the three quality criteria
        (char count, word count, alpha ratio) contributes 1/3.
    char_count:
        Total number of characters in the text.
    word_count:
        Number of whitespace-separated tokens.
    alpha_ratio:
        Fraction of non-whitespace characters that are alphabetic.
        ``0.0`` when the text is empty.
    sufficient:
        ``True`` when *all* three quality criteria pass — the text is
        ready for LLM extraction without OCR.
    """

    score: float
    char_count: int
    word_count: int
    alpha_ratio: float
    sufficient: bool


def score_quality(text: str) -> TextQuality:
    """Compute quality metrics for extracted text.

    Parameters
    ----------
    text:
        Plain text extracted from a document.

    Returns
    -------
    TextQuality:
        Quality metrics including a composite score and a convenience
        ``sufficient`` flag.
    """
    char_count = len(text)
    word_count = len(text.split()) if text.strip() else 0

    non_ws = [c for c in text if not c.isspace()]
    alpha_count = sum(1 for c in non_ws if c.isalpha())
    alpha_ratio = alpha_count / len(non_ws) if non_ws else 0.0

    passes_chars = char_count >= MIN_CHARS
    passes_words = word_count >= MIN_WORDS
    passes_alpha = alpha_ratio >= MIN_ALPHA_RATIO

    criteria_met = sum([passes_chars, passes_words, passes_alpha])
    score = criteria_met / 3.0
    sufficient = passes_chars and passes_words and passes_alpha

    return TextQuality(
        score=score,
        char_count=char_count,
        word_count=word_count,
        alpha_ratio=alpha_ratio,
        sufficient=sufficient,
    )


def is_text_sufficient(text: str) -> bool:
    """Return ``True`` if the text is good enough for LLM extraction.

    This is a convenience wrapper around :func:`score_quality` for
    callers that only need the boolean decision.
    """
    return score_quality(text).sufficient
