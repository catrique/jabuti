"""HTML pages served by the application."""

from flask import Blueprint, render_template

pages = Blueprint("pages", __name__)


@pages.get("/")
def index() -> str:
    """Render the home page."""
    return render_template("index.html", project_name="%%PROJECT_NAME%%")


@pages.get("/health")
def health() -> dict[str, str]:
    """Report that the application is running."""
    return {"status": "ok"}
