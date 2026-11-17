"""Server-side Flask web application generation."""

from pathlib import Path

from prumo.generators.python_project import prepare_python_project
from prumo.prerequisites import Toolchain
from prumo.project.planner import ComponentPlan
from prumo.rendering import write_template

_PACKAGES = ("flask", "pytest")


def generate_flask(
    component: ComponentPlan,
    target_directory: Path,
    tools: Toolchain,
) -> None:
    """Create a Flask app that renders Jinja templates and static files."""
    values = {"PROJECT_NAME": component.project_name}
    files = {
        "app/__init__.py": "flask/__init__.py.tpl",
        "app/routes.py": "flask/routes.py.tpl",
        "templates/index.html": "flask/index.html.tpl",
        "static/styles.css": "web/styles.css.tpl",
        "tests/test_routes.py": "flask/test_routes.py.tpl",
    }
    for relative_path, template in files.items():
        write_template(target_directory / relative_path, template, values)

    prepare_python_project(component, target_directory, tools, _PACKAGES)
