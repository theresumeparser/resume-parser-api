import time

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
)
from pydantic import ValidationError

from src.auth.dependencies import require_api_key
from src.config import settings
from src.extraction.base import ExtractionError
from src.extraction.factory import extract_text
from src.extraction.quality import score_text_quality
from src.logging import get_logger
from src.parsing.dependencies import validate_upload
from src.parsing.schemas import ParseMetadata, ParseOptions, ParseResponse
from src.rate_limit import limiter

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Parsing"])
UPLOAD_FILE_PARAM = File(..., description="Resume file (PDF, DOCX, MD, or TXT)")
OPTIONS_FORM_PARAM = Form(
    default=None,
    description="JSON string with parse options (parse_models, ocr_models, ocr)",
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
@limiter.limit(lambda: settings.RATE_LIMIT)
async def parse_resume(
    request: Request,
    response: Response,
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
        parse_models=parse_options.parse_models,
        ocr_models=parse_options.ocr_models,
        ocr=parse_options.ocr,
    )

    content = await file.read()

    try:
        extraction_result = extract_text(content, content_type, filename)
    except ExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    quality = score_text_quality(extraction_result)

    # TODO: Replace with actual pipeline execution
    # For now, return extraction results as metadata with a stub data response
    elapsed_ms = int((time.monotonic() - start_time) * 1000)

    logger.info(
        "parse_request_completed",
        key_identity=key_identity,
        filename=filename,
        extraction_method=extraction_result.method,
        text_sufficient=quality.is_sufficient,
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
            extraction_method=extraction_result.method,
            ocr_used=False,
            pages=extraction_result.pages,
            processing_time_ms=elapsed_ms,
            usage=[],
        ),
    )
