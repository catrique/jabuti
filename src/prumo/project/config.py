"""Project configuration and validation rules."""

import re
from dataclasses import dataclass
from enum import StrEnum

_PROJECT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
_MAX_PROJECT_NAME_LENGTH = 100
_WINDOWS_RESERVED_NAMES = {
    "AUX",
    "CON",
    "NUL",
    "PRN",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


class ProjectConfigError(ValueError):
    """Raised when a project configuration is invalid."""


class ProjectType(StrEnum):
    """Top-level project types offered by Prumo."""

    FRONTEND = "Frontend"
    API = "API"
    FULLSTACK = "Fullstack"
    WEB_APP = "Aplicação web"


class Frontend(StrEnum):
    """Frontend frameworks understood by Prumo."""

    REACT = "React"
    ANGULAR = "Angular"


class Backend(StrEnum):
    """Backend frameworks understood by Prumo."""

    FASTAPI = "FastAPI"
    EXPRESS = "Express"
    FLASK = "Flask"


class Topology(StrEnum):
    """How the components of a project relate to each other."""

    STANDALONE = "Aplicação única"
    SEPARATED = "Separada"
    BACKEND_SERVES_FRONTEND = "Backend serve frontend"


class Database(StrEnum):
    """Database choices understood by Prumo."""

    NONE = "Nenhum"
    MYSQL = "MySQL"


class MigrationStrategy(StrEnum):
    """Schema migration mechanisms understood by Prumo."""

    NONE = "Nenhuma"
    ALEMBIC = "Alembic"
    NPM_SCRIPT = "npm run migrar"


Framework = Frontend | Backend

PYTHON_BACKENDS = frozenset({Backend.FASTAPI, Backend.FLASK})

BACKENDS_BY_PROJECT_TYPE: dict[ProjectType, tuple[Backend, ...]] = {
    ProjectType.FRONTEND: (),
    ProjectType.API: (Backend.FASTAPI, Backend.EXPRESS),
    ProjectType.FULLSTACK: (Backend.FASTAPI, Backend.EXPRESS),
    ProjectType.WEB_APP: (Backend.FLASK, Backend.EXPRESS),
}

MIGRATIONS_BY_BACKEND: dict[Backend, tuple[MigrationStrategy, ...]] = {
    Backend.FASTAPI: (MigrationStrategy.ALEMBIC,),
    Backend.FLASK: (MigrationStrategy.ALEMBIC,),
    Backend.EXPRESS: (MigrationStrategy.NPM_SCRIPT,),
}

PROJECT_TYPES_WITH_FRONTEND = frozenset({ProjectType.FRONTEND, ProjectType.FULLSTACK})

_TOPOLOGY_BY_PROJECT_TYPE = {
    ProjectType.FRONTEND: Topology.STANDALONE,
    ProjectType.API: Topology.STANDALONE,
    ProjectType.FULLSTACK: Topology.SEPARATED,
    ProjectType.WEB_APP: Topology.BACKEND_SERVES_FRONTEND,
}

# Angular CLI only accepts names made of letter-initiated, dash-separated words.
_ANGULAR_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9]*(-[A-Za-z][A-Za-z0-9]*)*$")


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    """Validated choices for a project."""

    name: str
    project_type: ProjectType
    frontend: Frontend | None = None
    backend: Backend | None = None
    database: Database = Database.NONE
    migrations: MigrationStrategy = MigrationStrategy.NONE

    def __post_init__(self) -> None:
        validate_project_name(self.name)
        validate_project_components(self)

    @property
    def topology(self) -> Topology:
        """Topology implied by the project type."""
        return _TOPOLOGY_BY_PROJECT_TYPE[self.project_type]

def validate_project_name(name: str) -> None:
    """Ensure a name is a safe, portable directory name."""
    if not name:
        raise ProjectConfigError("o nome não pode ser vazio.")

    if len(name) > _MAX_PROJECT_NAME_LENGTH:
        raise ProjectConfigError(
            f"o nome deve ter no máximo {_MAX_PROJECT_NAME_LENGTH} caracteres."
        )

    if not _PROJECT_NAME_PATTERN.fullmatch(name):
        raise ProjectConfigError(
            "use apenas letras, números, hífen e sublinhado, começando por "
            "letra ou número."
        )

    if name.upper() in _WINDOWS_RESERVED_NAMES:
        raise ProjectConfigError("esse nome é reservado pelo sistema operacional.")


def validate_project_components(config: ProjectConfig) -> None:
    """Ensure that only choices relevant to the project type are populated."""
    expects_frontend = config.project_type in PROJECT_TYPES_WITH_FRONTEND
    if expects_frontend and config.frontend is None:
        raise ProjectConfigError(f"{config.project_type} exige um frontend.")
    if not expects_frontend and config.frontend is not None:
        raise ProjectConfigError(f"{config.project_type} não aceita frontend.")

    allowed_backends = BACKENDS_BY_PROJECT_TYPE[config.project_type]
    if allowed_backends and config.backend not in allowed_backends:
        raise ProjectConfigError(
            f"{config.project_type} exige um destes backends: "
            f"{', '.join(allowed_backends)}."
        )
    if not allowed_backends and config.backend is not None:
        raise ProjectConfigError(f"{config.project_type} não aceita backend.")

    if config.backend is None and config.database is not Database.NONE:
        raise ProjectConfigError("banco de dados exige um backend.")

    _validate_migrations(config)

    if config.frontend is Frontend.ANGULAR:
        _validate_angular_name(config.name)


def _validate_migrations(config: ProjectConfig) -> None:
    if config.migrations is MigrationStrategy.NONE:
        return

    if config.database is Database.NONE:
        raise ProjectConfigError("migrations exigem um banco de dados.")

    supported = MIGRATIONS_BY_BACKEND.get(config.backend, ()) if config.backend else ()
    if config.migrations not in supported:
        raise ProjectConfigError(
            f"{config.migrations} não é suportado com {config.backend}."
        )


def _validate_angular_name(name: str) -> None:
    if not _ANGULAR_NAME_PATTERN.fullmatch(name):
        raise ProjectConfigError(
            "Angular exige nomes formados por palavras separadas por hífen, "
            "cada uma começando por letra (ex.: portal-rh)."
        )
