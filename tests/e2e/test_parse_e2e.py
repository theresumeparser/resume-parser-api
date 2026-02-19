"""End-to-end parse tests: real server, real OpenRouter calls, real resume files.

Each test uploads the Senior Backend Developer PDF resume, parses it with an
OpenRouter model, validates the extracted data, and saves the full JSON
response to a temporary results directory.

Requirements:
  - .env with a valid OPENROUTER_API_KEY
  - .env API_KEYS containing the key used below
  - Network access to https://openrouter.ai

Run:
  uv run pytest tests/e2e/ -m e2e -v -s
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import httpx
import pytest

SERVER_PORT = 9876
BASE_URL = f"http://127.0.0.1:{SERVER_PORT}"

# Must match an entry in .env API_KEYS
API_KEY = "sk-parse-dev-key-1"
HEADERS = {"X-API-Key": API_KEY}

E2E_DIR = Path(__file__).resolve().parent
PDF_FILE = E2E_DIR / "fixtures" / "senior-backend-developer.pdf"

REQUEST_TIMEOUT = 180

MODELS = {
    "gemini_flash": "openrouter/google/gemini-2.5-flash",
    "grok_fast": "openrouter/x-ai/grok-4.1-fast",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _save_result(results_dir: Path, name: str, data: dict) -> Path:
    out = results_dir / f"{name}.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def _assert_john_doe_resume(data: dict) -> None:
    """Validate key fields from the known Senior Backend Developer resume."""
    assert data["success"] is True, f"Parse failed: {data.get('error')}"
    assert data["error"] is None
    assert data["data"] is not None

    # Personal info
    personal = data["data"]["personal_info"]
    name_lower = personal["name"].lower()
    assert "john" in name_lower and "doe" in name_lower, (
        f"Expected 'John Doe', got '{personal['name']}'"
    )

    # Experience
    experience = data["data"]["experience"]
    assert len(experience) >= 2, f"Expected >=2 experiences, got {len(experience)}"
    companies = {e["company"].lower() for e in experience}
    assert any("microsoft" in c for c in companies), (
        f"Missing Microsoft in {companies}"
    )
    assert any("google" in c for c in companies), f"Missing Google in {companies}"

    # Education
    education = data["data"]["education"]
    assert len(education) >= 1

    # Skills
    skills = data["data"]["skills"]
    assert len(skills) >= 3, f"Expected >=3 skills, got {len(skills)}"
    skill_names = {s["skill"].lower() for s in skills}
    assert any("python" in s for s in skill_names), (
        f"Missing Python in {skill_names}"
    )
    assert any("java" in s for s in skill_names), f"Missing Java in {skill_names}"

    # Metadata
    assert data["metadata"]["processing_time_ms"] > 0
    assert data["metadata"]["pages"] >= 1


def _check_server_health() -> None:
    """Verify the server is still responding before making a test request."""
    resp = httpx.get(f"{BASE_URL}/api/v1/health", timeout=10)
    assert resp.status_code == 200, f"Server health check failed: {resp.status_code}"


def _post_parse(options: dict) -> httpx.Response:
    """Upload the PDF and call the parse endpoint."""
    _check_server_health()
    with open(PDF_FILE, "rb") as f:
        return httpx.post(
            f"{BASE_URL}/api/v1/parse",
            headers=HEADERS,
            files={"file": ("senior-backend-developer.pdf", f, "application/pdf")},
            data={"options": json.dumps(options)},
            timeout=REQUEST_TIMEOUT,
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.e2e
def test_parse_pdf_with_gemini_flash(
    server: subprocess.Popen, results_dir: Path
) -> None:
    """Algorithmic extraction + Gemini 2.5 Flash parse."""
    resp = _post_parse(
        {
            "parse_models": MODELS["gemini_flash"],
            "ocr_models": "none",
            "ocr": "skip",
        }
    )

    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text}"
    data = resp.json()
    _assert_john_doe_resume(data)

    assert data["metadata"]["ocr_used"] is False

    out = _save_result(results_dir, "gemini_flash_parse", data)
    print(f"\n  Result saved: {out}")


@pytest.mark.e2e
def test_parse_pdf_with_grok_fast(
    server: subprocess.Popen, results_dir: Path
) -> None:
    """Algorithmic extraction + Grok 4.1 Fast parse."""
    resp = _post_parse(
        {
            "parse_models": MODELS["grok_fast"],
            "ocr_models": "none",
            "ocr": "skip",
        }
    )

    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text}"
    data = resp.json()
    _assert_john_doe_resume(data)

    assert data["metadata"]["ocr_used"] is False

    out = _save_result(results_dir, "grok_fast_parse", data)
    print(f"\n  Result saved: {out}")


@pytest.mark.e2e
def test_parse_pdf_with_forced_ocr(
    server: subprocess.Popen, results_dir: Path
) -> None:
    """Force OCR via Gemini 2.5 Flash + parse -- exercises the full vision pipeline."""
    resp = _post_parse(
        {
            "parse_models": MODELS["gemini_flash"],
            "ocr_models": MODELS["gemini_flash"],
            "ocr": "force",
        }
    )

    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text}"
    data = resp.json()
    _assert_john_doe_resume(data)

    usage_steps = [u["step"] for u in data["metadata"]["usage"]]
    assert "ocr" in usage_steps, f"Expected OCR step in usage, got {usage_steps}"

    out = _save_result(results_dir, "gemini_flash_ocr_forced", data)
    print(f"\n  Result saved: {out}")
