import io
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from src.auth.base import BaseAuthProvider
from src.auth.factory import get_auth_provider, reset_auth_provider
from src.main import app

TEST_API_KEY = "sk-parse-test-key"
INVALID_API_KEY = "sk-parse-invalid"


class StubAuthProvider(BaseAuthProvider):
    """Auth provider for tests — accepts only TEST_API_KEY."""

    async def validate_key(self, api_key: str) -> bool:
        return api_key == TEST_API_KEY

    async def get_key_identity(self, api_key: str) -> str:
        return "test-identity"


@pytest.fixture(autouse=True)
def _override_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace auth provider with a test stub for all tests."""
    reset_auth_provider()
    _stub = StubAuthProvider()
    monkeypatch.setattr(
        "src.auth.factory._instance",
        _stub,
    )
    yield  # type: ignore[misc]
    reset_auth_provider()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture
def invalid_auth_headers() -> dict[str, str]:
    return {"X-API-Key": INVALID_API_KEY}


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Minimal valid-ish PDF bytes for upload testing.

    This is not a real PDF — just enough to pass the upload endpoint.
    Real PDF parsing tests will use actual fixture files.
    """
    return b"%PDF-1.4 fake resume content for testing"


@pytest.fixture
def sample_pdf_file(sample_pdf_bytes: bytes) -> tuple[str, io.BytesIO, str]:
    """Returns (filename, file-like, content_type) tuple for upload."""
    return ("resume.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")
