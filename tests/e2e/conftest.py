"""Fixtures for end-to-end tests that start a real API server subprocess."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Generator

import httpx
import pytest

SERVER_PORT = 9876
BASE_URL = f"http://127.0.0.1:{SERVER_PORT}"
PROJECT_ROOT = Path(__file__).resolve().parents[2]

STARTUP_TIMEOUT_S = 30
SHUTDOWN_TIMEOUT_S = 10


@pytest.fixture(scope="module")
def results_dir() -> Path:
    """Persistent temp directory where parsed JSON results and logs are saved."""
    d = Path(tempfile.mkdtemp(prefix="resume_e2e_"))
    print(f"\n  E2E results directory: {d}")
    return d


@pytest.fixture(scope="module")
def server(results_dir: Path) -> Generator[subprocess.Popen[bytes], None, None]:
    """Start uvicorn in a subprocess and wait until the health endpoint responds.

    Server stdout/stderr is streamed to ``run.log`` inside the results directory.
    """
    log_path = results_dir / "run.log"
    log_file = open(log_path, "wb")  # noqa: SIM115
    print(f"  Server log: {log_path}")

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(SERVER_PORT),
        ],
        cwd=str(PROJECT_ROOT),
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )

    deadline = time.monotonic() + STARTUP_TIMEOUT_S
    while time.monotonic() < deadline:
        try:
            r = httpx.get(f"{BASE_URL}/api/v1/health", timeout=2)
            if r.status_code == 200:
                break
        except (httpx.ConnectError, httpx.ReadError):
            pass

        if proc.poll() is not None:
            log_file.close()
            log_content = log_path.read_text(encoding="utf-8", errors="replace")
            pytest.fail(
                f"Server process exited early (code {proc.returncode}).\n{log_content}"
            )

        time.sleep(0.5)
    else:
        proc.kill()
        log_file.close()
        log_content = log_path.read_text(encoding="utf-8", errors="replace")
        pytest.fail(
            f"Server did not become healthy within {STARTUP_TIMEOUT_S}s.\n{log_content}"
        )

    yield proc

    proc.terminate()
    try:
        proc.wait(timeout=SHUTDOWN_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    finally:
        log_file.close()
