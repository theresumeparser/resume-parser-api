import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import ValidationError

from src.auth.dependencies import require_api_key
from src.logging import get_logger
from src.parsing.dependencies import validate_upload
from src.parsing.schemas import ParseMetadata, ParseOptions, ParseResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Parsing"])
UPLOAD_FILE_PARAM = File(..., description="Resume file (PDF, DOCX, or image)")
OPTIONS_FORM_PARAM = Form(
    default=None,
    description="JSON string with parse options (model_parse, model_ocr, ocr)",
)


@router.post(
    "/parse",
    response_model=ParseResponse,
    description="Parse a resume file and return structured data.",
    responses={
        400: {"description": "Invalid file type or corrupt file"},
        401: {"description": "Invalid or missing API key"},
        413: {"description": "File exceeds size limit"},
        422: {"description": "Invalid request or options"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def parse_resume(
    file: UploadFile = UPLOAD_FILE_PARAM,
    options: str | None = OPTIONS_FORM_PARAM,
    key_identity: str = Depends(require_api_key),
) -> ParseResponse:
    start_time = time.monotonic()

    # Parse options from form field
    parse_options = ParseOptions()
    if options:
        try:
            parse_options = ParseOptions.model_validate_json(options)
        except ValidationError as e:
            raise HTTPException(
                status_code=422,
                detail=e.errors(),
            ) from e

    # Validate the uploaded file
    await validate_upload(file)

    filename = file.filename or "unknown"
    content_type = file.content_type or "unknown"

    logger.info(
        "parse_request_received",
        key_identity=key_identity,
        filename=filename,
        content_type=content_type,
        model_parse=parse_options.model_parse,
        model_ocr=parse_options.model_ocr,
        ocr=parse_options.ocr,
    )

    # TODO: Replace with actual pipeline execution
    # For now, return a stub successful response
    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    logger.info(
        "parse_request_completed",
        key_identity=key_identity,
        filename=filename,
        processing_time_ms=elapsed_ms,
    )

    return ParseResponse(
        success=True,
        data={
            "personal_info": {},
            "summary": None,
            "experience": [],
            "education": [],
            "skills": [],
            "certifications": [],
            "languages": [],
        },
        metadata=ParseMetadata(
            extraction_method="stub",
            ocr_used=False,
            pages=0,
            processing_time_ms=elapsed_ms,
            usage=[],
        ),
    )
