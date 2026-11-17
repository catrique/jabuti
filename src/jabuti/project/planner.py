"""Plan where each component lives and how it is published."""

from dataclasses import dataclass
from pathlib import Path

from jabuti.deployment.model import (
    DeploymentScope,
    DeploymentTarget,
    WorkflowTechnology,
    separated_backend_app_name,
)
from jabuti.project.config import (
    Database,
    Framework,
    Frontend,
    MigrationStrategy,
    ProjectConfig,
    Topology,
    validate_project_name,
)
from jabuti.project.stacks import Stack, stack_for

ROOT_DIRECTORY = "."
WORKFLOWS_DIRECTORY = Path(".github", "workflows")


@dataclass(frozen=True, slots=True)
class ComponentPlan:
    """One application inside the repository."""

    project_name: str
    framework: Framework
    directory: str
    serves_frontend: bool
    database: Database
    migrations: MigrationStrategy
    deployment: DeploymentTarget

    @property
    def stack(self) -> Stack:
        """Runtime and commands of the component."""
        return stack_for(self.framework, self.serves_frontend)


@dataclass(frozen=True, slots=True)
class ProjectPlan:
    """Repository layout and deployments calculated for a project."""

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
        components = (
            _plan_frontend(config, DeploymentScope.FRONTEND),
            _plan_backend(config, DeploymentScope.BACKEND),
        )
    elif config.frontend is not None:
        components = (_plan_frontend(config),)
    else:
        components = (_plan_backend(config),)

    return ProjectPlan(config=config, components=components)


def angular_output_directory(project_name: str) -> str:
    """Build output of an Angular project, relative to its directory."""
    return f"dist/{project_name}/browser"


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


def _plan_frontend(
    config: ProjectConfig,
    scope: DeploymentScope | None = None,
) -> ComponentPlan:
    frontend = config.frontend
    assert frontend is not None
    directory = scope.value if scope else ROOT_DIRECTORY
    technology = stack_for(frontend).technology
    output = (
        angular_output_directory(config.name)
        if frontend is Frontend.ANGULAR
        else None
    )
    deployment = DeploymentTarget(
        app_name=config.name,
        source=directory,
        technology=technology,
        scope=scope,
        angular_output=output,
    )
    return ComponentPlan(
        project_name=config.name,
        framework=frontend,
        directory=directory,
        serves_frontend=False,
        database=Database.NONE,
        migrations=MigrationStrategy.NONE,
        deployment=deployment,
    )


def _plan_backend(
    config: ProjectConfig,
    scope: DeploymentScope | None = None,
) -> ComponentPlan:
    backend = config.backend
    assert backend is not None
    directory = scope.value if scope else ROOT_DIRECTORY
    app_name = separated_backend_app_name(config.name) if scope else config.name
    serves_frontend = config.topology is Topology.BACKEND_SERVES_FRONTEND
    technology: WorkflowTechnology = stack_for(backend).technology
    deployment = DeploymentTarget(
        app_name=app_name,
        source=directory,
        technology=technology,
        scope=scope,
        migrations=config.migrations,
    )
    return ComponentPlan(
        project_name=config.name,
        framework=backend,
        directory=directory,
        serves_frontend=serves_frontend,
        database=config.database,
        migrations=config.migrations,
        deployment=deployment,
    )
