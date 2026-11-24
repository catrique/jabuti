"""Markdown fragments shared by the generated AGENTS.md and README.md."""

from collections.abc import Iterable

from jabuti.project.config import (
    Backend,
    Database,
    Frontend,
    MigrationStrategy,
    ProjectType,
)
from jabuti.project.planner import ROOT_DIRECTORY, ComponentPlan, ProjectPlan
from jabuti.project.stacks import Runtime

_ARCHITECTURE = {
    ProjectType.FRONTEND: "The application is frontend-only. It has no backend "
    "or database access.",
    ProjectType.API: "The application is a standalone API.",
    ProjectType.FULLSTACK: "Frontend and backend are independent applications "
    "in the same repository, built and run separately.",
    ProjectType.WEB_APP: "The application is a single server-side web app: the "
    "backend renders the HTML templates and serves the static files.",
}

ALEMBIC_REVISION = 'python -m alembic revision --autogenerate -m "descricao"'
ALEMBIC_UPGRADE = "python -m alembic upgrade head"
ALEMBIC_CURRENT = "python -m alembic current"


def architecture_description(plan: ProjectPlan) -> str:
    """One-sentence description of how the components relate."""
    return _ARCHITECTURE[plan.config.project_type]


def technology_lines(plan: ProjectPlan) -> list[str]:
    """Technologies used by each component."""
    return [
        f"{component_title(c)}: {', '.join(c.stack.technologies)}"
        for c in plan.components
    ]


def code_block(lines: Iterable[str], language: str = "bash") -> str:
    """Fenced code block."""
    return f"```{language}\n" + "\n".join(lines) + "\n```"


def section(title: str, *paragraphs: str, level: int = 2) -> str:
    """Markdown section with its paragraphs separated by blank lines."""
    return "\n\n".join((f"{'#' * level} {title}", *paragraphs))


def bullets(items: Iterable[str]) -> str:
    """Markdown bullet list."""
    return "\n".join(f"- {item}" for item in items)


def numbered(items: Iterable[str]) -> str:
    """Markdown numbered list."""
    return "\n".join(f"{number}. {item}" for number, item in enumerate(items, 1))


def location(component: ComponentPlan) -> str:
    """Directory of a component, as shown in documentation."""
    if component.directory == ROOT_DIRECTORY:
        return "the repository root"
    return f"`{component.directory}/`"


def component_title(component: ComponentPlan) -> str:
    """Framework name, qualified by the component directory when nested."""
    if component.directory == ROOT_DIRECTORY:
        return component.framework.value
    return f"{component.framework.value} ({component.directory}/)"


def command_lines(component: ComponentPlan) -> list[str]:
    """Commands to set up, run and check a component from the repository root."""
    stack = component.stack
    if stack.runtime is Runtime.PYTHON:
        run_command = {
            Backend.FASTAPI: "python -m uvicorn app.main:app --reload",
            Backend.FLASK: "python -m flask --app app run --debug",
        }[component.framework]
        commands = [
            "python -m pip install -r requirements.txt",
            run_command,
            "python -m pytest",
        ]
    else:
        commands = [*stack.setup_commands, stack.run_command, *stack.check_commands]
    return _from_root(component, commands)


def python_environment_setup(component: ComponentPlan) -> str:
    """Cross-platform instructions for creating and activating a Python venv."""
    prefix = [] if component.directory == ROOT_DIRECTORY else [
        f"cd {component.directory}"
    ]
    options = (
        (
            "Linux/macOS",
            "bash",
            ["python3 -m venv .venv", "source .venv/bin/activate"],
        ),
        (
            "Windows PowerShell",
            "powershell",
            ["py -m venv .venv", r".venv\Scripts\Activate.ps1"],
        ),
        (
            "Windows CMD",
            "batch",
            ["py -m venv .venv", r".venv\Scripts\activate.bat"],
        ),
    )
    blocks = [
        f"**{label}**\n\n{code_block([*prefix, *commands], language)}"
        for label, language, commands in options
    ]
    return "\n\n".join(blocks)


def migration_commands(component: ComponentPlan) -> list[str]:
    """Local commands to create and apply migrations."""
    if component.migrations is MigrationStrategy.ALEMBIC:
        return _from_root(
            component, [ALEMBIC_REVISION, ALEMBIC_UPGRADE, ALEMBIC_CURRENT]
        )
    return []


def _from_root(component: ComponentPlan, commands: list[str]) -> list[str]:
    if component.directory == ROOT_DIRECTORY:
        return commands
    return [f"cd {component.directory}", *commands]


def database_components(components: Iterable[ComponentPlan]) -> list[ComponentPlan]:
    """Components that talk to a database."""
    return [c for c in components if c.database is not Database.NONE]


def environment_components(
    components: Iterable[ComponentPlan],
) -> list[ComponentPlan]:
    """Components generated with a .env.example.

    React always has VITE_API_BASE_URL and Express always has PORT.
    """
    return [
        c
        for c in components
        if c.framework in (Frontend.REACT, Backend.EXPRESS)
        or c.database is not Database.NONE
    ]


def migration_components(components: Iterable[ComponentPlan]) -> list[ComponentPlan]:
    """Components with a migration mechanism."""
    return [c for c in components if c.migrations is not MigrationStrategy.NONE]

