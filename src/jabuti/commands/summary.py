"""Summary shown before a project is created."""

from jabuti.documentation.readme import structure_lines
from jabuti.project.config import Database, ProjectType, Topology
from jabuti.project.planner import ProjectPlan

_LABEL_WIDTH = 18
_STACK_FIELDS = {
    ProjectType.FRONTEND: (("Framework", "frontend"),),
    ProjectType.API: (("Backend", "backend"),),
    ProjectType.FULLSTACK: (("Frontend", "frontend"), ("Backend", "backend")),
    ProjectType.WEB_APP: (("Framework", "backend"),),
}


def summary_lines(plan: ProjectPlan) -> list[str]:
    """Only the choices relevant to the plan, followed by the structure."""
    fields = [
        f"{label + ':':<{_LABEL_WIDTH}}{value}" for label, value in _fields(plan)
    ]
    return [
        "Projeto",
        "-" * 32,
        "",
        *fields,
        "",
        "Estrutura:",
        "",
        *structure_lines(plan),
    ]


def _fields(plan: ProjectPlan) -> list[tuple[str, str]]:
    config = plan.config
    fields = [("Nome", config.name), ("Tipo", config.project_type.value)]
    fields.extend(
        (label, str(getattr(config, attribute)))
        for label, attribute in _STACK_FIELDS[config.project_type]
    )
    if config.topology is not Topology.STANDALONE:
        fields.append(("Arquitetura", config.topology.value))
    if config.backend is not None:
        fields.append(("Banco", config.database.value))
    if config.database is not Database.NONE:
        fields.append(("Migrations", config.migrations.value))
    return fields
