"""Facts about each supported framework shared by planning and documentation."""

from dataclasses import dataclass, replace
from enum import StrEnum

from jabuti.project.config import Backend, Framework, Frontend


class Runtime(StrEnum):
    """Runtime required to develop and run a component."""

    NODE = "Node.js"
    PYTHON = "Python"


@dataclass(frozen=True, slots=True)
class Stack:
    """Runtime, technologies and everyday commands of a framework."""

    runtime: Runtime
    technologies: tuple[str, ...]
    source_directories: tuple[str, ...]
    setup_commands: tuple[str, ...]
    run_command: str
    check_commands: tuple[str, ...]


_NODE_SETUP = ("npm install",)
_PYTHON_SETUP = (
    "python3 -m venv .venv",
    ".venv/bin/python -m pip install -r requirements.txt",
)
_PYTHON_TESTS = (".venv/bin/python -m pytest",)

_STACKS: dict[Framework, Stack] = {
    Frontend.REACT: Stack(
        runtime=Runtime.NODE,
        technologies=("React", "Vite", "TypeScript"),
        source_directories=("src/", "public/"),
        setup_commands=_NODE_SETUP,
        run_command="npm run dev",
        check_commands=("npm run lint", "npm run build"),
    ),
    Frontend.ANGULAR: Stack(
        runtime=Runtime.NODE,
        technologies=("Angular", "TypeScript"),
        source_directories=("src/", "public/"),
        setup_commands=_NODE_SETUP,
        run_command="npm start",
        check_commands=("npm run build",),
    ),
    Backend.FASTAPI: Stack(
        runtime=Runtime.PYTHON,
        technologies=("Python", "FastAPI", "Uvicorn"),
        source_directories=("app/", "tests/"),
        setup_commands=_PYTHON_SETUP,
        run_command=".venv/bin/python -m uvicorn app.main:app --reload",
        check_commands=_PYTHON_TESTS,
    ),
    Backend.FLASK: Stack(
        runtime=Runtime.PYTHON,
        technologies=("Python", "Flask", "Jinja"),
        source_directories=("app/", "templates/", "static/", "tests/"),
        setup_commands=_PYTHON_SETUP,
        run_command=".venv/bin/python -m flask --app app run --debug",
        check_commands=_PYTHON_TESTS,
    ),
    Backend.EXPRESS: Stack(
        runtime=Runtime.NODE,
        technologies=("Node.js", "Express"),
        source_directories=("src/", "tests/"),
        setup_commands=_NODE_SETUP,
        run_command="npm run dev",
        check_commands=("npm test",),
    ),
}

_EXPRESS_WEB = replace(
    _STACKS[Backend.EXPRESS],
    technologies=("Node.js", "Express", "EJS"),
    source_directories=("src/", "views/", "public/", "tests/"),
)


def stack_for(framework: Framework, serves_frontend: bool = False) -> Stack:
    """Return the stack facts of a framework in its role."""
    if framework is Backend.EXPRESS and serves_frontend:
        return _EXPRESS_WEB
    return _STACKS[framework]
