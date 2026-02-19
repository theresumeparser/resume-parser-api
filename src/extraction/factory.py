"""Content-type dispatcher for algorithmic text extraction.

Routes incoming file bytes to the correct extractor based on the MIME
type and/or file extension.  Image inputs return an empty result because
they require OCR and cannot be handled algorithmically.
"""

import os

from src.extraction.base import ExtractionResult
from src.extraction.docx import extract_docx
from src.extraction.pdf import extract_pdf

_PDF_CONTENT_TYPES = {"application/pdf"}
_DOCX_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}
_IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp", "image/tiff"}

_PDF_EXTENSIONS = {".pdf"}
_DOCX_EXTENSIONS = {".docx"}
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tiff"}


def extract_text(
    content: bytes,
    content_type: str,
    filename: str = "",
) -> ExtractionResult:
    """Dispatch to the appropriate extractor based on file type.

    The content type is checked first; if it is unrecognised or absent,
    the file extension is used as a fallback.

    Parameters
    ----------
    content:
        Raw bytes of the uploaded file.
    content_type:
        MIME type reported by the client (e.g. ``"application/pdf"``).
    filename:
        Original filename, used as a fallback when ``content_type`` is
        not a known type.

    Returns
    -------
    ExtractionResult:
        For PDFs and DOCX files: extracted text with
        ``method="algorithmic"``.
        For images: empty text with ``method="none"`` — the caller must
        route these to OCR.

    Raises
    ------
    ValueError:
        If the file type cannot be determined from either the content
        type or the filename extension.
    """
    ct = (content_type or "").strip().lower()
    ext = os.path.splitext(filename)[-1].lower() if filename else ""

    if ct in _PDF_CONTENT_TYPES or ext in _PDF_EXTENSIONS:
        return extract_pdf(content)

    if ct in _DOCX_CONTENT_TYPES or ext in _DOCX_EXTENSIONS:
        return extract_docx(content)

    if ct in _IMAGE_CONTENT_TYPES or ext in _IMAGE_EXTENSIONS:
        # Images have no selectable text; signal that OCR is required.
        return ExtractionResult(text="", pages=1, method="none")

    raise ValueError(
        f"Unsupported file type: content_type={content_type!r}, filename={filename!r}"
    )
