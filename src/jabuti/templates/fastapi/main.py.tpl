"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(title="%%PROJECT_NAME%%")


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the API is running."""
    return {"status": "ok"}
