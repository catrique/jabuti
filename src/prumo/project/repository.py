"""Repository-level files written after every component was generated."""

from pathlib import Path

from prumo.deployment.checks import verify_deployment_source
from prumo.deployment.workflows import render_workflows
from prumo.documentation.agents import render_agents
from prumo.documentation.readme import render_readme
from prumo.project.gitignore import write_gitignore
from prumo.project.planner import WORKFLOWS_DIRECTORY, ProjectPlan
from prumo.rendering import write_text_file


def write_repository_files(plan: ProjectPlan, project_root: Path) -> None:
    """Verify sources, then write workflows, .gitignore, README and AGENTS."""
    targets = [component.deployment for component in plan.components]
    for target in targets:
        verify_deployment_source(project_root, target)

    files: dict[Path, str] = {}
    for target in targets:
        for name, content in render_workflows(target).items():
            files[WORKFLOWS_DIRECTORY / name] = content
    files[Path("README.md")] = render_readme(plan)
    files[Path("AGENTS.md")] = render_agents(plan)

    for relative_path, content in files.items():
        write_text_file(project_root / relative_path, content)
    write_gitignore(project_root, plan)
