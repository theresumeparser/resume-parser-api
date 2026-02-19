"""DOCX text extraction using python-docx."""

import io

from docx import Document  # type: ignore[import-untyped]

from src.extraction.base import ExtractionResult


def extract_docx(content: bytes) -> ExtractionResult:
    """Extract plain text from a DOCX byte string.

    Opens the document from a BytesIO buffer, collects the text from
    every paragraph (body paragraphs and table cells), and joins them
    with newlines.

    Parameters
    ----------
    content:
        Raw bytes of the DOCX file.

    Returns
    -------
    ExtractionResult:
        Extracted text, page count (always 1 — python-docx does not
        expose page count), and extraction method ``"algorithmic"``.
    """
    doc = Document(io.BytesIO(content))

    parts: list[str] = []

    # Body paragraphs
    for para in doc.paragraphs:
        stripped = para.text.strip()
        if stripped:
            parts.append(stripped)

    # Table cells — resumes often use tables for layout
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                stripped = cell.text.strip()
                if stripped:
                    parts.append(stripped)

    text = "\n".join(parts)
    return ExtractionResult(text=text, pages=1, method="algorithmic")
