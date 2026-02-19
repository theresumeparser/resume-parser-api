"""PDF text extraction using PyMuPDF (fitz)."""

import fitz  # type: ignore[import-untyped]

from src.extraction.base import ExtractionResult


def extract_pdf(content: bytes) -> ExtractionResult:
    """Extract plain text from a PDF byte string.

    Opens the PDF from the raw bytes, iterates every page, and collects
    all text blocks.  The result is the concatenated text of all pages
    separated by newlines.

    Parameters
    ----------
    content:
        Raw bytes of the PDF file.

    Returns
    -------
    ExtractionResult:
        Extracted text, page count, and extraction method set to
        ``"algorithmic"``.  If the PDF has no selectable text (e.g. a
        scanned-only document) ``text`` will be an empty or near-empty
        string — the caller should check text quality and route to OCR.
    """
    doc: fitz.Document = fitz.open(stream=content, filetype="pdf")
    pages: int = doc.page_count

    page_texts: list[str] = []
    for page in doc:
        page_texts.append(page.get_text())

    doc.close()

    text = "\n".join(page_texts)
    return ExtractionResult(text=text, pages=pages, method="algorithmic")
