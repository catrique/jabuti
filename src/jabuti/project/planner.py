"""Plan where each component of a project lives."""

from dataclasses import dataclass, replace
from pathlib import Path

from jabuti.project.config import (
    Database,
    Framework,
    MigrationStrategy,
    ProjectConfig,
    Topology,
    validate_project_name,
)
from jabuti.project.stacks import Stack, stack_for

ROOT_DIRECTORY = "."
FRONTEND_DIRECTORY = "frontend"
BACKEND_DIRECTORY = "backend"


@dataclass(frozen=True, slots=True)
class ComponentPlan:
    """One application inside the repository."""

    project_name: str
    framework: Framework
    directory: str
    serves_frontend: bool
    database: Database
    migrations: MigrationStrategy
    api_base_url: str | None = None
    """Frontend only: local URL of the backend of the same repository."""
    frontend_origin: str | None = None
    """Backend only: local origin of the frontend allowed to call it."""

    @property
    def stack(self) -> Stack:
        """Runtime and commands of the component."""
        return stack_for(self.framework, self.serves_frontend)


@dataclass(frozen=True, slots=True)
class ProjectPlan:
    """Repository layout calculated for a project."""

    config: ProjectConfig
    components: tuple[ComponentPlan, ...]

    @property
    def root(self) -> str:
        """Repository directory name."""
        return self.config.name

    @property
    def directories(self) -> tuple[str, ...]:
        """Subdirectories that hold components."""
        return tuple(
            component.directory
            for component in self.components
            if component.directory != ROOT_DIRECTORY
        )


class ProjectTargetExistsError(FileExistsError):
    """Raised when the project destination already exists."""


def plan_project(config: ProjectConfig) -> ProjectPlan:
    """Calculate the project layout without touching the filesystem."""
    if config.topology is Topology.SEPARATED:
        frontend = _plan_frontend(config, FRONTEND_DIRECTORY)
        backend = _plan_backend(config, BACKEND_DIRECTORY)
        components = (
            replace(frontend, api_base_url=backend.stack.dev_url),
            replace(backend, frontend_origin=frontend.stack.dev_url),
        )
    elif config.frontend is not None:
        components = (_plan_frontend(config, ROOT_DIRECTORY),)
    else:
        components = (_plan_backend(config, ROOT_DIRECTORY),)

    return ProjectPlan(config=config, components=components)


def component_directory(component: ComponentPlan, project_root: Path) -> Path:
    """Resolve where a planned component is generated."""
    return project_root / component.directory


def create_project_structure(
    plan: ProjectPlan,
    base_directory: Path | None = None,
) -> Path:
    """Create only the directories described by a project plan."""
    validate_project_name(plan.root)
    base = Path.cwd() if base_directory is None else base_directory
    target = base.resolve() / plan.root

    try:
        target.mkdir(exist_ok=False)
    except FileExistsError:
        raise ProjectTargetExistsError(
            f"O destino '{plan.root}' já existe. Nenhum arquivo foi alterado."
        ) from None

    for directory in plan.directories:
        (target / directory).mkdir()

    return target


def _plan_frontend(config: ProjectConfig, directory: str) -> ComponentPlan:
    frontend = config.frontend
    assert frontend is not None
    return ComponentPlan(
        project_name=config.name,
        framework=frontend,
        directory=directory,
        serves_frontend=False,
        database=Database.NONE,
        migrations=MigrationStrategy.NONE,
    )


def _plan_backend(config: ProjectConfig, directory: str) -> ComponentPlan:
    backend = config.backend
    assert backend is not None
    return ComponentPlan(
        project_name=config.name,
        framework=backend,
        directory=directory,
        serves_frontend=config.topology is Topology.BACKEND_SERVES_FRONTEND,
        database=config.database,
        migrations=config.migrations,
    )
