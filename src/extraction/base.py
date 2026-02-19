from dataclasses import dataclass, field


@dataclass
class ExtractionResult:
    """Result of algorithmic text extraction from a document.

    Attributes
    ----------
    text:
        Extracted plain text.  Empty string when algorithmic extraction
        yields nothing (e.g. scanned image PDF) or for image uploads
        that must go straight to OCR.
    pages:
        Number of pages in the source document.  For DOCX files this is
        always 1 because python-docx does not expose page count.  For
        image files this is always 1.
    method:
        How the text was obtained.  ``"algorithmic"`` means the library
        extracted selectable text directly.  ``"none"`` means no
        algorithmic extraction was attempted (image input).
    """

    text: str
    pages: int
    method: str
    char_count: int = field(init=False)
    word_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.char_count = len(self.text)
        self.word_count = len(self.text.split()) if self.text.strip() else 0
