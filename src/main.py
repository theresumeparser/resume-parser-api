from typing import Any

from fastapi import FastAPI

from src.config import settings
from src.health import router as health_router
from src.logging import setup_logging
from src.parsing.router import router as parsing_router

setup_logging()


def create_app() -> FastAPI:
    app_config: dict[str, Any] = {
        "title": "Resume Parser API",
        "description": (
            "Parse resumes into structured JSON with a smart extraction "
            "pipeline."
        ),
        "version": "0.1.0",
    }

    if not settings.show_docs:
        app_config.update(
            {
                "openapi_url": None,
                "docs_url": None,
                "redoc_url": None,
            }
        )

    app = FastAPI(**app_config)

    app.include_router(health_router)
    app.include_router(parsing_router)

    return app


app = create_app()
