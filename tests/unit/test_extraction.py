"""Unit tests for the src/extraction/ module.

Tests cover:
- PDF text extraction (real PDF fixture with selectable text)
- DOCX text extraction (real DOCX fixture)
- Text quality scoring heuristic
- Content-type factory dispatch (PDF, DOCX, image, unknown)
"""

import os

import pytest

from src.extraction import (
    ExtractionResult,
    TextQuality,
    extract_text,
    is_text_sufficient,
    score_quality,
)
from src.extraction.docx import extract_docx
from src.extraction.pdf import extract_pdf
from src.extraction.quality import MIN_ALPHA_RATIO, MIN_CHARS, MIN_WORDS

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def _fixture_bytes(filename: str) -> bytes:
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path, "rb") as f:
        return f.read()


# ---------------------------------------------------------------------------
# ExtractionResult dataclass
# ---------------------------------------------------------------------------


class TestExtractionResult:
    def test_char_and_word_counts_computed(self) -> None:
        r = ExtractionResult(text="hello world foo", pages=1, method="algorithmic")
        assert r.char_count == 15
        assert r.word_count == 3

    def test_empty_text(self) -> None:
        r = ExtractionResult(text="", pages=1, method="none")
        assert r.char_count == 0
        assert r.word_count == 0

    def test_whitespace_only_text(self) -> None:
        r = ExtractionResult(text="   \n\t  ", pages=1, method="algorithmic")
        assert r.word_count == 0


# ---------------------------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------------------------


class TestExtractPdf:
    def test_returns_extraction_result(self) -> None:
        content = _fixture_bytes("sample_resume.pdf")
        result = extract_pdf(content)
        assert isinstance(result, ExtractionResult)

    def test_method_is_algorithmic(self) -> None:
        content = _fixture_bytes("sample_resume.pdf")
        result = extract_pdf(content)
        assert result.method == "algorithmic"

    def test_extracts_known_text(self) -> None:
        content = _fixture_bytes("sample_resume.pdf")
        result = extract_pdf(content)
        assert "Jane Smith" in result.text
        assert "Python" in result.text

    def test_page_count_is_correct(self) -> None:
        content = _fixture_bytes("sample_resume.pdf")
        result = extract_pdf(content)
        assert result.pages == 1

    def test_char_count_populated(self) -> None:
        content = _fixture_bytes("sample_resume.pdf")
        result = extract_pdf(content)
        assert result.char_count > 0


# ---------------------------------------------------------------------------
# DOCX extraction
# ---------------------------------------------------------------------------


class TestExtractDocx:
    def test_returns_extraction_result(self) -> None:
        content = _fixture_bytes("sample_resume.docx")
        result = extract_docx(content)
        assert isinstance(result, ExtractionResult)

    def test_method_is_algorithmic(self) -> None:
        content = _fixture_bytes("sample_resume.docx")
        result = extract_docx(content)
        assert result.method == "algorithmic"

    def test_extracts_known_text(self) -> None:
        content = _fixture_bytes("sample_resume.docx")
        result = extract_docx(content)
        assert "Jane Smith" in result.text
        assert "Python" in result.text

    def test_pages_is_one(self) -> None:
        """DOCX does not expose page count; always returns 1."""
        content = _fixture_bytes("sample_resume.docx")
        result = extract_docx(content)
        assert result.pages == 1

    def test_word_count_populated(self) -> None:
        content = _fixture_bytes("sample_resume.docx")
        result = extract_docx(content)
        assert result.word_count > 0


# ---------------------------------------------------------------------------
# Text quality scoring
# ---------------------------------------------------------------------------


class TestScoreQuality:
    def test_returns_text_quality(self) -> None:
        result = score_quality("hello world")
        assert isinstance(result, TextQuality)

    def test_empty_text_scores_zero(self) -> None:
        q = score_quality("")
        assert q.score == 0.0
        assert q.sufficient is False

    def test_sufficient_text_scores_one(self) -> None:
        # Build text that passes all three criteria
        good = ("The quick brown fox jumps over the lazy dog. " * 5).strip()
        q = score_quality(good)
        assert q.score == pytest.approx(1.0)
        assert q.sufficient is True

    def test_short_text_fails_char_criterion(self) -> None:
        # Text with fewer than MIN_CHARS characters
        short = "Hi there " * 5  # 45 chars, below MIN_CHARS=100
        q = score_quality(short)
        assert q.char_count < MIN_CHARS
        assert q.sufficient is False

    def test_low_word_count_fails(self) -> None:
        # Build a string > MIN_CHARS chars but < MIN_WORDS words
        few_words = "A" * (MIN_CHARS + 10)  # no spaces → 1 word
        q = score_quality(few_words)
        assert q.word_count < MIN_WORDS
        assert q.sufficient is False

    def test_low_alpha_ratio_fails(self) -> None:
        # Mostly digits/symbols; real text is sparse
        garbage = "1234567890!@#$%^&*() " * 20
        q = score_quality(garbage)
        assert q.alpha_ratio < MIN_ALPHA_RATIO
        assert q.sufficient is False

    def test_alpha_ratio_pure_text(self) -> None:
        text = "abcdefghij " * 20
        q = score_quality(text)
        assert q.alpha_ratio == pytest.approx(1.0)

    def test_score_partial_criteria(self) -> None:
        # Passes char count and word count but has poor alpha ratio
        mixed = ("abc123!@# " * 25).strip()
        q = score_quality(mixed)
        assert 0.0 < q.score < 1.0

    def test_real_resume_pdf_text_is_sufficient(self) -> None:
        content = _fixture_bytes("sample_resume.pdf")
        result = extract_pdf(content)
        q = score_quality(result.text)
        assert q.sufficient is True


class TestIsTextSufficient:
    def test_empty_is_not_sufficient(self) -> None:
        assert is_text_sufficient("") is False

    def test_good_text_is_sufficient(self) -> None:
        good = ("The quick brown fox jumps over the lazy dog. " * 5).strip()
        assert is_text_sufficient(good) is True

    def test_garbage_is_not_sufficient(self) -> None:
        garbage = "!!!! #### %%%% &&&& " * 10
        assert is_text_sufficient(garbage) is False


# ---------------------------------------------------------------------------
# Factory dispatch
# ---------------------------------------------------------------------------


class TestExtractText:
    def test_dispatches_pdf_by_content_type(self) -> None:
        content = _fixture_bytes("sample_resume.pdf")
        result = extract_text(content, "application/pdf", "resume.pdf")
        assert result.method == "algorithmic"
        assert "Jane Smith" in result.text

    def test_dispatches_pdf_by_extension(self) -> None:
        content = _fixture_bytes("sample_resume.pdf")
        # Blank content_type, rely on filename extension
        result = extract_text(content, "", "resume.pdf")
        assert result.method == "algorithmic"

    def test_dispatches_docx_by_content_type(self) -> None:
        content = _fixture_bytes("sample_resume.docx")
        ct = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        result = extract_text(content, ct, "resume.docx")
        assert result.method == "algorithmic"
        assert "Jane Smith" in result.text

    def test_dispatches_docx_by_extension(self) -> None:
        content = _fixture_bytes("sample_resume.docx")
        result = extract_text(content, "", "resume.docx")
        assert result.method == "algorithmic"

    def test_image_returns_none_method(self) -> None:
        # Minimal PNG header bytes (not a real image, but type dispatch is based on CT)
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        result = extract_text(fake_png, "image/png", "photo.png")
        assert result.method == "none"
        assert result.text == ""
        assert result.pages == 1

    def test_image_jpeg_returns_none_method(self) -> None:
        result = extract_text(b"\xff\xd8\xff" + b"\x00" * 50, "image/jpeg", "scan.jpg")
        assert result.method == "none"

    def test_image_dispatch_by_extension(self) -> None:
        result = extract_text(b"\x89PNG" + b"\x00" * 50, "", "scan.png")
        assert result.method == "none"

    def test_unknown_type_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_text(b"hello", "text/plain", "resume.txt")

    def test_unknown_type_no_filename_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_text(b"hello", "application/octet-stream", "")
