"""FastAPI application entry point."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="%%PROJECT_NAME%%")

# Browser origins allowed to call the API, comma-separated. Set
# FRONTEND_ORIGINS in each environment; the default only covers local work.
_origins = os.getenv("FRONTEND_ORIGINS", "%%FRONTEND_ORIGINS%%")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in _origins.split(",") if origin.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the API is running."""
    return {"status": "ok"}
