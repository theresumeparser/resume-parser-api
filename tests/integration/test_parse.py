import io
import json

from httpx import AsyncClient


async def test_parse_returns_success_response(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_pdf_bytes: bytes,
) -> None:
    response = await client.post(
        "/api/v1/parse",
        headers=auth_headers,
        files={"file": ("resume.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["success"] is True
    assert body["data"] is not None
    assert "personal_info" in body["data"]
    assert "experience" in body["data"]
    assert "education" in body["data"]
    assert "skills" in body["data"]


async def test_parse_returns_metadata(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_pdf_bytes: bytes,
) -> None:
    response = await client.post(
        "/api/v1/parse",
        headers=auth_headers,
        files={"file": ("resume.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    body = response.json()
    metadata = body["metadata"]

    assert metadata["extraction_method"] == "pdf"
    assert "ocr_used" in metadata
    assert metadata["pages"] >= 1
    assert "processing_time_ms" in metadata
    assert isinstance(metadata["usage"], list)


async def test_parse_with_options(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_pdf_bytes: bytes,
) -> None:
    options = json.dumps(
        {
            "parse_models": (
                "openrouter/google/gemini-flash-1.5,openrouter/openai/gpt-4o-mini"
            ),
            "ocr_models": "openrouter/google/gemini-flash-1.5",
            "ocr": "force",
        }
    )
    response = await client.post(
        "/api/v1/parse",
        headers=auth_headers,
        files={"file": ("resume.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
        data={"options": options},
    )
    assert response.status_code == 200


async def test_parse_with_invalid_options_returns_422(
    client: AsyncClient,
    auth_headers: dict[str, str],
    sample_pdf_bytes: bytes,
) -> None:
    options = json.dumps({"ocr": "invalid_value"})
    response = await client.post(
        "/api/v1/parse",
        headers=auth_headers,
        files={"file": ("resume.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
        data={"options": options},
    )
    assert response.status_code == 422


async def test_parse_rejects_image_upload(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await client.post(
        "/api/v1/parse",
        headers=auth_headers,
        files={"file": ("photo.png", io.BytesIO(b"\x89PNG fake"), "image/png")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


async def test_parse_accepts_markdown_upload(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    md_content = (
        b"# John Doe\n\nSoftware Engineer with experience in "
        b"Python, FastAPI, Docker, and PostgreSQL.\n\n"
        b"## Experience\n\nSenior Dev at Acme Corp for five years."
    )
    response = await client.post(
        "/api/v1/parse",
        headers=auth_headers,
        files={"file": ("resume.md", io.BytesIO(md_content), "text/markdown")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["extraction_method"] == "text"


async def test_parse_accepts_txt_upload(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    txt_content = (
        b"John Doe\nSoftware Engineer\n"
        b"Experienced developer with skills in Python, FastAPI, and Docker.\n"
        b"Education: B.S. Computer Science from State University."
    )
    response = await client.post(
        "/api/v1/parse",
        headers=auth_headers,
        files={"file": ("resume.txt", io.BytesIO(txt_content), "text/plain")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["extraction_method"] == "text"


async def test_parse_without_file_returns_422(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await client.post(
        "/api/v1/parse",
        headers=auth_headers,
    )
    assert response.status_code == 422
