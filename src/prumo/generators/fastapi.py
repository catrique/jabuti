"""Minimal FastAPI API generation."""

from pathlib import Path

from prumo.generators.python_project import prepare_python_project
from prumo.prerequisites import Toolchain
from prumo.project.planner import ComponentPlan
from prumo.rendering import write_template, write_text_file

_PACKAGES = ("fastapi", "uvicorn", "pytest", "httpx")


def generate_fastapi(
    component: ComponentPlan,
    target_directory: Path,
    tools: Toolchain,
) -> None:
    """Create the FastAPI application, its test and its .venv."""
    values = {"PROJECT_NAME": component.project_name}
    write_text_file(target_directory / "app" / "__init__.py", "")
    write_template(target_directory / "app" / "main.py", "fastapi/main.py.tpl", values)
    write_template(
        target_directory / "tests" / "test_health.py",
        "fastapi/test_health.py.tpl",
    )
    prepare_python_project(component, target_directory, tools, _PACKAGES)
