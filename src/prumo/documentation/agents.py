"""AGENTS.md generated from the project plan."""

from prumo.deployment.model import DEPLOY_ROOT
from prumo.documentation.markdown import (
    architecture_description,
    bullets,
    code_block,
    command_lines,
    component_title,
    database_components,
    deployment_lines,
    environment_components,
    location,
    migration_commands,
    migration_components,
    section,
    technology_lines,
)
from prumo.project.config import MigrationStrategy, Topology
from prumo.project.planner import ProjectPlan

_DEVELOPMENT_RULES = (
    "Preserve the existing architecture.",
    "Avoid unnecessary abstractions.",
    "Keep responsibilities separated and functions small.",
    "Never hardcode credentials or environment-specific URLs.",
    "Never commit `.env` files; keep `.env.example` up to date instead.",
    "Update tests when behavior changes.",
    "Run the relevant lint, build and tests before finishing a change.",
    "Do not change deployment paths casually. If they change, review the "
    "workflows and the documentation together.",
)

_GIT_RULES = (
    "Review all changes (`git diff`, `git status`) before committing.",
    "Write clear, objective commit messages.",
    "Never execute `git push` automatically.",
)


def render_agents(plan: ProjectPlan) -> str:
    """Instructions for coding agents that know this specific project."""
    sections = [
        _architecture(plan),
        _structure(plan),
        _commands(plan),
        _environment(plan),
        _database(plan),
        _migrations(plan),
        _deployment(plan),
        section("Development rules", bullets(_DEVELOPMENT_RULES)),
        section("Git rules", bullets(_GIT_RULES)),
    ]
    content = [section for section in sections if section]
    return "# Project instructions\n\n" + "\n\n".join(content) + "\n"


def _architecture(plan: ProjectPlan) -> str:
    return section(
        "Architecture",
        "This project uses:",
        bullets(technology_lines(plan)),
        architecture_description(plan),
    )


def _structure(plan: ProjectPlan) -> str:
    if plan.config.topology is Topology.SEPARATED:
        return section(
            "Repository structure",
            code_block((f"{d}/" for d in plan.directories), language="text"),
            "Frontend and backend are independent applications.",
            "Do not mix frontend code into backend or backend code into frontend.",
        )

    directories = plan.components[0].stack.source_directories
    return section(
        "Repository structure",
        code_block(directories, language="text"),
        f"Keep application code inside {', '.join(f'`{d}`' for d in directories)}.",
    )


def _commands(plan: ProjectPlan) -> str:
    if len(plan.components) == 1:
        commands = command_lines(plan.components[0])
        return section("Development commands", code_block(commands))

    blocks = [
        section(component_title(c), code_block(command_lines(c)), level=3)
        for c in plan.components
    ]
    return section("Development commands", *blocks)


def _environment(plan: ProjectPlan) -> str | None:
    if not environment_components(plan.components):
        return None

    return section(
        "Environment variables",
        "Copy `.env.example` to `.env` in the application directory and fill in "
        "local values. `.env` is ignored by Git and must never be committed.",
        "Never hardcode secrets. Production values live only on the server.",
    )


def _database(plan: ProjectPlan) -> str | None:
    components = database_components(plan.components)
    if not components:
        return None

    backend = components[0]
    paragraphs = [
        f"The backend ({location(backend)}) uses {backend.database}. Connection "
        "settings come from `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` and "
        "`DB_PASSWORD`.",
        "Database credentials must come from environment variables. Never "
        "hardcode database credentials.",
    ]
    if plan.config.topology is Topology.SEPARATED:
        paragraphs.append(
            "Only the backend talks to the database. The frontend must never "
            "connect to it directly nor hold database settings."
        )
    return section("Database", *paragraphs)


def _migrations(plan: ProjectPlan) -> str | None:
    components = migration_components(plan.components)
    if not components:
        return None

    component = components[0]
    mechanism = (
        "Alembic" if component.migrations is MigrationStrategy.ALEMBIC
        else "`npm run migrar`"
    )
    workflow = component.deployment.migrations_workflow
    return section(
        "Migrations",
        f"{mechanism} is the only supported mechanism for schema changes.",
        code_block(migration_commands(component)),
        "Do not modify the production schema manually. Review migrations before "
        "applying them.",
        f"Migrations never run on push. In production they are applied only by "
        f"the manual `{workflow}` workflow, in `{component.deployment.server_path}`.",
    )


def _deployment(plan: ProjectPlan) -> str:
    blocks = [
        section(component_title(c), bullets(deployment_lines(c.deployment)), level=3)
        for c in plan.components
    ]
    intro = (
        "Deployment uses GitHub Actions on a self-hosted Linux X64 runner. "
        f"Applications are published under `{DEPLOY_ROOT}`."
    )
    paragraphs = [intro, *blocks]
    if plan.config.topology is Topology.SEPARATED:
        frontend, backend = plan.components
        paragraphs.append(
            f"Frontend server application: `{frontend.deployment.app_name}`. "
            f"Backend server application: `{backend.deployment.app_name}`. "
            "Each one has its own deploy workflow."
        )
    return section("Deployment", *paragraphs)
