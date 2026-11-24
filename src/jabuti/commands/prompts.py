"""Interactive menu prompts used by Jabuti commands."""

from enum import StrEnum
from typing import TypeVar, cast

import questionary
import typer

from jabuti.project.config import (
    BACKENDS_BY_PROJECT_TYPE,
    PROJECT_TYPES_WITH_FRONTEND,
    Backend,
    Database,
    Frontend,
    MigrationStrategy,
    ProjectConfig,
    ProjectConfigError,
    ProjectType,
    validate_project_name,
)

MenuValue = TypeVar("MenuValue", bound=StrEnum)

_BACKEND_TITLES = {
    Backend.FASTAPI: "FastAPI (Python)",
    Backend.EXPRESS: "Express (Node.js)",
    Backend.FLASK: "Flask (Python)",
}
_FRONTEND_MESSAGES = {
    ProjectType.FRONTEND: "Framework:",
    ProjectType.FULLSTACK: "Frontend:",
}
_BACKEND_MESSAGES = {
    ProjectType.API: "Backend:",
    ProjectType.FULLSTACK: "Backend:",
    ProjectType.WEB_APP: "Framework:",
}
# Migrations are offered only where the scaffold creates a working mechanism.
_OFFERED_MIGRATIONS = {
    Backend.FASTAPI: MigrationStrategy.ALEMBIC,
    Backend.FLASK: MigrationStrategy.ALEMBIC,
}


class PromptCancelled(RuntimeError):
    """Raised when the user cancels an interactive menu."""


def select_option(
    message: str,
    options: tuple[tuple[str, MenuValue], ...],
) -> MenuValue:
    """Show an arrow-key menu and return its typed value."""
    choices = [
        questionary.Choice(title=title, value=value)
        for title, value in options
    ]
    answer = questionary.select(
        message,
        choices=choices,
        qmark="?",
        pointer=">",
        use_arrow_keys=True,
        use_shortcuts=False,
        instruction="Use as setas e Enter",
    ).ask()

    if answer is None:
        raise PromptCancelled

    return cast(MenuValue, answer)


def prompt_project_config() -> ProjectConfig:
    """Collect only the choices relevant to the selected project type."""
    name = _prompt_project_name()
    project_type = select_option(
        "O que você quer criar?",
        tuple((option.value, option) for option in ProjectType),
    )
    frontend = _prompt_frontend(project_type)
    backend = _prompt_backend(project_type)
    database = _prompt_database(backend)
    migrations = _prompt_migrations(backend, database)

    try:
        return ProjectConfig(
            name=name,
            project_type=project_type,
            frontend=frontend,
            backend=backend,
            database=database,
            migrations=migrations,
        )
    except ProjectConfigError as error:
        typer.echo(f"Configuração inválida: {error}", err=True)
        raise typer.Exit(code=2) from None


def _prompt_frontend(project_type: ProjectType) -> Frontend | None:
    if project_type not in PROJECT_TYPES_WITH_FRONTEND:
        return None
    return select_option(
        _FRONTEND_MESSAGES[project_type],
        tuple((option.value, option) for option in Frontend),
    )


def _prompt_backend(project_type: ProjectType) -> Backend | None:
    backends = BACKENDS_BY_PROJECT_TYPE[project_type]
    if not backends:
        return None
    return select_option(
        _BACKEND_MESSAGES[project_type],
        tuple((_BACKEND_TITLES[option], option) for option in backends),
    )


def _prompt_database(backend: Backend | None) -> Database:
    if backend is None:
        return Database.NONE
    return select_option(
        "Banco de dados:",
        tuple((option.value, option) for option in Database),
    )


def _prompt_migrations(
    backend: Backend | None,
    database: Database,
) -> MigrationStrategy:
    offered = _OFFERED_MIGRATIONS.get(backend) if backend else None
    if database is Database.NONE or offered is None:
        return MigrationStrategy.NONE
    no_migrations = MigrationStrategy.NONE
    return select_option(
        "Migrations:",
        ((offered.value, offered), (no_migrations.value, no_migrations)),
    )


def _prompt_project_name() -> str:
    while True:
        name = typer.prompt("Nome do projeto")

        try:
            validate_project_name(name)
        except ProjectConfigError as error:
            typer.echo(f"Nome inválido: {error}", err=True)
            continue

        return name
