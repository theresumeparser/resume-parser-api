from pydantic import BaseModel, Field

# -- Request schemas --


class ParseOptions(BaseModel):
    model_parse: str | None = Field(
        default=None,
        description="Override the default parse model (e.g. 'openai/gpt-4o-mini')",
    )
    model_ocr: str | None = Field(
        default=None,
        description="Override the default OCR model (e.g. 'google/gemini-flash-1.5')",
    )
    ocr: str = Field(
        default="auto",
        pattern="^(auto|force|skip)$",
        description="OCR preference: 'auto' (detect), 'force' (always), 'skip' (never)",
    )


# -- Response schemas --


class UsageEntry(BaseModel):
    step: str
    model: str
    input_tokens: int
    output_tokens: int


class ParseMetadata(BaseModel):
    extraction_method: str = Field(
        description="How text was extracted: 'algorithmic', 'ocr_base', 'ocr_advanced'"
    )
    ocr_used: bool
    pages: int
    processing_time_ms: int
    usage: list[UsageEntry] = Field(default_factory=list)


class ParseResponse(BaseModel):
    success: bool
    data: dict[str, object] | None = Field(
        default=None,
        description="Structured resume data. None on failure.",
    )
    metadata: ParseMetadata
    error: str | None = None
