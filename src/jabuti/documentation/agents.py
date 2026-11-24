"""AGENTS.md generated from the project plan."""

from jabuti.documentation.architecture import (
    BACKEND_RULES,
    CQRS_SUMMARY,
    FRONTEND_RULES,
    GENERAL_RULES,
    architecture_guide,
    is_frontend,
)
from jabuti.documentation.markdown import (
    architecture_description,
    bullets,
    code_block,
    command_lines,
    component_title,
    database_components,
    environment_components,
    location,
    migration_commands,
    migration_components,
    numbered,
    python_environment_setup,
    section,
    technology_lines,
)
from jabuti.project.config import Topology
from jabuti.project.planner import ProjectPlan
from jabuti.project.stacks import Runtime

_DEVELOPMENT_RULES = (
    "Preserve the existing architecture.",
    *GENERAL_RULES,
    "Keep responsibilities separated and functions small.",
    "Never hardcode credentials or environment-specific URLs.",
    "Never commit `.env` files; keep `.env.example` up to date instead.",
    "Update tests when behavior changes.",
    "Run the relevant lint, build and tests before finishing a change.",
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
        _cqrs(plan),
        _layer_rules("Backend rules", BACKEND_RULES, _has_backend(plan)),
        _layer_rules("Frontend rules", FRONTEND_RULES, _has_frontend(plan)),
        _commands(plan),
        _environment(plan),
        _database(plan),
        _migrations(plan),
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


def _cqrs(plan: ProjectPlan) -> str:
    blocks = []
    for component in plan.components:
        guide = architecture_guide(component)
        steps = numbered(guide.new_feature)
        content = (
            code_block(guide.layout, language="text"),
            bullets(guide.rules),
            "Adding a feature:",
            steps,
        )
        if len(plan.components) == 1:
            blocks.extend(content)
        else:
            blocks.append(section(component_title(component), *content, level=3))
    return section("Lightweight CQRS", CQRS_SUMMARY, *blocks)


def _layer_rules(title: str, rules: tuple[str, ...], applies: bool) -> str | None:
    return section(title, bullets(rules)) if applies else None


def _has_backend(plan: ProjectPlan) -> bool:
    return any(not is_frontend(c.framework) for c in plan.components)


def _has_frontend(plan: ProjectPlan) -> bool:
    return any(is_frontend(c.framework) for c in plan.components)


def _commands(plan: ProjectPlan) -> str:
    if len(plan.components) == 1:
        component = plan.components[0]
        blocks = []
        if component.stack.runtime is Runtime.PYTHON:
            blocks.append(python_environment_setup(component))
        blocks.append(code_block(command_lines(component)))
        return section("Development commands", *blocks)

    blocks = []
    for component in plan.components:
        component_blocks = []
        if component.stack.runtime is Runtime.PYTHON:
            component_blocks.append(python_environment_setup(component))
        component_blocks.append(code_block(command_lines(component)))
        blocks.append(section(component_title(component), *component_blocks, level=3))
    return section("Development commands", *blocks)


def _environment(plan: ProjectPlan) -> str | None:
    if not environment_components(plan.components):
        return None

    return section(
        "Environment variables",
        "Copy `.env.example` to `.env` in the application directory and fill in "
        "local values. `.env` is ignored by Git and must never be committed.",
        "Never hardcode secrets.",
        *_cors_note(plan),
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
    return section(
        "Migrations",
        "Alembic is the supported mechanism for schema changes.",
        code_block(migration_commands(component)),
        "Do not modify the production schema manually. Review migrations before "
        "applying them.",
        "Migrations never run automatically; apply them manually.",
    )



def _cors_note(plan: ProjectPlan) -> list[str]:
    if plan.config.topology is not Topology.SEPARATED:
        return []
    frontend, backend = plan.components
    return [
        f"The frontend calls the backend at `{frontend.api_base_url}` during "
        f"development; the backend accepts browser calls only from "
        f"`FRONTEND_ORIGINS` (default `{backend.frontend_origin}`). Configure "
        "both for every other environment."
    ]
