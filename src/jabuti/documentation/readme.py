"""README.md generated from the project plan."""

from jabuti.documentation.architecture import CQRS_SUMMARY, architecture_guide
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
    section,
    technology_lines,
)
from jabuti.project.config import Frontend, Topology
from jabuti.project.planner import ROOT_DIRECTORY, ComponentPlan, ProjectPlan
from jabuti.project.stacks import Runtime


def render_readme(plan: ProjectPlan) -> str:
    """Short README describing stack, structure and local commands."""
    sections = [
        f"# {plan.root}",
        f"{plan.config.project_type} project created with Jabuti.",
        section("Stack", bullets(technology_lines(plan))),
        _architecture(plan),
        section("Structure", code_block(structure_lines(plan), language="text")),
        _running(plan),
        _environment(plan),
        _migrations(plan),
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
        "  AGENTS.md",
        "  README.md",
    ]


def _architecture(plan: ProjectPlan) -> str:
    blocks = []
    for component in plan.components:
        layout = code_block(architecture_guide(component).layout, language="text")
        if len(plan.components) == 1:
            blocks.append(layout)
        else:
            blocks.append(section(component_title(component), layout, level=3))
    return section(
        "Architecture",
        architecture_description(plan),
        CQRS_SUMMARY,
        *blocks,
        "`AGENTS.md` describes the rules for growing the project.",
    )


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
    paragraphs = [
        f"Copy `.env.example` to `.env` in the {location(c)} and fill in the values."
        for c in components
    ]
    paragraphs.extend(_api_configuration(plan))
    if database_components(components):
        paragraphs.append(
            "The database (MySQL) must already exist; Jabuti never creates "
            "databases, users or passwords."
        )
    return section("Configuration", *paragraphs) if paragraphs else None


def _api_configuration(plan: ProjectPlan) -> list[str]:
    """Where the frontend API URL and the allowed browser origins are set."""
    notes = []
    for component in plan.components:
        if component.framework is Frontend.REACT:
            notes.append(
                "Frontend API base URL: `VITE_API_BASE_URL` (empty means same "
                "origin)."
            )
        elif component.framework is Frontend.ANGULAR:
            notes.append(
                "Frontend API base URL: `apiBaseUrl` in "
                f"{_in(component, 'src/environments/')} "
                "(`environment.development.ts` for `ng serve`)."
            )
        elif not component.serves_frontend:
            default = (
                f"default `{component.frontend_origin}`"
                if component.frontend_origin
                else "none allowed by default"
            )
            notes.append(
                "Browser origins allowed to call the API: environment variable "
                f"`FRONTEND_ORIGINS` (comma-separated, {default})."
            )
    return notes


def _in(component: ComponentPlan, path: str) -> str:
    if component.directory == ROOT_DIRECTORY:
        return f"`{path}`"
    return f"`{component.directory}/{path}`"


def _migrations(plan: ProjectPlan) -> str | None:
    components = migration_components(plan.components)
    if not components:
        return None

    component = components[0]
    return section(
        "Migrations",
        code_block(migration_commands(component)),
        "Migrations never run automatically; apply them manually.",
    )

