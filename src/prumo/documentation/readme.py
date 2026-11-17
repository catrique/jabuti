"""README.md generated from the project plan."""

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
from prumo.project.config import Topology
from prumo.project.planner import WORKFLOWS_DIRECTORY, ProjectPlan
from prumo.project.stacks import Runtime


def render_readme(plan: ProjectPlan) -> str:
    """Short README describing stack, structure, commands and deployment."""
    sections = [
        f"# {plan.root}",
        f"{plan.config.project_type} project created with Prumo.",
        section("Stack", bullets(technology_lines(plan))),
        section("Architecture", architecture_description(plan)),
        section("Structure", code_block(structure_lines(plan), language="text")),
        _running(plan),
        _environment(plan),
        _migrations(plan),
        _deployment(plan),
    ]
    return "\n\n".join(section for section in sections if section) + "\n"


def structure_lines(plan: ProjectPlan) -> list[str]:
    """Top-level entries of the generated repository."""
    if plan.config.topology is Topology.SEPARATED:
        directories = [f"{directory}/" for directory in plan.directories]
    else:
        directories = list(plan.components[0].stack.source_directories)

    return [
        f"{plan.root}/",
        *(f"  {entry}" for entry in directories),
        f"  {WORKFLOWS_DIRECTORY.as_posix()}/",
        "  AGENTS.md",
        "  README.md",
    ]


def _running(plan: ProjectPlan) -> str:
    if len(plan.components) == 1:
        blocks = [code_block(command_lines(plan.components[0]))]
    else:
        blocks = [
            section(component_title(c), code_block(command_lines(c)), level=3)
            for c in plan.components
        ]

    if any(c.stack.runtime is Runtime.PYTHON for c in plan.components):
        blocks.append(
            "On Windows, use `.venv\\Scripts\\python` instead of `.venv/bin/python`."
        )
    return section("Running locally", *blocks)


def _environment(plan: ProjectPlan) -> str | None:
    components = environment_components(plan.components)
    if not components:
        return None

    paragraphs = [
        f"Copy `.env.example` to `.env` in the {location(c)} and fill in the values."
        for c in components
    ]
    if database_components(components):
        paragraphs.append(
            "The database (MySQL) must already exist; Prumo never creates "
            "databases, users or passwords."
        )
    return section("Environment and database", *paragraphs)


def _migrations(plan: ProjectPlan) -> str | None:
    components = migration_components(plan.components)
    if not components:
        return None

    component = components[0]
    return section(
        "Migrations",
        code_block(migration_commands(component)),
        f"In production, run the `{component.deployment.migrations_workflow}` "
        "workflow manually. Migrations never run on push.",
    )


def _deployment(plan: ProjectPlan) -> str:
    blocks = [
        section(component_title(c), bullets(deployment_lines(c.deployment)), level=3)
        for c in plan.components
    ]
    paragraphs = ["GitHub Actions on a self-hosted Linux X64 runner.", *blocks]
    if plan.config.topology is Topology.SEPARATED:
        frontend, backend = plan.components
        paragraphs.append(
            f"Frontend server name: `{frontend.deployment.app_name}`  \n"
            f"Backend server name: `{backend.deployment.app_name}`"
        )
    return section("Deployment", *paragraphs)
