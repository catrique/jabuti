"""Markdown fragments shared by the generated AGENTS.md and README.md."""

from collections.abc import Iterable

from jabuti.deployment.model import DeploymentTarget
from jabuti.project.config import Backend, Database, MigrationStrategy, ProjectType
from jabuti.project.planner import (
    ROOT_DIRECTORY,
    WORKFLOWS_DIRECTORY,
    ComponentPlan,
    ProjectPlan,
)

_ARCHITECTURE = {
    ProjectType.FRONTEND: "The application is frontend-only. It has no backend "
    "or database access.",
    ProjectType.API: "The application is a standalone API.",
    ProjectType.FULLSTACK: "Frontend and backend are independent applications "
    "in the same repository, built and deployed separately.",
    ProjectType.WEB_APP: "The application is a single server-side web app: the "
    "backend renders the HTML templates and serves the static files.",
}

ALEMBIC_REVISION ='.venv/bin/python -m alembic revision --autogenerate -m "descricao"'
ALEMBIC_UPGRADE = ".venv/bin/python -m alembic upgrade head"
NODE_MIGRATION = "npm run migrar"


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
    commands = [*stack.setup_commands, stack.run_command, *stack.check_commands]
    return _from_root(component, commands)


def migration_commands(component: ComponentPlan) -> list[str]:
    """Local commands to create and apply migrations."""
    if component.migrations is MigrationStrategy.ALEMBIC:
        return _from_root(component, [ALEMBIC_REVISION, ALEMBIC_UPGRADE])
    if component.migrations is MigrationStrategy.NPM_SCRIPT:
        return _from_root(component, [NODE_MIGRATION])
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
    """Components generated with a .env.example (Express always has PORT)."""
    return [
        c
        for c in components
        if c.framework is Backend.EXPRESS or c.database is not Database.NONE
    ]


def migration_components(components: Iterable[ComponentPlan]) -> list[ComponentPlan]:
    """Components with a migration mechanism."""
    return [c for c in components if c.migrations is not MigrationStrategy.NONE]


DEPLOY_VARIABLES_LOCATION = (
    "**Settings → Secrets and variables → Actions → Variables**"
)
DEPLOY_VARIABLES = (
    (
        "DEPLOY_ROOT",
        "Required. Base directory where the applications are published on the "
        "server. It must be an existing absolute path; the workflows fail "
        "without it and never fall back to a default.",
    ),
    (
        "DEPLOY_USER",
        "Optional. User that owns the PM2 processes. Leave it empty when the "
        "runner already runs as the correct user.",
    ),
)


def deploy_variable_lines() -> list[str]:
    """GitHub Actions Variables read by the generated workflows."""
    return [f"`{name}`: {description}" for name, description in DEPLOY_VARIABLES]


def deployment_lines(target: DeploymentTarget) -> list[str]:
    """Workflow variables and server destination of a deployment target."""
    lines = [
        f"Workflow: `{(WORKFLOWS_DIRECTORY / target.deploy_workflow).as_posix()}`",
        f"APP: `{target.app_name}`",
        f"SRC: `{target.source}`",
        f"TIPO: `{target.technology}`",
    ]
    if target.angular_output:
        lines.append(f"OUT: `{target.angular_output}`")
    lines.append(f"Server path: `{target.server_path}`")
    if target.migrations_workflow:
        workflow = (WORKFLOWS_DIRECTORY / target.migrations_workflow).as_posix()
        lines.append(f"Migrations: `{workflow}` (manual, workflow_dispatch)")
    return lines
